# API参考

本文档提供给开发者使用的API参考。

---

## 🎯 规范检查器 API

### `GaokaoSpecCheckerV2` 类

用于检查志愿方案的规范性。

#### 构造函数

```python
from spec_checker_v2 import GaokaoSpecCheckerV2

checker = GaokaoSpecCheckerV2(province=None)
```

**参数**:

- `province` (str, 可选): 省份名称，如"湖南"、"浙江"。如果未指定，会自动检测。

#### 方法

##### `auto_detect_and_check(text)`

自动检测省份并检查方案。

**参数**:

- `text` (str): 志愿方案文本

**返回值**:

- `str`: 检查报告（Markdown格式）

**示例**:

```python
checker = GaokaoSpecCheckerV2()
report = checker.auto_detect_and_check("我是湖南考生，578分...")
print(report)
```

##### `check_volunteer_unit(text)`

检查志愿单位是否正确。

**检测条件**:

- 省份模式为"院校专业组"时，应使用"院校专业组"而非"学校"
- 省份模式为"专业+学校"时，不应使用"组内服从"

##### `check_volunteer_count(text)`

检查志愿数量是否合规。

**检测条件**:

- 是否超过本省最大志愿数
- 是否填满建议志愿数

##### `check_majors_per_group(text)`

检查每组专业数。

**检测条件**:

- 院校专业组模式：每组最多6个
- 专业+学校模式：每组1个

##### `check_adjustment_rule(text)`

检查调剂规则。

**检测条件**:

- 调剂范围是否符合本省模式
- 是否提到"组内专业"

---

## 🗺️ 省份规则 API

### `PROVINCE_RULES` 字典

包含27个省份的志愿填报规则。

```python
from spec_checker_v2 import PROVINCE_RULES

# 获取湖南规则
hunan_rule = PROVINCE_RULES["湖南"]

print(hunan_rule["mode"])              # "院校专业组"
print(hunan_rule["max_volunteers"])    # 45
print(hunan_rule["adjustment_scope"])  # "组内专业"
```

### 规则字段

| 字段                   | 类型 | 说明       | 示例                                |
| ---------------------- | ---- | ---------- | ----------------------------------- |
| `mode`                 | str  | 志愿模式   | "院校专业组" / "专业+学校" / "传统" |
| `max_volunteers`       | int  | 最大志愿数 | 45                                  |
| `max_majors_per_group` | int  | 每组专业数 | 6                                   |
| `has_adjustment`       | bool | 是否有调剂 | True                                |
| `adjustment_scope`     | str  | 调剂范围   | "组内专业" / "全部专业" / "无"      |
| `retrieval_rule`       | str  | 检索规则   | "分数优先、遵循志愿、一次投档"      |
| `collection_count`     | int  | 征集次数   | 2                                   |
| `subject_mode`         | str  | 选科模式   | "3+1+2" / "3+3" / "传统"            |
| `official_url`         | str  | 官方网址   | "http://jyt.hunan.gov.cn/"          |
| `exam_subject_total`   | int  | 总分       | 750                                 |

---

## 🔍 省份检测 API

### `detect_province(text)`

从文本中自动检测省份。

```python
from spec_checker_v2 import detect_province

province = detect_province("我是湖南考生...")
print(province)  # "湖南"

province = detect_province("浙江省，620分")
print(province)  # "浙江"
```

**支持检测形式**:

- 全称："湖南"、"浙江省"
- 简称："湘"、"浙"

---

## 🔤 错误模式 API

### 错误分类

#### 🔴 致命错误

```python
{
    "rule": "错误名称（省份）",
    "description": "问题描述",
    "fix": "修正建议"
}
```

**检测函数**: `_check_volunteer_unit()`

#### 🟡 严重错误

```python
{
    "rule": "错误名称",
    "description": "问题描述",
    "fix": "修正建议"
}
```

**检测函数**: `_check_data_accuracy()`

#### 🟢 一般警告

```python
{
    "rule": "警告名称",
    "description": "建议描述",
    "fix": "补充建议"
}
```

**检测函数**: `_check_risk_disclosure()`

---

## 📝 报告生成 API

### 检查报告格式

检查器返回的Markdown格式报告：

```markdown
╔══════════════════════════════════════════════════════════════════╗
║ ✅ 志愿方案规范检查报告 ║
╠══════════════════════════════════════════════════════════════════╣
║ 检测省份：湖南 ║
║ 志愿模式：院校专业组 ║
║ ...
╚══════════════════════════════════════════════════════════════════╝

🔴 【致命错误】
└──────────────────────────────────────────────────────────────────────

1. 错误名称
   ❌ 问题：...
   ✅ 修正：...

🟡 【严重错误】
└──────────────────────────────────────────────────────────────────────

1. 错误名称
   ⚠️ 问题：...
   🔧 修正：...

🟢 【一般警告】
└──────────────────────────────────────────────────────────────────────

1. 警告名称
   💡 建议：...
   📌 做法：...
```

---

## 🧪 测试 API

### `test_hunan_bad_plan()`

测试湖南错误版方案检测能力。

**预期**: 检测出1个致命错误（"45个学校"）

### `test_hunan_good_plan()`

测试湖南修正版方案合规性。

**预期**: 通过基础检查

### `test_zhejiang_wrong_mode()`

测试浙江模式错误检测。

**预期**: 检测出E005模式错误

---

## 🔧 扩展开发

### 添加新省份

```python
# 在 PROVINCE_RULES 中添加
PROVINCE_RULES["新省份"] = {
    "mode": "院校专业组",  # 或 "专业+学校" / "传统"
    "batch": "本科批",     # 或 "本科一批" / "普通批"
    "max_volunteers": 45,
    "max_majors_per_group": 6,
    "has_adjustment": True,
    "adjustment_scope": "组内专业",
    "retrieval_rule": "分数优先、遵循志愿、一次投档",
    "collection_count": 2,
    "subject_mode": "3+1+2",  # 或 "3+3" / "传统"
    "official_url": "http://...",  # 官方网址
    "exam_subject_total": 750,
}
```

### 添加新错误检测

```python
# 在 GaokaoSpecCheckerV2 类中添加方法

def _check_new_error(self, text):
    """检查新错误类型"""
    error_pattern = r'错误正则'
    if re.search(error_pattern, text):
        self.errors["fatal"].append({
            "rule": "新错误名称",
            "description": "问题描述",
            "fix": "修正建议"
        })
```

---

## 📦 导入路径

### 从项目根目录

```python
import sys
sys.path.insert(0, '/home/long/project/gaokao-volunteer-system/skills/gaokao-spec-checker/scripts')

from spec_checker_v2 import GaokaoSpecCheckerV2, PROVINCE_RULES, detect_province
```

### 从Skill目录

```python
# 相对路径（在Skill内使用）
from scripts.spec_checker_v2 import GaokaoSpecCheckerV2
```

---

## 🎨 输出格式

### 返回类型

所有API返回标准的Python数据类型：

- `str`: Markdown格式的检查报告
- `dict`: 省份规则配置
- `list`: 错误列表
- `bool`: 检测结果

---

## 📞 更多信息

- 完整实现: [skills/gaokao-spec-checker/scripts/spec_checker_v2.py](skills/gaokao-spec-checker/scripts/spec_checker_v2.py)
- 规则文档: [rules/provinces.md](rules/provinces.md)
- 错误模式: [rules/errors/ERRORS.md](rules/errors/ERRORS.md)

---

**版本**: v2.0  
**最后更新**: 2026-06-11
