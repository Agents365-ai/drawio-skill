# 对比

[English](COMPARISON.md)

## 与无 skill 的原生智能体对比

| 功能 | 原生智能体 | 本 skill |
|------|-----------|---------|
| 生成 draw.io XML | 是 — LLM 本身了解格式 | 是 |
| 导出后自检 | 否 | 是 — 读取 PNG 自动修复 6 类问题 |
| 迭代反馈循环 | 否 — 需手动重新提问 | 是 — 定向编辑，5 轮安全阀 |
| 主动触发 | 否 — 仅在明确要求时 | 是 — 3+ 组件时自动建议画图 |
| 布局规范 | 无 — 每次结果不一致 | 按复杂度分级间距、路由走廊、hub 居中策略 |
| 网格对齐 | 否 | 是 — 所有坐标对齐到 10px 倍数 |
| 图表类型预设 | 否 | 是 — 6 种预设（ERD、UML、序列图、架构图、ML/DL、流程图） |
| 可视化代码库 | 否 | 是 — 导入关系图（Py/JS/Go/Rust）+ 类图 |
| 大图自动布局 | 否 — 手动摆放、易重叠 | 是 — Graphviz 布点、正交路由、嵌套容器 |
| 结构校验 | 否 | 是 — 确定性 `.drawio` linter |
| 官方形状搜索 | 否 — 靠猜、变空白框 | 是 — 1 万+ AWS/Azure/GCP/UML 形状的精确 style |
| AI/LLM 品牌图标 | 否 — 没有 | 是 — 321 个 logo（OpenAI/Claude/Gemini/…）经 aiicons.py |
| 动画连接线 | 否 | 是 — `flowAnimation=1` 数据流可视化 |
| ML/DL 模型图 | 否 | 是 — 张量形状标注、层类型配色 |
| 配色方案 | 随机/不一致 | 7 色语义系统（蓝=服务、绿=数据库、紫=安全…） |
| 连线路由规则 | 基础 | 锚点分配、连接分布、走廊绕行 |
| 容器/分组 | 无 | Swimlane、Group、自定义容器 + 父子嵌套 |
| 嵌入式导出 | 否 | 是 — `--embed-diagram` 保持导出文件可编辑 |
| 浏览器降级 | 否 | 是 — CLI 不可用时生成 diagrams.net URL |
| 自动启动桌面版 | 否 | 是 — 导出后自动打开 `.drawio` 文件精修 |

## 与其他 draw.io Skills / 工具对比

| 功能 | 本 skill | [jgraph/drawio-mcp](https://github.com/jgraph/drawio-mcp)（官方）![stars](https://img.shields.io/github/stars/jgraph/drawio-mcp?style=flat-square&logo=github) | [bahayonghang/drawio-skills](https://github.com/bahayonghang/drawio-skills) ![stars](https://img.shields.io/github/stars/bahayonghang/drawio-skills?style=flat-square&logo=github) | [GBSOSS/ai-drawio](https://github.com/GBSOSS/ai-drawio) ![stars](https://img.shields.io/github/stars/GBSOSS/ai-drawio?style=flat-square&logo=github) |
|---------|-----------|---------------|-------------------|--------------|
| **方式** | 纯 SKILL.md | MCP 服务 / Claude Code 插件 / Project | YAML DSL + CLI（MCP 可选） | Claude Code 插件 |
| **依赖** | 仅 draw.io 桌面版 | draw.io 桌面版 | draw.io 桌面版（MCP 可选） | draw.io 插件 + 浏览器 |
| **多智能体** | ✅ 6 个平台 | ⚠️ MCP 宿主（Claude、Cursor、VS Code） | ✅ Claude / Gemini / Codex | ❌ 仅 Claude Code |
| **自检** | ✅ 2 轮视觉自检（读取 PNG） | ❌ | ✅ 校验 + 严格模式 | ❌ 仅截图 |
| **迭代审查** | ✅ 5 轮循环 | ❌ 一次生成 | ✅ 3 种工作流（create/edit/replicate） | ❌ |
| **布局指南** | ✅ 按复杂度分级 + 网格对齐 | ✅ 基础间距 | ✅ design-system | ❌ |
| **图表预设** | ✅ 6 种（ERD、UML、序列、架构、ML、流程） | ❌ | ✅ 论文模式分类（架构/路线图/工作流） | ❌ |
| **动画连线** | ✅ `flowAnimation=1` | ❌ | ❌ | ❌ |
| **ML/DL 图** | ✅ 张量标注、层配色 | ❌ | ❌ | ❌ |
| **配色系统** | ✅ 7 色语义 | ❌ | ✅ 6 种主题 | ❌ |
| **官方形状搜索** | ✅ 1 万+ 形状（本地） | ✅ 1 万+ 形状（MCP） | ❌ | ❌ |
| **AI/LLM 品牌图标** | ✅ 321 个（lobe-icons） | ❌ | ❌ | ❌ |
| **容器/分组** | ✅ swimlane + group | ✅ 详细 | ❌ | ❌ |
| **嵌入式导出** | ✅ `--embed-diagram` | ✅ | ❌ | ❌ |
| **连线路由** | ✅ 走廊 + waypoints | ✅ 箭头间距规则 + libavoid 自动绕行 | ❌ | ❌ |
| **浏览器降级** | ✅ diagrams.net URL | ✅ diagrams.net URL（插件）+ 内联预览 | ✅ 通过可选 MCP | ✅ diagrams.net viewer（主要） |
| **自动启动** | ✅ 打开桌面版 | ❌ | ❌ | ✅ 打开 Chrome |
| **云图标** | AWS 基础 | ❌ | ✅ AWS/GCP/Azure/K8s | ✅ AWS 基础 |
| **零配置** | ✅ 复制 skills/drawio-skill/ | ✅ | ✅ 桌面版模式 | ❌ 需安装插件 |

_最近一次依据各 repo README 核查：2026-07-10。如有出入欢迎提 issue / PR 修正 —— 竞品在演进，表格的准确性依赖社区帮助。_

## 核心优势

1. **自检 + 迭代循环** — 唯一纯 SKILL.md 方案中能自动读取输出、修复问题、支持多轮优化的
2. **6 种图表类型预设** — ERD、UML 类图、序列图、架构图、ML/深度学习、流程图 — 每种都有预设形状、样式和布局规范
3. **ML/DL 模型图** — 张量形状标注、层类型配色、编码器/解码器泳道 — 专为学术论文打造
4. **多智能体、零配置** — 跨 6 个平台运行，仅需 `skills/drawio-skill/` 目录 + draw.io 桌面版，无需 MCP、Python、Node.js、浏览器
5. **专业级布局** — 网格对齐坐标、按复杂度分级间距、路由走廊、hub 居中策略、动画连接线
6. **浏览器降级** — 桌面 CLI 不可用时生成 diagrams.net URL，导出后自动启动桌面版编辑
