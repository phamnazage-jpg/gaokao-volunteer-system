# CROWD_DB_DATA_QUALITY

最后更新: 2026-06-14

## 1. 目标

明确区分：

- **27 省结构覆盖**：所有省份文件存在、字段 schema 基本可读
- **高置信推荐覆盖**：可以对外输出较强推荐结论

防止把“文件齐全”误报为“所有省份都具备高质量反扎堆推荐能力”。

---

## 2. 当前已存在能力

代码中已经存在以下质量信号：

1. `confidence` 字段
2. `USABLE_CONFIDENCE_THRESHOLD = 0.5`
   - 位置：`data/crowd_db/loader.py`
3. 低置信度 warning
   - `confidence < 0.5` 会产生 `UserWarning`
4. CLI / risk report 已能暴露 `confidence`
   - `data/crowd_db/cli.py`
   - `data/crowd_db/risk_report.py`

这说明当前并不是“完全没有质量分层”，而是**尚未把分层规则沉淀成对外统一口径**。

---

## 3. 当前推荐的质量分级口径

### A 级（高置信）

- `confidence >= 0.8`
- 允许输出较强推荐/较明确风险提示

### B 级（可用）

- `0.5 <= confidence < 0.8`
- 可展示，但要保留审慎提示

### C 级（骨架）

- `confidence < 0.5`
- 只能作为结构占位或弱提示
- 不应对外宣称“高质量推荐已覆盖”

---

## 4. 当前真相

- 湖南应视为当前重点高置信省份
- 其他部分省份仍属于“结构覆盖已完成，但推荐质量待增强”
- 因此对外更准确说法应为：

> 已支持 27 省规则/数据结构接入；其中高置信推荐能力当前重点仍在湖南，其他省份按 confidence 分级展示。

---

## 5. 后续实现动作

1. 在报告/CLI 中显式输出质量等级（A/B/C）
2. 在低置信省份自动降级文案
3. 在 README / 产品文案中避免“27 省高质量推荐全覆盖”表述
4. 后续补 province-level completeness/quality summary

---

## 6. 完成口径

只有同时满足以下条件，才可将 X-08 视为整体完成：

- 已有统一质量分级文档（本文件）
- 报告/CLI/对外文案至少一处真实使用该分级
- 低置信省份不会再输出与湖南同级别强结论

当前状态：

- **文档基线已补齐**
- **`risk_report` 已输出 `quality_level / quality_label`**
- **`gaokao-data-trace --human` 已输出质量等级**
- **低置信省份已通过 confidence 分级与 warning 机制降级**
