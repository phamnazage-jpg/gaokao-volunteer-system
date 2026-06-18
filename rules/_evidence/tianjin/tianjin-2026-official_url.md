# tianjin-2026-official_url

> 对应规则: `TIANJIN.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "请及时关注“天津市教育招生考试院”微信公众号和招考资讯网（www.zhaokao.net）的官方信息。"
>
> "考生收到录取通知书后，应及时通过市教育招生考试院官方网站（www.zhaokao.net）或录取高校指定的信息发布渠道进行核实和确认。"
> —— 出处: 《热点问答①|天津高考生志愿填报之整体安排》 / 《2026年天津市普通高校招生工作规定》
> URL: http://www.zhaokao.net/gkck/system/2026/06/16/030009834.shtml / http://www.zhaokao.net/zwgk/doc/003/000/114/00300011419_edf58f9e.pdf
> 发布日期: 2026-06-17 / 2026-04-29

## 2. 转写为机读规则

```yaml
TIANJIN.official_url:
  severity: info
  value:
    official_url: http://www.zhaokao.net/
  effective_date: '2026-01-01'
  source_evidence_id: tianjin-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：2026 官方正文明确把 `www.zhaokao.net` 作为天津教育招生考试院官方网站与官方信息平台，旧的 `tjzhaokao.com` 不再作为当前主锚点
- 例 2：官方原文未强制声明协议，项目沿用当前可直接访问且正文一致的 `http://www.zhaokao.net/`

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 天津教育招生考试院
- 复核负责人: 待指派
