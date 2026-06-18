# xizang-2026-official_url

> 对应规则: `XIZANG.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生可登录西藏教育考试院官网或“西藏自治区教育考试院”微信公众号及时查询有关工作安排和各类招考信息。"
>
> "西藏教育考试院网址：http://zsks.edu.xizang.gov.cn/"
> —— 出处: 《西藏自治区2026年普通高等学校招生规定》
> URL: http://zsks.edu.xizang.gov.cn/71/74/7787.html
> 发布日期: 2026-05-29

## 2. 转写为机读规则

```yaml
XIZANG.official_url:
  severity: info
  value:
    official_url: http://zsks.edu.xizang.gov.cn/
  effective_date: '2026-01-01'
  source_evidence_id: xizang-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：西藏 2026 官方正文已直接给出考试院官网地址，truth 可继续锚定 `http://zsks.edu.xizang.gov.cn/`
- 例 2：西藏考生查分、查录取和查询招考信息都以考试院官网与官微为官方发布口径

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 西藏教育考试院
- 复核负责人: 待指派
