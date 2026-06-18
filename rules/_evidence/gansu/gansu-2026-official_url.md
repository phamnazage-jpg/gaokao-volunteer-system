# gansu-2026-official_url

> 对应规则: `GANSU.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "首页_甘肃省教育考试院"
>
> "甘肃省教育考试院 版权所有 Copyright@ AllRights Reserved"
> —— 出处: 甘肃省教育考试院首页源码页眉/页脚
> URL: https://www.ganseea.cn/
> 发布日期: 访问复核于 2026-06-18
>
> "关于做好2026年甘肃省普通高校招生工作的通知_甘肃省教育考试院"
> —— 出处: 甘肃省教育考试院高考高招栏目文章标题源码
> URL: https://www.ganseea.cn/gaokaogaozhao/1884.html
> 发布日期: 2026-05-20

## 2. 转写为机读规则

```yaml
GANSU.official_url:
  severity: info
  value:
    official_url: https://www.ganseea.cn/
  effective_date: '2026-01-01'
  source_evidence_id: gansu-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：甘肃普通高考招生规则、报名通知和志愿填报实施办法均挂载在 `ganseea.cn` 主域下，因此 `official_url` 统一指向考试院官网主站
- 例 2：`kw.ganseea.cn` 等业务子系统承载报名或查询流程，但不是当前规则真相源的主入口

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 甘肃省教育考试院
- 复核负责人: 待指派
