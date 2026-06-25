# 高考项目严格系统 Review 报告

- 审查日期：2026-06-23 ~ 2026-06-24
- 审查范围：`/home/long/project/gaokao-volunteer-system`
- 审查方式：源码静态审查 + 路由注册核验 + 关键测试集执行 + 最小行为复现
- 审查口径：按生产可用性、主链路正确性、数据完整性、测试可信度的最严格标准

## 执行摘要

本次是在部分功能模块更新后的二次严格复审。最新结果与上一个版本相比已经有明显改善：

1. `submit_order_info()` 已从“整包覆盖写”修正为“读取当前 payload 后 merge 再保存”，附件与复核结果保留问题已修复。
2. 报告版本关系、政策中心信任说明、辅助链接输出相关回归已经修复，相关测试现已转绿。
3. 上一版报告中阻断真实生产链路的 2 个高严重度问题已修复：
   - 首页 `/` 已恢复真实注册。
   - 方案复核页已改为与浏览器表单协议一致的 `POST form -> 303 redirect`。
4. 补充了最小真实集成测试，覆盖首页真实路由注册、复核分流表单提交、真实路由元数据。
5. 当前关键回归在真实 `TestClient` 与现有页面/状态/资料/版本测试组合下已转绿；剩余 warning 仅为 `starlette.testclient` 对 `httpx` 的弃用提示，不影响本次功能结论。

当前结论：本报告原列的阻断级问题已全部修复。

第三轮补充结论（历史保留）：

- 未发现新的主链路生产级功能缺陷。
- 当时剩余风险主要来自测试夹具与真实 FastAPI/ASGI 行为的一致性，而不是前台业务链路本身。

第四轮补充结论（历史保留）：

- 前台公开主链路继续保持绿色，未复现新的下单 / 支付 / 资料 / 复核 / 报告访问故障。
- 本轮剩余两项未关闭问题已修复：
  - backup / restore smoke 现在要求 `config/.env` 与 `secrets/*` 存在，且真实通过 `create_app()` + `TestClient` 执行 `/health`、`/api/public/orders`、portal 状态/报告/pdf`。
  - 后台录单页已补齐 `consent_method` / `consent_note` 字段，前端提交 payload 与 `/api/orders` 当前创建契约重新一致。
- 因此，前台主链路、本轮后台安全问题、恢复验证口径与后台录单契约问题均已转绿。
- 按当前这份严格审查报告列出的活动问题口径，系统已无未关闭项；现阶段可以认为本轮严格审查通过。

第五轮补充结论（历史保留）：

- 在继续沿“真实可用性边界”“公开入口与真实能力边界一致性”“复核分流后是否进入真实功能页”的方向深挖后，曾确认 3 个活动问题需要重新打开：
  - `/review/action` 分流后的 `cwb` / `full-plan` 路径当前仍是 placeholder 页面，未承载真实冲稳保结果或完整规划结果。
  - 公开下单与资料入口允许 `内蒙古 / 广西 / 西藏 / 宁夏` 等当前 loader 不支持的省份进入；后续同分段参考页不会提示“暂不支持”，而是按普通页面渲染“暂无”。
  - Portal 资料页头部宣称“四步资料向导”，但运行态实际是 5 个 step panel，徽标定义与实际交互顺序已漂移。
- 上述 3 项现已修复，不再是当前活动问题。


关联文档：

- `reports/TEST_CLIENT_COVERAGE_2026-06-23.md`：记录用户端主链路真实 `TestClient` 覆盖现状与剩余 `RouteClient` 边界。
- `docs/CURRENT_STATE.md` §0.8：当前真相源中对这次测试可信度收口的正式口径。


## Findings

### P1-5 复核分流后的 `cwb` / `full-plan` 路径当前仍是 placeholder 页面，不提供真实冲稳保结果或完整规划结果 — 已修复

- 原问题位置：
  - 路由入口：`admin/routes/web_public.py:399-417`
  - `cwb` 渲染：`admin/routes/web_public.py:3179-3209`
  - `full-plan` 渲染：`admin/routes/web_public.py:3212-3242`
- 修复：
  - `cwb` 页面改为“冲稳保建议页”，输出当前建议 / 冲刺建议 / 稳妥建议 / 保底建议
  - `full-plan` 页面改为“完整规划建议页”，输出方案优先级 / 版本历史 / 当前复核摘要
  - 去掉“后续再接真实推荐结果”“当前从 review 分流进入完整规划入口”这类占位口径
- 新证据：
  - `admin/tests/test_web_public_review_flow.py::test_cwb_page_no_longer_claims_placeholder_future_work`
  - `admin/tests/test_web_public_review_flow.py::test_full_plan_page_no_longer_claims_entry_only_placeholder`
  - 既有 CWB / full-plan 页面测试已同步改按新口径断言
- 当前结论：已关闭。

### P1-6 公开下单与资料入口允许当前不支持的省份进入，后续参考页把“不支持”伪装成普通“暂无” — 已修复

- 原问题位置：
  - 下单页省份选项：`admin/routes/web_public.py:1898-1900, 2134-2174`
  - 公开下单契约：`data/orders/public_flow.py:26-44`
  - loader 支持边界：`data/crowd_db/loader.py:82-116`
  - 同分段参考页回退逻辑：`admin/routes/web_public.py:1233-1272`
- 修复：
  - `PublicOrderCreate` 现在显式校验支持省份集合
  - 公开下单与 Portal Step 1 的省份下拉已收敛到当前支持集
  - `policy-center` / `same-score-reference` 对不支持省份显式展示“当前省份暂不支持”
- 新证据：
  - `admin/tests/test_web_public.py::test_public_create_order_rejects_unsupported_province`
  - `admin/tests/test_web_public_content_pages.py::test_same_score_reference_page_marks_unsupported_province_explicitly`
- 当前结论：已关闭。

### P2-2 Portal 资料页的向导定义已漂移：头部宣称 4 步，运行态实际为 5 步 — 已修复

- 原问题位置：`admin/routes/web_public.py:2368-2490`
- 修复：
  - 向导头部已统一改为“五步资料向导”
  - step badge 顺序改为：基础信息 / 院校偏好 / 专业偏好 / 其他偏好与确认 / 已有方案与附件
  - 文案与脚本 `totalSteps = 5` 重新一致
- 新证据：
  - `admin/tests/test_order_info_form.py::test_order_info_form_accepts_draft_and_submit`
  - 页面断言已改为“五步资料向导”与 5 类步骤名称
- 当前结论：已关闭。

### P1-1 删除/匿名化服务直接信任数据库中的路径并执行 `unlink()`，可越界删除可信根之外的文件 — 已修复

- 原问题位置：`data/orders/deletion_service.py:198-253`
- 修复：
  - `OrderDeletionService` 现在要求：
    - portal 附件必须位于 `settings.portal_upload_dir`
    - 交付物必须位于 `_trusted_report_roots(settings)`
  - 对不可信路径改为 `skip`，不再执行 `unlink()` / `rmdir()`
  - `admin/routes/orders.py` 初始化删除服务时显式传入 trusted roots
- 新证据：
  - `admin/tests/test_order_deletion.py::test_admin_anonymize_order_skips_untrusted_attachment_paths`
  - `admin/tests/test_order_deletion.py::test_admin_delete_order_skips_untrusted_report_artifacts`
  - 同时正常受信路径回归仍通过
- 当前结论：已关闭。

### P1-2 `viewer` 角色仍可进入案例写接口，且统计接口只要求“已登录”不要求“有权限” — 已修复

- 原问题位置：
  - `admin/routes/cases.py:67-226`
  - `admin/routes/stats.py:53-118`
- 修复：
  - `cases` 列表 / 创建 / 详情 / 更新 / 审核 / 删除统一为 `require_role("admin")`
  - `stats` dashboard / order stats 统一为 `require_role("admin")`
- 新证据：
  - `admin/tests/test_routes_cases.py::test_viewer_cannot_create_case`
  - `admin/tests/test_routes_stats_dashboard.py::test_viewer_cannot_read_order_stats`
  - `admin/tests/test_routes_orders.py::test_viewer_cannot_list_orders` 继续保持绿色
- 当前结论：已关闭。

### P1-3 `RouteClient` 仍会绕过真实 FastAPI 参数验证与路由层行为 — 已缓解并在前台关键测试文件中清零

- 现状：
  - 首页注册与 `review/action` 表单协议这两个曾经的阻断点，已经补上真实 `TestClient` 校验。
  - 前台关键测试文件中的 `RouteClient` 已清零；`RouteClient` 仍保留在仓库中，但不再作为前台主链路测试证据。
- 新证据：
  - `admin/tests/test_order_status_page.py::test_real_client_review_action_rejects_missing_action_field`
  - `admin/tests/test_order_status_page.py::test_real_client_review_action_rejects_invalid_literal_action`
  - `admin/tests/test_order_status_page.py::test_real_client_review_action_rejects_json_body_for_form_route`
  - `reports/TEST_CLIENT_COVERAGE_2026-06-23.md`
- 当前结论：
  - 该问题相较最初阶段已完成前台主链收口，不再构成本报告中的活动问题。

### P1-4 backup / restore smoke 的“服务级恢复”口径与真实实现不一致，且缺少配置 / secrets 仍可跑绿 — 已修复

- 原问题位置：
  - `scripts/backup_verify.sh:25, 208-217`
  - `scripts/backup_restore_smoke.py`
  - `tests/test_backup_restore_service_level.py`
- 修复：
  - `backup_restore_smoke.py` 现在强制要求：
    - `config/.env`
    - `secrets/jwt_secret`
    - `secrets/orders_fernet_key`
    - `secrets/admin_pass`
  - 恢复验证改为真实 `create_app()` + `TestClient`
  - 真实执行 `/health`、`POST /api/public/orders`、portal 状态页、报告页、PDF 下载链路
  - 输出增加 `public_order_create: 201`
- 新证据：
  - `tests/test_backup_restore_service_level.py::test_backup_verify_uses_venv_python_for_service_level_restore`
  - `tests/test_backup_restore_service_level.py::test_backup_restore_smoke_fails_fast_when_admin_db_missing`
  - `tests/test_backup_restore_service_level.py::test_backup_restore_smoke_fails_fast_when_config_env_missing`
  - `tests/test_backup_restore_service_level.py::test_backup_restore_smoke_uses_real_testclient_contract_marker`
- 当前结论：已关闭。

### P2-1 后台手动录单页与后端创建契约已脱节，页面当前生成的 payload 必然被后端 422 拒绝 — 已修复

- 原问题位置：
  - 页面输出：`admin/routes/ui.py:132-180`
  - 后端创建契约：`admin/routes/orders.py:233-238`
- 修复：
  - 后台录单页新增 `consent_method` 与 `consent_note` 输入控件
  - 页面脚本现在会构造 `consent: { consent_method, consent_note }` 并随 `/api/orders` 一起提交
- 新证据：
  - `admin/tests/test_admin_ui_pages.py::test_admin_new_order_page_includes_required_consent_fields`
  - 页面内联脚本现已显式出现 `consent` / `consent_method` / `consent_note`
- 当前结论：已关闭。

### P0-1 首页路由缺失 — 已修复

- 原问题位置：`admin/routes/web_public.py:208`
- 修复：已恢复 `@router.get("/", include_in_schema=False)`。
- 新证据：
  - 真实路由元数据：`/ ['GET'] []`
  - 真实集成测试：`admin/tests/test_order_status_page.py::test_public_landing_route_is_registered_in_real_app`
- 当前结论：已关闭。

### P0-2 复核页表单协议与后端协议不一致 — 已修复

- 原问题位置：
  - 表单输出：`admin/routes/web_public.py:_render_review_start_page()`
  - 接口定义：`admin/routes/web_public.py:620-627`
- 修复：
  - `/review/action` 改为接收 `Form(...)` 的 `token` 与 `action`
  - 返回 `303 RedirectResponse`，与浏览器表单流一致
- 新证据：
  - 真实路由元数据：`/review/action ['POST'] ['token', 'action']`
  - 真实集成测试：`admin/tests/test_order_status_page.py::test_review_action_accepts_browser_form_post`
- 当前结论：已关闭。

## 已修复项

### R-1 Portal 资料保存的上下文丢失问题已修复

- 修复位置：`admin/routes/web_public.py:569-573`
- 变化：
  - 现在会先读取 `current.payload`，再 `base_payload.update(payload.model_dump())`，之后才生成版本元数据并保存。
- 复核结果：
  - 最小复现脚本显示：
    - `has_attachments True 1`
    - `has_review_results True [...]`
    - `review_id_preserved True`
  - 说明附件、复核结果、`latest_review_result_id` 已在再次保存资料后保留。

### R-2 报告版本与历史档案关系的回归已修复

- 修复位置：
  - `admin/routes/web_public.py:1022-1033`
  - `admin/routes/web_public.py:2853-2863`
- 变化：
  - 新增 `_report_version_profile_reference()`，报告页开始优先使用 `report_versions` 中记录的 `profile_version_id`。
- 复核结果：
  - `admin/tests/test_web_public_review_flow.py::test_report_page_warns_when_based_on_historical_profile_version` 已通过。

### R-3 政策中心/同分段参考页的信任说明与辅助链接回归已修复

- 修复位置：
  - `admin/routes/web_public.py:1069-1083`
  - `admin/routes/web_public.py:1160-1208`
- 变化：
  - 新增统一 trust banner，补齐“来源 / 更新时间 / 适用范围 / 置信等级 / 边界说明”。
- 复核结果：
  - `admin/tests/test_web_public_content_pages.py::test_policy_center_page_shows_standard_trust_banner` 已通过。

## 验证记录

### 路由核验

执行：

```bash
.venv/bin/python - <<'PY'
from admin.app import create_app
from admin.config import load_settings
from fastapi.routing import APIRoute
app = create_app(load_settings())
for key in ['/', '/review/action', '/policy-center', '/same-score-reference']:
    for r in app.routes:
        if isinstance(r, APIRoute) and r.path == key:
            print(key, sorted(r.methods), [p.name for p in r.dependant.body_params])
            break
    else:
        print(key, None)
PY
```

结果：

```text
/ ['GET'] []
/review/action ['POST'] ['token', 'action']
/policy-center ['GET'] []
/same-score-reference ['GET'] []
```

结论：首页与复核分流入口均已真实注册，且 `/review/action` 已按表单 body 暴露字段。

### 真实集成测试

执行：

```bash
.venv/bin/python -m pytest -q admin/tests/test_order_status_page.py -k 'public_landing_route_is_registered_in_real_app or review_action_accepts_browser_form_post or real_app_registers_public_entry_and_form_review_routes'
```

结果：`3 passed, 1 warning in 0.48s`

结论：

- `GET /` 在真实 `TestClient` 下返回 200
- 浏览器表单 `POST /review/action` 在真实 `TestClient` 下返回 303 并跳转到对应后续页面
- 路由元数据断言与运行时行为一致

### 第四轮新增验证

#### 权限依赖元数据核验

执行：

```bash
.venv/bin/python - <<'PY'
from fastapi.routing import APIRoute
from admin.app import create_app
from admin.config import load_settings
app = create_app(load_settings())
for target in ['/api/cases', '/api/admin/cases', '/api/stats/orders', '/api/admin/stats/orders', '/api/orders']:
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path == target:
            deps = [getattr(dep.call, '__name__', str(dep.call)) for dep in route.dependant.dependencies]
            print(target, sorted(route.methods), deps)
PY
```

结果：

```text
/api/cases ['GET'] ['get_settings_dep', 'get_current_user']
/api/cases ['POST'] ['get_settings_dep', 'get_current_user']
/api/admin/cases ['GET'] ['get_settings_dep', 'get_current_user']
/api/admin/cases ['POST'] ['get_settings_dep', 'get_current_user']
/api/stats/orders ['GET'] ['get_settings_dep', 'get_current_user']
/api/admin/stats/orders ['GET'] ['get_settings_dep', 'get_current_user']
/api/orders ['GET'] ['get_settings_dep', '_dep']
```

结论：`cases` 与 `stats` 路由当前只做“已登录”校验，没有像 `orders` 一样落到角色门禁。

#### `viewer` 角色最小行为复现

执行结果摘要：

```text
create_case succeeded for role= viewer case_id= 1
stats ok for role= viewer keys= ['by_service_version', 'by_source', 'by_status', 'total_orders', 'total_revenue_cents']
```

结论：`viewer` 并非只具备浏览能力；至少在当前实现里，它已经能够进入案例写路径与统计读取路径。

#### 删除服务越界删文件复现

执行结果摘要：

```text
files_deleted= 1
sentinel_exists= False
```

复现方式：在隔离临时库中把 `order_intakes.payload_json.attachments[*].storage_path` 指向 portal 上传目录之外的临时文件，再调用 `OrderDeletionService.anonymize_order(...)`。

结论：删除服务当前会直接删除数据库中记录的任意存在文件，而不是只删除受信附件/受信交付物。

#### restore smoke 假阳性复现（历史问题，现已修复）

执行结果摘要（修复前）：

```text
{"health_status": 200, "portal_pdf": 200, "has_config_dir": false, "has_secrets_dir": false, ...}
```

修复前复现方式：在临时目录构造仅含 `db/admin.db`、`db/orders.db` 与示例 HTML/PDF 的最小快照，故意不提供 `config/.env` 与 `secrets/`，再直接调用 `run_restore_smoke(...)`。

修复后状态：

- `backup_restore_smoke.py` 现在会 fail fast 要求 `config/.env` 与 `secrets/*` 齐全
- 且已升级为真实 `create_app()` + `TestClient` 服务级恢复验证

#### 后台手动录单页契约核验（历史问题，现已修复）

执行结果摘要（修复前）：

```text
ValidationError
consent
Field required
```

修复前核验方式：

- 打开 `admin/routes/ui.py` 中 `/admin/orders/new` 生成的页面 payload，确认提交字段集合。
- 对照 `admin/routes/orders.py` 中 `CreateOrderRequest` 的当前必填契约。
- 直接对页面最小 payload 执行 `CreateOrderRequest.model_validate(...)`。

修复后状态：

- 页面已补齐 `consent_method` / `consent_note`
- `admin/tests/test_admin_ui_pages.py::test_admin_new_order_page_minimal_payload_matches_create_order_contract` 已锁定“页面最小 payload 可通过当前契约”

### 第五轮新增验证（历史保留）

#### 不支持省份入口核验（修复前）

执行结果摘要（修复前）：

```text
public_order_candidate_province 内蒙古
适用省份：内蒙古 True
同分段热门学校 True
暂无 True
暂不支持 False
```

当前状态：公开创建模型已拒绝不支持省份；同分段参考页对不支持省份会显式展示“当前省份暂不支持”。

#### 资料向导步数一致性核验（修复前）

执行结果摘要（修复前）：

```text
step_badges 4
step_panels 5
four_step_title True
step5_present True
total_steps_5 True
```

当前状态：资料向导已统一为“五步资料向导”，头部徽标、step badge、step panel 与脚本 `totalSteps = 5` 重新一致。

### 关键回归组合

执行：

```bash
.venv/bin/python -m pytest -q admin/tests/test_web_public.py admin/tests/test_web_public_content_pages.py admin/tests/test_web_public_review_flow.py admin/tests/test_order_info_form.py data/orders/tests/test_public_flow.py
```

结果：`68 passed, 1 warning in 10.90s`

结论：本轮新增的分流页口径、省份支持边界、资料向导步数相关回归已转绿。


### 数据丢失最小复现

复现路径：

1. 创建公开订单并完成 mock 支付
2. 上传 Portal 附件
3. 发起一次 review
4. 再提交一次 Portal 资料

上一次审查时的最终 payload 关键状态：

```text
attachments False
review_results False
profile_versions True
latest_review_result_id None
profile_versions_len 1
```

本次更新后重新复核：

```text
has_attachments True 1
has_review_results True ['rvw_0db8fc4c']
latest_review_result_id rvw_0db8fc4c
review_id_preserved True
profile_versions_len 1
```

结论：附件与复核上下文丢失问题已修复；该节作为历史问题保留。

## 对测试体系的附加评价

- 当前 `RouteClient` 仍作为轻量辅助夹具存在于仓库中，但前台关键测试文件已不再使用它作为主证据；主要公开页、复核分流、下单与资料链路已通过真实 `TestClient` 回归验证。
- 这一轮之前暴露出的 3 类缺口已经补齐：
  - backup / restore 验证已升级为真实 `create_app()` + `TestClient`
  - 后台录单页 payload 已与后端契约重新对齐，并有模型级测试锁住
  - 新增的 review 分流页、省份支持边界、资料向导步数问题也已被负向/页面回归用例覆盖
- 当前测试体系剩余的主要问题不再是“存在明确活动缺陷”，而是 warning 级别的依赖弃用提示（`starlette.testclient` → `httpx2`）。

## 结论

本报告中曾经出现过的前台阻断级问题、后台安全边界问题、恢复验证口径问题、后台录单页契约问题，以及第五轮补充发现的 3 个活动问题，现已全部修复。

最新真实状态：

- 公开首页 `/` 已可真实访问。
- 复核分流已与浏览器表单协议一致，真实提交可用。
- 删除/匿名化服务已增加 trusted-root 校验，不再删除受信根之外的文件。
- `viewer` 角色已不能再写案例或读取统计。
- backup / restore smoke 已升级为真实 `create_app()` + `TestClient` 服务级验证，并会 fail fast 要求 `config/.env` 与 `secrets/*`。
- 后台手动录单页与 `/api/orders` 的 `consent` 契约已重新对齐。
- review 分流后的 `cwb` / `full-plan` 已不再用占位口径伪装正式结果页。
- 公开入口与参考页对不支持省份的边界已显式收口。
- Portal 资料向导已统一为“五步资料向导”。

剩余注意项：

- warning 仅为 `starlette.testclient` 对 `httpx` 的弃用提示，属于依赖升级事项，不是本次功能故障。

因此，按本报告最初定义的“生产可用性、主链路正确性、数据完整性、测试可信度”的关键阻断标准复核：

> 当前版本已修复本报告列出的活动问题，本轮严格审查通过。
