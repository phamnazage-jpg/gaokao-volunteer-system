# PHASE6_LOCAL_GATE_EVIDENCE_2026-07-07

> 生成时间: 2026-07-07T13:14:04  
> 目标: 记录 v2 remediation Phase 6 的本地门禁、运行态 smoke、浏览器 snapshot 与剩余阻塞项。  
> 状态: `本地核心门禁通过 / 浏览器视觉验收 blocked by vision provider key expired / 线上真实 acceptance 待执行`

## 1. Core gates

来源: `/tmp/gaokao-phase6/core-gates.log`

关键结果:

```text
--- dev-verify ---
[dev-verify] python bin drift detected against default interpreter; reusing /home/long/project/gaokao-volunteer-system/.venv/bin/python
[dev-verify] skip install enabled
[dev-verify] running pytest with coverage gate
TOTAL                                                           19714   1935    90%
1386 passed, 3 skipped, 3 warnings in 154.79s (0:02:34)
[dev-verify] running core coverage verifier
[dev-verify] running ruff
@gaokao/web:codegen:check: ✅ Codegen contract gate passed: generated OpenAPI types/schemas are non-stub
 Tasks:    2 successful, 2 total
 Tasks:    1 successful, 1 total
@gaokao/web:test:  Test Files  85 passed (85)
@gaokao/web:test:       Tests  329 passed (329)
 Tasks:    1 successful, 1 total
@gaokao/web:codegen:check: ✅ Codegen contract gate passed: generated OpenAPI types/schemas are non-stub
@gaokao/web:build: TOTAL                               │    1.36 MB │  394.72 KB │ ✅
 Tasks:    2 successful, 2 total
  90 passed (32.8s)
Successfully tagged localhost/gaokao-poster-cli:review-final
[0m=== PHASE6 CORE GATES PASS ===
```

结论:
- `dev-verify`: 1386 passed, 3 skipped, 3 warnings；coverage / ruff / mypy / 100-case smoke 均通过。
- 前端 `typecheck/lint/test/build`: 通过。
- Playwright E2E all projects: 90 passed。
- Docker poster build: 通过。
- compose prod config: `GAOKAO_PAYMENT_PROVIDER=alipay` 下生成，未包含 mock provider。

## 2. Runtime smoke

来源: `/tmp/gaokao-phase6/http-probes.log`

```text
=== HTTP SNAPSHOT PROBES ===
/ code=200 bytes=27057 title=高考志愿填报智能规划服务
/pricing code=200 bytes=16965 title=服务套餐 - 高考志愿填报智能规划服务
/admin/login code=200 bytes=3883 title=管理后台登录
/privacy code=200 bytes=22260 title=隐私政策
/service-terms code=200 bytes=21184 title=服务说明与使用条款
/deletion-policy code=200 bytes=2769 title=删除申请 / 数据删除说明
/policy-center code=200 bytes=5565 title=政策中心
/same-score-reference code=200 bytes=4101 title=同分段参考
=== HEALTH ===
{"status":"ok","checks":{"db_writable":true,"disk_writable":true,"settings_valid":true}}
=== SNAPSHOT MARKERS ===
/tmp/gaokao-phase6/probe-_admin_login.html:<title>管理后台登录</title>
/tmp/gaokao-phase6/probe-_admin_login.html:<h1>管理后台</h1>
/tmp/gaokao-phase6/probe-_deletion-policy.html:<!doctype html><html lang='zh-CN'><head><meta charset='utf-8' /><meta name='viewport' content='width=device-width, initial-scale=1' /><title>删除申请 / 数据删除说明</title><link rel='stylesheet' href='/static/portal-ui.css' /><style>body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f4f7fb;padding:0;color:#172033;margin:0}.wrap{max-width:920px;margin:0 auto;display:grid;gap:18px;padding:32px 20px}.panel{background:#fff;border:1px solid #dbe3f0;border-radius:20px;padding:24px;box-shadow:0 18px 42px rgba(20,34,53,.08)}.eyebrow{display:inline-flex;padding:6px 10px;border-radius:999px;background:#eef6ff;color:#194fb6;font-size:12px;font-weight:700;letter-spacing:.04em;text-transform:uppercase}.lead{color:#5b6b88;line-height:1.8}.checklist{margin:0;padding-left:18px;color:#5b6b88;line-height:1.8}.meta{color:#5b6b88;line-height:1.8}</style></head><body><nav class="global-nav" aria-label="全局导航" role="navigation"><div class="global-nav-inner"><a class="global-nav-brand" href="/">高考志愿填报</a><div class="global-nav-links"><a class="global-nav-link" href="/">首页</a><a class="global-nav-link" href="/pricing">套餐</a><a class="global-nav-link" href="/data-query">数据查询</a><a class="global-nav-link" href="mailto:lon22@qq.com">客服</a></div></div></nav><nav class="global-nav" aria-label="全局导航" role="navigation"><div class="global-nav-inner"><a class="global-nav-brand" href="/">高考志愿填报</a><div class="global-nav-links"><a class="global-nav-link" href="/">首页</a><a class="global-nav-link" href="/pricing">套餐</a><a class="global-nav-link" href="mailto:lon22@qq.com">客服</a></div></div></nav><main class='wrap' role='main'><div style="margin-bottom:8px;"><a href="/" style="color:#194fb6;font-size:13px;text-decoration:none;">← 返回首页</a></div><section class='panel'><span class='eyebrow'>数据删除</span><h1>删除申请 / 数据删除说明</h1><p class='lead'>如需申请删除订单资料、附件或交付物，可在支付后的 Portal 中提交删除申请；系统会保留必要的审计记录，并由人工核验后处理。</p></section><section class='panel'><h2>你可以怎么做</h2><ul class='checklist'><li>在 Portal 中提交删除申请</li><li>填写申请人姓名、联系方式、删除范围与原因</li><li>确认监护人已知情并同意发起删除申请</li><li>处理结果会回到站内状态链路中查看</li></ul></section><footer style="margin-top:24px;color:#5b6b88;font-size:14px;"><a href="/privacy">隐私政策</a> · <a href="/service-terms">服务说明与免责声明</a> · <a href="/deletion-policy">删除申请 / 数据删除说明</a></footer></main>{_render_global_toast_script()}</body></html>
/tmp/gaokao-phase6/probe-_.html:    <title>高考志愿填报智能规划服务</title>
/tmp/gaokao-phase6/probe-_.html:          <h1>高考志愿填报智能规划服务</h1>
/tmp/gaokao-phase6/probe-_.html:          <a class="btn btn-secondary" href="/service-terms">查看服务说明</a>
/tmp/gaokao-phase6/probe-_.html:      <footer style="margin-top:24px;color:#5b6b88;font-size:14px;"><a href="/privacy">隐私政策</a> · <a href="/service-terms">服务说明与免责声明</a> · <a href="/deletion-policy">删除申请 / 数据删除说明</a></footer>
/tmp/gaokao-phase6/probe-_policy-center.html:<!doctype html><html lang="zh-CN"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>政策中心</title><link rel="stylesheet" href="/static/portal-ui.css" /><style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f4f7fb;padding:32px 20px;color:#172033;margin:0}.wrap{max-width:980px;margin:0 auto;display:grid;gap:18px}.panel{background:#fff;border:1px solid #dbe3f0;border-radius:20px;padding:24px;box-shadow:0 18px 42px rgba(20,34,53,.08)}.eyebrow{display:inline-flex;padding:6px 10px;border-radius:999px;background:#eef6ff;color:#194fb6;font-size:12px;font-weight:700;letter-spacing:.04em;text-transform:uppercase}.meta{color:#5b6b88;line-height:1.8}.actions{display:flex;gap:12px;flex-wrap:wrap}a{color:#1f6feb;text-decoration:none}</style></head><body><nav class="global-nav" aria-label="全局导航" role="navigation"><div class="global-nav-inner"><a class="global-nav-brand" href="/">高考志愿填报</a><div class="global-nav-links"><a class="global-nav-link" href="/">首页</a><a class="global-nav-link" href="/pricing">套餐</a><a class="global-nav-link" href="/data-query">数据查询</a><a class="global-nav-link" href="mailto:lon22@qq.com">客服</a></div></div></nav><main class="wrap"><section class="panel"><span class="eyebrow">政策中心</span><h1>政策中心</h1><p class="meta">适用省份：湖南</p><div class="trust-banner"><p class="meta">可信度说明：官方来源：湖南省教育考试院 · 更新时间：2026-06-22</p><p class="meta">适用范围：政策摘要与填报提醒 · 适用省份：湖南 · 置信等级：参考</p><p class="meta">未覆盖内容必须显式标注；页面仅提供摘要，不替代官方全文。</p></div><div class="actions"><a href="/same-score-reference?province=湖南&score=0">查看同分段参考</a><a href="/">返回首页</a></div></section><section class="panel"><h2>时间节点</h2><ul><li>查分后先核对成绩、位次与选科要求。</li><li>正式填报前再次确认批次与专业组选科约束。</li></ul></section><section class="panel"><h2>批次规则</h2><p class="meta">当前只整理普通类主链的关键规则；特殊批次、艺体类等未覆盖内容需另行核对。</p></section><section class="panel"><h2>提前批与专项计划</h2><p class="meta">提前批和专项计划是可以降分进入好学校的特殊渠道，但各有报考条件限制。以下列出主要类型：</p><ul><li><strong>军校（本科提前批）</strong>：入学即入伍，毕业分配工作。需通过政审+军检，年龄不超过20周岁。比同层次普通院校低30-80分。</li><li><strong>公安院校（本科提前批）</strong>：毕业参加公安联考入警率90%+，需通过体检+体能测试+政审。注意只有公安专业才能参加联考。</li><li><strong>国家专项计划</strong>：面向脱贫县农村考生，需当地连续3年户籍+学籍。通常降10-30分。</li><li><strong>地方专项计划</strong>：面向农村户籍考生，各省自定实施区域。通常降15-40分。</li><li><strong>高校专项计划</strong>：教育部直属高校面向农村考生，需4-5月提前报名。通常降20-60分。</li><li><strong>公费师范生</strong>：免学费+住宿费+补贴，毕业包分配有编有岗，需回生源省任教6年。</li><li><strong>免费医学定向</strong>：免学费，毕业回基层卫生院事业编，需服务6年。</li></ul><p class="meta">具体资格要求、体检标准和降分幅度以当地教育考试院和各院校官方招生简章为准。</p></section><section class="panel"><h2>选科要求</h2><p class="meta">先核对目标专业组选科要求，再判断是否要调整冲稳保结构。</p></section><section class="panel"><h2>常见误区</h2><ul><li>不要把同分段参考当成最终结论。</li><li>不要用去年的批次规则替代当年正式发布口径。</li></ul><p class="meta">以湖南省教育考试院官方信息为准。</p></section><footer style="margin-top:24px;color:#5b6b88;font-size:14px;"><a href="/privacy">隐私政策</a> · <a href="/service-terms">服务说明与免责声明</a> · <a href="/deletion-policy">删除申请 / 数据删除说明</a></footer></main><div class="state-toast-stack" id="toast-stack" aria-live="polite" aria-atomic="true"></div>
/tmp/gaokao-phase6/probe-_pricing.html:    <title>服务套餐 - 高考志愿填报智能规划服务</title>
/tmp/gaokao-phase6/probe-_pricing.html:          <h1>服务套餐</h1>
/tmp/gaokao-phase6/probe-_pricing.html:            <article class="trust-proof-item"><strong>隐私与删除入口可见</strong><span>隐私政策、服务说明和删除申请入口始终保留。</span></article>
/tmp/gaokao-phase6/probe-_pricing.html:            <li>隐私政策、服务说明与删除申请入口</li>
/tmp/gaokao-phase6/probe-_pricing.html:      <footer style="margin-top:24px;color:#5b6b88;font-size:14px;"><a href="/privacy">隐私政策</a> · <a href="/service-terms">服务说明与免责声明</a> · <a href="/deletion-policy">删除申请 / 数据删除说明</a></footer>
/tmp/gaokao-phase6/probe-_privacy.html:<!doctype html><html lang='zh-CN'><head><meta charset='utf-8' /><meta name='viewport' content='width=device-width, initial-scale=1' /><title>隐私政策</title><link rel='stylesheet' href='/static/portal-ui.css' /><style>body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f4f7fb;padding:0;color:#172033;margin:0}.wrap{max-width:920px;margin:0 auto;display:grid;gap:18px;padding:32px 20px}.panel{background:#fff;border:1px solid #dbe3f0;border-radius:20px;padding:32px;box-shadow:0 18px 42px rgba(20,34,53,.08)}.eyebrow{display:inline-flex;padding:6px 10px;border-radius:999px;background:#eef6ff;color:#194fb6;font-size:12px;font-weight:700;letter-spacing:.04em;text-transform:uppercase}.lead{color:#5b6b88;line-height:1.8;margin:8px 0 16px}.legal-doc h1{display:none}.legal-doc h2{color:#172033;font-size:18px;margin:24px 0 12px;border-bottom:2px solid #eef2fb;padding-bottom:6px}.legal-doc h3{color:#1f3a68;font-size:15px;margin:18px 0 8px}.legal-doc p{color:#34425b;line-height:1.85;margin:8px 0}.legal-doc ul,.legal-doc ol{color:#34425b;line-height:1.85;padding-left:22px;margin:8px 0}.legal-doc li{margin:4px 0}.legal-doc blockquote{border-left:3px solid #cfd9ee;color:#5b6b88;padding:8px 14px;margin:12px 0;background:#f8fbff;border-radius:0 8px 8px 0}.legal-doc table{border-collapse:collapse;width:100%;margin:12px 0;font-size:13.5px;background:#fff}.legal-doc th,.legal-doc td{border:1px solid #d7e3f1;padding:8px 10px;text-align:left;vertical-align:top}.legal-doc th{background:#eef4ff;color:#172033;font-weight:600}.legal-doc code{background:#f1f5fb;padding:1px 4px;border-radius:4px;font-size:12.5px;color:#1f3a68}</style></head><body><nav class="global-nav" aria-label="全局导航" role="navigation">
```

结论:
- 使用 `.venv/bin/python` + env file secrets 启动本地 admin app。
- `/health` 返回 `settings_valid=true`。
- `/`, `/pricing`, `/admin/login`, `/privacy`, `/service-terms`, `/deletion-policy`, `/policy-center`, `/same-score-reference` 全部 HTTP 200。

## 3. Browser snapshot evidence

已完成浏览器 snapshot:
- `/`: title `高考志愿填报智能规划服务`，包含全局导航、主 CTA、免费复核表单、套餐入口、隐私/条款/删除入口。
- `/pricing`: title `服务套餐 - 高考志愿填报智能规划服务`，包含套餐卡片、免费复核入口、信任说明、FAQ。
- `/admin/login`: title `管理后台登录`，包含用户名、密码、登录按钮、返回首页。

## 4. Visual acceptance blocker

`browser_vision` 和 `vision_analyze` 均返回 provider error:

```text
Error code: 403 - {'error': 'Key expired'}
```

因此本轮不能把“视觉质量验收”报告为 PASS。当前只能报告:

- 浏览器可访问 / DOM snapshot: PASS
- HTTP 页面 smoke: PASS
- 视觉质量判断: BLOCKED（外部 vision provider key expired）

## 5. Remaining non-local acceptance

仍不可宣称整体生产级完成:
- 线上真实支付 acceptance 未执行。
- 生产域名 / HTTPS / 真实反代链路未执行。
- 真实用户流量 acceptance 未执行。
