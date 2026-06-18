# CURRENT_RULES_STATE_2026-06-16

最后更新: 2026-06-18
真相源: `docs/RULES_SOURCE_OF_TRUTH.md`
执行上下文: `docs/ACTIVE_EXECUTION_BOARD_2026-06-17.md` §1.1

---

## 1. 国家级规则覆盖矩阵

| scope    | rule_key      | title        | severity | status | source_evidence_id          |
| -------- | ------------- | ------------ | -------- | ------ | --------------------------- |
| national | parallel_rule | 平行志愿规则 | info     | active | national-2026-parallel-rule |

> 当前国家级仅 1 条（参考用）；其余通用规则随各省差异实现。

---

## 2. 省级规则覆盖矩阵（2026 版）

| province | slug         | rules_count | status | yaml                                      |
| -------- | ------------ | ----------- | ------ | ----------------------------------------- |
| 北京     | beijing      | TBD         | active | `rules/_truth/province/beijing.yaml`      |
| 上海     | shanghai     | TBD         | active | `rules/_truth/province/shanghai.yaml`     |
| 天津     | tianjin      | TBD         | active | `rules/_truth/province/tianjin.yaml`      |
| 重庆     | chongqing    | TBD         | active | `rules/_truth/province/chongqing.yaml`    |
| 河北     | hebei        | TBD         | active | `rules/_truth/province/hebei.yaml`        |
| 山西     | shanxi       | TBD         | active | `rules/_truth/province/shanxi.yaml`       |
| 内蒙古   | (待补)       | —           | —      | —                                         |
| 辽宁     | liaoning     | TBD         | active | `rules/_truth/province/liaoning.yaml`     |
| 吉林     | jilin        | TBD         | active | `rules/_truth/province/jilin.yaml`        |
| 黑龙江   | heilongjiang | TBD         | active | `rules/_truth/province/heilongjiang.yaml` |
| 江苏     | jiangsu      | TBD         | active | `rules/_truth/province/jiangsu.yaml`      |
| 浙江     | zhejiang     | TBD         | active | `rules/_truth/province/zhejiang.yaml`     |
| 安徽     | anhui        | TBD         | active | `rules/_truth/province/anhui.yaml`        |
| 福建     | fujian       | TBD         | active | `rules/_truth/province/fujian.yaml`       |
| 江西     | jiangxi      | TBD         | active | `rules/_truth/province/jiangxi.yaml`      |
| 山东     | shandong     | TBD         | active | `rules/_truth/province/shandong.yaml`     |
| 河南     | henan        | TBD         | active | `rules/_truth/province/henan.yaml`        |
| 湖北     | hubei        | TBD         | active | `rules/_truth/province/hubei.yaml`        |
| 湖南     | hunan        | TBD         | active | `rules/_truth/province/hunan.yaml`        |
| 广东     | guangdong    | TBD         | active | `rules/_truth/province/guangdong.yaml`    |
| 广西     | guangxi      | TBD         | active | `rules/_truth/province/guangxi.yaml`      |
| 海南     | hainan       | TBD         | active | `rules/_truth/province/hainan.yaml`       |
| 四川     | sichuan      | TBD         | active | `rules/_truth/province/sichuan.yaml`      |
| 贵州     | guizhou      | TBD         | active | `rules/_truth/province/guizhou.yaml`      |
| 云南     | yunnan       | TBD         | active | `rules/_truth/province/yunnan.yaml`       |
| 西藏     | xizang       | TBD         | active | `rules/_truth/province/xizang.yaml`       |
| 陕西     | (待补)       | —           | —      | —                                         |
| 甘肃     | gansu        | TBD         | active | `rules/_truth/province/gansu.yaml`        |
| 青海     | qinghai      | TBD         | active | `rules/_truth/province/qinghai.yaml`      |
| 宁夏     | (待补)       | —           | —      | —                                         |
| 新疆     | xinjiang     | TBD         | active | `rules/_truth/province/xinjiang.yaml`     |

> 当前已落地 27 省 yaml（不含内蒙古/陕西/宁夏，3 个待补）。每省 `rules_count` 由本轮 Batch 4 候选任务回填。

---

## 3. 证据链覆盖矩阵

| 类别       | 已落地 | 备注 |
| ---------- | ------ | ---- |
| 国家级     | ✅ 1    | `rules/_evidence/national/national-2026-parallel-volunteer-principle.md` 已落样本 |
| 安徽样本   | ✅ 11/11 | `rules/_evidence/anhui/` 已覆盖 active 规则；其中普通本科批 `collection_count` 已按 2026 官方时间表修正为 `1`，`retrieval_rule` 也已按考试院通知更新为“缺额时可视情多轮次投档” |
| 北京样本   | ✅ 11/11 | `rules/_evidence/beijing/` 已覆盖 active 规则；其中 `collection_count` 已改为“动态安排 / 下一批次录取开始前完成”的机读表达，不再伪造固定次数 |
| 广东样本   | ✅ 11/11 | `rules/_evidence/guangdong/` 已覆盖 active 规则；其中 `collection_count` 已按 2026 官方实施办法修正为动态征集机读表达，不再写死为 `2` |
| 福建样本   | ✅ 11/11 | `rules/_evidence/fujian/` 已覆盖 active 规则；其中本科批 `max_volunteers` 已按 2026 官方实施办法从 `40` 修正为 `50`，`collection_count` 已从 `1` 修正为 `2`，`subject_mode / retrieval_rule / exam_subject_total` 也已按 `3+1+2` 结构、平行志愿投档规则与 `750` 分口径完成归一化落证 |
| 甘肃样本   | ✅ 11/11 | `rules/_evidence/gansu/` 已覆盖 active 规则；其中普通类本科批 `45+6+调剂+2次征集` 已按 2026 招生工作通知闭环，`subject_mode` 已按甘肃考试院 `3+1+2` 原文落证，`exam_subject_total` 当前按考试院两篇文件共同确认的六科结构归一化维持 `750` 分口径 |
| 贵州样本   | ✅ 11/11 | `rules/_evidence/guizhou/` 已覆盖 active 规则；其中普通类本科批已按考试院 2025 志愿规定修正为 `专业+学校 / 本科批 / 96`，`collection_count` 已按 2025 本科批三轮征集通告从 `1` 修正为 `3`，`subject_mode / exam_subject_total` 也已按报名问答与投档公式补齐 `3+1+2 / 750` 口径 |
| 江西样本   | ✅ 11/11 | `rules/_evidence/jiangxi/` 已覆盖 active 规则；其中普通类本科批 `max_volunteers` 已按考试院常见问答确认为 `45`，`collection_count` 已按同页规则确认为 `2`，`mode / has_adjustment / max_majors_per_group` 已按“院校专业组 + 6 专业 + 是否服从专业调剂”闭环，`subject_mode / exam_subject_total` 已按高考综合改革 50 问补齐 |
| 四川样本   | ✅ 11/11 | `rules/_evidence/sichuan/` 已覆盖 active 规则；其中 `mode` 已从 `传统` 修正为 `院校专业组`，`batch` 已从 `本科一批` 修正为 `本科批`，`max_volunteers` 已从 `9` 修正为 `45`，`collection_count` 已按官方动态征集口径改成 `null`，`retrieval_rule / subject_mode / exam_subject_total` 也已按 `位次优先、一轮投档`、`3+1+2` 结构与 `750` 分口径完成落证 |
| 云南样本   | ✅ 11/11 | `rules/_evidence/yunnan/` 已覆盖 active 规则；其中普通类主体规则已按 2025 改革首年实施方案从 `传统/本科一批/5志愿` 修正为 `院校专业组/本科批/40个院校专业组`，`collection_count` 已改为动态征集口径，`subject_mode / exam_subject_total` 也已按 `3+1+2 / 750` 闭环 |
| 海南样本   | ✅ 11/11 | `rules/_evidence/hainan/` 已覆盖 active 规则；其中本科普通批 `max_volunteers` 已按 2026 官方实施办法从 `24` 修正为 `30`，`collection_count` 已从 `1` 修正为 `2`，`retrieval_rule / subject_mode / exam_subject_total` 也已按投档程序、`3+3` 结构与 `900` 分量纲完成归一化落证 |
| 河北样本   | ✅ 11/11 | `rules/_evidence/hebei/` 已覆盖 active 规则；其中本科批 `collection_count` 已按 2026 官方时间表从 `1` 修正为 `2`，`retrieval_rule` 已由考试院须知直接补齐，`subject_mode / exam_subject_total` 已按考试院对统一高考、首选/再选科目与 `750` 分量纲的官方描述完成归一化落证 |
| 湖北样本   | ✅ 11/11 | `rules/_evidence/hubei/` 已覆盖 active 规则；其中普通类 `45+6`、`组内专业调剂`、`分数优先/一次投档` 已由湖北阳光招生问答闭环，`subject_mode` 与 `exam_subject_total` 已由 2026 报名问答回填 |
| 湖南样本   | ✅ 11/11 | `rules/_evidence/hunan/` 已覆盖 active 规则 |
| 江苏样本   | ✅ 11/11 | `rules/_evidence/jiangsu/` 已覆盖 active 规则；其中 `collection_count` 已改为动态征集 + 专科补录机读表达，`max_majors_per_group` / `exam_subject_total` 也已由 `2026` 通知衔接 `2025` 工作意见闭环 |
| 广西样本   | ✅ 11/11 | `rules/_evidence/guangxi/` 已覆盖 active 规则；其中普通类本科普通批已按自治区教育厅 `2026` 工作方案、自治区招生考试院 `2026` 志愿填报通知和 `2026` 招生工作实施细则闭环，并将旧的 `max_majors_per_group: 6` 修正为官方明确的 `20`、`collection_count: 2` 修正为动态征集口径 `null`，同步确认 `院校专业组 / 本科批 / 40 / 组内调剂 / 3+1+2 / 750` 口径 |
| 黑龙江样本 | ✅ 11/11 | `rules/_evidence/heilongjiang/` 已覆盖 active 规则；其中普通类本科批已按黑龙江省招生考试信息港 `2024` 实施方案/解读、`2026` 志愿填报须知与 `2025` 本科批第二次征集志愿公告闭环，并将旧的 `max_volunteers: 45` 纠正为官方明确的 `40`，同步确认 `院校专业组 / 本科批 / 6+调剂 / 2次征集 / 3+1+2 / 750` 口径 |
| 青海样本   | ✅ 11/11 | `rules/_evidence/qinghai/` 已覆盖 active 规则；其中普通类本科批已按青海省教育考试网 `2026` 招生录取工作实施细则与 `2025` 高考综合改革实施方案闭环，并将旧的 `batch: 普通批` 修正为 `本科批`、`collection_count: 1` 修正为动态机读口径 `null`、`official_url: http://www.qhzk.com/` 修正为当前官方站点 `https://www.qhjyks.com/`，同步确认 `专业+学校 / 96 / 无调剂 / 3+1+2 / 750` 口径 |
| 西藏样本   | ✅ 11/11 | `rules/_evidence/xizang/` 已覆盖 active 规则；其中普通高考主体规则已按西藏教育考试院 `2026` 普通高等学校招生规定闭环，并保留 `传统 / 本科二批 / 10+4+专业服从调剂 / 文史理工 / 750` 口径，同时将旧的 `retrieval_rule: 分数优先、遵循志愿` 修正为带“一轮投档”含义的 `分数优先、遵循志愿、一次投档`，将 `collection_count: 1` 修正为官方明确的动态机读口径 `null` |
| 新疆样本   | ✅ 11/11 | `rules/_evidence/xinjiang/` 已覆盖 active 规则；其中普通类本科一批已按新疆教育考试院 `2026` 招生工作规定、`2026-06-12` 志愿模拟填报通知与志愿填报系统操作手册闭环，并将旧的 `max_volunteers: 9` 修正为官方明确的 `18`、`retrieval_rule: 志愿优先、遵循志愿` 修正为 `分数优先、遵循志愿、一次投档`、`official_url: http://www.xjzk.gov.cn/` 修正为 `https://www.xjzk.gov.cn/`，同步确认 `传统 / 本科一批 / 18+6+统招/定向调剂 / 文史理工 / 750` 口径 |
| 天津样本   | ✅ 11/11 | `rules/_evidence/tianjin/` 已覆盖 active 规则；其中普通类本科批已按《2026年天津市普通高校招生工作规定》、`2026-06-17` 志愿填报整体安排问答与 `2025` 第二期热点问答闭环，并将旧的 `collection_count: 1` 修正为 `2`、`official_url: http://www.zhaoban.tjzhaokao.com/` 修正为 `http://www.zhaokao.net/`，同步确认 `院校专业组 / 本科批 / 50+6+组内调剂 / 2次征询 / 3+3 / 750` 口径 |
| 河南样本   | ✅ 11/11 | `rules/_evidence/henan/` 已覆盖 active 规则；其中普通类本科批已按《河南省2026年普通高等学校招生工作规定》、`2026-06-11` 二次模拟演练通知与 `2026-06-12` 辅助系统公告闭环，并将旧的 `mode: 传统` 修正为 `院校专业组`、`batch: 本科一批` 修正为 `本科批`、`max_volunteers: 6` 修正为 `48`、`collection_count: 1` 修正为动态机读口径 `null`、`subject_mode: 传统` 修正为 `3+1+2`，同步确认 `院校专业组 / 本科批 / 48+6+组内调剂 / 动态征集 / 3+1+2 / 750` 口径 |
| 重庆样本   | ✅ 11/11 | `rules/_evidence/chongqing/` 已覆盖 active 规则；其中普通类本科批已按重庆市教育考试院 `2025-06-17` 志愿设置 / 录取规则问答、`2026-06-09` 考后时间节点安排与重庆市教委 `2025` 实施办法闭环，并将旧的 `batch: 普通批` 修正为 `本科批`、`collection_count: 1` 修正为动态机读口径 `null`，同步确认 `专业+学校 / 本科批 / 96 / 无调剂 / 分数优先、遵循志愿、一次投档 / 3+1+2 / 750` 口径 |
| 吉林样本   | ✅ 11/11 | `rules/_evidence/jilin/` 已覆盖 active 规则；其中普通类本科批已按吉林省教育考试院 2026 志愿问答、时间安排和招生指南修正为 `院校专业组 / 本科批 / 50+6+调剂 / 2次征集 / 3+1+2 / 750` 口径 |
| 辽宁样本   | ✅ 11/11 | `rules/_evidence/liaoning/` 已覆盖 active 规则；其中普通类本科批已按辽宁招生考试之窗问答与 2025 录取分数线页面修正为 `专业+学校 / 本科批 / 112 / 无调剂 / 2次征集 / 3+1+2 / 750` 口径 |
| 上海样本   | ✅ 11/11 | `rules/_evidence/shanghai/` 已覆盖 active 规则；其中本科普通批 `collection_count` 已按官方实施办法与征求志愿问答修正为 `2` |
| 山东样本   | ✅ 11/11 | `rules/_evidence/shandong/` 已覆盖 active 规则；其中常规批 `collection_count` 已按 2026 实施办法归一化为 `2`，`retrieval_rule` 也已补成同分排序细则 |
| 浙江样本   | ✅ 11/11 | `rules/_evidence/zhejiang/` 已覆盖 active 规则；普通类 `mode/max_volunteers/collection_count` 等 11 条规则均已由 2026 招生通知、网报通知和百问百答闭环 |

---

## 4. 当前能力面

- ✅ `gaokao-cli rules status --json` 报告 27 省在场
- ✅ `gaokao-cli rules verify --json` 校验 `national.yaml` + `province/`，并报告 stale/evidence 缺口
- ✅ `gaokao-cli rules list --province <p> --json` 枚举某省已加载规则
- ✅ `gaokao-cli audit run --province <p> --plan <json> --json` 跑结构化审计
- ✅ `gaokao-cli rules explain <rule_id>` 输出规则与证据绑定
- ✅ `gaokao-cli rules scaffold-evidence --json` 批量生成缺失 evidence 模板与索引
- ✅ "最近验证时间 > 90 天"自动告警已接入 `rules status` / `rules verify` / `doctor`

---

## 5. 与旧 `PROVINCE_RULES` 的迁移

- 迁移方式: 一次性脚本 `scripts/migrate_province_rules_to_truth.py`
- 旧字典保留作为过渡期镜像，新代码只读 `_truth`
- 旧 `gaokao-checker` 内部已委托给 `audit_engine`
- 迁移完整性由 `tests/test_rules_truth_phase1.py` 锁定

---

## 6. 下一阶段（Batch 4 候选）

1. 补齐内蒙古 / 陕西 / 宁夏 3 省 truth yaml 与首批官方 evidence
2. 逐省 `rules_count` 实际数回填
3. 内蒙古/陕西/宁夏 3 省 yaml 补齐
