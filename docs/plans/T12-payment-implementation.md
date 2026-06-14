# T12 Payment Implementation Plan

> **For Hermes:** 先补真实 provider 前的模型/回调/验签/退款占位，再做外部联调。

**Goal:** 让 T12 支付域从当前 `mock/alipay_sim` 过渡到真实 provider 可接入、可验签、可追踪的结构。

**Architecture:** 复用现有 `data/payments/*`，优先保持 provider 抽象统一；订单状态与支付状态分离，portal 阶段由聚合逻辑推导。

**Tech Stack:** FastAPI、SQLite、现有 payment service、provider requirements、doctor 脚本。

---

## 阶段 1：当前已完成

- provider requirements 基线
- `mock` / `alipay_sim` provider
- 模拟支付宝用户 E2E
- 真实 `alipay` provider 本地代码链
  - `data/payments/providers/alipay.py`
  - `POST /api/public/payments/alipay/notify`
  - `GET /portal/payment-return`
  - RSA2 签名校验
  - 金额校验 / 幂等防重
  - refund 占位模型与接口约束

## 阶段 2：当前仍需继续推进（外部前置阻塞）

1. 商户 app_id / 产品签约 / 私钥公钥
2. 备案域名与公网 `notify_url`
3. 沙箱或真实商户联调
4. 生产域名一次真实支付 acceptance
5. 对账任务 / 退款回写 / 异常补偿产品化

## 阶段 3：外部前置到位后执行

- 商户 app_id
- 私钥/支付宝公钥
- notify_url / return_url
- webhook secret
- 真实域名与公网入口

## 阶段 4：验收

- provider doctor ready=true
- 本地/测试环境 notify 模拟通过
- 真实沙箱/真实商户联调通过
- 支付成功后 portal 阶段自动推进
