# Sprint 5 任务拆解（W8-9 · 12 人天 · 52 子任务）

> **主任务**：T-C-01 ~ T-C-13, T-D-01 ~ T-D-10
> **目标**：部署架构 + 监控 + 文档 + 10 基础组件
> **闸门**：G5（18 组件 dark story 全覆盖）

## 0. Sprint 5 概览

| 任务 | 主任务 | 估时 | 子任务数 |
|---|---|---|---|
| T-C-01 | 选部署平台 | 0.25d | 2 |
| T-C-02 | DNS + 域名 | 0.5d | 3 |
| T-C-03 | 反代配置 | 1.0d | 4 |
| T-C-04 | CORS 配置 | 0.25d | 2 |
| T-C-05 | CSP / HSTS | 1.0d | 4 |
| T-C-06 | Sentry 前端 | 1.0d | 4 |
| T-C-07 | Web Vitals 上报 | 0.5d | 3 |
| T-C-08 | trace 透传 | 0.5d | 3 |
| T-C-09 | 告警规则 | 0d | 2 |
| T-C-10 | 部署文档 | 1.0d | 2 |
| T-C-11 | 运维 Runbook | 1.0d | 2 |
| T-C-12 | 安全审计 | 1.0d | 2 |
| T-C-13 | 灰度发布流程 | 1.0d | 2 |
| T-D-01 ~ T-D-10 | 10 基础组件 | 4.0d | 35 |
| **合计** | **23 任务** | **12d + 缓冲 0d = 12d** | **52** |

> 注：12d 紧凑，缓冲在 Sprint 6-8

---

## C.1 部署架构（5 任务 · 11 子任务 · 3d）

### T-C-01 · 选部署平台（0.25d · 2 子任务）
- ST-S5-C-01.1 决策（CloudStudio / Vercel / 自托管）（0.125d）
- ST-S5-C-01.2 写 `docs/DEPLOY_DECISION.md`（0.125d）

### T-C-02 · DNS + 域名（0.5d · 3 子任务）
- ST-S5-C-02.1 注册 `web.gaokao.example.com`（0.125d）
- ST-S5-C-02.2 注册 `api.gaokao.example.com`（0.125d）
- ST-S5-C-02.3 HTTPS 证书自动续签（Let's Encrypt）（0.25d）

### T-C-03 · 反代配置（1.0d · 4 子任务）
- ST-S5-C-03.1 nginx / caddy 配置（0.5d）
- ST-S5-C-03.2 web → Next.js 静态产物（0.125d）
- ST-S5-C-03.3 api → FastAPI（0.125d）
- ST-S5-C-03.4 /api/* 转发（0.25d）
- **验收**：
  - [ ] 单一域名访问前端，浏览器无 CORS 报错

### T-C-04 · CORS 配置（0.25d · 2 子任务）
- ST-S5-C-04.1 `CORSMiddleware` 白名单（0.125d）
- ST-S5-C-04.2 OPTIONS 预检验证（0.125d）

### T-C-05 · CSP / HSTS（1.0d · 4 子任务）
- ST-S5-C-05.1 HSTS 配置（0.25d）
- ST-S5-C-05.2 X-Content-Type-Options（0.125d）
- ST-S5-C-05.3 X-Frame-Options DENY（0.125d）
- ST-S5-C-05.4 CSP 策略（0.5d）
  - `default-src 'self'`
  - `img-src 'self' data:`
  - `style-src 'self' 'unsafe-inline'`
  - `script-src 'self'`
  - `Referrer-Policy: strict-origin-when-cross-origin`

---

## C.2 监控（4 任务 · 12 子任务 · 2d）

### T-C-06 · Sentry 前端（1.0d · 4 子任务）
- ST-S5-C-06.1 `@sentry/nextjs` 集成（0.25d）
- ST-S5-C-06.2 错误 100% 上报（0.25d）
- ST-S5-C-06.3 Performance trace（路由切换）（0.25d）
- ST-S5-C-06.4 PII 脱敏（用户消息过滤）（0.25d）

### T-C-07 · Web Vitals 上报（0.5d · 3 子任务）
- ST-S5-C-07.1 `next/web-vitals` 接入（0.125d）
- ST-S5-C-07.2 自托管 endpoint（0.125d）
- ST-S5-C-07.3 Prometheus 75 分位存储（0.25d）

### T-C-08 · trace 透传（0.5d · 3 子任务）
- ST-S5-C-08.1 `x-trace-id` header 前端发送（0.125d）
- ST-S5-C-08.2 FastAPI 中间件接收（0.125d）
- ST-S5-C-08.3 Sentry 关联（0.25d）

### T-C-09 · 告警规则（0d · 2 子任务）
- ST-S5-C-09.1 错误率 > 1% 告警（0d）
- ST-S5-C-09.2 API P95 > 1s 告警（0d）
- ST-S5-C-09.3 Web Vitals P75 跌破告警（0d）
- **验收**：
  - [ ] Slack / 钉钉 webhook 接收

---

## C.3 文档 + 收口（4 任务 · 8 子任务 · 4d）

### T-C-10 · 部署文档（1.0d · 2 子任务）
- ST-S5-C-10.1 写 `docs/DEPLOY.md`（0.75d）
- ST-S5-C-10.2 3 路径说明（CloudStudio / 自托管 / Vercel）（0.25d）

### T-C-11 · 运维 Runbook（1.0d · 2 子任务）
- ST-S5-C-11.1 写 `docs/RUNBOOK.md`（0.75d）
- ST-S5-C-11.2 10 常见故障处理（0.25d）

### T-C-12 · 安全审计（1.0d · 2 子任务）
- ST-S5-C-12.1 OWASP top 10 自查（0.75d）
- ST-S5-C-12.2 写 `docs/SECURITY_AUDIT_2026-XX.md`（0.25d）

### T-C-13 · 灰度发布流程（1.0d · 2 子任务）
- ST-S5-C-13.1 5% → 20% → 100% 三步（0.75d）
- ST-S5-C-13.2 自动化脚本（0.25d）

---

## D.1 基础组件补齐（10 任务 · 35 子任务 · 4d）

> 通用模式：每组件 3-4 子任务（props/渲染/单测/Storybook）

### T-D-01 · Dialog（0.5d · 3 子任务）
- ST-S5-D-01.1 portal 渲染 + 焦点陷阱 + ESC + 点击外部（0.25d）
- ST-S5-D-01.2 单测（0.125d）
- ST-S5-D-01.3 Storybook 2 故事（0.125d）

### T-D-02 · Toast（0.5d · 4 子任务）
- ST-S5-D-02.1 4 种类型 + 自动消失（0.125d）
- ST-S5-D-02.2 队列管理（0.125d）
- ST-S5-D-02.3 单测（0.125d）
- ST-S5-D-02.4 Storybook 4 故事（0.125d）

### T-D-03 · Tooltip（0.25d · 2 子任务）
- ST-S5-D-03.1 hover 200ms 显示 + 3s 自动消失（0.125d）
- ST-S5-D-03.2 单测 + Storybook（0.125d）

### T-D-04 · Dropdown（0.5d · 3 子任务）
- ST-S5-D-04.1 Sidebar 头像菜单用（0.25d）
- ST-S5-D-04.2 键盘导航（0.125d）
- ST-S5-D-04.3 单测 + Storybook（0.125d）

### T-D-05 · Avatar（0.25d · 2 子任务）
- ST-S5-D-05.1 3 套（AI / User / 群组）（0.125d）
- ST-S5-D-05.2 单测 + Storybook（0.125d）

### T-D-06 · Skeleton（0.25d · 2 子任务）
- ST-S5-D-06.1 4 种形状（text/card/circle/avatar）（0.125d）
- ST-S5-D-06.2 单测 + Storybook（0.125d）

### T-D-07 · ProgressBar（0.25d · 2 子任务）
- ST-S5-D-07.1 通用（区别于 InfoCollectionProgress）（0.125d）
- ST-S5-D-07.2 单测 + Storybook（0.125d）

### T-D-08 · Switch（0.25d · 2 子任务）
- ST-S5-D-08.1 偏好设置用（0.125d）
- ST-S5-D-08.2 单测 + Storybook（0.125d）

### T-D-09 · Checkbox（0.5d · 3 子任务）
- ST-S5-D-09.1 FormCard 选科用（0.25d）
- ST-S5-D-09.2 受控/非受控（0.125d）
- ST-S5-D-09.3 单测 + Storybook（0.125d）

### T-D-10 · Radio（0.5d · 3 子任务）
- ST-S5-D-10.1 FormCard 单选用（0.25d）
- ST-S5-D-10.2 与 Checkbox 区分（0.125d）
- ST-S5-D-10.3 单测 + Storybook（0.125d）

---

## Sprint 5 收口验收

- [ ] 23 主任务 / 52 子任务全部完成
- [ ] **G5 通过**：18 组件 dark story 全覆盖
- [ ] 反代 / CSP / Sentry 跑通
- [ ] 进入 Sprint 6 前 commit：`<feat(s5): deploy+monitoring+10 components>`
