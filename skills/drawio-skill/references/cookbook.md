# Prompt Cookbook

Tested prompt patterns for the highest-quality results from this skill. Each
recipe states what to include, why it matters, and what the skill does with it.
Adapt the bracketed parts; keep the structural clauses.

## General rules that always help

1. **Name the audience and the file format.** "for an exec review, PNG +
   editable .drawio" changes layout, colors, and what gets simplified.
2. **List the components explicitly.** An enumerated list of nodes beats
   "a typical microservices system" — the skill cannot invent your topology.
3. **State the relations with verbs.** "Kafka consumes events from Order
   Service" yields labeled, directed edges instead of anonymous lines.
4. **Say what is external or out of scope** to get boundary containers and
   honest trust boundaries.
5. **For source-backed models, point at the real directory/manifest.** Anything
   the skill imports from code/IaC/SQL carries provenance; anything invented
   does not.

## Natural-language architecture diagram

```text
Draw a microservices e-commerce architecture for an exec review. Clients:
Mobile, Web. Edge: API Gateway (auth, rate limiting). Services: Order,
Payment, Inventory, Notification. Infrastructure: Kafka, PostgreSQL
(orders), Redis (cache). Stripe is an external SaaS. Mobile/Web reach the
gateway over HTTPS; services talk over gRPC inside the VPC; Payment calls
Stripe over mTLS. Output PNG + editable .drawio.
```

Why it works: enumerated nodes, protocol-labeled edges, explicit external
system, audience stated. Swap "exec review" for "security review" and the
same prompt projects a different view.

## Codebase visualization

```text
Visualize the module structure of ./myproject as an import graph. Group by
top-level package, and hide utilities modules. Export .drawio + PNG.
```

The directory path is doing the work here: `diagramctl.py build ./myproject
--group` reads the real imports, so the diagram stays syncable when the code
changes. Do not also list components by hand — the importer wins.

## Incremental sync (the "don't lose my layout" workflow)

```text
We added a Billing service and removed the legacy Auth service from
./src. Update architecture.drawio from the source, but keep my manual
positions and colors for everything that didn't change. Show me what
moved/remained before overwriting.
```

Triggers `diagramctl.py sync` (reviewable output, explicit pruning only).

## Architecture contracts (Diagram-as-Test)

```text
Check this architecture against our rules: no component may reach a
database directly from the Internet, no cyclic service dependencies, every
service must have an owner, and every external call must have a timeout.
Fail the build on errors.
```

Maps to a policy file + `diagramctl.py test`. Better: commit the IR JSON and
wire the `drawio-architecture-test` GitHub Action (see
`references/ci-gate.md`) so this runs on every PR.

## Multi-view projection

```text
From our architecture model, produce the executive view (only user-facing
services and external systems), the full system view, and a security view
highlighting trust-boundary crossings. Linked pages, one .drawio.
```

## Failure analysis (what-if)

```text
What happens if Kafka goes down? Show downstream impact and produce an
annotated diagram with the blast radius in red and isolated-but-alive
components in amber.
```

## Guided walkthrough (Story Mode)

```text
Turn our architecture model into an accessible HTML walkthrough for the
onboarding doc: keyboard navigation, a full text alternative, and a
failure-scenario section for the payment path. Chinese labels, keep
English as secondary.
```

## C4 with drill-down

```text
Build a C4 model for the payment platform: System Context on top,
containers below it (API Gateway, Order Service, Stripe connector,
PostgreSQL, Kafka), components inside Order Service. Every parent must
click through to its child page.
```

## UML class / sequence

```text
Draw the class diagram for the checkout domain: Order, OrderLine, Payment,
Receipt. Order has 1..* OrderLines; Payment references exactly one Order;
Receipt aggregates Payment. Show multiplicities and mark composition vs
association.
```

```text
Sequence for checkout: user submits cart -> API Gateway validates JWT ->
Order Service reserves inventory (gRPC) -> Payment Service charges Stripe
(HTTPS) -> on success Order Service persists to PostgreSQL and publishes
OrderPlaced to Kafka. Show the failure path when Stripe times out.
```

Multiplicities and explicit failure branches are the clauses agents skip
without them.

## ER diagram from DDL

```text
Turn schema.sql into an ER diagram with PK/FK markers and crow's-foot
notation; keep schema prefixes for the billing tables.
```

## ML / deep-learning model

```text
Draw a Transformer encoder-decoder for machine translation. 6+6 layers,
batch × 512 × 768 embeddings, sinusoidal positional encoding. Annotate
tensor shapes on every arrow and color-code by layer type (attention /
normalization / feed-forward).
```

Tensor-shape annotations are the difference between a poster and a
teachable figure; ask for them explicitly.

## Mermaid-first authoring (draw.io CLI >= 30)

```text
Draft this as a Mermaid mindmap first (it's structure-only), then convert
to native .drawio: quarterly OKRs with three branches...
```

Use Mermaid for standard types with no custom styling; switch to XML/IR
authoring the moment you need vendor icons, swimlanes, or precise geometry.

## Anti-patterns (these produce weak diagrams)

- "Draw a typical e-commerce architecture" — invented topology, no
  provenance, nothing to check. Enumerate nodes or name the source dir.
- "Make it beautiful" with no audience — the skill has to guess colors,
  density, and export format. Name the audience or a style preset.
- "Auto-layout it" for under ~15 nodes — hand-arranged placement from the
  IR preserves semantic grouping better; large graphs are where
  autolayout earns its keep.
- Mixing real sources and invented components in one request without
  saying which is which — provenance gets muddled and review findings
  become noise.
- Asking for PNG only on an architecture you will iterate on — always ask
  for the editable `.drawio` (or the IR JSON) as well.
