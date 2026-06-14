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

## 阶段 2：当前应继续推进

1. 真实 provider 文件骨架
   - `data/payments/providers/alipay.py`
2. notify 回调入口
   - `POST /api/public/payments/alipay/notify`
3. return 回跳入口
   - `GET /portal/payment-return`
4. provider 签名校验
5. 金额校验 / 幂等防重
6. refund 占位模型与接口约束

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
