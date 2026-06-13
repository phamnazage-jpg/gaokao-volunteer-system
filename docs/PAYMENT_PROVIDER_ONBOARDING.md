# T12 真实支付 Provider 接入与上线验收

## 当前结论

- 当前仓库已完成 **Mock 支付本地闭环**。
- 若要把 T12 推进到 **真实收款/线上验收完成**，当前最短路径建议：**支付宝优先，微信支付第二阶段补齐**。
- 当前机器/仓库未发现任何真实支付环境变量或证书路径配置，因此真实 provider 仍被外部条件阻塞。

## 为什么推荐支付宝优先

1. 当前支付模型只有 `checkout_url`，更贴合支付宝网页支付跳转模式。
2. 当前前端是静态 HTML + 少量 JS，不是小程序优先，也不是重前端。
3. Python/FastAPI 对接支付宝的工程形态更接近当前 checkout / return / notify 结构。

## 当前代码口径

- 本地闭环 provider: `mock`
- 配置键：
  - `GAOKAO_PAYMENT_PROVIDER`
  - `GAOKAO_PAYMENT_BASE_URL`
  - `GAOKAO_PAYMENT_WEBHOOK_SECRET`
  - `GAOKAO_PAYMENT_NOTIFY_URL`
  - `GAOKAO_PAYMENT_RETURN_URL`
  - `GAOKAO_PAYMENT_APP_ID`
  - `GAOKAO_PAYMENT_PRIVATE_KEY_PATH`
  - `GAOKAO_PAYMENT_ALIPAY_PUBLIC_KEY_PATH`

## 接入前置检查

先跑：

```bash
python3 scripts/payment_provider_doctor.py
```

### 期望结果

- `provider=mock`：ready=true，只代表本地/测试闭环
- `provider=alipay`：若缺少 app_id / key_path / notify_url / return_url，会返回 ready=false

## 支付宝最小上线前置

1. 企业/个体商户主体
2. 支付宝开放平台应用 `app_id`
3. 应用私钥文件
4. 支付宝公钥文件
5. 产品签约（电脑网站支付 / 手机网站支付）
6. 已备案域名
7. 公网可访问 `notify_url`
8. 明确 `return_url`

## 推荐环境变量模板

```bash
export GAOKAO_PAYMENT_PROVIDER=alipay
export GAOKAO_PAYMENT_BASE_URL=https://your-domain.example
export GAOKAO_PAYMENT_WEBHOOK_SECRET=replace-with-independent-payment-secret
export GAOKAO_PAYMENT_NOTIFY_URL=https://your-domain.example/api/public/payments/alipay/notify
export GAOKAO_PAYMENT_RETURN_URL=https://your-domain.example/portal/payment-return
export GAOKAO_PAYMENT_APP_ID=your-app-id
export GAOKAO_PAYMENT_PRIVATE_KEY_PATH=/secure/path/alipay_private.pem
export GAOKAO_PAYMENT_ALIPAY_PUBLIC_KEY_PATH=/secure/path/alipay_public.pem
```

## 当前外部阻塞（不可绕过）

- 无真实商户主体/签约产品
- 无真实支付证书/密钥文件
- 无公网 notify URL
- 无生产域名备案验收证据

## 真正完成 T12 的下一跳

当上面四类外部条件具备后，继续执行：

1. 实装支付宝 provider
2. 增加 `notify` / `return` 真实路由
3. 沙箱联调
4. 生产域名回调联调
5. 真实下单→支付→回调→portal 状态页→报告交付验收
