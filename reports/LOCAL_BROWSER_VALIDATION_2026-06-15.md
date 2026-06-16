# 本地浏览器端到端与 UI/可访问性验证补充（2026-06-15）

## 1. 背景

在前一轮整改与 `dev-verify` 通过后，又补做了一轮**本地真实浏览器验证**，目标是确认：

1. 不是只有后端单测 / TestClient 通过
2. 关键前台页面在真实浏览器中可访问、可导航
3. 新增的隐私 / 删除入口不是“接口已加，页面不可用”
4. 至少抽检基础 UI 一致性与表单可访问性

本次验证使用本机启动的 FastAPI 服务，而不是只依赖 TestClient。

## 2. 验证环境

本地服务启动方式：

```bash
python -m admin.app --host 127.0.0.1 --port 8010
```

使用的环境变量包括：

- `GAOKAO_ENV=dev`
- 独立临时 SQLite
- `GAOKAO_PAYMENT_PROVIDER=alipay_sim`
- 本地 `payment_base_url=http://127.0.0.1:8010`
- merchant/app/payment 相关配置使用本地测试值

浏览器验证工具：

- headless Chromium（通过 browser tool）

## 3. 已验证通过的页面与链路

### 3.1 Landing / Footer / 公共说明页

已确认：

- `/` 可打开
- `/pricing` 可打开
- `/privacy` 可打开
- `/service-terms` 可打开
- `/deletion-policy` 可打开

已观察到：

- landing 页标题与 H1 正常
- footer 中存在：
  - 隐私政策
  - 服务说明与免责声明
  - 删除申请 / 数据删除说明
- 键盘 Tab 焦点顺序至少覆盖首屏主操作：
  - 查看服务套餐
  - 进入运营后台

### 3.2 公开下单与支付页

已确认：

- `/checkout/standard` 可打开
- 表单字段可填写
- 点击“创建订单并去支付”可跳转到 `/pay/alipay-sim/...`
- 支付页标题为“支付宝模拟收银台”
- 支付按钮可见且可操作

### 3.3 支付完成后的 Portal 状态页

已确认：

- 模拟支付成功后成功跳回 `/portal/{token}/status`
- 浏览器中观察到状态页显示：
  - 处理中
  - 当前订单状态：`serving`
  - 支付状态：`paid`
  - 资料状态：处理中
- 资料摘要区域已展示：
  - 分数
  - 位次
  - 选科
  - 兴趣方向

### 3.4 Portal 删除申请页

已确认：

- `/portal/{token}/deletion-request` 可打开
- 页面包含：
  - 申请人姓名
  - 联系方式
  - 删除范围
  - 申请原因
  - 监护人确认复选框
- 页面 footer 保留隐私 / 服务说明 / 删除说明链接

## 4. 可访问性与基础语义抽检结果

已抽检页面：

- landing
- checkout
- deletion-request

结论：

- `lang="zh-CN"` 存在
- 每页均有单个主 `h1`
- checkout / deletion-request 的表单控件均有 label 绑定
- 抽检范围内未发现“输入控件无 label”问题
- footer 链接文本明确，不是空链接或仅图标链接

这说明：

- 本轮新增的前台入口不是只对接口存在
- 最基本的可访问性语义不是缺失状态

## 5. 新发现的问题

### 5.1 Portal 资料向导 Step 5 在真实浏览器中的提交流程不稳定

现象：

- 在真实浏览器里，按页面向导从 Step 1 点击到 Step 5 时
- 页面确认摘要里仍出现：
  - `candidate_interests: null`
  - `privacy_accepted: false`
  - `service_terms_accepted: false`
  - `guardian_confirmed: false`
- 直接点击“提交资料”后，没有稳定观察到前端自动跳转或结果反馈
- 但通过同页面直接对 `/portal/{token}/info` 发 POST 请求，后端返回：

```json
{
  "intake_status": "submitted",
  "stage": "processing",
  "order_id": "..."
}
```

这说明：

- **后端提交接口是通的**
- **前端 Step 向导状态汇总 / 提交交互仍有真实浏览器层面的不稳定问题**

### 5.2 UI 一致性仍偏 MVP

观察到的问题：

- landing 与 portal/status 的视觉风格差异较大
- 页面整体仍偏“功能先行”，没有统一设计系统
- portal status 信息密度较高，但层次与导航反馈一般
- 删除申请页样式可用，但仍是后端内联 HTML 的最低可用实现

这不构成功能阻塞，但说明：

- **前端还没有达到成体系的产品级 UI 一致性**

## 6. 结论修正

前面的“本轮完成项摘要”需要补上一条更准确的结论：

> 本轮已经完成仓库内的工程整改，并补做了本地真实浏览器验证；公开页面、支付沙箱页、portal 状态页、删除申请页都能真实打开和访问，基础 a11y 语义也成立。但 portal 资料向导 Step 5 的前端确认/提交交互在真实浏览器中仍不稳定，因此不能把当前前端链路表述为“已做完完整浏览器端到端验收”。

## 7. 建议下一步

优先级最高的前端后续项：

1. 修 Portal 资料向导 Step 5 的真实浏览器提交流程
2. 为公开链路补一条真正的浏览器 E2E 自动化（而不是仅 TestClient）
3. 补最小 UI 一致性整改：landing / pricing / portal 统一 spacing、按钮、卡片层级
4. 补更系统的 a11y 检查：焦点样式、颜色对比、错误提示、表单校验反馈
