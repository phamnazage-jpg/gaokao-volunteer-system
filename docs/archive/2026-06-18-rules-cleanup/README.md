# 2026-06-18 Rules Cleanup

本目录记录 2026-06-18 对“既有脏改动”中文档类文件做验证后的整理结论。

## 417 文件总盘点

盘点范围不是当前工作树的临时 diff，而是以下两个提交涉及文件的去重并集：

- `246f21c feat(review): land unified remediation and rules evidence closure`
- `2252157 docs(review): close out 2026-06-17 optimization goal`

复核命令：

```bash
git show --name-only --pretty=format: 246f21c 2252157 | sed '/^$/d' | sort -u | wc -l
```

复核结果：`417`

按最终处置状态分类：

- `integrated_source_of_truth`: 345
  - `rules/_truth/*` 与 `rules/_evidence/*`
  - 这些是当前规则可信化链路的真相源和证据层，不能归档
- `integrated_runtime_or_test`: 50
  - `admin/`、`data/`、`scripts/`、`ops/`、`tests/` 中被运行链路、验证链路或回归测试直接使用的文件
- `retained_current_doc`: 14
  - `README.md`、`rules/provinces.md`、`rules/provinces/README.md`、`docs/CURRENT_STATE.md`、`product/*.md` 等当前入口或当前口径文档
- `retained_historical_evidence`: 7
  - `docs/ACTIVE_MULTI_AGENT_EXECUTION_BOARD_2026-06-17.md`
  - `docs/FINAL_VERIFICATION_MATRIX_2026-06-17.md`
  - `docs/plans/2026-06-17-*.md`
  - `reports/COMPREHENSIVE_SYSTEM_REVIEW_2026-06-17.md`
- `archived_duplicate`: 1
  - `skills/gaokao-spec-checker/rules/provinces.md`

结论：

- 417 个文件已经全部完成“保留 / 归档”决策，不存在“还没判断”的剩余项。
- 真正需要落地变更的只有重复副本与过时入口页，其他大多数文件已经在项目里承担运行、验证、真相源或历史追溯职责，不应为了表面整洁继续移动。

## 已归档

- `skills-gaokao-spec-checker-rules-provinces.md`
  - 原路径: `skills/gaokao-spec-checker/rules/provinces.md`
  - 结论: 未被仓库内任何文件引用，且与 `rules/provinces.md` 为重复静态快照。
  - 处理: 从 skill 目录移出，保留为历史镜像，避免继续形成第二份省份规则文档。

## 已验证但保留

- `docs/ACTIVE_MULTI_AGENT_EXECUTION_BOARD_2026-06-17.md`
- `docs/FINAL_VERIFICATION_MATRIX_2026-06-17.md`
- `reports/COMPREHENSIVE_SYSTEM_REVIEW_2026-06-17.md`
- `docs/plans/2026-06-17-comprehensive-review-remediation.md`
- `docs/plans/2026-06-17-multi-agent-execution-checklist.md`
- `docs/plans/2026-06-17-subagent-work-orders.md`
- `docs/plans/2026-06-17-unified-remediation-and-optimization-task-list.md`

保留原因：

- 这些文件仍承担历史审计、结项证据或整改追溯作用。
- `docs/CURRENT_STATE.md` 的当前执行真相源是 `docs/ACTIVE_EXECUTION_BOARD_2026-06-17.md`，不是上面这批多代理过程文件；因此它们不是活跃入口，但也不是“无用文件”。
- 在未建立统一历史快照索引前，直接迁移整组文件会制造更多断链与失真，不符合最小改动原则。
