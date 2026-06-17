# data/majors_catalog

当前状态: `MVP curated subset`
最后更新: 2026-06-17

## 说明

- 本目录用于存放“国家级专业目录 / 校级招生专业目录”的结构化真相源。
- **当前仅落地国家级目录 MVP 子集**，目的是先闭合模型、loader、CLI、测试与门禁。
- 当前数据**不是完整教育部目录全集**，不能误读为完整覆盖。

## 当前已落地

- `national/2024.json`
- `national/latest.json`
- `schools/2026/10001.json`（北京大学示例骨架）

## coverage_mode

- `mvp_subset`: 人工精选子集，用于当前 Phase2 架构闭环与回归验证
- 后续完整目录落地后，改为 `full_catalog`

## 下一步

1. 扩充国家级目录到完整教育部 2024 本科专业目录
2. 新增 `schools/<year>/<school_code>.json`
3. 接入 majors validation 到 audit engine
