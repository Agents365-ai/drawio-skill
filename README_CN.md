# drawio-skill

用于在 Claude Code 中生成 Draw.io 图表并本地导出为 PNG/SVG/PDF 的 skill。

[English](README.md)

## 功能说明

- 根据自然语言描述生成 `.drawio` XML 文件
- 使用 draw.io 桌面版原生 CLI 将图表导出为 PNG、SVG、PDF 或 JPG
- 支持多页图表和分层分组
- 迭代设计：预览、获取反馈、反复优化直到图表满意为止
- 当图表有助于解释复杂系统时自动触发

## 支持的图表类型

- **架构图**：微服务架构、云架构（AWS/GCP/Azure）、网络拓扑、部署架构
- **流程图**：业务流程、工作流、决策树、状态机
- **UML**：类图、序列图、用例图
- **数据图**：ER 图、数据流图（DFD）
- **其他**：组织架构图、思维导图、线框图

## 工作流程

![工作流程](assets/workflow-cn.png)

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
draw.io --version
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
xvfb-run -a draw.io --version
```

### 平台说明

| 平台 | 额外步骤 |
|------|----------|
| **macOS** | Homebrew 安装后无需额外操作 |
| **Windows** | 如不在 PATH 中，使用完整路径 |
| **Linux** | 无头导出时命令前加 `xvfb-run -a` |

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

## 文件说明

- `SKILL.md` — Claude Code 加载的 skill 指令文件
- `README.md` — 英文说明
- `README_CN.md` — 本文件（中文）
- `assets/` — 示例图表

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
