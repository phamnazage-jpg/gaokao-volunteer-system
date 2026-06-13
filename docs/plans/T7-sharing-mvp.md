# T7: 分享功能 MVP — 实施计划

**版本**: v1.0
**状态**: 设计 → 实施中 (T7.1/T7.2/T7.3/T7.4 已完成, T7.5 待办)
**关联文档**:

- [产品设计 v1 - 分享](../PRODUCT_DESIGN_v1.md)
- [分享功能设计 SHARING_DESIGN.md](../SHARING_DESIGN.md)
- [实施计划 v2 - T7 节](../IMPLEMENTATION_PLAN_v2.md#t7-分享功能mvp-)

---

## 0. 范围与现状

T7 包含 5 个子任务 (来自 IMPLEMENTATION_PLAN_v2.md §T7):

| ID   | 任务           | 优先级 | 状态      | 工时 |
| ---- | -------------- | :----: | --------- | :--: |
| T7.1 | 短链接生成     |   P1   | ✅ 已完成 |  1d  |
| T7.2 | 海报生成 (PIL) |   P1   | ✅ 已完成 | 1.5d |
| T7.3 | 权限控制 (3级) |   P1   | ✅ 已完成 |  1d  |
| T7.4 | 撤销与统计     |   P1   | ✅ 已完成 |  1d  |
| T7.5 | 分享页 WebUI   |   P1   | ⏳ 待办   | 0.5d |

**本文档将按子任务分节详细化设计; T7.1-T7.4 已实现, T7.5 为待办设计草案。**

---

## T7.1 短链接生成 ✅

### 目标

为每条志愿方案生成形如 `/s/ABC123` 的短链接, 满足:

- URL 简短, 便于微信/短信/朋友圈传播
- 持久映射 (SQLite)
- 访问可控 (有效期 / 密码 / 权限)
- 访问可统计 (次数 / 时间)

### 现状

- **数据存储**: `data/share/short_links.db` (SQLite, WAL 模式)
- **核心模块**: `data/share/short_link.py`
- **CLI 入口**: `scripts/gaokao-shortlink`
- **路由辅助**: `data.share.short_link.route_short_link(code, ...)` 供 Web 框架挂载 `/s/<code>` 时调用
- **测试**: `data/share/tests/test_short_link.py` (25 个 pytest 用例, 137 个断言)

### 短码生成

```
字母表: 0-9, A-Z, a-z  (62 字符, URL-safe, 无需 urlencode)
长度:   默认 6 位, 范围 4-16 位
空间:   62^6 = 56,800,235,584 ≈ 568 亿
随机源: secrets.choice (加密安全)
冲突处理: 创建时捕获 IntegrityError 重试, 默认 8 次
```

**碰撞估算** (生日悖论):

- N = 1000 万条已存在, 短码 6 位
- p(碰撞) ≈ 1 - exp(-N^2 / (2 \* 62^6)) ≈ 8.8e-5, 仍然极低
- 短码 7 位: 空间 3.5e10, 实际不会撞

### 数据模型 (SQLite)

```sql
CREATE TABLE IF NOT EXISTS share_links (
    code            TEXT PRIMARY KEY,
    report_id       TEXT NOT NULL,
    owner_id        TEXT NOT NULL DEFAULT 'anonymous',
    permission      TEXT NOT NULL DEFAULT 'comment',
    password_hash   TEXT,            -- pbkdf2 salt_hex$digest_hex（兼容历史 sha256 迁移）
    expires_at      REAL,            -- unix timestamp, NULL=永久
    revoked         INTEGER NOT NULL DEFAULT 0,
    access_count    INTEGER NOT NULL DEFAULT 0,
    last_access_at  REAL,
    created_at      REAL NOT NULL,
    note            TEXT
);
CREATE INDEX IF NOT EXISTS idx_share_links_report ON share_links(report_id);
CREATE INDEX IF NOT EXISTS idx_share_links_owner  ON share_links(owner_id);
CREATE INDEX IF NOT EXISTS idx_share_links_expires ON share_links(expires_at);
```

### Python API

```python
from data.share.short_link import ShortLinkService

svc = ShortLinkService()  # 默认 db = data/share/short_links.db
link = svc.create(
    report_id="R-2026-001",
    owner_id="alice",
    permission="read",          # read / comment / edit / admin
    password="s3cr3t",          # 可选
    ttl_days=7,                 # 有效期(7d), None=永久
    code_length=6,              # 默认 6
)
print(link.code)               # e.g. "aB3xY7"
print(build_url(link.code))    # "http://localhost:8000/s/aB3xY7"

# 解析 (校验状态 + 计入访问次数)
res = svc.resolve(link.code, password="s3cr3t")
# res.status in {ok, not_found, revoked, expired, password_required, password_wrong}

# 撤销
svc.revoke(link.code, owner_id="alice")  # False if already revoked / wrong owner

# 列表 / 统计
svc.list_by_report("R-2026-001")
svc.list_by_owner("alice")
svc.get_stats(link.code)         # {access_count, last_access_at, ...}
```

### CLI

```bash
# 创建
python scripts/gaokao-shortlink create \
    --report-id R-2026-001 --owner alice \
    --permission read --ttl-days 30

# 创建带密码
python scripts/gaokao-shortlink create \
    --report-id R-2026-001 --owner alice \
    --password s3cr3t --ttl-days 7

# 解析
python scripts/gaokao-shortlink resolve ABC123
python scripts/gaokao-shortlink resolve ABC123 --password s3cr3t

# 撤销 (可选 owner 校验)
python scripts/gaokao-shortlink revoke ABC123 --owner alice

# 列表 / 统计 / 清理
python scripts/gaokao-shortlink list --report R-2026-001
python scripts/gaokao-shortlink list --owner alice
python scripts/gaokao-shortlink stats ABC123
python scripts/gaokao-shortlink purge
```

### 接入 Web 框架

```python
# Flask 示意 (项目当前无 Web 框架, 由 T7.5 引入)
from data.share.short_link import route_short_link
from flask import jsonify, request

@app.route("/s/<code>")
def short_link(code):
    return jsonify(route_short_link(
        code,
        password=request.args.get("pwd"),
        base_url=request.host_url.rstrip("/"),
    ))
```

### 验证

- 单元测试: `python3 -m pytest data/share/tests/test_short_link.py -v` → 25 passed
- E2E CLI: 已通过 24 项断言 (含 create/resolve/revoke/list/stats/purge 全部子命令)
- 短码唯一性: 50 次连续 create 无冲突
- 访问控制: 撤销 / 过期 / 密码错误三种状态正确返回

### 已知限制 (P2)

- 当前使用 PBKDF2-HMAC-SHA256（16B salt + 200k iterations）；历史无盐 sha256 会在成功校验后自动迁移
- DB 单文件, 不支持水平扩展; 高 QPS 时建议迁 Redis
- 暂未做 IP 限流 / 访问频率限制 (T7.4 之后再补)

---

## T7.2 海报生成 (PIL) ⏳

### 目标

把方案生成 1080×1920 PNG/JPG 海报, 含:

- 标题 / 关键信息 (考生脱敏版本可选)
- 推荐院校 TOP3
- 二维码 (内容 = /s/{code})
- 底部品牌区 (Powered by 龙老师)

### 设计草案

```
依赖: Pillow (PIL), qrcode
入口: scripts/gaokao-poster
数据源: 报告 JSON + 短码
输出: data/share/posters/{report_id}_{code}.png
```

---

## T7.3 权限控制 (3级) ✅

### 目标

把短链接层的 `permission` 字段真正翻译成分享页可执行的 UI 能力与字段可见性策略：

| 级别 | 字段值    | UI 行为                    | 姓名展示              |
| ---- | --------- | -------------------------- | --------------------- |
| 只读 | `read`    | 隐藏所有编辑/评论入口      | 脱敏显示（如 `张**`） |
| 评论 | `comment` | 显示「提建议」入口，禁编辑 | 脱敏显示（如 `张**`） |
| 编辑 | `edit`    | 显示完整编辑权限           | 原样展示              |

### 本次落地

- **策略模块**：`data/share/permission.py`
  - `PermissionPolicy.for_permission(permission)`：把 `read/comment/edit/admin` 归一化成前端能力策略
  - `allows_field(field)` / `can("view|comment|edit")`：统一权限判断
  - 未知 permission 一律回退到最严格的 `read` 拒止策略（防止越权）
- **姓名脱敏复用**：复用 `data/orders/masking.py::mask_name`
  - 仅策略层决定 "该不该脱敏"
  - 基础脱敏算法仍由订单模块统一维护；公开分享场景再做保守收敛：3 字及以上中文名统一为 `姓+**`，非中文名统一为 `**`
- **路由辅助扩展**：`data.share.short_link.route_short_link_with_report(...)`
  - 在 T7.1 的 `route_short_link()` 之上叠加报告 payload 渲染
  - 支持 `report=` 直接注入，或 `report_loader(report_id)` 回调懒加载
  - resolve 失败（not_found / revoked / expired / password_required / password_wrong）时不下发 `rendered`，避免泄露元数据
- **字段裁剪规则**：
  - `read`：回传最小元信息 + 脱敏姓名（公开场景采用更严格的 `张**` / `**` 收敛规则）
  - `comment`：回传 `title / summary / recommendations / volunteers / score / rank / year / province` + 脱敏姓名，但不暴露手机号/身份证/内部备注/哈希
  - `edit`：开放完整编辑所需业务字段，但仍强制隐藏 `password_hash / internal_note / note / debug_info / raw_payload` 等内部字段

### Python API

```python
from data.share.permission import PermissionPolicy, render_report_payload
from data.share.short_link import route_short_link_with_report

policy = PermissionPolicy.for_permission("comment")
assert policy.can_view is True
assert policy.can_comment is True
assert policy.can_edit is False

rendered = render_report_payload("comment", report_dict, share_url="https://gk.example.com/s/ABC123")
# rendered = {
#   "permission": "comment",
#   "policy": {"can_view": True, "can_comment": True, "can_edit": False, "mask_name": True},
#   "visible_fields": [...],
#   "payload": {...},
#   "masked_fields": [...],
# }

out = route_short_link_with_report(
    "ABC123",
    password="s3cr3t",
    base_url="https://gk.example.com",
    report_loader=lambda report_id: load_report(report_id),
)
```

### 验证

- `python3 -m pytest data/share/tests/test_permission.py -q` → **34 passed**
- `python3 -m pytest data/share/tests/ -q` → **61 passed**
- `python3 -m pytest data/share/ data/orders/ -q` → **231 passed**
- `python3 -m ruff check data/share/permission.py data/share/tests/test_permission.py data/share/short_link.py` → **All checks passed**

### 设计取舍 / 已知限制

- `admin` 作为 T7.1 历史兼容值，当前按 `edit` alias 处理；T7.3 的业务语义仍是 3 级权限模型
- `edit` 允许手机号/身份证等编辑所需业务字段，但 `password_hash / internal_note / note / debug_info / raw_payload` 这类内部字段仍被策略层强制隐藏
- 当前 `read/comment` 采用"最小字段白名单"，优先防泄露；如果 T7.5 UI 需要额外字段，应在策略表中显式增补，而不是默认放开

---

## T7.4 撤销与统计 ✅

### 本次落地

- 批量撤销: `ShortLinkService.revoke_by_report(report_id, owner_id=None)`
  - 同一 report 下可一次性撤销全部分享；传 `owner_id` 时只撤销该 owner 创建的链接，避免越权
  - CLI 新增 `python scripts/gaokao-shortlink revoke-report --report-id R-2026-001 --owner alice`
- 访问统计升级: 基于 `share_link_access_events` 访问事件表记录每次成功 resolve
  - 保留 T7.1 的 `access_count / last_access_at`
  - 新增 `unique_visitors`（按 `visitor_token` 去重）
  - 新增 `daily_accesses`（按 UTC 日聚合 `access_count / unique_visitors`）
- 报告级统计: `ShortLinkService.get_report_stats(report_id, owner_id=None, days=7)`
  - 返回 `total_links / active_links / revoked_links / expired_links / total_access_count / unique_visitors / daily_accesses`
  - CLI 新增 `python scripts/gaokao-shortlink stats-report --report-id R-2026-001 --days 7`

### 设计取舍

- 本期先做访问事件表，支撑按日趋势和访客去重；地域统计仍保持 P2，待后续接入 IP 反查/风控链路时再补
- `visitor_token` 由调用方透传（如 openid / session id / cookie 指纹）；未传时仍统计访问次数，但 `unique_visitors` 不会虚构数据
- 每次成功 `resolve(record_access=True)` 同时更新汇总字段与事件表，兼顾现有接口兼容性和后续统计扩展

### 验证

- `python3 -m pytest data/share/tests/test_short_link.py -q` → 27 passed
- 覆盖新增用例：`revoke_by_report` owner 隔离、报告级批量撤销、按日趋势聚合、访客去重、报告级汇总统计

---

## T7.5 分享页 WebUI ⏳

### 路由

```
GET  /s/{code}            公开分享页 (权限受控)
GET  /s/{code}?pwd=xxx    带密码参数
```

### UI 草案 (响应式)

```
┌─────────────────────────────────┐
│  高考志愿填报方案    [龙老师]   │
├─────────────────────────────────┤
│  考生: 张**  (脱敏 by permission)│
│  分数: 578  位次: 12,345        │
├─────────────────────────────────┤
│  推荐院校 TOP3                  │
│  1. 江西财经大学 - 会计学 35%  │
│  2. ...                         │
├─────────────────────────────────┤
│  扫码查看完整方案               │
│  [二维码]                       │
└─────────────────────────────────┘
```

---

## 时间表 (来自 IMPLEMENTATION_PLAN_v2.md §6)

| 日期      | 任务           |
| --------- | -------------- |
| 7/10 (五) | T7.1 ✅ + T7.2 |
| 7/11 (六) | T7.3 + T7.4    |
| 7/12 (日) | T7.5           |

T7.1 已于 2026-06-12 提前完成 (本提交), T7.2 按计划开始。

---

## 验收

- [x] 短码生成 (base62, 6位, 加密随机)
- [x] SQLite 持久化 (WAL 模式, 自动建表)
- [x] CRUD: create / get / resolve / revoke
- [x] 访问控制: 权限 / 有效期 / 密码
- [x] 访问统计: 次数 / 时间
- [x] CLI: create / resolve / revoke / list / stats / purge
- [x] 路由辅助: `route_short_link(code, ...)` 可挂载到任意 Web 框架
- [x] 测试: 25 个 pytest 全部通过
- [ ] 海报生成 (T7.2)
- [ ] UI / Web 路由 (T7.5)
