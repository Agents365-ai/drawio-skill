# Live infrastructure — draw what's actually running

The IaC importers (`tfimports.py`, `k8simports.py`, `composeimports.py`) draw the
**declared** config. These three recipes draw the **real** state — the resources
actually deployed, the containers actually running, the cluster as it is now.
Every path ends the same way: an importer emits autolayout graph JSON, then
`autolayout.py` renders an editable `.drawio` with the same official icons.

Read this when the user says things like *"draw my running cluster / stack"*,
*"diagram what's actually deployed"*, *"visualize my live AWS/Azure/GCP infra"*,
or *"map the containers I have up right now"*.

> The commands below read local tool state (`terraform`, `docker`, `kubectl`)
> the user already has authenticated. The skill never reaches out to a cloud
> account itself — it only parses the JSON those tools print. If a tool or its
> auth is missing, say so and fall back to the declared-config importer.

## 1. Deployed cloud resources — Terraform state

Provider-agnostic (AWS / Azure / GCP alike). Run from the Terraform working dir:

```bash
terraform show -json | python3 <this-skill-dir>/scripts/tfstate.py - -o graph.json
python3 <this-skill-dir>/scripts/autolayout.py graph.json -o deployed.drawio
```

- Works on live state (above) or a saved plan: `terraform show -json plan.tfplan | …`.
- `count` / `for_each` resources appear as their real instances (`name[0]`, `name[1]`).
- `--group` boxes resources by module; `--no-icons` for plain boxes; `--direction LR`.
- Edges are the dependencies Terraform recorded in state (`depends_on`). A state
  with no recorded dependencies still produces a useful **inventory** (every
  deployed resource with its official icon) — mention that if edges come out sparse.
- Contrast with `tfimports.py` (the `.tf` files) when the user wants declared-vs-actual.

## 2. Running containers — Docker

```bash
docker inspect $(docker ps -q) | python3 <this-skill-dir>/scripts/dockerimports.py - -o graph.json
python3 <this-skill-dir>/scripts/autolayout.py graph.json -o running.drawio
```

- Containers → rounded boxes (name + image); user networks → green ellipses;
  named volumes → cylinders. Built-in `bridge`/`host`/`none`/`ingress` networks
  and bind mounts are dropped as noise.
- Edges: container→network, container→volume, and container→container from
  `links` and the compose `depends_on` label.
- `--group` boxes containers by their compose project (else first network).
- `docker ps -q` lists only running containers; add `-a` to include stopped ones.

## 3. Live cluster — Kubernetes (via k8simports)

No new script — `k8simports.py` already ingests `kubectl get ... -o json`. Ask for
the resource kinds that make the architecture readable (workloads + what wires them):

```bash
kubectl get deploy,sts,ds,svc,ing,cm,secret,pvc,hpa -n <ns> -o json \
  | python3 <this-skill-dir>/scripts/k8simports.py - -o graph.json
python3 <this-skill-dir>/scripts/autolayout.py graph.json -o cluster.drawio
```

- `kubectl get all` alone omits Ingress / ConfigMap / Secret / PVC — list the
  kinds explicitly (as above) so the reference edges have endpoints to land on.
- `--group` boxes objects by namespace; add `-A` to `kubectl` for all namespaces.
- Edges are derived within a namespace: Ingress→Service, Service→workload
  (selector match), workload→ConfigMap/Secret/PVC, HPA→target.

## After any of them

Continue at the main workflow's **Export draft** step: preview PNG (`--width 2000`),
self-check, review, final export with `-e` + `repair_png.py`. A live snapshot is a
point in time — re-run the pipeline to refresh it.
