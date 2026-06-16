# FRONTEND_UI_EXECUTION_BOARD_2026-06-16

状态词: 当前有效前端整改执行板
真相源: `docs/CURRENT_STATE.md`
审计来源: `docs/FRONTEND_UI_AUDIT_2026-06-16.md`

---

## 1. 当前门禁结论

结论: 用户端前端未达到上线质量；后台前端未达到专业后台标准。

进展更新（2026-06-16 本轮本地实现）:
进展更新（2026-06-16 本轮本地实现）:

- B-UI-01 已完成：去除用户可见开发术语，并把缺少加密密钥时的下单失败改为友好 503 提示
- B-UI-02 已完成：`/pricing` 已完成首轮商业化重构
- B-UI-03 已完成：`/checkout/standard` 已完成首轮转化链重构
- H-UI-01 已完成：首页已完成首轮品牌/信任/信息架构重构
- H-UI-02 已完成：Portal 资料向导与状态页已完成首轮产品化重构
- H-UI-03 已完成：后台 `/dashboard` 已完成首轮去技术暴露与专业化重构
- M-UI-01 已完成：已建立共享 `portal-ui.css` 作为前端样式基线
- M-UI-02 已完成：已补关键页面 shared CSS 链接与页面级回归断言
- 当前剩余仅为 Git 交付（commit / 三仓推送）或下一轮更深层视觉迭代

禁止事项:

- 不得在用户可见页面继续保留 `Mock 支付沙箱`、`支付接入建设中`、`最小 Web 自助闭环` 等开发文案
- 不得把“测试通过”误报成“用户真实可用”
- 不得先做装饰性美化，跳过信任链、信息架构和关键路径设计
- 不得把后台 `/dashboard` 的技术暴露问题当成纯文案小问题忽略

---

## 2. 最短闭环主线

推荐执行顺序:

1. B-UI-01 用户端去开发术语与真实运行前置约束收口
2. B-UI-02 定价页商业化重构
3. B-UI-03 结账页转化链重构
4. H-UI-01 首页品牌/信任/信息架构重构
5. H-UI-02 Portal 向导页与状态页产品化
6. H-UI-03 后台仪表盘去技术暴露与专业化重构
7. M-UI-01 建立前端 design token / 共享样式基线
8. M-UI-02 补前端真实验收门禁与回归样例

说明:

- 第一批先改 `/pricing`、`/checkout/standard`、`/`，因为这三页直接影响付费转化。
- `/dashboard` 放第二批，但必须纳入本轮执行板，不再拖延为“以后再美化”。

---

## 3. 执行任务清单

### B-UI-01 用户端去开发术语与真实运行前置约束收口

Owner: engineer / PM
优先级: P0
状态: completed（本地验证完成）

目标:

- 去掉所有用户可见开发术语，补齐真实运行前置约束说明，避免假可用界面。

文件:

- 修改: `admin/routes/web_public.py`
- 修改: `admin/tests/test_web_public.py`
- 参考: `docs/FRONTEND_UI_AUDIT_2026-06-16.md`

完成标准:

- 页面不再出现以下文案：
  - `Mock 支付沙箱`
  - `支付接入建设中`
  - `最小 Web 自助闭环`
- 若真实支付/下单前置仍未满足，必须改成用户可理解的非技术提示或仅在内部环境显示
- 重新跑相关页面测试并更新断言

验证方法:

- `grep -R "Mock 支付沙箱\|支付接入建设中\|最小 Web 自助闭环" -n admin/routes admin/static`
- 浏览器重新打开 `/` `/pricing` `/checkout/standard`

依赖:

- 无

---

### B-UI-02 定价页商业化重构

Owner: frontend-ui-expert / engineer
优先级: P0
状态: completed（本地验证完成）

目标:

- 把 `/pricing` 从模板定价卡改成真正可转化的商业化套餐页。

文件:

- 修改: `admin/routes/web_public.py::_render_pricing_page`
- 测试: `admin/tests/test_web_public.py`

完成标准:

- 每个套餐卡至少包含：
  - 标题
  - 价格
  - 适用人群
  - 3-5 条功能清单
  - CTA
- `99元 完整志愿方案` 作为主推档，需视觉高亮
- 页面增加至少一个信任模块：服务保障 / FAQ / 联系方式 / 专家背书占位
- 移除任何开发状态横幅

验证方法:

- 浏览器审查 `/pricing`
- 断言测试补齐新文案/结构

依赖:

- B-UI-01

---

### B-UI-03 结账页转化链重构

Owner: frontend-ui-expert / engineer
优先级: P0
状态: completed（本地验证完成）

目标:

- 把 `/checkout/standard` 从表单页升级为可付费的结账页。

文件:

- 修改: `admin/routes/web_public.py::_render_checkout_page`
- 测试: `admin/tests/test_web_public.py`

完成标准:

- 增加订单摘要区
- 增加服务说明/交付说明/隐私与保障提示
- 优化字段分组：联系人 / 考生 / 备注
- 增加更专业的 submit 状态反馈（loading / error / success）
- 不再出现内部术语，如“最小下单”

验证方法:

- 浏览器审查 `/checkout/standard`
- 真实 `POST /api/public/orders` 至少在具备必需 env 时可成功
- 若 env 缺失，错误提示必须专业且可诊断，不暴露堆栈

依赖:

- B-UI-01

---

### H-UI-01 首页品牌/信任/信息架构重构

Owner: PM / frontend-ui-expert / engineer
优先级: P1
状态: completed（本地验证完成）

目标:

- 让首页从“项目介绍页”变成“高考付费服务落地页”。

文件:

- 修改: `admin/routes/web_public.py::_render_landing_page`
- 测试: `admin/tests/test_web_public.py`

完成标准:

- 去掉 C 端首页中的后台入口并弱化内部链接
- 增加品牌/服务价值主张
- 增加至少一个信任模块（专家、案例、保障、流程）
- “当前自助流程建设重点”改成用户视角表达

验证方法:

- 浏览器审查 `/`
- 页面不再像内部开发首页

依赖:

- B-UI-01

---

### H-UI-02 Portal 向导页与状态页产品化

Owner: frontend-ui-expert / engineer
优先级: P1
状态: completed（本地验证完成）

目标:

- 提升 `/portal/{token}/info` 与 `/portal/{token}/status` 的产品体验与用户理解成本控制。

文件:

- 修改: `admin/routes/web_public.py::_render_info_page`
- 修改: `admin/routes/web_public.py::_render_status_page`
- 测试: `admin/tests/test_web_public.py`

完成标准:

- 5 步向导有更清晰层级、状态、帮助文案
- 状态页有更明确的下一步引导、通知状态、交付状态表达
- 不再只是系统数据回显页

验证方法:

- 浏览器打开 portal 页面（有 token 时）
- 检查步骤/状态表达是否面向家长用户，而不是内部系统

依赖:

- B-UI-03

---

### H-UI-03 后台仪表盘去技术暴露与专业化重构

Owner: frontend-design-reviewer / engineer
优先级: P1
状态: completed（本地验证完成）

目标:

- 把 `/dashboard` 从开发者自检页提升为专业运营后台。

文件:

- 修改: `admin/static/dashboard.html`
- 修改: `admin/static/dashboard.js`
- 测试: `admin/tests/test_admin_ui_pages.py`

完成标准:

- 去掉以下用户可见技术暴露：
  - `最小仪表盘`
  - `接口: /api/stats/dashboard`
  - `admin_users 总数`
- 登录区与业务区分层更清晰
- 指标/图表补齐 loading/empty/error 语义
- 关键快捷入口不再使用廉价裸链接样式

验证方法:

- 浏览器审查 `/dashboard`
- 文案与结构不再像开发自检页

依赖:

- 无

---

### M-UI-01 建立前端 design token / 共享样式基线

Owner: tech-lead / engineer
优先级: P2
状态: completed（本地验证完成）

目标:

- 逐步摆脱大段 inline style，建立共享样式基线。

文件:

- 新建或重构: `admin/static/*.css`（待设计落点）
- 修改: `admin/routes/web_public.py`
- 修改: `admin/routes/notifications.py`

完成标准:

- 抽出颜色、圆角、间距、按钮、卡片、表单等通用规则
- 新改页面优先复用共享样式
- 为后续统一去 AI 痕迹提供基础设施

验证方法:

- inline style 数量下降
- 新旧页面视觉一致性提升

依赖:

- B-UI-02
- B-UI-03
- H-UI-01

---

### M-UI-02 补前端真实验收门禁与回归样例

Owner: QA / engineer
优先级: P2
状态: completed（本地验证完成）

目标:

- 让前端页面不只是测试字符串存在，而是有更贴近体验的回归门禁。

文件:

- 修改: `admin/tests/test_web_public.py`
- 修改: `admin/tests/test_admin_ui_pages.py`
- 可新增: 浏览器/HTTP smoke 用例

完成标准:

- 补充对关键文案、分组、按钮、信任模块的断言
- 对真实下单闭环至少补环境前置或 fail-closed 断言
- 对后台去技术暴露的文案补回归保护

验证方法:

- pytest 全绿
- 新增断言能覆盖本轮整改目标

依赖:

- B-UI-02
- B-UI-03
- H-UI-03

---

## 4. 首批改造页面建议

第一批（必须先做）:

1. `/pricing`
2. `/checkout/standard`
3. `/`

第二批: 4. `/dashboard` 5. `/portal/{token}/info` 6. `/portal/{token}/status`

原因:

- 第一批直接影响“能不能让家长愿意下单”
- 第二批解决后台专业度和购买后的持续体验

---

## 5. 推荐提交边界

建议按任务单独提交：

- `B-UI-01: ...`
- `B-UI-02: ...`
- `B-UI-03: ...`
- `H-UI-01: ...`

每项整改后同步更新：

- `docs/CURRENT_STATE.md`
- 本执行板状态
- 相关测试断言
