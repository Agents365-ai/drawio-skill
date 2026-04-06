# drawio-skill — From Text to Professional Diagrams

[English](README.md)

## 功能说明

- 根据自然语言描述生成 `.drawio` XML 文件
- 使用 draw.io 桌面版原生 CLI 将图表导出为 PNG、SVG、PDF 或 JPG
- **6 种图表类型预设**：ERD、UML 类图、序列图、架构图、ML/深度学习、流程图 — 包含预设形状、样式和布局规范
- **动画连接线** (`flowAnimation=1`) 适用于数据流和管道图（在 SVG 和 draw.io 桌面版中可见）
- **ML 模型图支持** 带张量形状标注 `(B, C, H, W)` — 适合 NeurIPS/ICML/ICLR 论文
- **网格对齐布局** — 所有坐标对齐到 10px 倍数，确保整洁对齐
- **浏览器降级方案** — 当桌面 CLI 不可用时生成 diagrams.net URL
- 迭代设计：预览、获取反馈、反复优化直到图表满意为止
- **自动启动** draw.io 桌面版，导出后可直接精修
- 当图表有助于解释复杂系统时自动触发

## 多平台支持

兼容所有主流支持 [Agent Skills](https://agentskills.io) 格式的 AI 编码智能体：

| 平台 | 支持状态 | 说明 |
|------|----------|------|
| **Claude Code** | ✅ 完全支持 | 原生 SKILL.md 格式 |
| **OpenClaw** | ✅ 完全支持 | `metadata.openclaw` 命名空间，依赖检测，安装器 |
| **Hermes Agent** | ✅ 完全支持 | `metadata.hermes` 命名空间，标签分类，工具门控 |
| **OpenAI Codex** | ✅ 完全支持 | `agents/openai.yaml` 侧车文件 |
| **SkillsMP** | ✅ 可索引 | GitHub topics 已配置 |

## 对比

### 与无 skill 的原生智能体对比

| 功能 | 原生智能体 | 本 skill |
|------|-----------|---------|
| 生成 draw.io XML | 是 — LLM 本身了解格式 | 是 |
| 导出后自检 | 否 | 是 — 读取 PNG 自动修复 6 类问题 |
| 迭代反馈循环 | 否 — 需手动重新提问 | 是 — 定向编辑，5 轮安全阀 |
| 主动触发 | 否 — 仅在明确要求时 | 是 — 3+ 组件时自动建议画图 |
| 布局规范 | 无 — 每次结果不一致 | 按复杂度分级间距、路由走廊、hub 居中策略 |
| 网格对齐 | 否 | 是 — 所有坐标对齐到 10px 倍数 |
| 图表类型预设 | 否 | 是 — 6 种预设（ERD、UML、序列图、架构图、ML/DL、流程图） |
| 动画连接线 | 否 | 是 — `flowAnimation=1` 数据流可视化 |
| ML/DL 模型图 | 否 | 是 — 张量形状标注、层类型配色 |
| 配色方案 | 随机/不一致 | 7 色语义系统（蓝=服务、绿=数据库、紫=安全…） |
| 连线路由规则 | 基础 | 锚点分配、连接分布、走廊绕行 |
| 容器/分组 | 无 | Swimlane、Group、自定义容器 + 父子嵌套 |
| 嵌入式导出 | 否 | 是 — `--embed-diagram` 保持导出文件可编辑 |
| 浏览器降级 | 否 | 是 — CLI 不可用时生成 diagrams.net URL |
| 自动启动桌面版 | 否 | 是 — 导出后自动打开 `.drawio` 文件精修 |

### 与其他 draw.io Skills / 工具对比

| 功能 | 本 skill | [jgraph/drawio-mcp](https://github.com/jgraph/drawio-mcp)（官方，1.3k⭐） | [bahayonghang/drawio-skills](https://github.com/bahayonghang/drawio-skills)（60⭐） | [GBSOSS/ai-drawio](https://github.com/GBSOSS/ai-drawio)（63⭐） |
|---------|-----------|---------------|-------------------|--------------|
| **方式** | 纯 SKILL.md | SKILL.md / MCP / Project | YAML DSL + MCP | 插件 + 浏览器 |
| **依赖** | 仅 draw.io 桌面版 | draw.io 桌面版 | MCP 服务（`npx`） | 浏览器 + 本地服务 |
| **多智能体** | ✅ 5 个平台 | ❌ 仅 Claude Code | ❌ 仅 Claude Code | ❌ |
| **自检** | ✅ 2 轮自动修复 | ❌ | ❌ | ❌ 截图 |
| **迭代审查** | ✅ 5 轮循环 | ❌ 一次生成 | ✅ 3 种工作流 | ❌ |
| **布局指南** | ✅ 按复杂度分级 + 网格对齐 | ✅ 基础间距 | ❌ 依赖 MCP | ❌ |
| **图表预设** | ✅ 6 种（ERD、UML、序列、架构、ML、流程） | ❌ | ❌ | ❌ |
| **动画连线** | ✅ `flowAnimation=1` | ❌ | ❌ | ❌ |
| **ML/DL 图** | ✅ 张量标注、层配色 | ❌ | ❌ | ❌ |
| **配色系统** | ✅ 7 色语义 | ❌ | ✅ 5 种主题 | ❌ |
| **容器/分组** | ✅ swimlane + group | ✅ 详细 | ❌ | ❌ |
| **嵌入式导出** | ✅ `--embed-diagram` | ✅ | ❌ | ❌ |
| **连线路由** | ✅ 走廊 + waypoints | ✅ 箭头间距规则 | ❌ | ❌ |
| **浏览器降级** | ✅ diagrams.net URL | ❌ | ❌ | ❌ |
| **自动启动** | ✅ 打开桌面版 | ❌ | ❌ | ❌ |
| **云图标** | AWS 基础 | ❌ | ✅ AWS/GCP/Azure/K8s | ❌ |
| **零配置** | ✅ 复制 SKILL.md | ✅ | ❌ 需要 `npx` | ❌ 需安装插件 |

### 核心优势

1. **自检 + 迭代循环** — 唯一纯 SKILL.md 方案中能自动读取输出、修复问题、支持多轮优化的
2. **6 种图表类型预设** — ERD、UML 类图、序列图、架构图、ML/深度学习、流程图 — 每种都有预设形状、样式和布局规范
3. **ML/DL 模型图** — 张量形状标注、层类型配色、编码器/解码器泳道 — 专为学术论文打造
4. **多智能体、零配置** — 跨 5 个平台运行，仅需一个 `SKILL.md` 文件 + draw.io 桌面版，无需 MCP、Python、Node.js、浏览器
5. **专业级布局** — 网格对齐坐标、按复杂度分级间距、路由走廊、hub 居中策略、动画连接线
6. **浏览器降级** — 桌面 CLI 不可用时生成 diagrams.net URL，导出后自动启动桌面版编辑

## 支持的图表类型

- **架构图**：微服务架构、云架构（AWS/GCP/Azure）、网络拓扑、部署架构 — 带分层泳道和 hub 居中策略
- **ML / 深度学习**：Transformer、CNN、LSTM、GRU 架构 — 带张量形状标注和层类型配色
- **流程图**：业务流程、工作流、决策树、状态机 — 带语义形状（平行四边形 I/O、菱形判断）
- **UML**：类图（继承/组合/聚合箭头）、序列图（生命线、激活框）
- **数据图**：ER 图（表容器、PK/FK 标记）、数据流图（DFD）
- **其他**：组织架构图、思维导图、线框图

## 工作流程

<p align="center">
  <img src="assets/workflow-cn.png" width="420" alt="工作流程">
</p>

## 前置依赖

需要安装 draw.io 桌面版用于图表导出：

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

| 平台 | 额外步骤 |
|------|----------|
| **macOS** | Homebrew 安装后无需额外操作 |
| **Windows** | 如不在 PATH 中，使用完整路径 |
| **Linux** | 无头导出时命令前加 `xvfb-run -a` |

## Skill 安装

### Claude Code

```bash
# 全局安装（所有项目可用）
git clone https://github.com/Agents365-ai/drawio-skill.git ~/.claude/skills/drawio-skill

# 项目级安装
git clone https://github.com/Agents365-ai/drawio-skill.git .claude/skills/drawio-skill
```

### OpenClaw

```bash
# 通过 ClawHub 安装
clawhub install drawio-pro-skill

# 手动安装
git clone https://github.com/Agents365-ai/drawio-skill.git ~/.openclaw/skills/drawio-skill

# 项目级安装
git clone https://github.com/Agents365-ai/drawio-skill.git skills/drawio-skill
```

### Hermes Agent

```bash
# 安装到 design 分类
git clone https://github.com/Agents365-ai/drawio-skill.git ~/.hermes/skills/design/drawio-skill
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
git clone https://github.com/Agents365-ai/drawio-skill.git ~/.agents/skills/drawio-skill

# 项目级安装
git clone https://github.com/Agents365-ai/drawio-skill.git .agents/skills/drawio-skill
```

### SkillsMP

在 [SkillsMP](https://skillsmp.com/skills/agents365-ai-drawio-skill-skill-md) 浏览或使用 CLI：

```bash
skills install drawio-skill
```

### ClawHub

在 [ClawHub](https://clawhub.ai/agents365-ai/drawio-pro-skill) 浏览或使用 CLI：

```bash
clawhub install drawio-pro-skill
```

### 安装路径总结

| 平台 | 全局路径 | 项目路径 |
|------|----------|----------|
| Claude Code | `~/.claude/skills/drawio-skill/` | `.claude/skills/drawio-skill/` |
| OpenClaw | `~/.openclaw/skills/drawio-skill/` | `skills/drawio-skill/` |
| Hermes Agent | `~/.hermes/skills/design/drawio-skill/` | 通过 `external_dirs` 配置 |
| OpenAI Codex | `~/.agents/skills/drawio-skill/` | `.agents/skills/drawio-skill/` |
| SkillsMP | N/A（通过 CLI 安装） | N/A |

## 更新

检查是否有新版本：

```bash
# 从任意位置运行 — 传入安装路径
bash ~/.claude/skills/drawio-skill/scripts/check-update.sh

# 或在 skill 目录下运行
cd ~/.claude/skills/drawio-skill && bash scripts/check-update.sh
```

更新到最新版本：

```bash
cd <你的安装路径>/drawio-skill && git pull
```

平台包管理器：

```bash
# OpenClaw
clawhub update drawio-skill

# SkillsMP
skills update drawio-skill
```

## 使用方式

直接描述你想要的图表：

```
画一个微服务电商架构图，包含 Mobile/Web/Admin 客户端，API Gateway，
Auth/User/Order/Product/Payment 微服务，Kafka 消息队列，Notification 服务，
以及各自独立的数据库
```

智能体会自动生成 `.drawio` 文件并导出为 PNG。

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

## 文件说明

- `SKILL.md` — **唯一必需的文件**，所有平台加载的 skill 指令
- `agents/openai.yaml` — OpenAI Codex 专用配置（界面、策略）
- `scripts/check-update.sh` — 轻量级更新检查器（比较本地与远程 HEAD）
- `README.md` — 英文说明（GitHub 首页显示）
- `README_CN.md` — 本文件（中文）
- `assets/` — 示例图表和工作流图片

> **提示：** 仅 `SKILL.md` 是 skill 运行所必需的。`agents/openai.yaml` 仅 Codex 需要。`assets/` 和 README 文件仅为文档用途，可以安全删除以节省空间。

> 所有示例图表均由 Claude Opus 4.6 配合本 skill 生成。

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
