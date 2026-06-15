# CROWD_DB_DATA_QUALITY

最后更新: 2026-06-14
适用范围: `data/crowd_db/*.json` + `skills/gaokao-spec-checker/scripts/...` 反扎堆模块

---

## 1. 设计目标

`data/crowd_db` 当前有 27 省的结构化 JSON 文件。本设计目标:

- 区分“结构覆盖”与“高置信推荐数据覆盖”。
- 在不出现误导的前提下,允许其它省份逐步补齐。
- 报告、portal、咨询输出都必须显式声明该省的 data completeness level。

## 2. 字段约定

`data/crowd_db/<province>.json` 推荐数据:

```json
{
  "province": "湖南",
  "data_completeness": "high",
  "confidence": 0.85,
  "score_buckets": [
    {"score": 500, "rank_estimate": 20000, "schools": [{"name": "...", "majors": [...]}]}
  ],
  "source": {"type": "official", "url": "...", "year": 2025},
  "last_updated": "2026-06-01"
}
```

字段说明:

- `data_completeness` (required): 4 档之一
  - `high` : 高置信, 推荐输出可作为强结论
  - `medium`: 中置信, 推荐输出可作为参考结论
  - `low` : 低置信, 推荐输出只能作为弱提示
  - `skeleton`: 仅骨架, 不允许对外推荐结论
- `confidence` (required, 0.0-1.0): 与 data_completeness 一致
- `source.type` (required): 4 档之一
  - `official` : 考试院 / 阳光高考
  - `report` : 第三方权威报告
  - `estimate` : 内部估算
  - `placeholder`: 暂存占位, 不允许用于结论
- `source.year` (required): 数据年份
- `last_updated` (required, ISO8601)

## 3. 高置信数据完整性矩阵

| 省份       | data_completeness | confidence | 当前状态           | 推荐输出       |
| ---------- | ----------------- | ---------- | ------------------ | -------------- |
| 湖南       | high              | ≥ 0.8      | 实际数据, 多分数段 | 强结论         |
| 北京       | medium            | 0.5-0.8    | 骨架, 部分数据     | 弱提示         |
| 上海       | medium            | 0.5-0.8    | 骨架, 部分数据     | 弱提示         |
| 广东       | medium            | 0.5-0.8    | 骨架, 部分数据     | 弱提示         |
| 浙江       | medium            | 0.5-0.8    | 骨架, 部分数据     | 弱提示         |
| 其它 22 省 | skeleton          | < 0.5      | 仅省份规则         | 不允许推荐结论 |

## 4. 报告输出文案规则

`skills/gaokao-spec-checker` / 反扎堆报告 / `gaokao_visual_report` 输出:

- `data_completeness == high` : 直接给出推荐结论
- `data_completeness == medium` : 在结论前必须加 `[置信度: 中]` 标签
- `data_completeness == low` : 只给弱提示, 禁止结论
- `data_completeness == skeleton`: 报告必须写明“暂无该省的高质量推荐数据”

## 5. 强制不变量

- `data_completeness` 与 `confidence` 必须一致
  - `high` ⇒ confidence >= 0.80
  - `medium` ⇒ confidence >= 0.50
  - `low` ⇒ confidence < 0.50
  - `skeleton` ⇒ confidence < 0.20
- `source.type` 与 `data_completeness` 必须一致
  - `official` ⇒ `data_completeness in {high, medium}`
  - `placeholder` ⇒ `data_completeness == skeleton`
- `last_updated` 必须在 source.year 之后 (或同一年)
- 高置信省 (`high`) 的 `score_buckets` 必须至少覆盖 5 个分数段

## 6. 实现侧

`data/orders/loader.py` 与 `data/crowd_db/crowd_detector.py` 加载时:

1. 校验 `data_completeness` 与 `confidence` 一致
2. 校验 `source.type` 与 `data_completeness` 一致
3. 把 `data_completeness` 暴露给报告渲染器

## 7. 测试锁死

`tests/test_crowd_db_data_quality.py` 必须锁死:

1. `data/crowd_db/湖南.json` 的 `data_completeness == high`, 至少 5 个 score_buckets
2. 其它 26 省的 `data_completeness in {medium, skeleton}`
3. 任何省的 `data_completeness` 与 `confidence` 数值必须满足第 5 节不变量
4. 报告渲染器在 `data_completeness == skeleton` 时必须输出 “暂无该省的高质量推荐数据”

## 8. 后续工作

- 持续补充中等置信省份的数据
- 把 `gaokao_visual_report` 改造成在结论前自动插入置信度标签
- 在反扎堆报告中显式标出该省份的 data_completeness
