import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "skills", "drawio-skill", "scripts", "protoimports.py")
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
    spec = importlib.util.spec_from_file_location("protoimports", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestProtoImports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.importer = load_importer()

    def test_services_messages_enums_and_edges(self):
        proto = """
        syntax = "proto3";
        package bookstore.v1;

        import "google/protobuf/timestamp.proto";
        option go_package = "example.com/bookstore/v1";

        enum Format {
          FORMAT_UNSPECIFIED = 0;
          FORMAT_HARDCOVER = 1;
          FORMAT_PAPERBACK = 2;
          FORMAT_EBOOK = 3;
        }

        message Author {
          string id = 1;
          string name = 2;
        }

        message Book {
          string isbn = 1;
          string title = 2;
          Author author = 3;
          Format format = 4;
          repeated string tags = 5;
        }

        message GetBookRequest {
          string isbn = 1;
        }

        message GetBookResponse {
          Book book = 1;
        }

        service BookstoreService {
          rpc GetBook (GetBookRequest) returns (GetBookResponse);
          rpc ListBooks (GetBookRequest) returns (stream Book);
        }
        """
        parsed = self.importer.parse_proto(proto, "bookstore.proto")
        graph = self.importer.build([parsed], group=True, direction="TB")
        by_id = {node["id"]: node for node in graph["nodes"]}
        pairs = {(edge["source"], edge["target"]) for edge in graph["edges"]}

        self.assertEqual(graph["direction"], "TB")
        self.assertIn("bookstore.v1.BookstoreService", by_id)
        self.assertIn("bookstore.v1.Book", by_id)
        self.assertIn("bookstore.v1.Author", by_id)
        self.assertIn("bookstore.v1.Format", by_id)

        # Service node has RPC methods
        srv_node = by_id["bookstore.v1.BookstoreService"]
        self.assertEqual(srv_node["group"], "bookstore.v1")
        self.assertIn("GetBook(GetBookRequest): GetBookResponse", srv_node["label"])
        self.assertIn("ListBooks(GetBookRequest): stream Book", srv_node["label"])

        # Service -> request/response edges
        self.assertIn(
            ("bookstore.v1.BookstoreService", "bookstore.v1.GetBookRequest"), pairs
        )
        self.assertIn(
            ("bookstore.v1.BookstoreService", "bookstore.v1.GetBookResponse"), pairs
        )
        self.assertIn(("bookstore.v1.BookstoreService", "bookstore.v1.Book"), pairs)

        # Message -> field type edges
        self.assertIn(("bookstore.v1.Book", "bookstore.v1.Author"), pairs)
        self.assertIn(("bookstore.v1.Book", "bookstore.v1.Format"), pairs)
        self.assertIn(("bookstore.v1.GetBookResponse", "bookstore.v1.Book"), pairs)

    def test_nested_messages_enums_and_maps(self):
        proto = """
        syntax = "proto3";
        package shop;

        message Cart {
          enum State {
            STATE_ACTIVE = 0;
            STATE_ABANDONED = 1;
          }
          message Item {
            string item_id = 1;
            int32 qty = 2;
          }
          string cart_id = 1;
          State state = 2;
          repeated Item items = 3;
          map<string, Item> item_map = 4;
        }
        """
        parsed = self.importer.parse_proto(proto, "shop.proto")
        graph = self.importer.build([parsed], group=False)
        by_id = {node["id"]: node for node in graph["nodes"]}
        pairs = {(edge["source"], edge["target"]) for edge in graph["edges"]}

        self.assertIn("shop.Cart", by_id)
        self.assertIn("shop.Cart.State", by_id)
        self.assertIn("shop.Cart.Item", by_id)

        self.assertIn(("shop.Cart", "shop.Cart.State"), pairs)
        self.assertIn(("shop.Cart", "shop.Cart.Item"), pairs)

    def test_nested_name_only_shadows_inside_its_parent(self):
        # A nested Cart.Item used to win every lookup of the short name `Item`,
        # so Order and the service pointed at Cart.Item, not the top-level Item.
        proto = """
        syntax = "proto3";
        package shop;

        message Item { string sku = 1; }
        enum Status { STATUS_OPEN = 0; }

        message Cart {
          message Item { int32 qty = 1; }
          enum Status { STATUS_ACTIVE = 0; }
          message Line { Item item = 1; }
          repeated Item lines = 1;
        }

        message Order {
          Item item = 1;
          Cart.Item cart_item = 2;
          Status status = 3;
        }

        service OrderService {
          rpc Get (Item) returns (Order);
        }
        """
        parsed = self.importer.parse_proto(proto, "shop.proto")
        graph = self.importer.build([parsed])
        targets = {}
        for edge in graph["edges"]:
            targets.setdefault((edge["source"], edge["label"]), set()).add(edge["target"])

        self.assertEqual({"shop.Item"}, targets[("shop.Order", "item")])
        self.assertEqual({"shop.Cart.Item"}, targets[("shop.Order", "cart_item")])
        self.assertEqual({"shop.Status"}, targets[("shop.Order", "status")])
        self.assertEqual({"shop.Item", "shop.Order"}, targets[("shop.OrderService", "Get")])
        # Inside Cart (and messages nested in it) the nested Item still wins.
        self.assertEqual({"shop.Cart.Item"}, targets[("shop.Cart", "lines")])
        self.assertEqual({"shop.Cart.Item"}, targets[("shop.Cart.Line", "item")])

    def test_comments_do_not_swallow_string_literals(self):
        # A "//" inside a string used to be stripped as a comment, which also
        # removed the brace that closed the message and dropped the rest of the
        # file (URLs in options/defaults are the realistic case).
        proto = '''
        syntax = "proto3";
        package demo;

        /* block comment */
        message Req { string url = 1 [default = "https://example.com/a"]; }
        message Resp { string ok = 1; }  // trailing comment
        service DemoService { rpc Get (Req) returns (Resp); }
        '''
        parsed = self.importer.parse_proto(proto, "demo.proto")
        self.assertEqual(["Req", "Resp"], [m["name"] for m in parsed["messages"]])
        self.assertEqual(["DemoService"], [s["name"] for s in parsed["services"]])
        # Line numbers stay accurate across the block and trailing comments.
        self.assertEqual([6, 7], [m["line"] for m in parsed["messages"]])

    def test_map_types_survive_html_label_rendering(self):
        proto = '''
        syntax = "proto3";
        package shop;
        message Cart { map<string, Item> items = 1; }
        message Item { string sku = 1; }
        '''
        parsed = self.importer.parse_proto(proto, "shop.proto")
        graph = self.importer.build([parsed])
        label = next(n for n in graph["nodes"] if n["id"] == "shop.Cart")["label"]
        self.assertIn("items: map&lt;string, Item&gt;", label)

    def test_directory_detection_keeps_project_language_markers(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "go.mod"), "w", encoding="utf-8") as f:
                f.write("module example.com/svc\n")
            with open(os.path.join(td, "svc.proto"), "w", encoding="utf-8") as f:
                f.write('syntax = "proto3";\nmessage A {}\n')
            self.assertEqual("go", diagramctl.detect_source(td))

        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "svc.proto"), "w", encoding="utf-8") as f:
                f.write('syntax = "proto3";\nmessage A {}\n')
            self.assertEqual("proto", diagramctl.detect_source(td))

    def test_cli_reads_file_and_directory(self):
        with tempfile.TemporaryDirectory() as td:
            p1 = os.path.join(td, "user.proto")
            with open(p1, "w", encoding="utf-8") as f:
                f.write("""
                syntax = "proto3";
                package users;
                message User { string id = 1; string name = 2; }
                """)

            p2 = os.path.join(td, "auth.proto")
            with open(p2, "w", encoding="utf-8") as f:
                f.write("""
                syntax = "proto3";
                package users;
                message AuthRequest { string username = 1; }
                service AuthService {
                  rpc Login (AuthRequest) returns (User);
                }
                """)

            # Run CLI on directory
            out_json = os.path.join(td, "graph.json")
            res = subprocess.run(
                [sys.executable, SCRIPT, td, "--group", "-o", out_json],
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertTrue(os.path.isfile(out_json))

            with open(out_json, encoding="utf-8") as f:
                graph = json.load(f)

            node_ids = {n["id"] for n in graph["nodes"]}
            self.assertIn("users.User", node_ids)
            self.assertIn("users.AuthRequest", node_ids)
            self.assertIn("users.AuthService", node_ids)

    def test_diagramctl_auto_detects_proto(self):
        with tempfile.TemporaryDirectory() as td:
            proto_file = os.path.join(td, "service.proto")
            with open(proto_file, "w", encoding="utf-8") as f:
                f.write("""
                syntax = "proto3";
                package test;
                message PingRequest {}
                message PingResponse {}
                service PingService {
                  rpc Ping (PingRequest) returns (PingResponse);
                }
                """)
            out_drawio = os.path.join(td, "service.drawio")
            ir_json = os.path.join(td, "service.ir.json")

            res = subprocess.run(
                [
                    sys.executable,
                    DIAGRAMCTL,
                    "build",
                    td,
                    "--group",
                    "--ir-output",
                    ir_json,
                    "-o",
                    out_drawio,
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            result_meta = json.loads(res.stdout)
            self.assertEqual(result_meta["source_type"], "proto")
            self.assertTrue(os.path.isfile(out_drawio))
            self.assertTrue(os.path.isfile(ir_json))

            with open(ir_json, encoding="utf-8") as f:
                ir = json.load(f)
            self.assertEqual(ir["metadata"]["importer"], "proto")
            self.assertTrue(any(n["id"] == "test.PingService" for n in ir["nodes"]))


if __name__ == "__main__":
    unittest.main()
