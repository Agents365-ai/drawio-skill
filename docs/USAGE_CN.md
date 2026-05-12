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
