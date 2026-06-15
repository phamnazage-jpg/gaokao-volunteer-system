# PRODUCTION_DEPLOYMENT_CHECKLIST

最后更新: 2026-06-15
适用范围: `gaokao-volunteer-system` 在在线服务器上的首次部署 / 上线前联调
真相源: `docs/CURRENT_STATE.md`

---

## 1. 目标

本清单只解决三类上线前最后缺口：

1. 真实支付 acceptance
2. 真实 SMTP / IM 告警推送联调
3. 生产监控联调

不在本清单范围内：

- 新功能开发
- 本地模拟支付
- 历史审计回顾

---

## 2. 上线前准备材料

必须准备：

### 支付

- `GAOKAO_PAYMENT_PROVIDER`（如 `alipay`）
- `GAOKAO_PAYMENT_APP_ID`
- `GAOKAO_PAYMENT_PRIVATE_KEY_PATH`
- `GAOKAO_PAYMENT_ALIPAY_PUBLIC_KEY_PATH`
- `GAOKAO_PAYMENT_NOTIFY_URL`（公网可回调 URL）
- `GAOKAO_PAYMENT_RETURN_URL`
- `GAOKAO_PAYMENT_WEBHOOK_SECRET`

### 应用安全

- `GAOKAO_JWT_SECRET`
- `GAOKAO_PORTAL_TOKEN_SECRET`
- `GAOKAO_ORDERS_FERNET_KEY`
- `GAOKAO_ADMIN_PASS`

### Portal / 上传

- `GAOKAO_PORTAL_UPLOAD_DIR`
- `GAOKAO_PORTAL_UPLOAD_MAX_BYTES`
- `GAOKAO_PORTAL_UPLOAD_MAX_FILES`

### 告警

- `GAOKAO_SMTP_HOST`
- `GAOKAO_SMTP_PORT`
- `GAOKAO_SMTP_SENDER`
- `GAOKAO_SMTP_USER`
- `GAOKAO_SMTP_PASS`
- `GAOKAO_SMTP_USE_TLS`
- `GAOKAO_SMTP_USE_SSL`
- `GAOKAO_ALERT_RECIPIENTS`
- `GAOKAO_ALERT_WEBHOOK_URLS`
- `GAOKAO_OPS_ALERT_LOG`

### 基础运行

- `GAOKAO_ENV=prod`
- `GAOKAO_ADMIN_BIND`
- `GAOKAO_ADMIN_PORT`
- `GAOKAO_ORDERS_DB_PATH`
- `GAOKAO_SHARE_DB_PATH`
- `GAOKAO_SHARE_REPORT_DIR`
- `GAOKAO_PYTHON_BIN`

参考模板：

- `.env.docker.example`
- `deploy/systemd/gaokao-jobs.env.example`

---

## 3. 线上配置注入顺序

### Step 1: 安全密钥先到位

必须先配：

- JWT secret
- Portal token secret
- Orders fernet key
- Admin password

验证：

```bash
python - <<'PY'
from admin.config import load_settings
s = load_settings()
print('env', s.env)
print('jwt', len(s.jwt_secret))
print('portal', len(s.portal_token_secret))
PY
```

通过标准：

- 不使用默认 dev secret
- prod 配置 load_settings() 不抛异常

### Step 2: 目录与文件权限

确保这些路径存在且可写：

- orders db 所在目录
- share reports 目录
- portal uploads 目录
- ops alerts log 所在目录

验证：

```bash
mkdir -p /var/lib/gaokao/portal_uploads
mkdir -p /var/log/gaokao-volunteer-system
touch /var/log/gaokao-volunteer-system/ops-alerts.jsonl
```

### Step 3: SMTP / IM 配置

先注入配置，再做联调；不要边调边猜。

验证：

- SMTP 至少有 host + sender
- IM webhook 至少有 1 个可达 URL

---

## 4. 真实支付 acceptance（部署后）

### 必做路径

1. 启动生产配置应用
2. 打开 `/pricing`
3. 选一个服务创建订单
4. 跳转真实 provider 支付页
5. 完成真实支付
6. provider 回调命中 `GAOKAO_PAYMENT_NOTIFY_URL`
7. portal 状态页应从：
   - `pending_payment`
     自动推进到
   - `info_required`
8. 提交资料后推进到：
   - `processing`

### 验证命令

```bash
curl -i http://127.0.0.1:${GAOKAO_ADMIN_PORT}/health
curl -i http://127.0.0.1:${GAOKAO_ADMIN_PORT}/openapi.json
```

数据库核验：

```bash
sqlite3 "$GAOKAO_ORDERS_DB_PATH" "select id,status,amount_cents,paid_at from orders order by created_at desc limit 5;"
sqlite3 "$GAOKAO_ORDERS_DB_PATH" "select id,order_id,status,provider_trade_no,paid_at from payments order by created_at desc limit 5;"
```

通过标准：

- payment.status = paid
- order.status = paid 或后续状态
- provider_trade_no 已落库
- portal 状态页同步变化

禁止：

- 只验证跳转到支付页就说“支付完成”
- 只看 provider 成功页，不看回调落库

---

## 5. SMTP / IM 告警联调

### SMTP 联调

准备：

- `GAOKAO_ALERT_RECIPIENTS` 至少配置一个真实收件地址
- `GAOKAO_SMTP_*` 全量配置

手动触发：

```bash
python - <<'PY'
from admin.config import load_settings
from data.notifications.ops_alerts import build_alert_sink_from_settings
s = load_settings()
sink = build_alert_sink_from_settings(s)
result = sink.emit(
    alert_type='manual_probe',
    title='manual probe',
    body='smtp probe',
    details={'source':'deploy-check'}
)
print(result)
PY
```

通过标准：

- `ops-alerts.jsonl` 有日志
- 收件箱收到告警邮件

### IM webhook 联调

准备：

- `GAOKAO_ALERT_WEBHOOK_URLS` 至少配置一个真实 webhook

手动触发同上。

通过标准：

- `ops-alerts.jsonl` 有日志
- 对应 IM 渠道收到告警消息

禁止：

- 只验证日志写入就说“告警推送完成”
- 只配置 env 不做真实通道接收测试

---

## 6. 生产监控联调

当前仓库已经具备：

- watchdog
- ops alert sink
- admin ops alert page

上线前最少还要确认：

1. watchdog 周期运行
2. 失败时退出码为 2
3. 退出码失败会产生：
   - ops alert jsonl
   - SMTP 或 IM 告警
4. 后台 `/admin/ops-alerts` 可看到最新告警

建议联调路径：

1. 人为制造一个 delivery failure（如报告文件缺失）
2. 运行 watchdog
3. 验证：
   - 退出码 = 2
   - ops-alerts.jsonl 有记录
   - 邮件 / IM 收到告警
   - 后台运维告警页可见

---

## 7. 上线前最终验收清单

### A. 必须通过

- [ ] prod 配置可成功启动
- [ ] 真实支付回调成功落库
- [ ] portal 支付后状态自动推进
- [ ] 资料提交后状态推进到 processing
- [ ] watchdog 失败时产生真实告警
- [ ] `/admin/notifications` 可查看通知审计
- [ ] `/admin/ops-alerts` 可查看运维告警
- [ ] `bash scripts/backup_verify.sh --from-backup ...` 在目标机可跑通

### B. 不可伪完成

- [ ] 真实支付未测，不说“支付已完成”
- [ ] 真实 SMTP/IM 未收消息，不说“告警推送已完成”
- [ ] 未做恢复演练，不说“灾备已完成”

---

## 8. 最后的真实口径

上线前如果只完成了本地/测试环境，不应说：

- “生产可用”
- “支付已上线”
- “告警已联通”

只有在本清单第 7 节 A 全部打勾后，才能说：

> 当前版本已达到生产上线前的最小可验证标准。
