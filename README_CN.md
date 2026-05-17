# drawio-skill —— 从文字到专业图表

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/Agents365-ai/drawio-skill?style=flat&logo=github)](https://github.com/Agents365-ai/drawio-skill/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Agents365-ai/drawio-skill?style=flat&logo=github)](https://github.com/Agents365-ai/drawio-skill/network/members)
[![Latest Release](https://img.shields.io/github/v/release/Agents365-ai/drawio-skill?logo=github)](https://github.com/Agents365-ai/drawio-skill/releases/latest)
[![Last Commit](https://img.shields.io/github/last-commit/Agents365-ai/drawio-skill?logo=github)](https://github.com/Agents365-ai/drawio-skill/commits/main)

[![SkillsMP](https://img.shields.io/badge/SkillsMP-listed-1f6feb)](https://skillsmp.com/skills/agents365-ai-drawio-skill-skills-drawio-skill-skill-md)
[![ClawHub](https://img.shields.io/badge/ClawHub-listed-ff6b35)](https://clawhub.ai/agents365-ai/drawio-pro-skill)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-plugin-8a2be2)](https://github.com/Agents365-ai/365-skills)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-兼容-2ea44f)](https://agentskills.io)

[English](README.md) · **中文** · [📖 在线文档](https://agents365-ai.github.io/drawio-skill/)

一个把自然语言描述变成 `.drawio` XML，并通过 draw.io 桌面版原生 CLI 导出 PNG / SVG / PDF / JPG 的技能。支持 **Claude Code、Cursor、Copilot、OpenClaw、Codex、Hermes** 等任何兼容 [Agent Skills](https://agentskills.io) 规范的 agent。

<p align="center">
  <img src="assets/workflow-cn.png" width="900" alt="工作流程">
</p>

## ✨ 核心亮点

- **6 种图表类型预设** —— ER 图、UML 类图、序列图、架构图、ML/深度学习、流程图
- **自检 + 自动修复** —— 读取自己导出的 PNG，自动修复 6 类问题（最多 2 轮）
- **迭代反馈循环** —— 最多 5 轮定向优化，直到你满意为止
- **样式预设** —— 用 `.drawio` 文件或图片"教会"Skill 你的风格，命名保存后随时复用
- **网格对齐布局** —— 按复杂度分级间距、路由走廊、hub 居中策略
- **多智能体、零配置** —— 纯 SKILL.md，无需 MCP、Python、Node.js

## 🖼️ 示例

> [!TIP]
> **试试这条提示词**，生成下图：

```
画一个微服务电商架构图，包含 Mobile/Web/Admin 客户端，API Gateway（含认证+限流+路由），
Auth/User/Order/Product/Payment 微服务，Kafka 消息队列，Notification 服务，
以及 User DB / Order DB / Product DB / Redis Cache / Stripe API
```

<p align="center">
  <img src="assets/microservices-example.png" width="800" alt="微服务架构图">
</p>

Skill 还支持多种图表拓扑，线条路由清晰 —— 不会穿越无关的形状：

<table>
  <tr>
    <td align="center" width="33%">
      <img src="assets/demo-star-cn.png" alt="星形拓扑" width="100%"><br>
      <b>星形</b> · 7 个节点<br>
      <sub>中央消息代理 + 6 个微服务辐射排列，连线零交叉。</sub>
    </td>
    <td align="center" width="33%">
      <img src="assets/demo-layered-cn.png" alt="分层流程" width="100%"><br>
      <b>分层</b> · 10 节点 / 4 层<br>
      <sub>电商架构，同层水平 + 对角线交叉连线均通过路由走廊绕行。</sub>
    </td>
    <td align="center" width="33%">
      <img src="assets/demo-ring-cn.png" alt="环形拓扑" width="100%"><br>
      <b>环形</b> · 8 个节点<br>
      <sub>CI/CD 流水线，含闭合回路和 2 个分支，沿矩形外围流动。</sub>
    </td>
  </tr>
</table>

完整演练见 [docs/USAGE_CN.md](docs/USAGE_CN.md)。

## 🚀 安装

### 1. 安装 draw.io 桌面版 CLI

| 平台 | 命令 |
|------|------|
| **macOS** | `brew install --cask drawio` |
| **Windows** | [下载安装包](https://github.com/jgraph/drawio-desktop/releases) |
| **Linux** | 从 [releases](https://github.com/jgraph/drawio-desktop/releases) 下载 `.deb`/`.rpm`；无头导出需 `sudo apt install xvfb` |

用 `drawio --version` 验证。完整方案见 [docs/INSTALL_CLI_CN.md](docs/INSTALL_CLI_CN.md)。

### 2. 安装技能

```bash
# 任意 Agent（Claude Code、Cursor、Copilot 等）
npx skills add Agents365-ai/365-skills -g
```

```text
# Claude Code 插件市场
> /plugin marketplace add Agents365-ai/365-skills
> /plugin install drawio
```

```bash
# 手动安装
git clone https://github.com/Agents365-ai/drawio-skill.git \
  ~/.claude/skills/drawio-skill
```

同时索引于 [SkillsMP](https://skillsmp.com/skills/agents365-ai-drawio-skill-skills-drawio-skill-skill-md) 与 [ClawHub](https://clawhub.ai/agents365-ai/drawio-pro-skill)。

**更新：** `/plugin update drawio`（Claude Code）、`skills update drawio-skill`（SkillsMP）、`clawhub update drawio-pro-skill`（OpenClaw），或 `git pull`（手动安装）—— 详见 [docs/INSTALL_SKILL_CN.md#更新](docs/INSTALL_SKILL_CN.md#更新)。

## ⚡ 快速开始

装好之后直接描述你想要的图表：

```
画一个微服务电商架构图，包含 API Gateway、用户/订单/商品/支付服务、
Kafka 消息队列、通知服务，以及各自独立的数据库
```

Skill 会自动规划布局、生成 `.drawio` XML、导出为你选择的格式、自检结果，并支持后续迭代。

## 🧩 支持的图表类型

| 类别 | 示例 | 特色 |
|------|------|------|
| 架构图 | 微服务、云（AWS/GCP/Azure）、网络拓扑、部署 | 分层泳道、hub 居中策略 |
| ML / 深度学习 | Transformer、CNN、LSTM、GRU | 张量形状标注、层类型配色 |
| 流程图 | 业务流程、工作流、决策树、状态机 | 语义形状（平行四边形 I/O、菱形判断） |
| UML | 类图、序列图 | 继承 / 组合 / 聚合箭头；生命线 + 激活框 |
| 数据图 | ER 图、数据流图（DFD） | 表容器、PK/FK 标记 |
| 其他 | 组织架构图、思维导图、线框图 | — |

## 🎨 样式预设

把视觉风格"教"给 Skill 一次，所有图表自动复用。内置三种预设：`default`、`corporate`、`handdrawn`；也可以从 `.drawio` 文件或图片学习你的风格：

```
画一个微服务架构图，使用我的 "corporate" 样式
```

```
从 ~/diagrams/brand.drawio 学习我的样式，保存为 "mybrand"
```

Skill 会提取配色、形状、字体和连线风格，渲染预览图，**确认后**才保存预设。完整管理命令见 [docs/STYLE_PRESETS_CN.md](docs/STYLE_PRESETS_CN.md)。

## 🆚 对比

### 对比原生智能体（无 skill）

| 功能 | 原生智能体 | drawio-skill |
|------|-----------|--------------|
| 导出后自检 | ❌ | ✅ 读取 PNG 自动修复 6 类问题 |
| 迭代审查循环 | ❌ 需手动重新提问 | ✅ 定向编辑，5 轮安全阀 |
| 图表类型预设 | ❌ | ✅ 6 种（ERD、UML、序列、架构、ML、流程） |
| 网格对齐布局 | ❌ | ✅ 10px 对齐、路由走廊 |
| 配色方案 | 随机 / 不一致 | ✅ 7 色语义系统 |
| 样式预设 | ❌ | ✅ 从 `.drawio` 文件或图片学习 |

### 对比其他 draw.io Skills 与工具

| 功能 | drawio-skill | [jgraph/drawio-mcp](https://github.com/jgraph/drawio-mcp)（官方）<br>![](https://img.shields.io/github/stars/jgraph/drawio-mcp?style=flat-square&logo=github) | [bahayonghang/drawio-skills](https://github.com/bahayonghang/drawio-skills)<br>![](https://img.shields.io/github/stars/bahayonghang/drawio-skills?style=flat-square&logo=github) | [GBSOSS/ai-drawio](https://github.com/GBSOSS/ai-drawio)<br>![](https://img.shields.io/github/stars/GBSOSS/ai-drawio?style=flat-square&logo=github) |
|------|------|------|------|------|
| **方式** | 纯 SKILL.md | SKILL.md / MCP / Project | YAML DSL + MCP | 插件 + 浏览器 |
| **依赖** | 仅 draw.io 桌面版 | draw.io 桌面版 | MCP 服务（`npx`） | 浏览器 + 本地服务 |
| **多智能体支持** | ✅ 6 个平台 | ❌ 仅 Claude Code | ❌ 仅 Claude Code | ❌ |
| **自检 + 自动修复** | ✅ 2 轮 | ❌ | ❌ | ❌ 仅截图 |
| **迭代审查** | ✅ 5 轮循环 | ❌ 一次生成 | ✅ 3 种工作流 | ❌ |
| **图表预设** | ✅ 6 种 | ❌ | ❌ | ❌ |
| **ML/DL 图** | ✅ 张量标注、层配色 | ❌ | ❌ | ❌ |
| **配色系统** | ✅ 7 色语义 | ❌ | ✅ 5 种主题 | ❌ |
| **浏览器降级** | ✅ diagrams.net URL | ❌ | ❌ | ❌ |
| **零配置** | ✅ 复制 `skills/drawio-skill/` | ✅ | ❌ 需 `npx` | ❌ 需安装插件 |

完整 18 行对比 + 核心优势总结见 [docs/COMPARISON_CN.md](docs/COMPARISON_CN.md)。

## 📚 文档导航

| 文档 | 内容 |
|------|------|
| [docs/INSTALL_CLI_CN.md](docs/INSTALL_CLI_CN.md) | macOS / Windows / Linux 各平台的 draw.io 桌面版 CLI 安装配方 |
| [docs/INSTALL_SKILL_CN.md](docs/INSTALL_SKILL_CN.md) | 插件市场、手动克隆与更新命令 |
| [docs/USAGE_CN.md](docs/USAGE_CN.md) | 自然语言提示词、微服务示例、多种拓扑演示 |
| [docs/STYLE_PRESETS_CN.md](docs/STYLE_PRESETS_CN.md) | 内置预设、"从文件学习样式"流程、完整管理命令 |
| [docs/COMPARISON_CN.md](docs/COMPARISON_CN.md) | 与原生智能体、其他 draw.io skills/工具的对照表 |
| [skills/drawio-skill/SKILL.md](skills/drawio-skill/SKILL.md) | agent 加载的工作流指南 |

## 💬 社区

- **Discord：** https://discord.gg/79JF5Atuk
- **微信：** 扫描下方二维码

<p align="center">
  <img src="https://raw.githubusercontent.com/Agents365-ai/images_payment/main/qrcode/agents365ai_wechat_1.png" width="200" alt="微信交流群">
</p>

## ❤️ 支持作者

如果这个 skill 对你有帮助，欢迎支持作者：

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

## 👤 作者

**Agents365-ai**

- GitHub: https://github.com/Agents365-ai
- Bilibili: https://space.bilibili.com/441831884

## 📄 License

[MIT](LICENSE)
