# 渠道 SDK 集成设计 (T8)

日期: 2026-06-12
作者: coder (kanban t_884fbeee)
关联任务: T8.1 闲鱼Webhook集成 / T8.2 微信SDK集成 / T8.3 企业微信集成 / T8.4 失败兜底
交付状态: T8.1/T8.2/T8.3 已实现并完成本地验证；远程推送不在本文档范围

---

## 0. 范围

本文档定义 v2.1 渠道 SDK 集成层（Channel Sync）的设计方案，以及 T8.1 闲鱼 Webhook、T8.2 微信最小 client、T8.3 企业微信最小 client 的当前实现边界。

目标: 在不引入重 SDK 依赖（不集成闲鱼/微信官方 SDK）的前提下,实现:

- **主路径**: Webhook 推送 + HMAC 签名校验 + 订单去重入库
- **兜底路径**: 定时轮询未确认订单 + 手动录入后台（人工兜底）
- **消息能力**: 基于标准库的微信/企业微信最小发送 client（payload 组装、token 缓存、错误包装）
- **不推荐**: 爬虫/逆向（合规风险,合规审计明确否决）

适用范围:

- 闲鱼(主)
- 微信（最小标准库 client 已实现；生产联调/企业认证不在本期）
- 企业微信（最小标准库 client 已实现；生产联调/企业配置开通不在本期）

---

## 1. 设计目标与不做清单

### 1.1 设计目标

1. **合规优先**: 仅使用平台公开的 Webhook / 开放 API,绝不爬虫/逆向
2. **订单自动同步**: 闲鱼下单/付款/退款事件在 5 分钟内进入 `orders` 表
3. **幂等性**: 同一外部订单号重复推送不产生重复记录（依赖既有 `uniq_orders_external` 唯一索引）
4. **签名校验**: HMAC-SHA256 校验 Webhook 头,失败立即拒绝
5. **可观测**: 所有 Webhook 接收/拒绝/解析失败均落审计表
6. **可降级**: Webhook 不可用时,轮询任务可独立运行并补偿

### 1.2 不做清单

- ❌ 不接入闲鱼/微信官方 SDK（避免依赖膨胀 + 合规边界）
- ❌ 不做用户身份 OAuth 登录（人工服务场景,客户名/手机号由人工补录）
- ❌ 不做 IM 消息实时收发（本期只做订单事件,消息推送属 T8.2）
- ❌ 不做自动发卡/自动发货（人工交付,避免合规风险）
- ❌ 不在宿主数据库内建表（v2.1 独立 SQLite,本期不写 sub2api）

---

## 2. 架构

```
                ┌─────────────────────────────────────────┐
                │  外部渠道 (闲鱼开放平台)                 │
                └────────────────────┬────────────────────┘
                                     │ HTTPS POST
                                     │  X-Signature: hmac-sha256=...
                                     │  X-Timestamp: 1700000000
                                     ▼
       ┌─────────────────────────────────────────────────────┐
       │  Channel Webhook Receiver (Python stdlib http.server)│
       │  ① 验签 → ② 去重 → ③ 解析 → ④ 写库 → ⑤ ACK         │
       └──────────────────────┬──────────────────────────────┘
                              │
                              ▼
                ┌─────────────────────────────┐
                │  data/orders DAO (T4.2)     │
                │  - upsert_by_external_id()  │
                │  - insert_status_history()  │
                └──────────────┬──────────────┘
                               │
                               ▼
                ┌─────────────────────────────┐
                │  data/channel_sync/         │
                │  - signature.py (HMAC)      │
                │  - xianyu_adapter.py        │
                │  - poller.py (兜底轮询)     │
                │  - audit.py (审计日志)      │
                └─────────────────────────────┘
```

### 2.1 模块清单

| 文件                                  | 职责                                            | 行数预估 |
| ------------------------------------- | ----------------------------------------------- | -------- |
| `data/channel_sync/__init__.py`       | 模块入口,导出公共 API                           | 30       |
| `data/channel_sync/signature.py`      | HMAC-SHA256 签名/校验,时间戳防重放              | 80       |
| `data/channel_sync/audit.py`          | Webhook 接收/拒绝/解析失败审计表                | 120      |
| `data/channel_sync/xianyu_adapter.py` | 闲鱼事件→Order 模型映射                         | 150      |
| `data/channel_sync/poller.py`         | 兜底轮询(从外部 API 拉未确认订单)               | 200      |
| `data/channel_sync/webhook_server.py` | 标准库 http.server 实现的最小 Webhook 接收端    | 180      |
| `data/channel_sync/dao_extension.py`  | 在 T4.2 DAO 之上添加 upsert_by_external_id 扩展 | 100      |
| `tests/test_xianyu_channel.py`        | 单测:签名/解析/去重/兜底轮询                    | 250+     |

合计 ≈ 1100 行(含测试)。

---

## 3. 关键流程

### 3.1 Webhook 接收流程

```
1. 接收 POST /webhook/xianyu
2. 读取 Header:
   - X-Signature: hmac-sha256=<hex>
   - X-Timestamp: <unix-seconds>
   - X-Nonce: <random>
3. 时间戳校验: |now - ts| <= 300s (防重放窗口 5 分钟)
4. 签名校验: HMAC-SHA256(secret, f"{ts}.{nonce}.{body}") == X-Signature
5. 解析 body (JSON) → XianyuEvent
6. 调 XianyuAdapter.to_order(event) → Order
7. DAO.upsert_by_external_id(source='xianyu', external_id=event.order_id, order=order)
   - 已存在: 更新 status / status_updated_at / 写历史
   - 不存在: insert
8. 写 audit_log(decision='accepted', event_id=..., order_id=...)
9. 返回 200 OK
```

### 3.2 兜底轮询流程

```
1. 定时任务(每 5 分钟):
   - 从 poller_state 读 cursor(上次拉取时间)
   - 调 XianyuOpenAPI.list_orders(since=cursor)
   - 对每个返回的订单:
     a. 若 orders 表已存在: 比对状态,有变化则更新
     b. 若不存在: insert + 写历史
   - 更新 cursor = max(updated_at)
   - 写 poller_run 审计行
2. 失败重试: 指数退避(5/15/45 分钟),3 次失败告警
3. 与 Webhook 关系: Webhook 为主路径,poller 补漏;同一订单在两端都到时,以外部订单号幂等
```

### 3.3 手动兜底

- 管理后台 (T6) 提供"新建订单"表单,source 字段可选 'xianyu'/'wechat'/'web'/'school'
- 提交时: external_id 留空可空(允许未带外部订单号的人工补录)
- 状态: 默认 pending,可手动推到 paid/serving/...

---

## 4. 数据契约

### 4.1 XianyuEvent(Webhook body 解析后)

```python
@dataclass
class XianyuEvent:
    event_id: str          # 闲鱼侧事件唯一 ID(用于去重审计)
    event_type: str        # 'order.created' | 'order.paid' | 'order.refunded'
    order_id: str          # 闲鱼订单号 → external_id
    service_version: str   # 'audit' | 'basic' | 'standard' | 'premium'
    amount_cents: int      # 单位:分
    customer_name: str
    customer_phone: str
    customer_wechat: Optional[str]
    candidate_name: Optional[str]
    candidate_province: Optional[str]
    created_at: str        # ISO8601
    paid_at: Optional[str]
    refunded_at: Optional[str]
```

### 4.2 状态映射

| 闲鱼 event_type | Order.status | 备注               |
| --------------- | ------------ | ------------------ |
| order.created   | pending      | 拍下未付           |
| order.paid      | paid         | 担保交易付款成功   |
| order.delivered | serving      | (可选,闲鱼发货)    |
| order.completed | completed    | 交易完成           |
| order.refunded  | refunded     | 退款(任意阶段可入) |

转换合法性由 `data/orders/state_machine.py` 的 `ALLOWED_TRANSITIONS` 强制约束。

### 4.3 审计表 (新增)

```sql
CREATE TABLE IF NOT EXISTS webhook_audit (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    received_at     TEXT NOT NULL,
    channel         TEXT NOT NULL,           -- 'xianyu'
    event_id        TEXT,
    decision        TEXT NOT NULL,           -- 'accepted' | 'rejected' | 'parse_error' | 'duplicate'
    reject_reason   TEXT,
    order_id        TEXT,                    -- 已映射到的内部订单号
    raw_body_hash   TEXT,                    -- SHA-256(body),避免大字段落库
    remote_addr     TEXT
);

CREATE INDEX IF NOT EXISTS idx_webhook_audit_event
    ON webhook_audit(channel, event_id);
```

---

## 5. 安全与合规

### 5.1 签名密钥管理

- 来源: 环境变量 `GAOKAO_XIANYU_WEBHOOK_SECRET`
- 不入库,不入 git,不在日志中打印完整 secret
- 测试用固定值 `test-secret-for-unit-tests` 通过环境变量注入

### 5.2 防重放

- 时间戳窗口 300s(可配置 `XIANYU_WEBHOOK_TS_TOLERANCE`)
- 已用 nonce 缓存 10 分钟(内存 + 审计表任选其一;v1 用内存 LRU)

### 5.3 限流

- 单 IP 60 req/min(标准库实现,避免引入 redis)
- 超出返回 429 + Retry-After

### 5.4 数据脱敏

- 接收时即按既有 `data/orders/crypto.py` 加密手机/身份证
- 审计表只存 raw_body_hash,不存原始 body(避免敏感信息二次落地)

### 5.5 合规边界

- 仅接收业务事件,不主动调用闲鱼 API 抓取用户/聊天/地址等敏感信息
- 退款事件只更新订单状态,不主动调退款 API(避免代操作风险)
- 客户身份证号不在 Webhook 中接收(如闲鱼返回则丢弃,落审计 `reject_reason='pii_dropped'`)

---

## 6. 部署与运行

### 6.1 启动 Webhook 服务

```bash
# 监听 0.0.0.0:8080,挂载 /webhook/xianyu 路由
GAOKAO_XIANYU_WEBHOOK_SECRET=<...> \
GAOKAO_ORDERS_FERNET_KEY=<...> \
python -m data.channel_sync.webhook_server --port 8080
```

### 6.2 启动兜底轮询(独立进程)

```bash
# 每 5 分钟拉一次
python -m data.channel_sync.poller --interval 300
```

### 6.3 关闭 Webhook 时的兜底

- Webhook 不可用(闲鱼平台维护)时,poller 仍运行
- 平台恢复后,poller 与 Webhook 数据自动按 external_id 幂等合并

---

## 7. T8 任务依赖与拆分

| ID   | 任务            | 依赖 | 落地文件                                                      | 状态        |
| ---- | --------------- | ---- | ------------------------------------------------------------- | ----------- |
| T8.1 | 闲鱼Webhook集成 | T4.1 | 本设计 + channel_sync/\* + tests/test_xianyu_channel.py       | 已实现并本地验证 |
| T8.2 | 微信SDK集成     | T8.1 | channel_sync/wechat_adapter.py + tests/test_wechat_adapter.py | 已实现并本地验证 |
| T8.3 | 企业微信集成    | T8.2 | channel_sync/wecom_adapter.py + tests/test_wecom_adapter.py   | 已实现并本地验证 |
| T8.4 | 失败兜底(手动)  | T6   | T6 管理后台"新建订单"表单 + poller 自动补偿                   | T6 实施时补 |

T8.1 不阻塞 T6/T7;但 T6 必须有"手动新建"入口作为兜底。

---

## 8. 验收标准 (T8.1 DoD)

- [ ] 接收 `POST /webhook/xianyu` 能解析 body 并入库(单测 + 集成测试覆盖)
- [ ] 签名错误 / 时间戳过期 → 401/408 拒绝,审计记录 `decision='rejected'`
- [ ] 重复 event_id → 不重复入库,审计记录 `decision='duplicate'`
- [ ] Webhook 主路径与 poller 兜底路径在并发下幂等(单测覆盖)
- [ ] webhook_audit 表 schema 与索引存在
- [ ] `pytest data/orders/tests data/channel_sync/tests -q` 全绿
- [ ] 核心代码覆盖率 ≥ 80%
- [ ] gofmt/ruff 等价: ruff check data/channel_sync 0 warning
- [ ] 文档落地:本文件 + CHANGELOG + IMPLEMENTATION_PLAN 更新
- [ ] 已提交到本地 git,推送 3 仓(GitHub/tksea/gitea-local)

---

## 9. 风险与缓解

| 风险                          | 可能性 | 影响 | 缓解                                                |
| ----------------------------- | ------ | ---- | --------------------------------------------------- |
| 闲鱼未公开 Webhook 协议       | 高     | 高   | 本设计采用通用 HMAC 模式,可在签约开放平台时按需调整 |
| 平台限流 / IP 黑名单          | 中     | 中   | poller 兜底 + 退避重试                              |
| 客户身份证号出现在 Webhook 中 | 中     | 高   | 接收时丢弃 PII 字段,审计记录 reject_reason          |
| 订单状态与闲鱼侧不一致        | 中     | 中   | 状态机强制约束 + 历史审计,异常告警                  |
| 测试覆盖率不达 80%            | 低     | 中   | TDD 强制,先写单测再实现                             |

---

## 10. 不在本期范围

- 微信 SDK 生产联调与企业认证申请（本任务仅落地标准库 client + payload/错误处理封装）
- 闲鱼 IM 消息自动回复(属客服机器人,独立产品)
- 闲鱼退款自动审批(人工审核更安全)
- 多渠道统一网关(等 T8.1/T8.2/T8.3 都稳定后做抽象层)
