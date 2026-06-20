# Q-A 数据质量审计报告 — 非湖南数据密度

审计时间: 2026-06-20 | HEAD: 604c8b3 | 范围: `data/crowd_db/*`

## 1. crowd_db 现状 (省份覆盖, 时间窗口, 关键字段)

- **省份覆盖**: 27 个 JSON 文件齐全（23 省 + 4 直辖市），不含 5 自治区/港澳台。结构 100% 落地。
- **时间窗口**: 所有 27 个文件 `data_year=2025`、`last_updated=2026-06-12`（同一批次生成）。
- **关键字段**: 顶层 8 字段（province / last_updated / data_year / source / source_url / source_type / confidence / score_ranges）全部齐备，符合 T3.1 schema。
- **不存位次/分数/选科/院校代码原始字段**——本数据库是"大厂 AI 反扎堆推荐"库，不是录取数据库；院校用 name+major 标识，无标准院校代码。

## 2. 非湖南数据密度评估

| 维度                 | 湖南       | 其它 26 省      | 高考生源大省（北京/上海/广东/江苏/山东/河南/四川） |
| -------------------- | ---------- | --------------- | -------------------------------------------------- |
| confidence           | 0.85       | 0.45 全部       | 0.45 全部                                          |
| quality_level        | high (A级) | skeleton (C级)  | skeleton (C级)                                     |
| score_ranges 段数    | 10         | 1-3             | 2-3                                                |
| recommendations 条数 | 68         | 1-8             | 2-8                                                |
| alternatives 条数    | 136        | 0-3             | 0-3                                                |
| 覆盖分数段           | 440-690    | 多为头部 1-2 段 | 头部 2-3 段                                        |

**结论**: 湖南与其它 26 省是"高原+26 骨架"二八结构。高考生源大省无一例外都是 C 级骨架，平均只覆盖头部 2-3 个分数段、2-8 条推荐；典型如广东 2 段/4 条、贵州仅 1 段/1 条，**不足以驱动反扎堆结论**。

## 3. 已有数据质量工具

- `data/crowd_db/quality_summary.py` + `python -m data.crowd_db.quality_summary --human`：列出 27 省质量分级（实测 high=1 / skeleton=26）。
- `data/crowd_db/cli.py` + `scripts/gaokao-data-trace`：按校名溯源查询（输出 confidence / quality_level / last_updated）。
- `data/crowd_db/risk_report.py`：三色风险分级，模板已绑 `audit_report.html`。
- 测试: `tests/test_crowd_db_data_quality.py`（**设计文档要求**，实测**未在仓库找到该文件**——缺口）。`data/crowd_db/tests/test_provenance.py` 已锁死湖南 confidence≥0.8、record_count>0，但未锁死"非湖南 ≤ skeleton"。

## 4. 2026 高考季数据完备性

- **2024 历史数据**: 仓库无 2024 单独快照（`data_year=2025` 即为当前)。
- **2025 实际数据**: 27 省全部为 `data_year=2025`，但实质只有湖南是真实整理。
- **2026 模拟数据**: 不存在。`data_completeness=skeleton` 的 26 省 `predicted_increase` 是"预测 2026 上涨分"（仅 1 条/省的元字段），不是 2026 模拟卷。
- **官方进度**：`spec_checker_v2.py:780` 注释"2026 年招生计划 6/15-20 公布、位次 6/25 出分后确定"——**当前 6/20 处于真空期**，可解释为何 2026 数据未落库。

## 5. 推荐改进 Top 5

1. **补 `tests/test_crowd_db_data_quality.py`**（CROWD_DB_DATA_QUALITY §7 承诺的锁死文件），断言"湖南 high + 其它 26 省 in {medium, skeleton}"——当前测试网有缺口。
2. **明确 2026 高考季数据来源策略**：在 `data/crowd_db/README.md` 加 `data_year=2026` 字段约定与"6/25 前仅 2025 基线+湖南优先"口径。
3. **为广东/江苏/山东/河南/四川优先扩容**——这些是 top 5 考生大省，当前 C 级骨架对业务无支撑意义；按湖南 10 段模板补到 medium 即可大幅改善报告可用性。
4. **CRITICAL：修正 `docs/CURRENT_STATE.md:302`** —— 文档写"27 省 crowd_db 均为高置信强推荐数据"，与代码事实（仅 1 省 high）严重不符，存在合规风险。
5. **加 `data_completeness` 字段到 JSON 顶层**（CROWD_DB_DATA_QUALITY §2 已约定，但当前 27 个 JSON 均无此字段，仅以 `confidence` 间接推导），与 `quality_level` 一一对应后报告渲染可自动加 `[置信度: 中]` 标签。
