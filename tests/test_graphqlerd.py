import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "skills", "drawio-skill", "scripts", "graphqlerd.py")
DIAGRAMCTL = os.path.join(ROOT, "skills", "drawio-skill", "scripts", "diagramctl.py")
sys.path.insert(0, os.path.dirname(DIAGRAMCTL))


def load_bundled(name):
    """Load a bundled script by path (the scripts directory is not a package)."""
    path = os.path.join(os.path.dirname(DIAGRAMCTL), name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


diagramctl = load_bundled("diagramctl")


def load_importer():
    spec = importlib.util.spec_from_file_location("graphqlerd", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCHEMA = textwrap.dedent(
    '''
    """The node interface."""
    interface Node {
      id: ID!
    }

    """
    A description block whose text is not schema:
    type Ghost {
      boo: String
    }
    """
    # type Phantom { boo: String }
    type Product implements Node & Timestamped @key(fields: "id") {
      id: ID!
      name: String!
      price: Money!
      status: Status
      reviews(first: Int = 10, after: String): [Review!]!
      legacyCode: String @deprecated(reason: "use sku")
    }

    type Review implements Node {
      id: ID!
      author: User
    }

    interface Timestamped {
      createdAt: DateTime!
    }

    type User implements Node {
      id: ID!
      email: String!
    }

    input ProductFilter {
      status: Status
      minPrice: Money
    }

    enum Status {
      DRAFT
      PUBLISHED
      ARCHIVED @deprecated
    }

    union SearchResult = Product | Review | User

    scalar DateTime
    scalar Money
    '''
)


class TestGraphqlErdParsing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.importer = load_importer()
        cls.defs = cls.importer.parse_sdl(SCHEMA, file_path="catalog.graphql")
        cls.by_name = {d["name"]: d for d in cls.defs}

    def test_every_definition_kind_is_recognised(self):
        kinds = {}
        for d in self.defs:
            kinds.setdefault(d["kind"], []).append(d["name"])
        self.assertEqual(sorted(kinds["type"]), ["Product", "Review", "User"])
        self.assertEqual(sorted(kinds["interface"]), ["Node", "Timestamped"])
        self.assertEqual(kinds["input"], ["ProductFilter"])
        self.assertEqual(kinds["enum"], ["Status"])
        self.assertEqual(kinds["union"], ["SearchResult"])
        self.assertEqual(sorted(kinds["scalar"]), ["DateTime", "Money"])

    def test_a_definition_inside_a_description_or_comment_is_not_parsed(self):
        # Both decoys start at the beginning of their line, so the definition
        # scan would match them if strip_ignored had not blanked the block
        # string and the comment first.
        self.assertNotIn("Ghost", self.by_name)
        self.assertNotIn("Phantom", self.by_name)

    def test_field_arguments_are_stripped_from_the_type(self):
        fields = dict((f[0], f[1]) for f in self.by_name["Product"]["fields"])
        self.assertEqual(fields["reviews"], "[Review!]!")

    def test_list_and_non_null_wrappers_reduce_to_the_base_type(self):
        self.assertEqual(self.importer.base_type("[Review!]!"), "Review")
        self.assertEqual(self.importer.base_type("String"), "String")

    def test_deprecated_is_marked_on_fields_and_enum_values(self):
        fields = dict((f[0], f[2]) for f in self.by_name["Product"]["fields"])
        self.assertTrue(fields["legacyCode"])
        self.assertFalse(fields["name"])
        values = dict((f[0], f[2]) for f in self.by_name["Status"]["fields"])
        self.assertTrue(values["ARCHIVED"])
        self.assertFalse(values["DRAFT"])

    def test_multiple_interfaces_are_captured(self):
        self.assertEqual(self.by_name["Product"]["implements"], ["Node", "Timestamped"])

    def test_union_members_are_captured(self):
        self.assertEqual(
            self.by_name["SearchResult"]["members"], ["Product", "Review", "User"]
        )

    def test_enum_values_are_read_as_values_not_fields(self):
        self.assertEqual(
            [f[0] for f in self.by_name["Status"]["fields"]],
            ["DRAFT", "PUBLISHED", "ARCHIVED"],
        )

    def test_line_numbers_survive_comment_stripping(self):
        # strip_ignored replaces ignored text with spaces rather than deleting
        # it, so a provenance line still points at the real source line.
        lines = SCHEMA.splitlines()
        for name in ("Product", "Status", "SearchResult"):
            line = self.by_name[name]["line"]
            self.assertIn(name, lines[line - 1])


class TestGraphqlErdGraph(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.importer = load_importer()
        defs = cls.importer.parse_sdl(SCHEMA, file_path="catalog.graphql")
        cls.graph = cls.importer.build(defs)
        cls.edges = set(
            (e["source"], e["target"], e["label"]) for e in cls.graph["edges"]
        )

    def test_implements_produces_an_edge(self):
        self.assertIn(("Product", "Node", "implements"), self.edges)
        self.assertIn(("Product", "Timestamped", "implements"), self.edges)

    def test_field_reference_produces_an_edge_labelled_with_the_field(self):
        self.assertIn(("Product", "Review", "reviews"), self.edges)
        self.assertIn(("Review", "User", "author"), self.edges)

    def test_union_membership_produces_an_edge(self):
        self.assertIn(("SearchResult", "Product", ""), self.edges)

    def test_builtin_scalars_never_become_nodes_or_edges(self):
        ids = set(n["id"] for n in self.graph["nodes"])
        self.assertFalse(ids & {"ID", "String", "Int", "Float", "Boolean"})
        targets = set(t for _, t, _ in self.edges)
        self.assertFalse(targets & {"ID", "String", "Int", "Float", "Boolean"})

    def test_custom_scalars_do_become_nodes_and_are_dimmed(self):
        by_id = dict((n["id"], n) for n in self.graph["nodes"])
        self.assertIn("Money", by_id)
        self.assertEqual(by_id["Money"]["style"], self.importer.LEAF_STYLE)
        self.assertIn(("Product", "Money", "price"), self.edges)

    def test_enum_nodes_are_dimmed_rather_than_unlinked(self):
        by_id = dict((n["id"], n) for n in self.graph["nodes"])
        self.assertEqual(by_id["Status"]["style"], self.importer.LEAF_STYLE)
        self.assertIn(("Product", "Status", "status"), self.edges)

    def test_every_node_carries_provenance(self):
        for node in self.graph["nodes"]:
            self.assertEqual(node["provenance"]["path"], "catalog.graphql")
            self.assertGreater(node["provenance"]["line"], 0)

    def test_labels_escape_html_metacharacters(self):
        defs = self.importer.parse_sdl("type A { f: B }\ntype B { g: String }")
        graph = self.importer.build(defs)
        for node in graph["nodes"]:
            self.assertNotIn("<", node["label"])

    def test_an_edge_to_an_unknown_type_is_dropped(self):
        defs = self.importer.parse_sdl("type A { missing: Nowhere }")
        self.assertEqual(self.importer.build(defs)["edges"], [])

    def test_no_types_hides_the_field_types(self):
        defs = self.importer.parse_sdl("type A { f: String }")
        graph = self.importer.build(defs, show_types=False)
        self.assertIn("\nf", graph["nodes"][0]["label"])
        self.assertNotIn("String", graph["nodes"][0]["label"])

    def test_extends_merge_into_a_single_node(self):
        defs = self.importer.parse_sdl(
            "type Foo { a: Int }\n"
            "extend type Foo { b: String @deprecated }\n"
            "interface Bar { c: ID! }\n"
            "extend interface Bar implements Foo { d: Foo }"
        )
        graph = self.importer.build(defs)
        self.assertEqual([n["id"] for n in graph["nodes"]], ["Foo", "Bar"])
        labels = dict((n["id"], n["label"]) for n in graph["nodes"])
        self.assertIn("a: Int", labels["Foo"])
        self.assertIn("b: String (deprecated)", labels["Foo"])
        self.assertIn(("Bar", "Foo", "implements"),
                      set((e["source"], e["target"], e["label"])
                          for e in graph["edges"]))

    def test_extends_merge_across_schema_files(self):
        base = self.importer.parse_sdl("union U = A | B\n", file_path="a.graphql")
        ext = self.importer.parse_sdl("extend union U = C\n", file_path="b.graphql")
        graph = self.importer.build(base + ext)
        self.assertEqual([n["id"] for n in graph["nodes"]], ["U"])
        members = [line for line in graph["nodes"][0]["label"].split("\n")
                   if line in ("A", "B", "C")]
        self.assertEqual(members, ["A", "B", "C"])


class TestGraphqlErdIntrospection(unittest.TestCase):
    PAYLOAD = {
        "data": {
            "__schema": {
                "types": [
                    {
                        "kind": "OBJECT",
                        "name": "Product",
                        "interfaces": [{"name": "Node"}],
                        "fields": [
                            {
                                "name": "reviews",
                                "type": {
                                    "kind": "LIST",
                                    "ofType": {"kind": "OBJECT", "name": "Review"},
                                },
                                "isDeprecated": False,
                            },
                            {
                                "name": "old",
                                "type": {"kind": "SCALAR", "name": "String"},
                                "isDeprecated": True,
                            },
                        ],
                    },
                    {"kind": "INTERFACE", "name": "Node", "fields": []},
                    {"kind": "OBJECT", "name": "Review", "fields": []},
                    {"kind": "OBJECT", "name": "__Type", "fields": []},
                ]
            }
        }
    }

    @classmethod
    def setUpClass(cls):
        cls.importer = load_importer()

    def test_introspection_types_map_to_the_same_definitions(self):
        defs = self.importer.parse_introspection(self.PAYLOAD, file_path="i.json")
        self.assertEqual(
            sorted((d["kind"], d["name"]) for d in defs),
            [("interface", "Node"), ("type", "Product"), ("type", "Review")],
        )

    def test_introspection_meta_types_are_skipped(self):
        defs = self.importer.parse_introspection(self.PAYLOAD)
        self.assertNotIn("__Type", [d["name"] for d in defs])

    def test_wrapped_types_are_rendered_back_to_sdl_notation(self):
        defs = self.importer.parse_introspection(self.PAYLOAD)
        product = [d for d in defs if d["name"] == "Product"][0]
        self.assertEqual(product["fields"][0][1], "[Review]")
        self.assertTrue(product["fields"][1][2])

    def test_builtin_scalars_from_an_introspection_dump_are_skipped(self):
        # A real dump always lists String/Int/ID/Boolean/Float as SCALAR types.
        # Keeping them would add five orphan nodes to every introspection run.
        payload = {
            "data": {
                "__schema": {
                    "types": [
                        {"kind": "SCALAR", "name": n}
                        for n in ("String", "Int", "ID", "Boolean", "Float", "DateTime")
                    ]
                }
            }
        }
        defs = self.importer.parse_introspection(payload)
        self.assertEqual([d["name"] for d in defs], ["DateTime"])

    def test_a_payload_without_a_schema_key_is_rejected(self):
        with self.assertRaises(ValueError):
            self.importer.parse_introspection({"data": {}})


class TestGraphqlErdCli(unittest.TestCase):
    def _run(self, *args):
        return subprocess.run(
            [sys.executable, SCRIPT] + list(args),
            capture_output=True,
            text=True,
            check=True,
        )

    def test_directory_scan_groups_by_source_file(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "catalog.graphql"), "w", encoding="utf-8") as fh:
                fh.write("type Product { id: ID! }\n")
            with open(os.path.join(d, "billing.gql"), "w", encoding="utf-8") as fh:
                fh.write("type Invoice { product: Product }\n")
            graph = json.loads(self._run(d, "--group").stdout)
        groups = dict((n["id"], n["group"]) for n in graph["nodes"])
        self.assertEqual(groups, {"Product": "catalog", "Invoice": "billing"})
        self.assertEqual(
            [(e["source"], e["target"]) for e in graph["edges"]], [("Invoice", "Product")]
        )

    def test_a_schema_with_no_definitions_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "empty.graphql")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("# nothing here\n")
            proc = subprocess.run(
                [sys.executable, SCRIPT, path], capture_output=True, text=True
            )
        self.assertNotEqual(proc.returncode, 0)

    def test_detect_source_recognises_a_graphql_directory(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "schema.graphql"), "w", encoding="utf-8") as fh:
                fh.write("type Query { ok: Boolean }\n")
            self.assertEqual("graphql", diagramctl.detect_source(d))


if __name__ == "__main__":
    unittest.main()
