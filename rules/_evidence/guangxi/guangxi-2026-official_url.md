# guangxi-2026-official_url

> 对应规则: `GUANGXI.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "通过电脑端填报的考生，须在志愿填报规定时间内登录“广西招生考试院”网站（填报志愿的唯一网站），点击“志愿填报”栏目，在“2026年普通高校招生志愿填报系统”中进行填报。"
>
> "各批次征集志愿的填报时间将在“广西招生考试院”网站（https://www.gxeea.cn/，下同）公布。"
> —— 出处: 《自治区招生考试院关于做好我区2026年普通高校招生统一考试志愿填报工作的通知》
> URL: https://www.gxeea.cn/view/content_1013_32855.htm
> 发布日期: 2026-06-17

## 2. 转写为机读规则

```yaml
GUANGXI.official_url:
  severity: info
  value:
    official_url: https://www.gxeea.cn/
  effective_date: '2026-01-01'
  source_evidence_id: guangxi-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：广西 2026 志愿填报通知明确 `https://www.gxeea.cn/` 是志愿填报唯一网站，适合作为规则标准来源
- 例 2：如后续考试院更换统一域名，应同步更新 truth 和 evidence

## 4. 后续维护

- 下次复核时间: 2026-07-10
- 复核来源: 广西招生考试院
- 复核负责人: 待指派
