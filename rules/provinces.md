# 高考志愿填报省份规则索引

本文件不再维护逐省静态快照表，而是作为 2026 版省份规则的统一入口。

这样做的目的只有一个：避免同一套规则在文档、脚本和 skill 副本里反复漂移。

## 当前真相源

- 省级规则事实：`rules/_truth/province/*.yaml`
- 国家级共性规则：`rules/_truth/national.yaml`
- 官方摘录证据链：`rules/_evidence/`
- 运行时加载入口：`data/rules/loader.py`
- 命令行验证入口：`python scripts/gaokao-cli rules status --json`

当前仓库的 27 省规则，以 truth yaml 和 evidence 摘录为准；本页只保留导航与阅读说明。

## 如何定位某个省的规则

1. 打开对应 truth 文件，例如 `rules/_truth/province/hunan.yaml`
2. 查看对应证据目录，例如 `rules/_evidence/hunan/`
3. 需要机器校验时，执行：

```bash
python scripts/gaokao-cli rules status --json
python scripts/gaokao-cli rules verify --json
python scripts/gaokao-cli rules explain HUNAN.undergrad_regular_batch.volunteer_mode --json
```

## 模式级摘要

以下摘要只用于帮助快速辨认规则类型，不作为逐省字段真相源：

### 院校专业组模式

- 志愿单位通常是“院校专业组”
- 调剂通常限定在组内专业
- 常见于新高考省份

### 专业+学校模式

- 志愿单位通常是“专业（类）+学校”
- 一般不提供传统意义上的校内调剂
- 关注专业级别的直接投档

### 传统院校志愿模式

- 仍以批次和院校志愿为主要表达方式
- 志愿数量、征集规则和批次设置差异更大
- 必须以当年省考试院公告为准

## 使用约束

- 不要再把本页当作“完整字段明细表”手工追加内容。
- 需要更新规则时，优先修改 `rules/_truth/province/*.yaml` 并补齐 `rules/_evidence/`。
- 如果只是给用户或文档提供入口，链接到本页即可。
