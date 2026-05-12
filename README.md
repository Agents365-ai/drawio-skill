# drawio-skill — From Text to Professional Diagrams

[中文文档](README_CN.md) | [Online Docs](https://agents365-ai.github.io/drawio-skill/)

<p align="center">
  <img src="assets/workflow.png" width="900" alt="Workflow">
</p>

A skill that turns natural-language descriptions into `.drawio` XML and exports them to PNG / SVG / PDF / JPG via the native draw.io desktop CLI — with 6 diagram presets (ERD, UML Class, Sequence, Architecture, ML/DL, Flowchart), self-check + auto-fix (2 rounds), an iterative feedback loop (5 rounds), and style presets you can capture from a sample file or image.

Works with Claude Code, Cursor, Copilot, OpenClaw, Codex, Hermes, and any agent that supports the [Agent Skills](https://agentskills.io) format.

## Documentation

| Doc | What's inside |
|---|---|
| [docs/COMPARISON.md](docs/COMPARISON.md) | Side-by-side tables vs. native agents and other draw.io skills/tools, with key-advantages summary |
| [docs/INSTALL_CLI.md](docs/INSTALL_CLI.md) | draw.io desktop CLI install recipes for macOS / Windows / Linux |
| [docs/INSTALL_SKILL.md](docs/INSTALL_SKILL.md) | Plugin marketplace, manual clone, and update commands |
| [docs/USAGE.md](docs/USAGE.md) | Natural-language prompts, microservices walkthrough, topology demos (star / layered / ring) |
| [docs/STYLE_PRESETS.md](docs/STYLE_PRESETS.md) | Built-in presets, "learn my style from a file" workflow, manage-presets commands |
| [skills/drawio-skill/SKILL.md](skills/drawio-skill/SKILL.md) | Workflow guide loaded by the agent |

## What it does

| Capability | Description |
|---|---|
| `.drawio` XML generation | From natural-language descriptions |
| Multi-format export | PNG / SVG / PDF / JPG via the native draw.io desktop CLI |
| 6 diagram type presets | ERD, UML Class, Sequence, Architecture, ML/Deep Learning, Flowchart |
| Iterative review | Self-check + auto-fix (up to 2 rounds), then a 5-round feedback loop until you approve |
| Style presets | Capture your visual style from a `.drawio` file or image, save by name, reapply on demand |
| Auto-trigger | Activates whenever diagrams would help explain complex systems |

## Supported diagram types

| Category | Examples | Notable features |
|---|---|---|
| Architecture | microservices, cloud (AWS/GCP/Azure), network topology, deployment | Tier-based swimlanes, hub-center strategy |
| ML / Deep Learning | Transformer, CNN, LSTM, GRU | Tensor shape annotations, layer-type color coding |
| Flowcharts | business processes, workflows, decision trees, state machines | Semantic shapes (parallelogram I/O, diamond decisions) |
| UML | class diagrams, sequence diagrams | Inheritance / composition / aggregation arrows; lifelines + activation boxes |
| Data | ER diagrams, data flow diagrams (DFD) | Table containers, PK/FK notation |
| Other | org charts, mind maps, wireframes | — |

## Quick Start

Two steps — install the draw.io CLI first (see [docs/INSTALL_CLI.md](docs/INSTALL_CLI.md)), then drop the skill into your host (see [docs/INSTALL_SKILL.md](docs/INSTALL_SKILL.md)). After that, just describe what you want:

```
Create a microservices e-commerce architecture with API Gateway, auth/user/order/product/payment services,
Kafka message queue, notification service, and separate databases for each service
```

The skill plans the layout, generates the `.drawio` XML, exports to your chosen format, self-checks, and lets you iterate.

## Community

Join us for help, Q&A, and updates:

- **Discord:** https://discord.gg/79JF5Atuk
- **WeChat:** scan the QR code below

<p align="center">
  <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/agents365ai_wechat_1.png" width="200" alt="WeChat Community Group">
</p>

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
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/awarding/award.gif" width="180" alt="Give a Reward">
      <br>
      <b>Give a Reward</b>
    </td>
  </tr>
</table>

## Author

**Agents365-ai**

- Bilibili: https://space.bilibili.com/441831884
- GitHub: https://github.com/Agents365-ai

## License

MIT
