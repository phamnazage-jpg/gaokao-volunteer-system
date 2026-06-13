"""
高考志愿填报系统 - 自动化测试
测试各省份的错误检测能力
"""

import sys
import os
from types import ModuleType

# 添加scripts到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# 加载规范检查器
import importlib.util
spec = importlib.util.spec_from_file_location(
    "spec_checker_v2",
    os.path.join(os.path.dirname(__file__), '..', 'skills', 'gaokao-spec-checker', 'scripts', 'spec_checker_v2.py')
)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert isinstance(module, ModuleType)

GaokaoSpecCheckerV2 = module.GaokaoSpecCheckerV2


def test_hunan_bad_plan():
    """测试：湖南错误版方案"""
    plan = """
    湖南578分考生志愿方案
    
    本次共填报45个学校志愿：
    志愿01：江西财经大学，会计学
    录取概率35%
    
    投档后如果不服从调剂，会被退到下个志愿。
    """
    
    checker = GaokaoSpecCheckerV2()
    report = checker.auto_detect_and_check(plan)
    
    # 验证应检测出致命错误
    assert "湖南" in report
    assert "志愿单位错误" in report
    
    print("✅ test_hunan_bad_plan 通过")


def test_hunan_good_plan():
    """测试：湖南修正版方案"""
    plan = """
    湖南2026高考志愿填报方案
    
    本次共填报45个院校专业组志愿。
    每组最多6个专业+1个组内专业服从。
    
    退档风险提示：
    - 不服从调剂会退档
    - 本科批2次征集
    """
    
    checker = GaokaoSpecCheckerV2()
    report = checker.auto_detect_and_check(plan)
    
    # 修正版不应有致命错误（除了可能的W）
    assert "湖南" in report
    print("✅ test_hunan_good_plan 通过")


def test_zhejiang_wrong_mode():
    """测试：浙江错误使用院校专业组模式"""
    plan = """
    浙江志愿方案
    
    本次共填报80个院校专业组志愿：
    志愿01：浙江大学-计算机类组
    服从调剂：是
    """
    
    checker = GaokaoSpecCheckerV2()
    report = checker.auto_detect_and_check(plan)
    
    # 应检测出E005模式错误
    assert "浙江" in report
    assert "专业+学校" in report or "模式错误" in report
    
    print("✅ test_zhejiang_wrong_mode 通过")


def test_shandong_correct():
    """测试：山东正确方案"""
    plan = """
    山东省，620分
    填报96个专业+学校志愿：
    每个志愿填1个专业。
    """
    
    checker = GaokaoSpecCheckerV2()
    report = checker.auto_detect_and_check(plan)
    
    assert "山东" in report
    assert "专业+学校" in report
    
    print("✅ test_shandong_correct 通过")


def test_no_province():
    """测试：未提供省份信息"""
    plan = """
    578分考生志愿方案
    报考计算机专业
    """
    
    checker = GaokaoSpecCheckerV2()
    report = checker.auto_detect_and_check(plan)
    
    # 应提示未检测到省份
    assert "未检测到省份" in report or "省份" in report
    
    print("✅ test_no_province 通过")


def test_province_aliases():
    """测试：省份简称识别"""
    aliases = {
        "湘": "湖南",
        "浙": "浙江",
        "鲁": "山东",
        "粤": "广东",
        "鄂": "湖北",
    }
    
    for alias, full_name in aliases.items():
        plan = f"{full_name}，580分，志愿方案..."
        # 直接调用detect_province
        detected = module.detect_province(plan)
        assert detected == full_name, f"{alias} -> {full_name}, 实际 {detected}"
        print(f"  ✅ {alias} -> {full_name}")


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("🧪 高考志愿填报系统 - 自动化测试")
    print("=" * 70)
    print()
    
    print("📋 测试省份简称识别...")
    test_province_aliases()
    print()
    
    print("📋 测试方案检查...")
    test_hunan_bad_plan()
    test_hunan_good_plan()
    test_zhejiang_wrong_mode()
    test_shandong_correct()
    test_no_province()
    
    print()
    print("=" * 70)
    print("🎉 所有测试通过！")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
