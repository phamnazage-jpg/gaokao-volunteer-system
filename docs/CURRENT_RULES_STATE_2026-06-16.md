# CURRENT_RULES_STATE_2026-06-16

最后更新: 2026-06-16
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

| 类别     | 已落地 | 备注                                                    |
| -------- | ------ | ------------------------------------------------------- |
| 国家级   | ⚠ 占位 | `national-2026-parallel-rule` 是占位 ID，未指向真实文件 |
| 27 省    | ❌ 0   | `rules/_evidence/` 目录尚未建                           |
| 全国通用 | ❌ 0   | 需 `rules/_evidence/national/` 子目录                   |

---

## 4. 当前能力面

- ✅ `gaokao-cli rules status --json` 报告 27 省在场
- ✅ `gaokao-cli rules verify --json` 校验 `national.yaml` + `province/`
- ✅ `gaokao-cli audit run --province <p> --plan <json> --json` 跑结构化审计
- ❌ `gaokao-cli rules explain <rule_id>` 未实现
- ❌ "最近验证时间 > 90 天"自动告警未实现

---

## 5. 与旧 `PROVINCE_RULES` 的迁移

- 迁移方式: 一次性脚本 `scripts/migrate_province_rules_to_truth.py`
- 旧字典保留作为过渡期镜像，新代码只读 `_truth`
- 旧 `gaokao-checker` 内部已委托给 `audit_engine`
- 迁移完整性由 `tests/test_rules_truth_phase1.py` 锁定

---

## 6. 下一阶段（Batch 4 候选）

1. `rules/_evidence/<prov>/<year>-<topic>.md` 补建
2. 逐省 `rules_count` 实际数回填
3. `gaokao-cli rules explain <rule_id>` 命令
4. "最近验证时间 > 90 天"自动告警
5. 内蒙古/陕西/宁夏 3 省 yaml 补齐
