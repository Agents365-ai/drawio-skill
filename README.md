# drawio-skill

Claude Code skill for generating Draw.io diagrams and exporting to PNG/SVG/PDF locally.

[中文文档](README_CN.md)

## What it does

- Generates `.drawio` XML files from natural language descriptions
- Exports diagrams to PNG, SVG, PDF, or JPG using the native draw.io desktop CLI
- Supports multi-page diagrams and layered grouping
- Iterative design: preview, get feedback, and refine diagrams until they look right
- Triggers automatically when diagrams would help explain complex systems

## Supported diagram types

- **Architecture**: microservices, cloud (AWS/GCP/Azure), network topology, deployment
- **Flowcharts**: business processes, workflows, decision trees, state machines
- **UML**: class diagrams, sequence diagrams, use case diagrams
- **Data**: ER diagrams, data flow diagrams (DFD)
- **Other**: org charts, mind maps, wireframes

## How it works

![Workflow](assets/workflow.png)

## Dependencies

| Tool | Purpose |
|------|---------|
| `draw.io` desktop app | Native CLI to export `.drawio` → PNG/SVG/PDF |

No browser automation or Node.js dependency required.

## Install

### macOS

```bash
# Recommended — Homebrew
brew install --cask drawio

# Verify
draw.io --version
```

### Windows

Download and install from: https://github.com/jgraph/drawio-desktop/releases

```powershell
# Verify
"C:\Program Files\draw.io\draw.io.exe" --version
```

### Linux

Download `.deb` or `.rpm` from: https://github.com/jgraph/drawio-desktop/releases

```bash
# Headless export (required on Linux servers without display)
sudo apt install xvfb  # Debian/Ubuntu
xvfb-run -a draw.io --version
```

### Platform notes

| Platform | Extra step |
|----------|------------|
| **macOS** | No extra steps after Homebrew install |
| **Windows** | Use full path if not in PATH |
| **Linux** | Wrap commands with `xvfb-run -a` for headless export |

## Usage

Just describe what you want:

```
Create a microservices e-commerce architecture with API Gateway, auth/user/order/product/payment services,
Kafka message queue, notification service, and separate databases for each service
```

Claude will generate the `.drawio` XML file and export it to PNG automatically.

## Example

**Prompt:**
> Create a microservices e-commerce architecture with Mobile/Web/Admin clients, API Gateway,
> Auth/User/Order/Product/Payment services, Kafka message queue, Notification service,
> and User DB / Order DB / Product DB / Redis Cache / Stripe API

**Output:**

![Microservices Architecture](assets/microservices-example.png)

## Topology demos

The skill handles various diagram topologies with clean edge routing — no lines crossing through shapes.

### Star topology (7 nodes)

Central message broker with 6 microservices radiating outward. Edges enter Kafka from different sides, zero crossings.

![Star topology](assets/demo-star.png)

### Layered flow (10 nodes, 4 tiers)

E-commerce architecture with 2 cross-connections: Order→Product (same-tier horizontal) and Auth→Redis (diagonal via routing corridor). All edges route cleanly.

![Layered flow](assets/demo-layered.png)

### Ring / cycle (8 nodes)

CI/CD pipeline with a closed loop and 2 spur branches. Edges flow along the perimeter without crossing the interior.

![Ring cycle](assets/demo-ring.png)

## Files

- `SKILL.md` — **the only required file**. This is what Claude Code loads as the skill instructions.
- `README.md` — this file (English documentation)
- `README_CN.md` — Chinese documentation
- `assets/` — example diagrams and workflow images

> **Note:** Only `SKILL.md` is needed for the skill to work. The `assets/`, `README.md`, and `README_CN.md` files are documentation only and can be safely deleted to save space.

## License

MIT

## Support

If this skill helps you, consider supporting the author:

<table>
  <tr>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/wechat-pay.png" width="180" alt="WeChat Pay">
      <br>
      <b>WeChat Pay</b>
    </td>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/alipay.png" width="180" alt="Alipay">
      <br>
      <b>Alipay</b>
    </td>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/buymeacoffee.png" width="180" alt="Buy Me a Coffee">
      <br>
      <b>Buy Me a Coffee</b>
    </td>
  </tr>
</table>

## Author

**Agents365-ai**

- Bilibili: https://space.bilibili.com/441831884
- GitHub: https://github.com/Agents365-ai
