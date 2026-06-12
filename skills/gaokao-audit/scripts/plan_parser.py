"""
方案解析器

从大厂AI生成的方案（PDF文本/纯文本/截图OCR）中
提取考生信息和志愿列表。

输出 ParsedPlan dataclass，可序列化为 dict 后送入
audit_report.html 模板进行渲染。
"""

import re
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Tuple


# 省份名称映射（支持多种写法）
# 注意：键的顺序决定了"省份：HN"在河南/海南/湖南三者中匹配哪一个。
# 由于实际场景下"省份：HN"通常指 Hunan（湖南考生最常见），
# 把湖南放在前面以避免被河南或海南先吃掉。
PROVINCE_MAPPING = [
    ("湖南", ["湖南", "湘", "HN", "Hunan"]),
    ("湖北", ["湖北", "鄂", "Hubei"]),
    ("广东", ["广东", "粤", "GD", "Guangdong"]),
    ("浙江", ["浙江", "浙", "ZJ", "Zhejiang"]),
    ("江苏", ["江苏", "苏", "JS", "Jiangsu"]),
    ("山东", ["山东", "鲁", "SD", "Shandong"]),
    ("河南", ["河南", "豫", "Henan"]),
    ("四川", ["四川", "川", "蜀", "SC", "Sichuan"]),
    ("福建", ["福建", "闽", "FJ", "Fujian"]),
    ("北京", ["北京", "京", "BJ", "Beijing"]),
    ("上海", ["上海", "沪", "SH", "Shanghai"]),
    ("天津", ["天津", "津", "TJ", "Tianjin"]),
    ("重庆", ["重庆", "渝", "CQ", "Chongqing"]),
    ("陕西", ["陕西", "陕", "秦", "Shaanxi"]),
    ("辽宁", ["辽宁", "辽", "LN", "Liaoning"]),
    ("江西", ["江西", "赣", "JX", "Jiangxi"]),
    ("安徽", ["安徽", "皖", "AH", "Anhui"]),
    ("广西", ["广西", "桂", "GX", "Guangxi"]),
    ("河北", ["河北", "冀", "HB", "Hebei"]),
    ("山西", ["山西", "晋", "SX", "Shanxi"]),
    ("云南", ["云南", "滇", "云", "YN", "Yunnan"]),
    ("贵州", ["贵州", "黔", "贵", "GZ", "Guizhou"]),
    ("黑龙江", ["黑龙江", "黑", "HLJ", "Heilongjiang"]),
    ("吉林", ["吉林", "吉", "JL", "Jilin"]),
    ("甘肃", ["甘肃", "甘", "陇", "GS", "Gansu"]),
    ("内蒙古", ["内蒙古", "蒙", "NMG", "Inner Mongolia", "NeiMenggu"]),
    ("新疆", ["新疆", "新", "XJ", "Xinjiang"]),
    ("宁夏", ["宁夏", "宁", "NX", "Ningxia"]),
    ("青海", ["青海", "青", "QH", "Qinghai"]),
    ("西藏", ["西藏", "藏", "XZ", "Tibet", "Xizang"]),
    ("海南", ["海南", "琼", "Hainan"]),
]


@dataclass
class ParsedPlan:
    """解析后的方案"""

    province: Optional[str] = None
    score: Optional[int] = None
    rank: Optional[int] = None
    subjects: Optional[str] = None
    source: Optional[str] = None  # AI来源（千问/元宝等）
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

    # ---------- 字段提取器 ----------

    def _extract_province(self, text: str) -> Optional[str]:
        """提取省份"""
        # 先尝试强匹配（"省份：xxx"、"所在地：xxx"），优先保证显式标注胜出
        for standard, aliases in PROVINCE_MAPPING:
            for alias in aliases:
                patterns = [
                    rf"省份[:：]\s*{re.escape(alias)}\b",
                    rf"所在地[:：]\s*{re.escape(alias)}\b",
                    rf"{re.escape(alias)}考生",
                    rf"{re.escape(alias)}省",
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
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                return int(m.group(1))
        # 兜底：抓"考了xxx分"这类口语表达，限定三位数避免年份干扰
        m = re.search(r"考了?\s*(\d{3})\s*分", text)
        if m:
            return int(m.group(1))
        return None

    def _extract_rank(self, text: str) -> Optional[int]:
        """提取全省位次"""
        patterns = [
            r"位次[:：]\s*[约~]?\s*(\d+)",
            r"全省排名[:：]\s*(\d+)",
            r"全省位次[:：]\s*(\d+)",
            r"排名[:：]\s*[约~]?\s*(\d+)",
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                return int(m.group(1))
        return None

    def _extract_subjects(self, text: str) -> Optional[str]:
        """提取选科组合"""
        # 先匹配"选科：xxx"；兼容用 + / 空格 / 中文逗号分隔
        m = re.search(r"选科(?:组合)?[:：]\s*([^\n]+)", text)
        if m:
            raw = m.group(1).strip()
            # 去掉行尾可能的尾巴（如"选科"标题里延伸出的下一行内容）
            # 先用换行切断（如果有 \n 已被吃掉，则取第一段）
            raw = raw.split("\n")[0].strip()
            # 清理：用"+"替换所有空白/常见分隔符
            normalized = re.sub(r"[+\s,，、/]+", "+", raw)
            # 提取纯学科 token
            allowed = {"物理", "化学", "生物", "历史", "政治", "地理"}
            tokens = [t for t in normalized.split("+") if t in allowed]
            if tokens:
                return "+".join(tokens)
        return None

    def _extract_source(self, text: str) -> Optional[str]:
        """提取AI来源"""
        # 顺序很重要：更长的别名优先（"通义千问" 优先于 "千问"）
        sources = [
            "通义千问",
            "千问",
            "腾讯元宝",
            "元宝",
            "文心一言",
            "文心",
            "百度AI",
            "百度",
            "豆包",
            "字节",
        ]
        for s in sources:
            if s in text:
                return s
        return None

    def _extract_volunteers(self, text: str) -> List[Dict[str, Any]]:
        """提取志愿列表

        支持格式:
        - 1. 学校 - 专业
        - 1、学校 专业
        - 1) 学校 专业
        """
        volunteers: List[Dict[str, Any]] = []

        # 匹配志愿行（行首编号 + 内容）
        # 支持以下行首编号格式：
        #   "1. xxx"  "1、xxx"  "1) xxx"        — 编号后跟标点
        #   "1 xxx"                            — 编号后直接空格（PDF 提取常见）
        pattern = r"^\s*(\d{1,3})\s*[.、)]\s*([^\n]+)|^\s*(\d{1,3})\s+([^\n]+)"

        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue

            m = re.match(pattern, line)
            if not m:
                continue

            # 两个分支分别捕获编号和内容
            if m.group(1) is not None:
                index = int(m.group(1))
                content = m.group(2).strip()
            else:
                index = int(m.group(3))
                content = m.group(4).strip()

            # 解析学校和专业
            school, major = self._parse_school_major(content)

            if school:
                volunteers.append(
                    {
                        "index": index,
                        "school": school,
                        "major": major or "",
                        "raw": content,
                    }
                )

        return volunteers

    def _parse_school_major(self, content: str) -> Tuple[str, str]:
        """从一行内容解析学校和专业

        支持格式:
        - 学校 - 专业
        - 学校：专业
        - 学校（专业）
        - 学校 专业
        """
        # 1) 优先尝试 " - " 分隔（用户最常见的格式："长沙理工大学 - 会计学"）
        if " - " in content:
            parts = content.split(" - ", 1)
            return parts[0].strip(), parts[1].strip()

        # 2) 中文/英文冒号分隔
        m = re.match(r"^(.+?)\s*[:：]\s*(.+)$", content)
        if m:
            return m.group(1).strip(), m.group(2).strip()

        # 3) 括号："湖南师范大学（专业组001）"
        m = re.match(r"^(.+?)\s*[（(]([^）)]+?)[）)]", content)
        if m:
            return m.group(1).strip(), m.group(2).strip()

        # 4) 兜底：以"大学/学院/学校"作为学校名边界
        m = re.match(r"^(.{2,15}(?:大学|学院|学校))(?:\s+(.+))?$", content)
        if m:
            school = m.group(1).strip()
            major = (m.group(2) or "").strip()
            return school, major

        # 5) 实在识别不出，按整体当作学校
        return content.strip(), ""


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
