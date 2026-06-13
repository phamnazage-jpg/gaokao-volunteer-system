"""
高考志愿填报 - 3分钟快速收集版
只保留最关键的问题，适合快速咨询场景
"""

# 3分钟快速问卷模板
QUICK_3MIN_TEMPLATE = """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║              ⚡ 高考志愿填报 - 3分钟快速问卷                        ║
║                                                                   ║
║     填写以下7个关键问题，即可生成个性化志愿建议                     ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

【必填 - 基本信息】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
□ 1. 考生姓名：_______________
□ 2. 所在省份：_______________
□ 3. 高考总分：_______ 分
□ 4. 全省位次：_______ 名（查一分一段表）

【必填 - 核心匹配】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
□ 5. 你属于哪种类型？（单选）
   
   R. 🔧 喜欢动手拆装修东西（电脑/模型/电器）
       → 推荐：计算机、电子、机械、自动化
   
   I. 🔬 喜欢研究探索（解难题/做实验/查资料）
       → 推荐：数学、物理、医学、科研类
   
   A. 🎨 喜欢创意创作（画画/设计/写作）
       → 推荐：设计、建筑、传媒、艺术
   
   S. 🤝 喜欢帮助人（志愿者/当老师/照顾人）
       → 推荐：师范、医学、心理学、社工
   
   E. 📊 喜欢领导组织（当班干部/策划活动/做生意）
       → 推荐：管理、经济、法学、商科
   
   C. 📝 喜欢规范有序（整理数据/做表格/规划）
       → 推荐：会计、统计、财务、行政

□ 6. 你最擅长哪2门学科？（选填）
   例：物理、数学

□ 7. 明确不喜欢的？（多选）
   A. 背诵记忆  B. 数学计算  C. 社交应酬
   D. 做实验   E. 写代码    F. 都喜欢

【选填 - 关键约束】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
□ 8. 家庭经济条件：
   ①困难 ②一般 ③中等 ④较好

□ 9. 毕业后最想：
   ①直接工作赚钱  ②读研深造  ③考公务员  ④不确定

□ 10. 想去哪里工作：
   ①一线城市 ②新一线 ③本省 ④都能接受

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 填写说明：
• 复制以上内容，填写后发回
• 必填1-7项，选填8-10项可选
• 位次查法：省教育考试院官网

📤 发送格式示例：
1. 李明
2. 浙江省  
3. 612
4. 15230
5. R
6. 物理、数学
7. C
8. ③
9. ①
10. ②
"""


# 极简1分钟版
ULTRA_1MIN_TEMPLATE = """
╔═══════════════════════════════════════════════════════════════════╗
║              ⚡ 高考志愿 - 1分钟极速版                              ║
╚════════════════════════════════━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━═══╝

只需要回答这5个问题：

1️⃣ 姓名+省份：______________（如：李明 浙江）
2️⃣ 分数+位次：______________（如：612分 15230名）
3️⃣ 选科：__________________（如：物化地）
4️⃣ 类型：__________________（R/I/A/S/E/C 选1个）
   R=动手型 I=研究型 A=艺术型 S=助人型 E=管理型 C=常规型
5️⃣ 不能接受的：_____________（如：背诵、数学、社交）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
示例回复：
李明 浙江 612分 15230名 物化地 R类型 不接受社交
"""


def parse_quick_response(text: str) -> dict:
    """
    解析快速问卷回复
    支持多种格式：带编号、无编号、紧凑型
    """
    info: dict[str, dict[str, object]] = {
        "basic": {},
        "exam": {},
        "profile": {},
        "constraints": {},
    }

    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]

    # 类型映射
    type_map = {
        "R": ("现实型", ["计算机", "电子", "机械", "自动化"]),
        "I": ("研究型", ["数学", "物理", "医学", "化学"]),
        "A": ("艺术型", ["设计", "建筑", "传媒", "中文"]),
        "S": ("社会型", ["师范", "医学", "心理学", "社工"]),
        "E": ("企业型", ["管理", "经济", "金融", "法学"]),
        "C": ("常规型", ["会计", "统计", "财务", "信息"]),
    }

    for line in lines:
        # 尝试各种格式提取

        # 格式1: "1. 李明" 或 "1、李明" 或 "1 李明"
        if line[0].isdigit() and len(line) > 2:
            parts = line.replace("、", " ").replace(".", " ").replace("：", " ").split()
            if len(parts) >= 2:
                key_num = parts[0]
                value = " ".join(parts[1:])

                if key_num == "1":
                    # 可能包含省份
                    if " " in value or "\t" in value:
                        parts2 = value.replace("\t", " ").split()
                        info["basic"]["name"] = parts2[0]
                        if len(parts2) > 1:
                            info["basic"]["province"] = parts2[1]
                    else:
                        info["basic"]["name"] = value
                elif key_num == "2":
                    # 省份
                    provinces = [
                        "北京",
                        "天津",
                        "河北",
                        "山西",
                        "内蒙古",
                        "辽宁",
                        "吉林",
                        "黑龙江",
                        "上海",
                        "江苏",
                        "浙江",
                        "安徽",
                        "福建",
                        "江西",
                        "山东",
                        "河南",
                        "湖北",
                        "湖南",
                        "广东",
                        "广西",
                        "海南",
                        "重庆",
                        "四川",
                        "贵州",
                        "云南",
                        "西藏",
                        "陕西",
                        "甘肃",
                        "青海",
                        "宁夏",
                        "新疆",
                    ]
                    for p in provinces:
                        if p in value:
                            info["basic"]["province"] = p
                            break
                    else:
                        info["basic"]["province"] = value.replace("省", "").strip()
                elif key_num == "3":
                    # 分数
                    import re

                    numbers = re.findall(r"\d+", value)
                    if numbers:
                        info["exam"]["score"] = int(numbers[0])
                elif key_num == "4":
                    # 位次
                    import re

                    numbers = re.findall(r"\d+", value)
                    if numbers:
                        info["exam"]["rank"] = int(numbers[0])
                elif key_num == "5":
                    # 兴趣类型
                    code = value.upper()
                    if code in type_map:
                        info["profile"]["type_code"] = code
                        info["profile"]["type_name"] = type_map[code][0]
                        info["profile"]["recommended_majors"] = type_map[code][1]
                elif key_num == "6":
                    # 优势学科
                    info["profile"]["strong_subjects"] = value.replace("、", " ")
                elif key_num == "7":
                    # 不喜欢的内容
                    info["profile"]["dislikes"] = value
                elif key_num in ["8", "9", "10"]:
                    # 选填项
                    if "经济" in line or key_num == "8":
                        info["constraints"]["economic"] = value
                    elif "毕业" in line or key_num == "9":
                        info["constraints"]["plan"] = value
                    elif "工作" in line or key_num == "10":
                        info["constraints"]["city"] = value

        # 格式2: 紧凑型 "李明 浙江 612分 15230名 物化地 R 不接受社交"
        elif " " in line and len(line.split()) >= 3:
            parts = line.split()
            # 尝试识别各部分
            for i, part in enumerate(parts):
                # 名字（通常第一个）
                if i == 0 and len(part) >= 2 and part.isalpha():
                    info["basic"]["name"] = part
                # 省份
                elif part.replace("省", "") in [
                    "北京",
                    "天津",
                    "河北",
                    "山西",
                    "内蒙古",
                    "辽宁",
                    "吉林",
                    "黑龙江",
                    "上海",
                    "江苏",
                    "浙江",
                    "安徽",
                    "福建",
                    "江西",
                    "山东",
                    "河南",
                    "湖北",
                    "湖南",
                    "广东",
                    "广西",
                    "海南",
                    "重庆",
                    "四川",
                    "贵州",
                    "云南",
                    "西藏",
                    "陕西",
                    "甘肃",
                    "青海",
                    "宁夏",
                    "新疆",
                ]:
                    info["basic"]["province"] = part.replace("省", "")
                # 分数（带"分"）
                elif "分" in part:
                    import re

                    nums = re.findall(r"\d+", part)
                    if nums:
                        info["exam"]["score"] = int(nums[0])
                # 位次（带"名"或"位次"）
                elif "名" in part or "位次" in part:
                    import re

                    nums = re.findall(r"\d+", part)
                    if nums:
                        info["exam"]["rank"] = int(nums[0])
                # 兴趣类型
                elif part.upper() in type_map:
                    code = part.upper()
                    info["profile"]["type_code"] = code
                    info["profile"]["type_name"] = type_map[code][0]
                    info["profile"]["recommended_majors"] = type_map[code][1]

    return info


def generate_quick_summary(info: dict) -> str:
    """生成快速摘要"""
    lines = []
    lines.append("\n" + "=" * 50)
    lines.append("📋 快速信息汇总")
    lines.append("=" * 50)

    # 基本信息
    name = info.get("basic", {}).get("name", "未知")
    province = info.get("basic", {}).get("province", "未知")
    lines.append(f"\n👤 {name} | {province}")

    # 考试信息
    score = info.get("exam", {}).get("score")
    rank = info.get("exam", {}).get("rank")
    if score:
        lines.append(f"📊 高考：{score}分")
    if rank:
        lines.append(f"📊 位次：{rank}名")

    # 兴趣类型
    type_name = info.get("profile", {}).get("type_name")
    type_code = info.get("profile", {}).get("type_code")
    majors = info.get("profile", {}).get("recommended_majors", [])
    if type_name:
        lines.append(f"\n🎯 兴趣类型：{type_name} ({type_code})")
        if majors:
            lines.append(f"   推荐专业：{'、'.join(majors)}")

    # 强项学科
    strong = info.get("profile", {}).get("strong_subjects")
    if strong:
        lines.append(f"💪 优势学科：{strong}")

    # 不喜欢
    dislikes = info.get("profile", {}).get("dislikes")
    if dislikes:
        lines.append(f"❌ 应避免：{dislikes}")

    # 约束
    plan = info.get("constraints", {}).get("plan")
    city = info.get("constraints", {}).get("city")
    if plan or city:
        lines.append(f"\n📍 规划：{plan or '未指定'} | 地域：{city or '未指定'}")

    lines.append("\n" + "=" * 50)

    # 缺失信息提醒
    missing = []
    if not info.get("basic", {}).get("name"):
        missing.append("姓名")
    if not info.get("exam", {}).get("score"):
        missing.append("分数")
    if not info.get("exam", {}).get("rank"):
        missing.append("位次")
    if not info.get("profile", {}).get("type_code"):
        missing.append("兴趣类型")

    if missing:
        lines.append(f"⚠️  还需补充：{', '.join(missing)}")
    else:
        lines.append("✅ 核心信息完整！可以开始推荐")

    return "\n".join(lines)


def generate_quick_recommendation(info: dict) -> str:
    """基于快速信息生成初步推荐"""
    lines = []
    lines.append("\n" + "=" * 50)
    lines.append("🎯 初步志愿建议")
    lines.append("=" * 50)

    # 基于霍兰德类型的推荐
    type_code = info.get("profile", {}).get("type_code")
    strong = info.get("profile", {}).get("strong_subjects", "")
    dislikes = info.get("profile", {}).get("dislikes", "")

    recommendations = {
        "R": {
            "majors": [
                "计算机科学与技术",
                "软件工程",
                "电子信息工程",
                "自动化",
                "机械设计",
            ],
            "reason": "喜欢动手操作，适合工科技术类专业",
            "caution": "数学物理不能弱",
        },
        "I": {
            "majors": ["数学与应用数学", "物理学", "临床医学", "生物科学", "化学"],
            "reason": "喜欢研究探索，适合理科或医学类",
            "caution": "需深造，本科就业面窄",
        },
        "A": {
            "majors": [
                "数字媒体技术",
                "建筑学",
                "工业设计",
                "视觉传达设计",
                "网络与新媒体",
            ],
            "reason": "有创造力，适合设计或创意类专业",
            "caution": "纯艺术就业难，推荐技术+艺术结合",
        },
        "S": {
            "majors": ["临床医学", "师范类", "心理学", "护理学", "社会工作"],
            "reason": "喜欢助人，适合医学或教育类专业",
            "caution": "医学需长期投入，师范稳定但收入一般",
        },
        "E": {
            "majors": ["工商管理", "经济学", "金融学", "法学", "市场营销"],
            "reason": "有领导力，适合商科或管理类专业",
            "caution": "非名校就业难，竞争激烈",
        },
        "C": {
            "majors": ["会计学", "统计学", "财务管理", "信息管理与信息系统"],
            "reason": "喜欢规范有序，适合财会或统计类专业",
            "caution": "AI替代风险，需持续学习",
        },
    }

    if type_code and type_code in recommendations:
        rec = recommendations[type_code]
        lines.append(f"\n【基于兴趣类型 {type_code}】")
        lines.append(f"{rec['reason']}")
        lines.append("\n📚 推荐专业方向：")
        for i, major in enumerate(rec["majors"][:4], 1):
            lines.append(f"  {i}. {major}")
        lines.append(f"\n⚠️ 注意事项：{rec['caution']}")

    # 基于强学科的推荐
    if strong:
        lines.append("\n【基于优势学科】")
        if "物理" in strong and "数学" in strong:
            lines.append("物理数学强 → 计算机、电子信息、自动化")
        elif "物理" in strong:
            lines.append("物理强 → 工科类专业均可")
        elif "数学" in strong:
            lines.append("数学强 → 计算机、金融、统计、数学类")
        elif "化学" in strong:
            lines.append("化学强 → 医学、药学、材料、化工")
        elif "生物" in strong:
            lines.append("生物强 → 医学、生物科学、农学")
        elif "语文" in strong or "英语" in strong:
            lines.append("文科强 → 师范、法学、外语、新闻传播")

    # 基于不喜欢的排除
    if dislikes:
        lines.append("\n【反向排除】")
        if "数学" in dislikes or "计算" in dislikes:
            lines.append("❌ 不喜欢数学 → 避开计算机、金融、人工智能")
        if "背诵" in dislikes or "记忆" in dislikes:
            lines.append("❌ 不喜欢背诵 → 避开法学、医学、文史哲")
        if "社交" in dislikes or "应酬" in dislikes:
            lines.append("❌ 不喜欢社交 → 避开市场营销、管理、师范")
        if "实验" in dislikes:
            lines.append("❌ 不喜欢实验 → 避开化学、生物、材料")

    lines.append("\n" + "=" * 50)

    return "\n".join(lines)


def main():
    """主函数 - 输出问卷模板"""
    print(QUICK_3MIN_TEMPLATE)

    print("\n" + "=" * 50)
    print("或者使用极速版（1分钟）：")
    print("=" * 50)
    print(ULTRA_1MIN_TEMPLATE)


if __name__ == "__main__":
    main()
