# yunnan-2026-official_url

> 对应规则: `YUNNAN.official_url`
> 所属: 省级
> 规则版本: `2026.1`
> 摘录时间: 2026-06-18
> 摘录人: Hermes Agent (主代理)
> 证据状态: complete

## 1. 官方原文摘录

> "考生应主动关注云南省招生考试院官方网站（https://www.ynzs.cn/）发布的有关通知、公告，以免错过重要信息。"
> —— 出处: 《2026年云南省普通高校招生补报名考生须知》
> URL: https://www.ynzs.cn/html/content/8350.html
> 发布日期: 2026-02-12

## 2. 转写为机读规则

```yaml
YUNNAN.official_url:
  severity: info
  value:
    official_url: https://www.ynzs.cn/
  effective_date: '2026-01-01'
  source_evidence_id: yunnan-2026-official_url
  status: active
```

## 3. 关键边界与例外

- 例 1：云南考试院已直接把 `https://www.ynzs.cn/` 指定为高考通知公告的主发布入口，因此项目层 `official_url` 继续保留站点根地址
- 例 2：具体报名、志愿填报与成绩查询会跳转到子系统，但根站仍是规则公告与政策文件的统一入口

## 4. 后续维护

- 下次复核时间: 2026-07-20
- 复核来源: 云南省招生考试院
- 复核负责人: 待指派
