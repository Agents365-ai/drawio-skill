# 使用方式

[English](USAGE.md)

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

![微服务架构图](../assets/microservices-example.png)

## 拓扑示例

本 skill 支持多种图表拓扑，线条路由清晰 —— 不会穿越无关的形状。

### 星形拓扑（7 个节点）

中央消息代理 + 6 个微服务辐射排列。连线从不同方向进入 Kafka，零交叉。

![星形拓扑](../assets/demo-star-cn.png)

### 分层流程（10 个节点，4 层）

电商架构，含 2 条交叉连线：订单→商品（同层水平）和 认证→Redis（对角线，经路由走廊绕行）。所有线条路由清晰。

![分层流程](../assets/demo-layered-cn.png)

### 环形 / 循环（8 个节点）

CI/CD 流水线，包含闭合回路和 2 个分支。线条沿矩形外围流动，不穿越内部区域。

![环形拓扑](../assets/demo-ring-cn.png)

## 可视化代码库

把现有项目变成自动布局的结构图 —— 无需手动摆坐标。直接说：*"可视化这个 Python 项目的模块结构"* 或 *"画出 `mypackage` 的类继承层级"*。幕后是一条 提取器 → 自动布局 → 校验 的流水线：

```bash
# 导入关系图 —— Python / JS-TS / Go / Rust
python3 scripts/pyimports.py   myproject --group -o graph.json
python3 scripts/jsimports.py   ./src     --group -o graph.json
python3 scripts/goimports.py   ./module  --group -o graph.json
python3 scripts/rustimports.py ./crate   --group -o graph.json

# Python 类继承层级
python3 scripts/pyclasses.py   mypackage --group -o graph.json

# 任一提取器 → 自动布局 → 可编辑的 .drawio
python3 scripts/autolayout.py  graph.json -o diagram.drawio
```

Graphviz 自动布点，正交连线绕开节点，传递约简把密集图变清晰，`--group` 按子包给模块分框，`validate.py` 在视觉自检前先做结构 lint（悬空边、重复 id、重叠）。布局需要 Graphviz（`brew install graphviz` / `apt install graphviz`）—— 可选，其余功能无需它。

## 形状搜索

需要真实的 AWS / Azure / GCP / Cisco / Kubernetes / UML / BPMN 图标？Skill 会在 10,000+ 个官方 draw.io 形状中搜出精确的 style 字符串 —— 厂商图标正确渲染，而不是因为猜错 `shape=mxgraph.*` 名称而退化成空白方框：

```bash
python3 scripts/shapesearch.py "aws lambda" --limit 5
# → Lambda (77x93)
#   outlineConnect=0;...;shape=mxgraph.aws3.lambda;fillColor=#F58534;...
```

## AI / LLM 品牌图标

draw.io 没有任何现代 AI/LLM 品牌图标，所以画 LLM 应用架构时只能是一堆方框。`aiicons.py` 能把品牌名解析成 draw.io 图片样式，覆盖 [lobe-icons](https://github.com/lobehub/lobe-icons)（MIT）的 321 个图标（OpenAI、Claude、Gemini、Mistral、Llama、Ollama、LangChain……）：

```bash
python3 scripts/aiicons.py "claude" --json      # CDN 引用（默认）
python3 scripts/aiicons.py "openai" --embed     # 内联为自包含 data URI
```

## 在 CI 中渲染

在 GitHub Actions 里无头地重新生成、校验（`validate.py --strict`）并导出图表 —— 走 xvfb 下的 draw.io 桌面版或 Docker REST 渲染器。完整 workflow 配方见 [CI_CN.md](CI_CN.md)。
