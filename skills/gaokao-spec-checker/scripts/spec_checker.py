"""
高考志愿填报规范检查脚本
专门检查志愿方案是否符合湖南省2026年最新政策
"""

import re
from datetime import datetime


class GaokaoSpecChecker:
    """
    高考志愿填报规范检查器
    """
    
    def __init__(self, province="湖南", year=2026):
        self.province = province
        self.year = year
        self.errors = {
            "fatal": [],      # 致命错误（必须修改）
            "serious": [],    # 严重错误（强烈建议修改）
            "warning": [],    # 一般警告（建议补充）
        }
        self.warnings = []
        self.suggestions = []
        
    def check_plan(self, plan_text):
        """
        检查志愿方案
        """
        self._check_policy_compliance(plan_text)
        self._check_data_accuracy(plan_text)
        self._check_subject_requirements(plan_text)
        self._check_risk_disclosure(plan_text)
        self._check_data_completeness(plan_text)
        
        return self._generate_report()
    
    def _check_policy_compliance(self, text):
        """政策合规性检查"""
        # 检查1：志愿单位
        if "45个学校" in text or "45所学校" in text or "45个院校" in text:
            self.errors["fatal"].append({
                "rule": "志愿单位错误",
                "description": "湖南2026年本科批是45个'院校专业组'，不是45所学校/45个院校",
                "fix": "改为'45个院校专业组'，每组最多6个专业+1个服从"
            })
        
        # 检查2：调剂范围
        if "服从调剂" in text and ("全校" in text or "学校所有专业" in text):
            self.errors["fatal"].append({
                "rule": "调剂范围错误",
                "description": "调剂范围是'组内专业'，不是全校",
                "fix": "明确'组内专业调剂'"
            })
        
        # 检查3：投档后规则
        if re.search(r"(退档后|被退).*?(下个志愿|下一个|其他志愿)", text):
            self.errors["fatal"].append({
                "rule": "投档后规则错误",
                "description": "本科批一次投档，被某校退档后不会进入下个志愿，直接进入征集志愿",
                "fix": "说明'一次投档'原则"
            })
        
        # 检查4：征集志愿次数
        if "征集" in text and "1次" in text and "本科" in text:
            self.errors["fatal"].append({
                "rule": "征集志愿次数错误",
                "description": "湖南2026年本科批有2次征集志愿，不是1次",
                "fix": "改为'本科批2次征集志愿'"
            })
    
    def _check_data_accuracy(self, text):
        """数据准确性检查"""
        # 检查1：主观概率
        prob_pattern = r'(\d{2,3})\s*%\s*[\u4e00-\u9fa5]*(?:录取|概率|机会|把握)'
        matches = re.findall(prob_pattern, text)
        if matches:
            self.errors["serious"].append({
                "rule": "主观概率估算",
                "description": f"方案中含主观概率{set(matches)}，未基于真实数据",
                "fix": "删除主观概率，改用2025年位次作为参考"
            })
        
        # 检查2：位次数据来源
        if "位次" in text and "2025" not in text and "2024" in text:
            self.errors["serious"].append({
                "rule": "位次数据年份",
                "description": "方案可能使用2024年及更早数据，应使用2025年数据",
                "fix": "核实并明确标注'2025年参考位次'"
            })
        
        # 检查3：2026年位次
        if "2026年位次" in text and "待官方" not in text and "以官方为准" not in text:
            self.errors["serious"].append({
                "rule": "2026年位次",
                "description": "2026年位次待官方公布（6月25日出分后），不应假设",
                "fix": "明确'2026年位次待官方公布'"
            })
    
    def _check_subject_requirements(self, text):
        """选科要求检查"""
        # 检查1：选科一刀切
        one_size_patterns = [
            r'会计.{0,20}物.{0,5}化.{0,5}生',
            r'财经.{0,20}物.{0,5}化.{0,5}生',
            r'所有.{0,30}要求.{0,10}物.{0,5}化.{0,5}生',
        ]
        for pattern in one_size_patterns:
            if re.search(pattern, text):
                self.errors["serious"].append({
                    "rule": "选科要求一刀切",
                    "description": "财经类专业选科要求因校而异，不能假设都要求'物+化+生'",
                    "fix": "逐校核实选科要求"
                })
                break
    
    def _check_risk_disclosure(self, text):
        """风险评估检查"""
        risk_keywords = ["退档", "风险", "调剂", "体检", "单科"]
        has_risk = any(kw in text for kw in risk_keywords)
        
        if not has_risk:
            self.errors["serious"].append({
                "rule": "风险提示缺失",
                "description": "方案未明确说明退档风险（体检/单科/不服从调剂）",
                "fix": "增加风险提示章节"
            })
        
        # 检查体检要求
        if "体检" not in text:
            self.warnings.append({
                "rule": "体检要求",
                "description": "未提体检要求（色盲、色弱等可能影响专业选择）",
                "fix": "提示用户查看招生章程"
            })
    
    def _check_data_completeness(self, text):
        """数据完整性检查"""
        # 检查1：缺少院校代码
        if "院校" in text and "代码" not in text:
            self.warnings.append({
                "rule": "院校代码",
                "description": "未提供院校代码（4位数字）",
                "fix": "补充每所院校的代码"
            })
        
        # 检查2：缺少专业代码
        if "专业" in text and "代码" not in text:
            self.warnings.append({
                "rule": "专业代码",
                "description": "未提供专业代码",
                "fix": "补充每个专业的代码"
            })
    
    def _generate_report(self):
        """生成检查报告"""
        report = f"""
╔══════════════════════════════════════════════════════════════════╗
║             ✅ 志愿方案规范检查报告                              ║
╠══════════════════════════════════════════════════════════════════╣
║  检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                             ║
║  检查省份：{self.province}                                              ║
║  政策年份：{self.year}                                              ║
╚══════════════════════════════════════════════════════════════════╝
"""
        
        # 致命错误
        if self.errors["fatal"]:
            report += "\n🔴 【致命错误】（必须立即修改）\n"
            report += "─" * 70 + "\n"
            for i, err in enumerate(self.errors["fatal"], 1):
                report += f"""
  {i}. {err['rule']}
     ❌ 问题：{err['description']}
     ✅ 修正：{err['fix']}
"""
        
        # 严重错误
        if self.errors["serious"]:
            report += "\n🟡 【严重错误】（强烈建议修改）\n"
            report += "─" * 70 + "\n"
            for i, err in enumerate(self.errors["serious"], 1):
                report += f"""
  {i}. {err['rule']}
     ⚠️  问题：{err['description']}
     🔧 修正：{err['fix']}
"""
        
        # 一般警告
        if self.warnings:
            report += "\n🟢 【一般警告】（建议补充）\n"
            report += "─" * 70 + "\n"
            for i, warn in enumerate(self.warnings, 1):
                report += f"""
  {i}. {warn['rule']}
     💡 建议：{warn['description']}
     📌 做法：{warn['fix']}
"""
        
        # 总结
        total = sum(len(v) for v in self.errors.values()) + len(self.warnings)
        report += f"""
═══════════════════════════════════════════════════════════════════
📊 【检查统计】
═══════════════════════════════════════════════════════════════════
  🔴 致命错误：{len(self.errors['fatal'])} 个
  🟡 严重错误：{len(self.errors['serious'])} 个
  🟢 一般警告：{len(self.warnings)} 个
  📊 问题总数：{total} 个
"""
        
        if total == 0:
            report += """
  🎉 恭喜！方案基本合规，可以作为参考。
"""
        elif len(self.errors["fatal"]) == 0 and len(self.errors["serious"]) == 0:
            report += """
  ✅ 方案基本合规，仅有少量建议补充项。
"""
        elif len(self.errors["fatal"]) > 0:
            report += """
  ❌ 方案存在致命错误，必须立即修改后才能使用。
"""
        else:
            report += """
  ⚠️ 方案存在严重问题，需要重大修改后才能使用。
"""
        
        # 行动建议
        report += """
═══════════════════════════════════════════════════════════════════
🎯 【行动建议】
═══════════════════════════════════════════════════════════════════
"""
        if self.errors["fatal"]:
            report += """
  1. 立即处理致命错误
  2. 修改后重新检查
  3. 出分前完成所有核实
  4. 填报前最终确认
"""
        else:
            report += """
  1. 补充严重错误项
  2. 完善一般警告项
  3. 出分后重新精确化
  4. 填报前最终确认
"""
        
        report += """
═══════════════════════════════════════════════════════════════════
📌 重要提醒
═══════════════════════════════════════════════════════════════════
  • 本检查仅基于文字内容，无法核实代码、链接等
  • 实际填报前必须登录官方系统查询
  • 2026年招生计划6月15-20日公布
  • 2026年实际位次6月25日出分后确定
  • 最终以湖南省教育考试院官方信息为准

  官网：http://jyt.hunan.gov.cn/jyt/sjyt/hnsjyksy/
═══════════════════════════════════════════════════════════════════
"""
        return report


# 使用示例
if __name__ == "__main__":
    # 测试：原始方案（错误版）
    bad_plan = """
    湖南578分考生志愿方案
    
    本次共填报45个学校志愿：
    志愿01：江西财经大学，会计学
    志愿02：长沙理工大学，财务管理
    志愿03：山东财经大学，会计学
    ...
    
    录取概率：
    志愿01 35%
    志愿02 45%
    志愿03 50%
    ...
    
    投档后如果不服从调剂，会被退到下个志愿。
    
    所有会计学专业都要求物理+化学+生物选科。
    """
    
    print("=" * 70)
    print("测试1：检查错误方案")
    print("=" * 70)
    
    checker = GaokaoSpecChecker()
    report = checker.check_plan(bad_plan)
    print(report)
    
    # 测试：修正版方案
    print("\n\n")
    print("=" * 70)
    print("测试2：检查修正版方案")
    print("=" * 70)
    
    good_plan = """
    湖南2026高考志愿填报方案（578分）
    
    本次共填报45个院校专业组志愿，每个专业组最多6个专业+1个组内专业服从。
    
    院校专业组示例：
    志愿01：江西财经大学-会计学类组（要求物理+化学）
    - 6个专业：会计学/审计学/财务管理/资产评估/工商管理/经济学
    - 2025年参考位次：~20000
    
    志愿02：江西财经大学-经济金融组（要求物理）
    - 6个专业：金融学/经济学/金融工程/投资学/保险学/国际经济
    - 2025年参考位次：~22000
    
    数据来源：2025年湖南物理类一分一段表
    2026年位次待官方公布（6月25日出分后）
    
    风险提示：
    - 退档风险：体检受限、单科不达标、不服从调剂
    - 本科批2次征集志愿
    - 一次投档，退档进入征集
    """
    
    checker2 = GaokaoSpecChecker()
    report2 = checker2.check_plan(good_plan)
    print(report2)
