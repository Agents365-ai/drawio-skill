# drawio-skill —— 从文字到专业图表

[English](README.md) | [Online Docs](https://agents365-ai.github.io/drawio-skill/)

<p align="center">
  <img src="assets/workflow-cn.png" width="900" alt="工作流程">
</p>

一个把自然语言描述变成 `.drawio` XML,并通过 draw.io 桌面版原生 CLI 导出 PNG / SVG / PDF / JPG 的技能 —— 内置 6 种图表预设(ER 图、UML 类图、序列图、架构图、ML/DL、流程图)、自检 + 自动修复(2 轮)、迭代反馈循环(5 轮),以及可以从样例文件或图片学习的样式预设。

支持 Claude Code、Cursor、Copilot、OpenClaw、Codex、Hermes 等任何兼容 [Agent Skills](https://agentskills.io) 规范的 agent。

## 文档导航

| 文档 | 内容 |
|---|---|
| [docs/COMPARISON_CN.md](docs/COMPARISON_CN.md) | 与原生智能体、其他 draw.io skills/工具的对照表与核心优势 |
| [docs/INSTALL_CLI_CN.md](docs/INSTALL_CLI_CN.md) | macOS / Windows / Linux 各平台的 draw.io 桌面版 CLI 安装配方 |
| [docs/INSTALL_SKILL_CN.md](docs/INSTALL_SKILL_CN.md) | 插件市场、手动克隆与更新命令 |
| [docs/USAGE_CN.md](docs/USAGE_CN.md) | 自然语言提示词、微服务示例、多种拓扑演示(星形 / 分层 / 环形) |
| [docs/STYLE_PRESETS_CN.md](docs/STYLE_PRESETS_CN.md) | 内置预设、"从文件学习样式"流程、完整的预设管理命令 |
| [skills/drawio-skill/SKILL.md](skills/drawio-skill/SKILL.md) | agent 加载的工作流指南 |

## 功能说明

| 能力 | 说明 |
|---|---|
| `.drawio` XML 生成 | 根据自然语言描述生成 |
| 多格式导出 | PNG / SVG / PDF / JPG,使用 draw.io 桌面版原生 CLI |
| 6 种图表类型预设 | ERD、UML 类图、序列图、架构图、ML/深度学习、流程图 |
| 迭代审查 | 自检 + 自动修复(最多 2 轮),再走 5 轮反馈循环直到你满意 |
| 样式预设 | 用 `.drawio` 文件或图片"教会"Skill 你的风格,命名保存后随时复用 |
| 自动触发 | 图表有助于解释复杂系统时自动调用 |

## 支持的图表类型

| 类别 | 示例 | 特色 |
|---|---|---|
| 架构图 | 微服务、云(AWS/GCP/Azure)、网络拓扑、部署 | 分层泳道、hub 居中策略 |
| ML / 深度学习 | Transformer、CNN、LSTM、GRU | 张量形状标注、层类型配色 |
| 流程图 | 业务流程、工作流、决策树、状态机 | 语义形状(平行四边形 I/O、菱形判断) |
| UML | 类图、序列图 | 继承 / 组合 / 聚合箭头;生命线 + 激活框 |
| 数据图 | ER 图、数据流图(DFD) | 表容器、PK/FK 标记 |
| 其他 | 组织架构图、思维导图、线框图 | — |

## 快速开始

两步 —— 先装 draw.io CLI(见 [docs/INSTALL_CLI_CN.md](docs/INSTALL_CLI_CN.md)),再把技能加载到 host(见 [docs/INSTALL_SKILL_CN.md](docs/INSTALL_SKILL_CN.md))。装好之后直接描述你想要的:

```
画一个微服务电商架构图,包含 API Gateway、用户/订单/商品/支付服务、
Kafka 消息队列、通知服务,以及各自独立的数据库
```

技能会规划布局、生成 `.drawio` XML、导出为你选择的格式、自检,然后让你迭代。

## 社区

加入交流群获取帮助、提问和最新动态:

- **Discord:** https://discord.gg/79JF5Atuk
- **微信:** 扫描下方二维码

<p align="center">
  <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/agents365ai_wechat_1.png" width="200" alt="微信交流群">
</p>

## 支持作者

如果这个 skill 对你有帮助,欢迎支持作者:

<table>
  <tr>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/wechat-pay.png" width="180" alt="微信支付">
      <br>
      <b>微信支付</b>
    </td>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/alipay.png" width="180" alt="支付宝">
      <br>
      <b>支付宝</b>
    </td>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/buymeacoffee.png" width="180" alt="Buy Me a Coffee">
      <br>
      <b>Buy Me a Coffee</b>
    </td>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/awarding/award.gif" width="180" alt="打赏">
      <br>
      <b>打赏</b>
    </td>
  </tr>
</table>

## 作者

**Agents365-ai**

- Bilibili: https://space.bilibili.com/441831884
- GitHub: https://github.com/Agents365-ai

## License

MIT
