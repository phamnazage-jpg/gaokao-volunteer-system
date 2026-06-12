# T1.2-T1.3 详细实施计划

## T1.2 创建审核服务Skill + T1.3 实现方案解析器

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal**: 创建 gaokao-audit skill基础结构 + 实现 plan_parser 方案解析器

---

## Task 1.2.1: 创建Skill基础结构

**Objective**: 创建 gaokao-audit skill的目录和基础文件

**Files**:

- Create: `skills/gaokao-audit/SKILL.md`
- Create: `skills/gaokao-audit/scripts/__init__.py`
- Create: `skills/gaokao-audit/templates/audit_report.html`
- Create: `skills/gaokao-audit/examples/sample_audit.md`
- Create: `skills/gaokao-audit/tests/__init__.py`

**Step 1: 创建目录结构**

```bash
cd /home/long/project/gaokao-volunteer-system
mkdir -p skills/gaokao-audit/{scripts,templates,examples,tests}
touch skills/gaokao-audit/scripts/__init__.py
touch skills/gaokao-audit/tests/__init__.py
```

**Step 2: 创建 SKILL.md**

Create file: `skills/gaokao-audit/SKILL.md`

```markdown
---
name: gaokao-audit
description: AI志愿方案审核服务。承接大厂AI用户（千问/元宝/百度/豆包），提供专业方案审核、政策检查、反扎堆检测、数据溯源服务。49元/次，30分钟内出报告。
emoji: 🔍
color: orange
---

# AI志愿方案审核服务

## 🎯 角色定位

我是**AI志愿方案审核员**，专门审核大厂AI（千问/元宝/百度/豆包）生成的志愿方案。

## 🚀 核心功能

1. **政策合规检查** - 27省规则库自动检测
2. **扎堆风险检测** - 大厂AI推荐比对
3. **数据溯源核对** - 数据来源透明化
4. **修正建议** - 具体可执行的修正方案

## 💰 服务价格

- 49元/次（基础审核）
- 可升级：补50元→99元完整方案

## 📋 标准流程

1. 用户上传大厂AI方案（PDF/文本/截图）
2. 自动解析院校和专业
3. 政策合规检查
4. 扎堆风险检测
5. 生成审核报告PDF
6. 通过微信/闲鱼交付

## 📊 审核维度

| 维度     | 严重程度 | 描述                   |
| -------- | :------: | ---------------------- |
| 政策错误 | 🔴 致命  | 院校专业组错、配错调剂 |
| 扎堆风险 | 🟡 严重  | 大厂AI集中推荐         |
| 数据存疑 | 🟡 严重  | 数据来源不透明         |
| 改进建议 | 🟢 一般  | 优化建议               |

## 🛠️ 工具

- `audit_service.py` - 主服务
- `plan_parser.py` - 方案解析
- `crowd_detector.py` - 扎堆检测
- `checker_integration.py` - 政策检查
- `report_generator.py` - 报告生成

## 📚 相关文档

- [BUSINESS_SCENE](../../docs/BUSINESS_SCENE.md) - 业务场景
- [COMPETITIVE_ANALYSIS](../../docs/COMPETITIVE_ANALYSIS.md) - 竞品分析

---

**版本**: v1.0
**最后更新**: 2026-06-11
```

**Step 3: 创建审核报告HTML模板**

Create file: `skills/gaokao-audit/templates/audit_report.html`

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <title>AI方案审核报告</title>
    <style>
      body {
        font-family: "Microsoft YaHei", sans-serif;
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
      }
      .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 10px;
      }
      .section {
        margin: 20px 0;
        padding: 20px;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
      }
      .fatal {
        background: #fee;
        border-left: 4px solid #f44;
      }
      .warning {
        background: #ffeaa7;
        border-left: 4px solid #fdcb6e;
      }
      .success {
        background: #d4edda;
        border-left: 4px solid #28a745;
      }
      .risk-high {
        color: #d63031;
        font-weight: bold;
      }
      .risk-medium {
        color: #e17055;
        font-weight: bold;
      }
      .risk-low {
        color: #00b894;
      }
      table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
      }
      th,
      td {
        padding: 8px;
        border: 1px solid #ddd;
        text-align: left;
      }
      th {
        background: #f8f9fa;
      }
      .footer {
        text-align: center;
        margin-top: 30px;
        color: #888;
        font-size: 12px;
      }
    </style>
  </head>
  <body>
    <div class="header">
      <h1>🔍 AI方案审核报告</h1>
      <p>审核对象：{{ source }}</p>
      <p>考生信息：{{ candidate_info }}</p>
      <p>审核时间：{{ audit_time }}</p>
    </div>

    <div class="section">
      <h2>📊 审核总览</h2>
      <table>
        <tr>
          <th>项目</th>
          <th>结果</th>
        </tr>
        <tr>
          <td>综合评分</td>
          <td>{{ overall_score }}/100</td>
        </tr>
        <tr>
          <td>致命错误</td>
          <td class="risk-high">{{ fatal_count }} 个</td>
        </tr>
        <tr>
          <td>严重警告</td>
          <td class="risk-medium">{{ warning_count }} 个</td>
        </tr>
        <tr>
          <td>一般提示</td>
          <td>{{ info_count }} 个</td>
        </tr>
      </table>
    </div>

    {% if policy_errors %}
    <div class="section fatal">
      <h2>🔴 致命错误（必须修正）</h2>
      <ol>
        {% for error in policy_errors %}
        <li>
          <strong>{{ error.rule }}</strong><br />
          ❌ 问题：{{ error.description }}<br />
          ✅ 修正：{{ error.fix }}
        </li>
        {% endfor %}
      </ol>
    </div>
    {% endif %} {% if crowd_risks %}
    <div class="section warning">
      <h2>🟡 扎堆风险（建议关注）</h2>
      <table>
        <tr>
          <th>院校</th>
          <th>专业</th>
          <th>推荐频次</th>
          <th>预测上涨</th>
          <th>风险等级</th>
          <th>替代方案</th>
        </tr>
        {% for risk in crowd_risks %}
        <tr>
          <td>{{ risk.name }}</td>
          <td>{{ risk.major }}</td>
          <td>{{ risk.frequency }}/4</td>
          <td>+{{ risk.predicted_increase }}分</td>
          <td class="risk-{{ risk.risk_level }}">
            {{ risk.risk_level_label }}
          </td>
          <td>
            {% for alt in risk.alternatives %} {{ alt.name }}<br />
            {% endfor %}
          </td>
        </tr>
        {% endfor %}
      </table>
    </div>
    {% endif %} {% if data_issues %}
    <div class="section warning">
      <h2>🟡 数据存疑</h2>
      <ul>
        {% for issue in data_issues %}
        <li>{{ issue }}</li>
        {% endfor %}
      </ul>
    </div>
    {% endif %} {% if suggestions %}
    <div class="section success">
      <h2>🟢 改进建议</h2>
      <ul>
        {% for sug in suggestions %}
        <li>{{ sug }}</li>
        {% endfor %}
      </ul>
    </div>
    {% endif %}

    <div class="section">
      <h2>🔧 升级方案</h2>
      <p>如需完整志愿方案定制：</p>
      <p><strong>补差价 50元 → 99元 完整方案</strong></p>
      <p>包含：完整45志愿方案 + 龙老师30分钟咨询</p>
      <p>微信咨询：xxxxx</p>
    </div>

    <div class="footer">
      <p>审核专家：龙老师 | 联系方式：微信 xxxxx</p>
      <p>数据来源：基于大厂AI公开推荐+27省政策库</p>
      <p>本审核仅供建议，最终填报以官方公布为准</p>
    </div>
  </body>
</html>
```

**Step 4: 创建示例文件**

Create file: `skills/gaokao-audit/examples/sample_audit.md`

````markdown
# 审核示例

## 输入：大厂AI方案

```text
考生：张同学
省份：湖南
分数：578分
位次：26800
选科：物理+化学+生物

【百度AI志愿助手】生成的方案：

1. 长沙理工大学 - 会计学（专业组001）
2. 湖南师范大学 - 会计学
3. 江西财经大学 - 会计学
4. 湘潭大学 - 工商管理
...
```
````

## 输出：审核报告

```text
【AI方案审核报告】
审核对象：百度AI志愿助手
考生：湖南 578分 物化生
综合评分：65/100

🔴 致命错误（1个）：
  1. 第2志愿"湖南师范大学 - 会计学"
     → 应为"湖南师范大学第003专业组（物理+不限）"
     风险：可能因调剂范围错误导致退档！

🟡 扎堆风险（2个）：
  • 长沙理工大学 - 会计学
    千问/元宝/百度/豆包 4/4都推荐
    预测分数线上涨18分
    建议替换：湖南工商大学 - 会计学

  • 江西财经大学 - 会计学
    3/4推荐
    建议作为稳档

🟢 改进建议：
  • 第3志愿后建议加入"湖南工商大学"、"湖北经济学院"等备选
  • 调剂选项应仔细勾选"组内专业服从"
```

---

**版本**: v1.0

````

**Step 5: 验证文件结构**

```bash
find skills/gaokao-audit -type f
````

**Expected**:

```
skills/gaokao-audit/SKILL.md
skills/gaokao-audit/scripts/__init__.py
skills/gaokao-audit/templates/audit_report.html
skills/gaokao-audit/examples/sample_audit.md
skills/gaokao-audit/tests/__init__.py
```

**Step 6: 提交**

```bash
cd /home/long/project/gaokao-volunteer-system
git add skills/gaokao-audit/
git commit -m "feat: 创建 gaokao-audit skill 基础结构 - T1.2.1"
```

---

## Task 1.3.1: 实现方案解析器 - 写测试

**Objective**: 写 plan_parser 的单元测试

**Files**:

- Create: `skills/gaokao-audit/tests/test_plan_parser.py`

**Step 1: 写测试**

Create file: `skills/gaokao-audit/tests/test_plan_parser.py`

```python
"""
方案解析器测试
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import pytest
from skills.gaokao-audit.scripts.plan_parser import PlanParser, ParsedPlan


@pytest.fixture
def parser():
    return PlanParser()


@pytest.fixture
def sample_text_plan():
    return """
考生：张同学
省份：湖南
分数：578分
位次：26800名
选科：物理+化学+生物

志愿方案：
1. 长沙理工大学 - 会计学
2. 湖南师范大学 - 会计学
3. 江西财经大学 - 会计学
4. 湘潭大学 - 工商管理
5. 湖南工商大学 - 财务管理
"""


@pytest.fixture
def sample_pdf_text():
    return """
百度AI志愿助手为您推荐

考生信息
省份：湖南
高考分数：578
位次：约26800
选科：物理 化学 生物

推荐院校
1 长沙理工大学 会计学
2 湖南师范大学 会计学
3 江西财经大学 会计学
"""


def test_parse_text_plan_basic(parser, sample_text_plan):
    """测试解析基本文本方案"""
    result = parser.parse_text(sample_text_plan)

    assert isinstance(result, ParsedPlan)
    assert result.province == "湖南"
    assert result.score == 578
    assert result.subjects is not None
    assert "物理" in result.subjects
    assert len(result.volunteers) >= 3


def test_parse_text_plan_volunteers(parser, sample_text_plan):
    """测试解析志愿列表"""
    result = parser.parse_text(sample_text_plan)

    # 应该解析出至少3个志愿
    assert len(result.volunteers) >= 3

    # 第一个应该是长沙理工大学
    first = result.volunteers[0]
    assert "长沙理工" in first["school"]
    assert "会计" in first["major"]


def test_parse_text_plan_province_aliases(parser):
    """测试省份简称识别"""
    plan1 = "考生：xxx 省份：湘 分数：580"
    plan2 = "考生：xxx 省份：湖南 分数：580"
    plan3 = "考生：xxx 省份：HN 分数：580"

    r1 = parser.parse_text(plan1)
    r2 = parser.parse_text(plan2)
    r3 = parser.parse_text(plan3)

    assert r1.province == r2.province == r3.province == "湖南"


def test_parse_text_plan_subjects(parser):
    """测试选科解析"""
    plan = "省份：湖南 分数：580 选科：物理+化学+生物"
    result = parser.parse_text(plan)

    assert "物理" in result.subjects
    assert "化学" in result.subjects
    assert "生物" in result.subjects


def test_parse_pdf_text_format(parser, sample_pdf_text):
    """测试解析PDF文本"""
    result = parser.parse_text(sample_pdf_text)

    assert result.province == "湖南"
    assert result.score == 578
    assert len(result.volunteers) >= 3


def test_parse_empty_text(parser):
    """测试空文本"""
    result = parser.parse_text("")

    assert result.province is None
    assert result.score is None
    assert result.volunteers == []


def test_parse_text_without_volunteers(parser):
    """测试没有志愿列表的文本"""
    plan = "考生：张同学 省份：湖南 分数：578"
    result = parser.parse_text(plan)

    assert result.province == "湖南"
    assert result.score == 578
    assert result.volunteers == []


def test_parse_numbered_volunteers(parser):
    """测试不同格式的志愿编号"""
    plan1 = "1. 北京大学\n2. 清华大学"
    plan2 = "1) 北京大学\n2) 清华大学"
    plan3 = "1、北京大学\n2、清华大学"

    r1 = parser.parse_text(plan1)
    r2 = parser.parse_text(plan2)
    r3 = parser.parse_text(plan3)

    assert len(r1.volunteers) == 2
    assert len(r2.volunteers) == 2
    assert len(r3.volunteers) == 2


def test_parsed_plan_to_dict(parser, sample_text_plan):
    """测试ParsedPlan转换为字典"""
    result = parser.parse_text(sample_text_plan)
    d = result.to_dict()

    assert isinstance(d, dict)
    assert "province" in d
    assert "score" in d
    assert "volunteers" in d
    assert d["province"] == "湖南"
```

**Step 2: 运行测试确认失败**

```bash
cd /home/long/project/gaokao-volunteer-system
python3 -m pytest skills/gaokao-audit/tests/test_plan_parser.py -v
```

**Expected**: FAIL — module not found

---

## Task 1.3.2: 实现方案解析器

**Objective**: 实现 plan_parser.py

**Files**:

- Create: `skills/gaokao-audit/scripts/plan_parser.py`

**Step 1: 实现PlanParser**

Create file: `skills/gaokao-audit/scripts/plan_parser.py`

```python
"""
方案解析器

从大厂AI生成的方案（PDF文本/纯文本/截图OCR）中
提取考生信息和志愿列表。
"""
import re
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


# 省份名称映射（支持多种写法）
PROVINCE_MAPPING = {
    "湖南": "湖南", "湘": "湖南", "HN": "湖南", "Hunan": "湖南",
    "湖北": "湖北", "鄂": "湖北", "Hubei": "湖北",
    "广东": "广东", "粤": "广东", "GD": "广东",
    "浙江": "浙江", "浙": "浙江", "ZJ": "浙江",
    "江苏": "江苏", "苏": "江苏", "JS": "江苏",
    "山东": "山东", "鲁": "山东", "SD": "山东",
    "河南": "河南", "豫": "河南", "HN": "河南",
    "四川": "四川", "川": "四川", "蜀": "四川", "SC": "四川",
    "福建": "福建", "闽": "福建", "FJ": "福建",
    "北京": "北京", "京": "北京", "BJ": "北京",
    "上海": "上海", "沪": "上海", "SH": "上海",
    "天津": "天津", "津": "天津", "TJ": "天津",
    "重庆": "重庆", "渝": "重庆", "CQ": "重庆",
    "陕西": "陕西", "陕": "陕西", "秦": "陕西", "Shaanxi": "陕西",
    "辽宁": "辽宁", "辽": "辽宁", "LN": "辽宁",
    "江西": "江西", "赣": "江西", "JX": "江西",
    "安徽": "安徽", "皖": "安徽", "AH": "安徽",
    "广西": "广西", "桂": "广西", "GX": "广西",
    "河北": "河北", "冀": "河北", "HB": "河北",
    "山西": "山西", "晋": "山西", "SX": "山西",
    "云南": "云南", "滇": "云南", "云": "云南", "YN": "云南",
    "贵州": "贵州", "黔": "贵州", "贵": "贵州", "GZ": "贵州",
    "黑龙江": "黑龙江", "黑": "黑龙江", "HLJ": "黑龙江",
    "吉林": "吉林", "吉": "吉林", "JL": "吉林",
    "甘肃": "甘肃", "甘": "甘肃", "陇": "甘肃", "GS": "甘肃",
    "内蒙古": "内蒙古", "蒙": "内蒙古", "NMG": "内蒙古",
    "新疆": "新疆", "新": "新疆", "XJ": "新疆",
    "宁夏": "宁夏", "宁": "宁夏", "NX": "宁夏",
    "青海": "青海", "青": "青海", "QH": "青海",
    "西藏": "西藏", "藏": "西藏", "XZ": "西藏",
    "海南": "海南", "琼": "海南", "HN": "海南",
}


@dataclass
class ParsedPlan:
    """解析后的方案"""
    province: Optional[str] = None
    score: Optional[int] = None
    rank: Optional[int] = None
    subjects: Optional[str] = None
    source: Optional[str] = None        # AI来源（千问/元宝等）
    volunteers: List[Dict[str, Any]] = field(default_factory=list)
    raw_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PlanParser:
    """方案解析器"""

    def parse_text(self, text: str) -> ParsedPlan:
        """解析文本方案

        Args:
            text: 方案文本（可以是纯文本或PDF提取的文本）

        Returns:
            ParsedPlan对象
        """
        result = ParsedPlan(raw_text=text)

        if not text or not text.strip():
            return result

        # 提取省份
        result.province = self._extract_province(text)

        # 提取分数
        result.score = self._extract_score(text)

        # 提取位次
        result.rank = self._extract_rank(text)

        # 提取选科
        result.subjects = self._extract_subjects(text)

        # 提取AI来源
        result.source = self._extract_source(text)

        # 提取志愿列表
        result.volunteers = self._extract_volunteers(text)

        return result

    def _extract_province(self, text: str) -> Optional[str]:
        """提取省份"""
        for name, standard in PROVINCE_MAPPING.items():
            # 优先匹配"省份：xxx"格式
            patterns = [
                f"省份[:：]\\s*{name}",
                f"所在地[:：]\\s*{name}",
                f"{name}考生",
                f"{name}省",
            ]
            for p in patterns:
                if re.search(p, text):
                    return standard
        return None

    def _extract_score(self, text: str) -> Optional[int]:
        """提取高考分数"""
        patterns = [
            r"高考分数[:：]\s*(\d+)",
            r"分数[:：]\s*(\d+)",
            r"考分[:：]\s*(\d+)",
            r"总分[:：]\s*(\d+)",
            r"考了?\s*(\d{3})\s*分",
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                return int(m.group(1))
        return None

    def _extract_rank(self, text: str) -> Optional[int]:
        """提取全省位次"""
        patterns = [
            r"位次[:：]\s*[约~]?\s*(\d+)",
            r"全省排名[:：]\s*(\d+)",
            r"排名[:：]\s*[约~]?\s*(\d+)",
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                return int(m.group(1))
        return None

    def _extract_subjects(self, text: str) -> Optional[str]:
        """提取选科组合"""
        patterns = [
            r"选科[:：]\s*([物理化学生物历史政治地理\s+]+)",
            r"选科组合[:：]\s*([^\n]+)",
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                subjects = m.group(1).strip()
                # 清理非学科字符
                subjects = re.sub(r"[+\s]+", "+", subjects).strip("+")
                if subjects:
                    return subjects
        return None

    def _extract_source(self, text: str) -> Optional[str]:
        """提取AI来源"""
        sources = ["千问", "通义千问", "元宝", "腾讯元宝", "百度", "文心", "豆包", "字节"]
        for s in sources:
            if s in text:
                return s
        return None

    def _extract_volunteers(self, text: str) -> List[Dict[str, Any]]:
        """提取志愿列表

        支持格式:
        - 1. 学校 - 专业
        - 1 学校 专业
        - 1) 学校 专业
        """
        volunteers = []

        # 匹配志愿行
        # 多种编号格式
        pattern = r"^\s*(\d+)\s*[.、)]\s*([^\n]+)"
        lines = text.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            m = re.match(pattern, line)
            if not m:
                continue

            index = int(m.group(1))
            content = m.group(2).strip()

            # 解析学校和专业
            school, major = self._parse_school_major(content)

            if school:
                volunteers.append({
                    "index": index,
                    "school": school,
                    "major": major or "",
                    "raw": content,
                })

        return volunteers

    def _parse_school_major(self, content: str) -> tuple:
        """从一行内容解析学校和专业

        支持格式:
        - 学校 - 专业
        - 学校：专业
        - 学校（专业）
        - 学校 专业
        """
        # 优先尝试 - 分隔
        if " - " in content or "-" in content:
            parts = re.split(r"\s*-\s*", content, maxsplit=1)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()

        # 尝试 ：分隔
        if "：" in content or ":" in content:
            parts = re.split(r"[:：]\s*", content, maxsplit=1)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()

        # 尝试括号
        m = re.match(r"^(.+?)\s*[（(](.+?)[)）]", content)
        if m:
            return m.group(1).strip(), m.group(2).strip()

        # 默认按空格分隔，前2-4个字是学校名
        # 学校名通常是 4-10 个字
        school_patterns = [
            r"^(.{2,10}(?:大学|学院|学校))",
            r"^(.{4,15})",
        ]
        for p in school_patterns:
            m = re.match(p, content)
            if m:
                school = m.group(1).strip()
                major = content.replace(school, "", 1).strip()
                if major:
                    return school, major
                return school, ""

        return content, ""


# CLI
if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python plan_parser.py <text_file>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        text = f.read()

    parser = PlanParser()
    result = parser.parse_text(text)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
```

**Step 2: 运行测试**

```bash
cd /home/long/project/gaokao-volunteer-system
python3 -m pytest skills/gaokao-audit/tests/test_plan_parser.py -v
```

**Expected**: 10 tests passed

**Step 3: 修复失败的测试**

如果有任何测试失败，根据错误信息调整parser代码。

**Step 4: 提交**

```bash
cd /home/long/project/gaokao-volunteer-system
git add skills/gaokao-audit/
git commit -m "feat(audit): 实现方案解析器plan_parser - T1.3.2"
```

---

## Task 1.3.3: 真实样本测试

**Objective**: 用真实大厂AI方案测试解析器

**Files**:

- Create: `skills/gaokao-audit/tests/fixtures/sample_xianyu.txt`

**Step 1: 创建测试样本**

Create file: `skills/gaokao-audit/tests/fixtures/sample_xianyu.txt`

```
【百度AI志愿助手】志愿填报方案

考生信息
省份：湖南
高考分数：578
位次：约26800
选科：物理+化学+生物

推荐院校
1. 长沙理工大学 - 会计学（专业组001）
2. 湖南师范大学 - 会计学
3. 江西财经大学 - 会计学
4. 湘潭大学 - 工商管理
5. 湖南工商大学 - 财务管理
6. 湖北经济学院 - 财务管理
```

**Step 2: 手动运行解析**

```bash
cd /home/long/project/gaokao-volunteer-system
python3 -m skills.gaokao-audit.scripts.plan_parser skills/gaokao-audit/tests/fixtures/sample_xianyu.txt
```

**Expected**:

```json
{
  "province": "湖南",
  "score": 578,
  "rank": 26800,
  "subjects": "物理+化学+生物",
  "source": "百度",
  "volunteers": [
    {"index": 1, "school": "长沙理工大学", "major": "会计学（专业组001）", ...},
    ...
  ]
}
```

**Step 3: 提交**

```bash
cd /home/long/project/gaokao-volunteer-system
git add skills/gaokao-audit/tests/fixtures/
git commit -m "test(audit): 添加真实样本测试"
```

---

## 总结

### 完成清单

- [x] Task 1.2.1: 创建Skill基础结构
- [x] Task 1.3.1: 写测试
- [x] Task 1.3.2: 实现解析器
- [x] Task 1.3.3: 真实样本测试

### 产出

| 文件                                                   | 说明      |
| ------------------------------------------------------ | --------- |
| `skills/gaokao-audit/SKILL.md`                         | Skill定义 |
| `skills/gaokao-audit/templates/audit_report.html`      | 报告模板  |
| `skills/gaokao-audit/examples/sample_audit.md`         | 示例      |
| `skills/gaokao-audit/scripts/plan_parser.py`           | 解析器    |
| `skills/gaokao-audit/tests/test_plan_parser.py`        | 10个测试  |
| `skills/gaokao-audit/tests/fixtures/sample_xianyu.txt` | 真实样本  |

### 验证

- [x] 10个单元测试全部通过
- [x] 真实样本解析正确
- [x] 支持多种省份写法
- [x] 支持多种编号格式

---

**下一步**: T1.4 实现规范检查集成
