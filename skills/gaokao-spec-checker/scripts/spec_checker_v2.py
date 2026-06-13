"""
高考志愿填报规范检查器 V2.0
支持多省份自动识别
"""

import re
import sys
from datetime import datetime


# 各省规则库
PROVINCE_RULES = {
    # 院校专业组模式
    "湖南": {
        "mode": "院校专业组",
        "batch": "本科批",
        "max_volunteers": 45,
        "max_majors_per_group": 6,
        "has_adjustment": True,
        "adjustment_scope": "组内专业",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 2,  # 征集志愿次数
        "subject_mode": "3+1+2",
        "official_url": "http://jyt.hunan.gov.cn/jyt/sjyt/hnsjyksy/",
        "exam_subject_total": 750,
    },
    "广东": {
        "mode": "院校专业组",
        "batch": "本科批",
        "max_volunteers": 45,
        "max_majors_per_group": 6,
        "has_adjustment": True,
        "adjustment_scope": "组内专业",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 2,
        "subject_mode": "3+1+2",
        "official_url": "http://eea.gd.gov.cn/",
        "exam_subject_total": 750,
    },
    "湖北": {
        "mode": "院校专业组",
        "batch": "本科批",
        "max_volunteers": 45,
        "max_majors_per_group": 6,
        "has_adjustment": True,
        "adjustment_scope": "组内专业",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 2,
        "subject_mode": "3+1+2",
        "official_url": "http://www.hbea.edu.cn/",
        "exam_subject_total": 750,
    },
    "江苏": {
        "mode": "院校专业组",
        "batch": "本科批",
        "max_volunteers": 40,
        "max_majors_per_group": 6,
        "has_adjustment": True,
        "adjustment_scope": "组内专业",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 1,
        "subject_mode": "3+1+2",
        "official_url": "http://www.jseea.cn/",
        "exam_subject_total": 750,
    },
    "福建": {
        "mode": "院校专业组",
        "batch": "本科批",
        "max_volunteers": 40,
        "max_majors_per_group": 6,
        "has_adjustment": True,
        "adjustment_scope": "组内专业",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 1,
        "subject_mode": "3+1+2",
        "official_url": "https://www.eeafj.cn/",
        "exam_subject_total": 750,
    },
    "安徽": {
        "mode": "院校专业组",
        "batch": "本科批",
        "max_volunteers": 45,
        "max_majors_per_group": 6,
        "has_adjustment": True,
        "adjustment_scope": "组内专业",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 2,
        "subject_mode": "3+1+2",
        "official_url": "https://www.ahzsks.cn/",
        "exam_subject_total": 750,
    },
    "江西": {
        "mode": "院校专业组",
        "batch": "本科批",
        "max_volunteers": 45,
        "max_majors_per_group": 6,
        "has_adjustment": True,
        "adjustment_scope": "组内专业",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 2,
        "subject_mode": "3+1+2",
        "official_url": "http://www.jxeea.cn/",
        "exam_subject_total": 750,
    },
    "甘肃": {
        "mode": "院校专业组",
        "batch": "本科批",
        "max_volunteers": 45,
        "max_majors_per_group": 6,
        "has_adjustment": True,
        "adjustment_scope": "组内专业",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 2,
        "subject_mode": "3+1+2",
        "official_url": "https://www.ganseea.cn/",
        "exam_subject_total": 750,
    },
    "黑龙江": {
        "mode": "院校专业组",
        "batch": "本科批",
        "max_volunteers": 45,
        "max_majors_per_group": 6,
        "has_adjustment": True,
        "adjustment_scope": "组内专业",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 2,
        "subject_mode": "3+1+2",
        "official_url": "https://www.lzk.hl.cn/",
        "exam_subject_total": 750,
    },
    "广西": {
        "mode": "院校专业组",
        "batch": "本科批",
        "max_volunteers": 40,
        "max_majors_per_group": 6,
        "has_adjustment": True,
        "adjustment_scope": "组内专业",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 2,
        "subject_mode": "3+1+2",
        "official_url": "https://www.gxeea.cn/",
        "exam_subject_total": 750,
    },
    "北京": {
        "mode": "院校专业组",
        "batch": "本科批",
        "max_volunteers": 30,
        "max_majors_per_group": 6,
        "has_adjustment": True,
        "adjustment_scope": "组内专业",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 1,
        "subject_mode": "3+3",
        "official_url": "https://www.bjeea.cn/",
        "exam_subject_total": 750,
    },
    "上海": {
        "mode": "院校专业组",
        "batch": "本科批",
        "max_volunteers": 24,
        "max_majors_per_group": 4,
        "has_adjustment": True,
        "adjustment_scope": "组内专业",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 1,
        "subject_mode": "3+3",
        "official_url": "https://www.shmeea.edu.cn/",
        "exam_subject_total": 660,
    },
    "天津": {
        "mode": "院校专业组",
        "batch": "本科批",
        "max_volunteers": 50,
        "max_majors_per_group": 6,
        "has_adjustment": True,
        "adjustment_scope": "组内专业",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 1,
        "subject_mode": "3+3",
        "official_url": "http://www.zhaoban.tjzhaokao.com/",
        "exam_subject_total": 750,
    },
    "海南": {
        "mode": "院校专业组",
        "batch": "本科批",
        "max_volunteers": 24,
        "max_majors_per_group": 6,
        "has_adjustment": True,
        "adjustment_scope": "组内专业",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 1,
        "subject_mode": "3+3",
        "official_url": "https://ea.hainan.gov.cn/",
        "exam_subject_total": 900,
    },
    # 专业+学校模式
    "浙江": {
        "mode": "专业+学校",
        "batch": "普通批",
        "max_volunteers": 80,
        "max_majors_per_group": 1,  # 每个志愿只填1个专业
        "has_adjustment": False,  # 无调剂
        "adjustment_scope": "无",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 1,
        "subject_mode": "3+3",
        "official_url": "https://www.zjzs.net/",
        "exam_subject_total": 750,
    },
    "山东": {
        "mode": "专业+学校",
        "batch": "普通批",
        "max_volunteers": 96,
        "max_majors_per_group": 1,
        "has_adjustment": False,
        "adjustment_scope": "无",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 1,
        "subject_mode": "3+3",
        "official_url": "https://www.sdzk.cn/",
        "exam_subject_total": 750,
    },
    "河北": {
        "mode": "专业+学校",
        "batch": "普通批",
        "max_volunteers": 96,
        "max_majors_per_group": 1,
        "has_adjustment": False,
        "adjustment_scope": "无",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 1,
        "subject_mode": "3+1+2",
        "official_url": "https://www.hebeea.edu.cn/",
        "exam_subject_total": 750,
    },
    "重庆": {
        "mode": "专业+学校",
        "batch": "普通批",
        "max_volunteers": 96,
        "max_majors_per_group": 1,
        "has_adjustment": False,
        "adjustment_scope": "无",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 1,
        "subject_mode": "3+1+2",
        "official_url": "https://www.cqksy.cn/",
        "exam_subject_total": 750,
    },
    "辽宁": {
        "mode": "专业+学校",
        "batch": "普通批",
        "max_volunteers": 112,
        "max_majors_per_group": 1,
        "has_adjustment": False,
        "adjustment_scope": "无",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 1,
        "subject_mode": "3+1+2",
        "official_url": "https://www.lnzsks.com/",
        "exam_subject_total": 750,
    },
    "贵州": {
        "mode": "专业+学校",
        "batch": "普通批",
        "max_volunteers": 96,
        "max_majors_per_group": 1,
        "has_adjustment": False,
        "adjustment_scope": "无",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 1,
        "subject_mode": "3+1+2",
        "official_url": "https://zsksy.guizhou.gov.cn/",
        "exam_subject_total": 750,
    },
    "青海": {
        "mode": "专业+学校",
        "batch": "普通批",
        "max_volunteers": 96,
        "max_majors_per_group": 1,
        "has_adjustment": False,
        "adjustment_scope": "无",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 1,
        "subject_mode": "3+1+2",
        "official_url": "http://www.qhzk.com/",
        "exam_subject_total": 750,
    },
    "吉林": {
        "mode": "专业+学校",
        "batch": "普通批",
        "max_volunteers": 50,
        "max_majors_per_group": 1,
        "has_adjustment": False,
        "adjustment_scope": "无",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 1,
        "subject_mode": "3+1+2",
        "official_url": "https://www.jleea.com.cn/",
        "exam_subject_total": 750,
    },
    # 传统模式
    "河南": {
        "mode": "传统",
        "batch": "本科一批",
        "max_volunteers": 6,
        "max_majors_per_group": 5,
        "has_adjustment": True,
        "adjustment_scope": "全部专业",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 1,
        "subject_mode": "传统",
        "official_url": "https://www.haeea.cn/",
        "exam_subject_total": 750,
    },
    "四川": {
        "mode": "传统",
        "batch": "本科一批",
        "max_volunteers": 9,
        "max_majors_per_group": 6,
        "has_adjustment": True,
        "adjustment_scope": "全部专业",
        "retrieval_rule": "分数优先、遵循志愿、一次投档",
        "collection_count": 1,
        "subject_mode": "传统",
        "official_url": "https://www.sceea.cn/",
        "exam_subject_total": 750,
    },
    "新疆": {
        "mode": "传统",
        "batch": "本科一批",
        "max_volunteers": 9,
        "max_majors_per_group": 6,
        "has_adjustment": True,
        "adjustment_scope": "全部专业",
        "retrieval_rule": "志愿优先、遵循志愿",
        "collection_count": 1,
        "subject_mode": "传统",
        "official_url": "http://www.xjzk.gov.cn/",
        "exam_subject_total": 750,
    },
    "云南": {
        "mode": "传统",
        "batch": "本科一批",
        "max_volunteers": 5,
        "max_majors_per_group": 5,
        "has_adjustment": True,
        "adjustment_scope": "全部专业",
        "retrieval_rule": "分数优先、遵循志愿",
        "collection_count": 1,
        "subject_mode": "传统",
        "official_url": "https://www.ynzs.cn/",
        "exam_subject_total": 750,
    },
    "西藏": {
        "mode": "传统",
        "batch": "本科二批",
        "max_volunteers": 10,
        "max_majors_per_group": 4,
        "has_adjustment": True,
        "adjustment_scope": "全部专业",
        "retrieval_rule": "分数优先、遵循志愿",
        "collection_count": 1,
        "subject_mode": "传统",
        "official_url": "http://zsks.edu.xizang.gov.cn/",
        "exam_subject_total": 750,
    },
}


# 省份别名
PROVINCE_ALIASES = {
    "湘": "湖南",
    "粤": "广东",
    "鄂": "湖北",
    "苏": "江苏",
    "闽": "福建",
    "皖": "安徽",
    "赣": "江西",
    "甘": "甘肃",
    "陇": "甘肃",
    "黑": "黑龙江",
    "桂": "广西",
    "京": "北京",
    "沪": "上海",
    "津": "天津",
    "琼": "海南",
    "浙": "浙江",
    "鲁": "山东",
    "冀": "河北",
    "渝": "重庆",
    "辽": "辽宁",
    "黔": "贵州",
    "青": "青海",
    "吉": "吉林",
    "豫": "河南",
    "川": "四川",
    "蜀": "四川",
    "新": "新疆",
    "滇": "云南",
    "云": "云南",
    "藏": "西藏",
}


def detect_province(text):
    """
    从文本中自动检测省份
    """
    # 1. 优先匹配全称
    for prov in PROVINCE_RULES.keys():
        if prov in text:
            return prov

    # 2. 匹配简称
    for alias, prov in PROVINCE_ALIASES.items():
        # 排除"其他"等含简称的词
        pattern = f"({alias}[省市区]?)|(省{alias})"
        if re.search(pattern, text):
            return prov

    # 3. 匹配省份全称
    prov_full_names = {
        "北京": "北京",
        "天津": "天津",
        "河北": "河北",
        "山西": "山西",
        "内蒙古": "内蒙古",
        "辽宁": "辽宁",
        "吉林": "吉林",
        "黑龙江": "黑龙江",
        "上海": "上海",
        "江苏": "江苏",
        "浙江": "浙江",
        "安徽": "安徽",
        "福建": "福建",
        "江西": "江西",
        "山东": "山东",
        "河南": "河南",
        "湖北": "湖北",
        "湖南": "湖南",
        "广东": "广东",
        "广西": "广西",
        "海南": "海南",
        "重庆": "重庆",
        "四川": "四川",
        "贵州": "贵州",
        "云南": "云南",
        "西藏": "西藏",
        "陕西": "陕西",
        "甘肃": "甘肃",
        "青海": "青海",
        "宁夏": "宁夏",
        "新疆": "新疆",
    }

    for full_name in prov_full_names.keys():
        if full_name in text:
            return full_name

    return None


class GaokaoSpecCheckerV2:
    """
    高考志愿填报规范检查器 V2.0
    支持多省份自动识别
    """

    def __init__(self, province=None):
        self.province = province
        self.province_rule = None
        self.errors = {
            "fatal": [],
            "serious": [],
            "warning": [],
        }

    def auto_detect_and_check(self, text):
        """
        自动检测省份并检查
        """
        # 自动检测省份
        if not self.province:
            self.province = detect_province(text)

        if not self.province:
            return self._report_no_province()

        if self.province not in PROVINCE_RULES:
            return self._report_unsupported_province()

        self.province_rule = PROVINCE_RULES[self.province]

        # 执行检查
        self._check_volunteer_unit(text)
        self._check_volunteer_count(text)
        self._check_majors_per_group(text)
        self._check_adjustment_rule(text)
        self._check_data_accuracy(text)
        self._check_subject_requirements(text)
        self._check_risk_disclosure(text)

        return self._generate_report()

    def _check_volunteer_unit(self, text):
        """检查志愿单位"""
        max_v = self.province_rule["max_volunteers"]
        mode = self.province_rule["mode"]

        if mode == "院校专业组":
            # 检查1：是否说"学校"或"院校"
            wrong_patterns = [
                f"{max_v}个学校",
                f"{max_v}所学校",
                f"{max_v}个院校",
            ]
            for pattern in wrong_patterns:
                if pattern in text:
                    self.errors["fatal"].append({
                        "rule": f"志愿单位错误（{self.province}）",
                        "description": f"{self.province}是{mode}模式，应该是{self.province_rule['max_volunteers']}个'{mode}'，不是{max_v}个'学校'或'院校'",
                        "fix": f"改为'{max_v}个院校专业组'",
                    })
                    break

            # 检查2：模式本身
            if "院校专业组" not in text and "专业组" not in text:
                self.errors["serious"].append({
                    "rule": f"未提及'{mode}'概念（{self.province}）",
                    "description": f"{self.province}采用{mode}模式，应在方案中明确",
                    "fix": "明确使用'院校专业组'概念",
                })

        elif mode == "专业+学校":
            # 浙江、山东等模式
            if "专业组" in text and "组内" in text:
                self.errors["fatal"].append({
                    "rule": f"模式错误（{self.province}）",
                    "description": f"{self.province}是'专业+学校'模式，不是'院校专业组'模式，无调剂选项",
                    "fix": "改为'专业+学校'，删除'组内服从'等概念",
                })

            if "调剂" in text and "无" not in text.split("调剂")[0][-10:]:
                # 简单检测：如果提到调剂但没说"无"
                if "不服从" not in text and "无需" not in text and "没有" not in text:
                    self.errors["serious"].append({
                        "rule": f"调剂概念错误（{self.province}）",
                        "description": f"{self.province}采用'专业+学校'模式，**没有调剂选项**",
                        "fix": "删除所有'服从调剂'相关描述",
                    })

    def _check_volunteer_count(self, text):
        """检查志愿数量"""
        max_v = self.province_rule["max_volunteers"]

        # 提取方案中提到的志愿数
        count_patterns = [
            r"共(\d+)个",
            r"填报(\d+)个",
            r"填了(\d+)个",
        ]

        for pattern in count_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                count = int(match)
                if count > max_v:
                    self.errors["fatal"].append({
                        "rule": f"志愿数量超标（{self.province}）",
                        "description": f"方案提到{count}个志愿，超过{self.province}本批次的{max_v}个上限",
                        "fix": f"志愿数不超过{max_v}个",
                    })
                elif count < max_v * 0.5 and "少" not in text:
                    self.warnings = getattr(self, "warnings", [])
                    self.warnings.append({
                        "rule": f"志愿数量较少（{self.province}）",
                        "description": f"方案只填了{count}个，建议填满{max_v}个（除非明确不需要）",
                        "fix": f"建议填满{max_v}个志愿",
                    })

    def _check_majors_per_group(self, text):
        """检查每组专业数"""
        max_m = self.province_rule["max_majors_per_group"]
        mode = self.province_rule["mode"]

        if mode == "院校专业组" and max_m > 1:
            # 院校专业组模式：每组最多6个专业
            if "6个专业" not in text and "六个专业" not in text:
                self.errors["warning"].append({
                    "rule": f"专业数说明缺失（{self.province}）",
                    "description": f"未说明每个专业组最多{max_m}个专业",
                    "fix": f"明确说明每组最多{max_m}个专业",
                })

        elif mode == "专业+学校":
            # 专业+学校模式：每志愿1个专业
            if "1个专业" not in text and "1所学校" not in text:
                self.errors["warning"].append({
                    "rule": f"专业数说明缺失（{self.province}）",
                    "description": f"未说明{self.province}是'专业+学校'模式，每志愿只填1个专业",
                    "fix": "明确'每个志愿1个专业'",
                })

    def _check_adjustment_rule(self, text):
        """检查调剂规则"""
        if not self.province_rule["has_adjustment"]:
            # 无调剂模式
            if "服从调剂" in text and "无需" not in text and "无调剂" not in text:
                self.errors["fatal"].append({
                    "rule": f"调剂规则错误（{self.province}）",
                    "description": f"{self.province}采用'专业+学校'模式，**没有调剂选项**",
                    "fix": "删除所有'服从调剂'相关描述",
                })
        else:
            # 有调剂模式
            adjustment_scope = self.province_rule["adjustment_scope"]
            if "服从调剂" in text and "全部专业" in text:
                if adjustment_scope == "组内专业":
                    self.errors["fatal"].append({
                        "rule": f"调剂范围错误（{self.province}）",
                        "description": f"{self.province}的调剂范围是'组内专业'，不是'全部专业'",
                        "fix": "改为'组内专业调剂'",
                    })

    def _check_data_accuracy(self, text):
        """检查数据准确性"""
        # 主观概率
        prob_pattern = r"(\d{2,3})\s*%\s*[\u4e00-\u9fa5]*(?:录取|概率|机会|把握)"
        matches = re.findall(prob_pattern, text)
        if matches:
            self.errors["serious"].append({
                "rule": "主观概率估算",
                "description": f"方案中含主观概率{set(matches)}，未基于真实数据",
                "fix": "删除主观概率，改用2025年位次作为参考",
            })

        # 2026年位次未说明
        if (
            "位次" in text
            and "2026" in text
            and "待官方" not in text
            and "以官方为准" not in text
        ):
            self.errors["serious"].append({
                "rule": "2026年位次",
                "description": "2026年位次待官方公布（6月25日出分后），不应假设",
                "fix": "明确'2026年位次待官方公布'",
            })

    def _check_subject_requirements(self, text):
        """检查选科要求"""
        if self.province_rule["subject_mode"] == "3+1+2":
            # 检查是否有"物+化+生"一刀切
            if re.search(r"会计.{0,20}物.{0,5}化.{0,5}生", text):
                self.errors["serious"].append({
                    "rule": "选科要求一刀切",
                    "description": "财经类专业选科要求因校而异，不能假设都要求'物+化+生'",
                    "fix": "逐校核实选科要求",
                })

    def _check_risk_disclosure(self, text):
        """检查风险提示"""
        risk_keywords = ["退档", "风险", "调剂", "体检", "单科"]
        has_risk = any(kw in text for kw in risk_keywords)

        if not has_risk:
            self.errors["serious"].append({
                "rule": "风险提示缺失",
                "description": "方案未明确说明退档风险（体检/单科/不服从调剂）",
                "fix": "增加风险提示章节",
            })

    def _report_no_province(self):
        """未检测到省份的报告"""
        return """
╔══════════════════════════════════════════════════════════════════╗
║             ⚠️  未检测到省份信息                                  ║
╚══════════════════════════════════════════════════════════════════╝

【问题】
方案中未明确省份信息，无法进行针对性检查。

【支持检测的省份】
  北京、天津、河北、山西、内蒙古、辽宁、吉林、黑龙江
  上海、江苏、浙江、安徽、福建、江西、山东、河南
  湖北、湖南、广东、广西、海南、重庆、四川、贵州
  云南、西藏、陕西、甘肃、青海、宁夏、新疆

【解决方式】
请在方案中明确省份信息，例如：
  "湖南考生，578分..."
  "浙江省，630分..."
"""

    def _report_unsupported_province(self):
        """省份不支持的报告"""
        return f"""
╔══════════════════════════════════════════════════════════════════╗
║             ⚠️  暂不支持 {self.province}                                          ║
╚══════════════════════════════════════════════════════════════════╝

【问题】
当前检查器暂不支持{self.province}的具体规则检查。

【已支持的省份】
{", ".join(sorted(PROVINCE_RULES.keys()))}

【后续计划】
将持续添加更多省份支持。
"""

    def _generate_report(self):
        """生成检查报告"""
        report = f"""
╔══════════════════════════════════════════════════════════════════╗
║             ✅ 志愿方案规范检查报告                              ║
╠══════════════════════════════════════════════════════════════════╣
║  检测省份：{self.province}                                              ║
║  志愿模式：{self.province_rule["mode"]}                                       ║
║  志愿数量：{self.province_rule["max_volunteers"]}个（{self.province_rule["batch"]}）                    ║
║  每组专业：{self.province_rule["max_majors_per_group"]}个                                            ║
║  调剂选项：{"有" if self.province_rule["has_adjustment"] else "无"}                                              ║
║  调剂范围：{self.province_rule["adjustment_scope"]}                                       ║
║  选科模式：{self.province_rule["subject_mode"]}                                          ║
║  检查时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}                             ║
╚══════════════════════════════════════════════════════════════════╝
"""

        if self.errors["fatal"]:
            report += "\n🔴 【致命错误】\n" + "─" * 70 + "\n"
            for i, err in enumerate(self.errors["fatal"], 1):
                report += f"""
  {i}. {err["rule"]}
     ❌ 问题：{err["description"]}
     ✅ 修正：{err["fix"]}
"""

        if self.errors["serious"]:
            report += "\n🟡 【严重错误】\n" + "─" * 70 + "\n"
            for i, err in enumerate(self.errors["serious"], 1):
                report += f"""
  {i}. {err["rule"]}
     ⚠️  问题：{err["description"]}
     🔧 修正：{err["fix"]}
"""

        if self.errors["warning"]:
            report += "\n🟢 【一般警告】\n" + "─" * 70 + "\n"
            for i, warn in enumerate(self.errors["warning"], 1):
                report += f"""
  {i}. {warn["rule"]}
     💡 建议：{warn["description"]}
     📌 做法：{warn["fix"]}
"""

        total = sum(len(v) for v in self.errors.values())
        report += f"""
═══════════════════════════════════════════════════════════════════
📊 【检查统计】
═══════════════════════════════════════════════════════════════════
  🔴 致命错误：{len(self.errors["fatal"])} 个
  🟡 严重错误：{len(self.errors["serious"])} 个
  🟢 一般警告：{len(self.errors["warning"])} 个
  📊 问题总数：{total} 个
"""

        if total == 0:
            report += "\n  🎉 方案基本合规！\n"
        elif len(self.errors["fatal"]) > 0:
            report += "\n  ❌ 必须修改致命错误后才能使用\n"
        else:
            report += "\n  ⚠️ 建议补充完善后使用\n"

        report += f"""
═══════════════════════════════════════════════════════════════════
📌 【重要提醒】
═══════════════════════════════════════════════════════════════════
  • 最终以{self.province}省教育考试院官方信息为准
  • 官方网址：{self.province_rule["official_url"]}
  • 2026年招生计划6月15-20日公布
  • 2026年实际位次6月25日出分后确定
═══════════════════════════════════════════════════════════════════
"""

        return report


# 主函数
if __name__ == "__main__":
    if len(sys.argv) < 2:
        # 默认测试
        print("用法: python spec_checker_v2.py <方案文件> [省份]")
        print("或: python spec_checker_v2.py (无参数时显示测试)")
        print()

        # 测试：湖南方案
        print("=" * 70)
        print("测试1：湖南方案（错误版）")
        print("=" * 70)

        bad_plan = """
        湖南578分考生志愿方案
        本次共填报45个学校志愿：
        志愿01：江西财经大学，会计学
        录取概率35%
        """

        checker = GaokaoSpecCheckerV2()
        print(checker.auto_detect_and_check(bad_plan))

        # 测试：浙江方案
        print("\n\n")
        print("=" * 70)
        print("测试2：浙江方案（专业+学校模式）")
        print("=" * 70)

        zj_plan = """
        浙江省，630分，选科物化生
        本次共填报80个专业+学校志愿：
        志愿01：浙江大学，计算机科学与技术
        志愿02：浙江工业大学，软件工程
        每个志愿填1个专业。
        """

        checker = GaokaoSpecCheckerV2()
        print(checker.auto_detect_and_check(zj_plan))

        # 测试：山东方案
        print("\n\n")
        print("=" * 70)
        print("测试3：山东方案")
        print("=" * 70)

        sd_plan = """
        山东高考，620分
        填报96个志愿：
        01-山东大学-会计学
        02-中国海洋大学-金融学
        """

        checker = GaokaoSpecCheckerV2()
        print(checker.auto_detect_and_check(sd_plan))
    else:
        # 从文件读取方案
        filename = sys.argv[1]
        province = sys.argv[2] if len(sys.argv) > 2 else None

        with open(filename, "r", encoding="utf-8") as f:
            plan = f.read()

        checker = GaokaoSpecCheckerV2(province)
        print(checker.auto_detect_and_check(plan))
