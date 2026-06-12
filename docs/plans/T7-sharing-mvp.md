# T7: 分享功能 MVP — 实施计划

**版本**: v1.0
**状态**: 设计 → 实施中 (T7.1 已完成, T7.2 等待)
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
| T7.2 | 海报生成 (PIL) |   P1   | ⏳ 待办   | 1.5d |
| T7.3 | 权限控制 (3级) |   P1   | ⏳ 待办   |  1d  |
| T7.4 | 撤销与统计     |   P1   | ⏳ 待办   |  1d  |
| T7.5 | 分享页 WebUI   |   P1   | ⏳ 待办   | 0.5d |

**本文档将按子任务分节详细化设计; T7.1 已实现, 其它章节为待办设计草案。**

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
    password_hash   TEXT,            -- sha256 hex (无盐, 简单场景)
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

- 密码用 sha256 无盐哈希, 简单场景够用; 真实部署应换 argon2
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

## T7.3 权限控制 (3级) ⏳

| 级别 | 字段值    | UI 行为            |
| ---- | --------- | ------------------ |
| 只读 | `read`    | 隐藏所有编辑入口   |
| 评论 | `comment` | 显示「提建议」入口 |
| 编辑 | `edit`    | 显示完整编辑权限   |

T7.1 已在 `permission` 字段落地 (4 级: read/comment/edit/admin), UI 层 T7.5 实施。

---

## T7.4 撤销与统计 ⏳

T7.1 已提供 `revoke` 和 `get_stats`。T7.4 增量:

- 批量撤销: `revoke_by_report(report_id, owner_id)`
- 统计: 按日 / 按地域 (IP 反查, P2)
- 自动清理: cron 跑 `purge_expired` 每天一次

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
