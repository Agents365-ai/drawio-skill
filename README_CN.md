# drawio-skill

[English](README.md)

## 功能说明

- 根据自然语言描述生成 `.drawio` XML 文件
- 使用 draw.io 桌面版原生 CLI 将图表导出为 PNG、SVG、PDF 或 JPG
- 支持多页图表和分层分组
- 迭代设计：预览、获取反馈、反复优化直到图表满意为止
- 当图表有助于解释复杂系统时自动触发

## 对比

### 与原生 Claude Code（无 skill）对比

| 功能 | 原生 Claude Code | 本 skill |
|------|-----------------|---------|
| 生成 draw.io XML | 是 — Claude 本身了解格式 | 是 |
| 导出后自检 | 否 | 是 — 读取 PNG 自动修复 6 类问题 |
| 迭代反馈循环 | 否 — 需手动重新提问 | 是 — 定向编辑，5 轮安全阀 |
| 主动触发 | 否 — 仅在明确要求时 | 是 — 3+ 组件时自动建议画图 |
| 布局规范 | 无 — 每次结果不一致 | 按复杂度分级间距、路由走廊、hub 居中策略 |
| 配色方案 | 随机/不一致 | 7 色语义系统（蓝=服务、绿=数据库、紫=安全…） |
| 连线路由规则 | 基础 | 锚点分配、连接分布、走廊绕行 |
| 容器/分组 | 无 | Swimlane、Group、自定义容器 + 父子嵌套 |
| 嵌入式导出 | 否 | 是 — `--embed-diagram` 保持导出文件可编辑 |
| 中文支持 | 否 | 是 — "画图"、"架构图"、"流程图" |

### 与其他 draw.io Skills / 工具对比

| 功能 | 本 skill | [jgraph/drawio-mcp](https://github.com/jgraph/drawio-mcp)（官方，1.3k⭐） | [bahayonghang/drawio-skills](https://github.com/bahayonghang/drawio-skills)（60⭐） | [GBSOSS/ai-drawio](https://github.com/GBSOSS/ai-drawio)（63⭐） |
|---------|-----------|---------------|-------------------|--------------|
| **方式** | 纯 SKILL.md | SKILL.md / MCP / Project | YAML DSL + MCP | 插件 + 浏览器 |
| **依赖** | 仅 draw.io 桌面版 | draw.io 桌面版 | MCP 服务（`npx`） | 浏览器 + 本地服务 |
| **自检** | ✅ 2 轮自动修复 | ❌ | ❌ | ❌ 截图 |
| **迭代审查** | ✅ 5 轮循环 | ❌ 一次生成 | ✅ 3 种工作流 | ❌ |
| **布局指南** | ✅ 按复杂度分级 | ✅ 基础间距 | ❌ 依赖 MCP | ❌ |
| **配色系统** | ✅ 7 色语义 | ❌ | ✅ 5 种主题 | ❌ |
| **容器/分组** | ✅ swimlane + group | ✅ 详细 | ❌ | ❌ |
| **嵌入式导出** | ✅ `--embed-diagram` | ✅ | ❌ | ❌ |
| **连线路由** | ✅ 走廊 + waypoints | ✅ 箭头间距规则 | ❌ | ❌ |
| **中文支持** | ✅ 触发词 + 文档 | ❌ | ❌ | ✅ |
| **云图标** | AWS 基础 | ❌ | ✅ AWS/GCP/Azure/K8s | ❌ |
| **零配置** | ✅ 复制 SKILL.md | ✅ | ❌ 需要 `npx` | ❌ 需安装插件 |

### 本 skill 核心优势

1. **自检 + 迭代循环** — 唯一纯 SKILL.md 方案中能自动读取输出、修复问题、支持多轮优化的
2. **零配置、零依赖** — 仅需一个 `SKILL.md` 文件 + draw.io 桌面版，无需 MCP、Python、Node.js、浏览器
3. **专业级布局** — 按复杂度分级间距、路由走廊、hub 居中、连接分布规则
4. **完整中文支持** — 主动触发词（"画图"、"架构图"）、双语文档

## 支持的图表类型

- **架构图**：微服务架构、云架构（AWS/GCP/Azure）、网络拓扑、部署架构
- **流程图**：业务流程、工作流、决策树、状态机
- **UML**：类图、序列图、用例图
- **数据图**：ER 图、数据流图（DFD）
- **其他**：组织架构图、思维导图、线框图

## 工作流程

<p align="center">
  <img src="assets/workflow-cn.png" width="420" alt="工作流程">
</p>

## 依赖项

| 工具 | 用途 |
|------|------|
| `draw.io` 桌面应用 | 原生 CLI，用于将 `.drawio` 导出为 PNG/SVG/PDF |

无需浏览器自动化或 Node.js 依赖。

## 安装

### macOS

```bash
# 推荐方式 — Homebrew
brew install --cask drawio

# 验证安装
drawio --version
```

### Windows

从以下地址下载安装包：https://github.com/jgraph/drawio-desktop/releases

```powershell
# 验证安装
"C:\Program Files\draw.io\draw.io.exe" --version
```

### Linux

从以下地址下载 `.deb` 或 `.rpm` 包：https://github.com/jgraph/drawio-desktop/releases

```bash
# 无头导出（Linux 服务器无显示器时必须）
sudo apt install xvfb  # Debian/Ubuntu
xvfb-run -a drawio --version
```

### 平台说明

| 平台 | 额外步骤 |
|------|----------|
| **macOS** | Homebrew 安装后无需额外操作 |
| **Windows** | 如不在 PATH 中，使用完整路径 |
| **Linux** | 无头导出时命令前加 `xvfb-run -a` |

## Skill 安装

### Claude Code

```bash
# 全局安装（所有项目可用）
git clone https://github.com/Agents365-ai/drawio-skill.git ~/.claude/skills/drawio

# 项目级安装
git clone https://github.com/Agents365-ai/drawio-skill.git .claude/skills/drawio
```

### OpenClaw

```bash
# 通过 ClawHub 安装
clawhub install drawio

# 手动安装
git clone https://github.com/Agents365-ai/drawio-skill.git ~/.openclaw/skills/drawio

# 项目级安装
git clone https://github.com/Agents365-ai/drawio-skill.git skills/drawio
```

### Hermes Agent

```bash
# 安装到 design 分类
git clone https://github.com/Agents365-ai/drawio-skill.git ~/.hermes/skills/design/drawio
```

或在 `~/.hermes/config.yaml` 中添加外部目录：

```yaml
skills:
  external_dirs:
    - ~/myskills/drawio-skill
```

### OpenAI Codex

```bash
# 用户级安装
git clone https://github.com/Agents365-ai/drawio-skill.git ~/.agents/skills/drawio

# 项目级安装
git clone https://github.com/Agents365-ai/drawio-skill.git .agents/skills/drawio
```

### SkillsMP

在 [skillsmp.com](https://skillsmp.com) 搜索 `drawio` 或使用 CLI：

```bash
skills install drawio
```

### 安装路径总结

| 平台 | 全局路径 | 项目路径 |
|------|----------|----------|
| Claude Code | `~/.claude/skills/drawio/` | `.claude/skills/drawio/` |
| OpenClaw | `~/.openclaw/skills/drawio/` | `skills/drawio/` |
| Hermes Agent | `~/.hermes/skills/design/drawio/` | 通过 `external_dirs` 配置 |
| OpenAI Codex | `~/.agents/skills/drawio/` | `.agents/skills/drawio/` |
| SkillsMP | N/A（通过 CLI 安装） | N/A |

## 使用方式

直接描述你想要的图表：

```
画一个微服务电商架构图，包含 Mobile/Web/Admin 客户端，API Gateway，
Auth/User/Order/Product/Payment 微服务，Kafka 消息队列，Notification 服务，
以及各自独立的数据库
```

Claude 会自动生成 `.drawio` 文件并导出为 PNG。

## 示例

**提示词：**
> 画一个微服务电商架构图，包含 Mobile/Web/Admin 客户端，API Gateway（含认证+限流+路由），
> Auth/User/Order/Product/Payment 微服务，Kafka 消息队列，Notification 服务，
> User DB / Order DB / Product DB / Redis Cache / Stripe API

**输出效果：**

![微服务架构图](assets/microservices-example.png)

## 拓扑示例

本 skill 支持多种图表拓扑，线条路由清晰 —— 不会穿越无关的形状。

### 星形拓扑（7 个节点）

中央消息代理 + 6 个微服务辐射排列。连线从不同方向进入 Kafka，零交叉。

![星形拓扑](assets/demo-star-cn.png)

### 分层流程（10 个节点，4 层）

电商架构，含 2 条交叉连线：订单→商品（同层水平）和 认证→Redis（对角线，经路由走廊绕行）。所有线条路由清晰。

![分层流程](assets/demo-layered-cn.png)

### 环形 / 循环（8 个节点）

CI/CD 流水线，包含闭合回路和 2 个分支。线条沿矩形外围流动，不穿越内部区域。

![环形循环](assets/demo-ring-cn.png)

## 多平台支持

本 skill 兼容以下平台：

| 平台 | 支持状态 | 说明 |
|------|----------|------|
| **Claude Code** | ✅ 完全支持 | 原生 SKILL.md 格式 |
| **OpenClaw** | ✅ 完全支持 | `metadata.openclaw` 命名空间，依赖检测，安装器 |
| **Hermes Agent** | ✅ 完全支持 | `metadata.hermes` 命名空间，标签分类，工具门控 |
| **OpenAI Codex** | ✅ 完全支持 | `agents/openai.yaml` 侧车文件 |
| **SkillsMP** | ✅ 可索引 | GitHub topics 已配置 |

## 文件说明

- `SKILL.md` — **唯一必需的文件**，所有平台加载的 skill 指令
- `agents/openai.yaml` — OpenAI Codex 专用配置（界面、策略）
- `README.md` — 英文说明（GitHub 首页显示）
- `README_CN.md` — 本文件（中文）
- `assets/` — 示例图表和工作流图片

> **提示：** 仅 `SKILL.md` 是 skill 运行所必需的。`agents/openai.yaml` 仅 Codex 需要。`assets/`、`README.md` 和 `README_EN.md` 仅为文档用途，可以安全删除以节省空间。

> 所有示例图表均由 Claude Code 配合 Claude Opus 4.6 模型生成。

## 开源协议

MIT

## 支持作者

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
  </tr>
</table>

## 作者

**Agents365-ai**

- Bilibili: https://space.bilibili.com/441831884
- GitHub: https://github.com/Agents365-ai
