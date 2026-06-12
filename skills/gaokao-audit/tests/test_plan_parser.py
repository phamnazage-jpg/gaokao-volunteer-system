"""
方案解析器测试

覆盖：
- 文本方案基本解析（省份、分数、选科、志愿列表）
- 多种省份别名（湘/湖南/HN）
- 多种志愿编号格式（. / 、/ ））
- PDF 提取文本（行内空格分隔）
- 边界：空文本、无志愿列表
- ParsedPlan.to_dict 序列化
"""

import sys
import os
import importlib

# 让 `from skills.gaokao-audit.scripts.plan_parser import ...` 能找到包根
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import pytest  # noqa: E402

# Note: the directory name "gaokao-audit" contains a hyphen, which is not
# legal in a Python module identifier. The plan literally writes
# `from skills.gaokao-audit.scripts.plan_parser import ...`, which the
# interpreter rejects. We load the module via importlib so the test keeps
# the spirit of the plan while remaining valid Python.
_PLAN_PARSER = importlib.import_module("skills.gaokao-audit.scripts.plan_parser")  # noqa: E402
PlanParser = _PLAN_PARSER.PlanParser
ParsedPlan = _PLAN_PARSER.ParsedPlan


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


def test_parse_real_xianyu_fixture(parser):
    """真实样本：百度AI志愿助手输出（来自 T1.3.3 真实场景回归）

    验证解析器对真实大厂AI方案输出的健壮性：
    - "约"前缀的位次
    - 中文括号 "(专业组001)"
    - 多种分隔符
    """
    fixture_path = os.path.join(
        os.path.dirname(__file__), "fixtures", "sample_xianyu.txt"
    )
    if not os.path.exists(fixture_path):
        pytest.skip(f"fixture not found: {fixture_path}")

    with open(fixture_path, "r", encoding="utf-8") as f:
        text = f.read()

    result = parser.parse_text(text)

    assert result.province == "湖南"
    assert result.score == 578
    assert result.rank == 26800
    assert result.subjects == "物理+化学+生物"
    assert result.source is not None
    assert "百度" in result.source
    assert len(result.volunteers) == 6
    assert result.volunteers[0]["school"] == "长沙理工大学"
    assert "会计学" in result.volunteers[0]["major"]
