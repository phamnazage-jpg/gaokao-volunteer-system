# 高考志愿填报 - 交互式信息收集系统
# 优先级2：优化信息收集体验

import os
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional


class GaokaoInfoCollector:
    """
    高考志愿填报信息收集器
    采用分步骤引导式交互，确保收集完整、准确的信息
    """
    
    def __init__(self):
        self.data = {
            "basic_info": {},      # 基本信息
            "exam_info": {},       # 考试信息
            "interest_profile": {}, # 兴趣测评
            "ability_assessment": {}, # 能力评估
            "career_goals": {},    # 职业目标
            "family_background": {}, # 家庭背景
            "preferences": {},     # 偏好设置
        }
        self.current_step = 0
        self.total_steps = 7
        
    def welcome(self):
        """欢迎界面"""
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║           🎓 高考志愿填报智能助手 v2.0                            ║
║                                                                  ║
║   本系统将引导您完成志愿填报所需的信息收集                        ║
║   预计用时：5-8分钟                                               ║
║                                                                  ║
║   💡 提示：                                                       ║
║   • 请准备：高考成绩单、一分一段表、意向专业名单                   ║
║   • 建议考生本人参与填写                                          ║
║   • 信息越详细，推荐越精准                                        ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        input("\n按 Enter 键开始...")
        
    def step_1_basic_info(self) -> bool:
        """
        步骤1：基本信息收集
        """
        print("""
╔══════════════════════════════════════════════════════════════════╗
║  步骤 1/7：基本信息                                               ║
╠══════════════════════════════════════════════════════════════════╣
║  请填写考生的基本信息                                             ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        
        # 姓名
        while True:
            name = input("1. 考生姓名：").strip()
            if name:
                self.data["basic_info"]["name"] = name
                break
            print("   ⚠️  姓名不能为空，请重新输入")
            
        # 省份
        provinces = [
            "北京", "天津", "河北", "山西", "内蒙古",
            "辽宁", "吉林", "黑龙江", "上海", "江苏",
            "浙江", "安徽", "福建", "江西", "山东",
            "河南", "湖北", "湖南", "广东", "广西",
            "海南", "重庆", "四川", "贵州", "云南",
            "西藏", "陕西", "甘肃", "青海", "宁夏",
            "新疆"
        ]
        while True:
            print("\n2. 所在省份（输入编号）：")
            for i, p in enumerate(provinces, 1):
                print(f"   {i:2d}. {p}", end="  ")
                if i % 5 == 0:
                    print()
            try:
                choice = int(input("\n请选择："))
                if 1 <= choice <= len(provinces):
                    self.data["basic_info"]["province"] = provinces[choice-1]
                    break
            except ValueError:
                pass
            print("   ⚠️  无效选择，请重新输入")
            
        # 手机号（可选，用于接收报告）
        phone = input("\n3. 家长手机号（可选，用于接收报告）：").strip()
        if phone:
            self.data["basic_info"]["phone"] = phone
            
        print(f"\n✅ 基本信息已收集：{self.data['basic_info']['name']}，{self.data['basic_info']['province']}")
        return True
        
    def step_2_exam_info(self) -> bool:
        """
        步骤2：考试信息收集
        """
        print("""
╔══════════════════════════════════════════════════════════════════╗
║  步骤 2/7：高考信息                                               ║
╠══════════════════════════════════════════════════════════════════╣
║  请填写高考相关信息                                               ║
║  这些信息将用于精准匹配院校和专业                                 ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        
        # 高考模式
        print("\n1. 高考模式：")
        print("   1. 传统文理分科")
        print("   2. 3+3 模式（浙江、上海、北京、天津、山东、海南）")
        print("   3. 3+1+2 模式（其他新高考省份）")
        
        while True:
            try:
                mode = int(input("请选择："))
                if mode == 1:
                    self.data["exam_info"]["mode"] = "传统文理"
                    self.data["exam_info"]["batch"] = input("   文/理科：").strip()
                elif mode == 2:
                    self.data["exam_info"]["mode"] = "3+3"
                elif mode == 3:
                    self.data["exam_info"]["mode"] = "3+1+2"
                    self.data["exam_info"]["main_subject"] = input("   首选科目（物理/历史）：").strip()
                else:
                    raise ValueError
                break
            except (ValueError, IndexError):
                print("   ⚠️  无效选择，请重新输入")
                
        # 选科组合
        print("\n2. 选科组合（已选科目，空格分隔）：")
        print("   可选：语文 数学 英语 物理 历史 化学 生物 政治 地理 技术")
        subjects_input = input("   请输入：").strip()
        self.data["exam_info"]["subjects"] = subjects_input.split()
        
        # 高考总分
        while True:
            try:
                score = int(input("\n3. 高考总分（满分750）："))
                if 0 <= score <= 750:
                    self.data["exam_info"]["total_score"] = score
                    break
                print("   ⚠️  分数应在0-750之间")
            except ValueError:
                print("   ⚠️  请输入有效数字")
                
        # 全省位次
        while True:
            try:
                rank = int(input("\n4. 全省位次（一分一段表查询）："))
                if rank > 0:
                    self.data["exam_info"]["rank"] = rank
                    break
                print("   ⚠️  位次应为正数")
            except ValueError:
                print("   ⚠️  请输入有效数字")
                
        # 各科成绩（可选，用于能力评估）
        print("\n5. 各科成绩（可选，用于精准匹配）：")
        subjects_score = {}
        for subject in ["语文", "数学", "英语"]:
            score_input = input(f"   {subject}成绩（回车跳过）：").strip()
            if score_input:
                try:
                    subjects_score[subject] = int(score_input)
                except ValueError:
                    pass
        self.data["exam_info"]["subject_scores"] = subjects_score
        
        print(f"\n✅ 高考信息已收集：{score}分，位次：{rank}")
        return True
        
    def step_3_interest_profile(self) -> bool:
        """
        步骤3：兴趣测评（霍兰德模型）
        """
        print("""
╔══════════════════════════════════════════════════════════════════╗
║  步骤 3/7：兴趣测评                                               ║
╠══════════════════════════════════════════════════════════════════╣
║  这部分用于了解考生的兴趣类型                                     ║
║  帮助匹配最适合的专业方向                                         ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        
        print("\n💡 说明：请选择最符合实际情况的选项")
        print("-" * 60)
        
        questions = [
            {
                "q": "课余时间，你最喜欢做什么？",
                "options": [
                    ("A", "拆解/组装东西（电器、模型、电脑）", "R"),
                    ("B", "看书、研究问题、探索原理", "I"),
                    ("C", "画画、设计、创作、写作", "A"),
                    ("D", "和朋友出去玩、组织活动", "S"),
                    ("E", "做小生意、策划活动、当组织者", "E"),
                    ("F", "整理房间、做规划、记账", "C"),
                ]
            },
            {
                "q": "如果完全不用担心钱，你最想做什么？",
                "options": [
                    ("A", "研究新技术、搞发明创造", "R"),
                    ("B", "做科学研究、发现新知识", "I"),
                    ("C", "成为艺术家、作家、设计师", "A"),
                    ("D", "做志愿者、帮助他人", "S"),
                    ("E", "创办公司、当企业家", "E"),
                    ("F", "做管理、让一切井井有条", "C"),
                ]
            },
            {
                "q": "你在哪些事情上容易'忘记时间'？",
                "options": [
                    ("A", "修东西、做手工、编程", "R"),
                    ("B", "解难题、做实验、查资料", "I"),
                    ("C", "创作、设计、欣赏艺术", "A"),
                    ("D", "和人交流、帮助别人解决问题", "S"),
                    ("E", "策划、组织、领导项目", "E"),
                    ("F", "整理数据、制定计划", "C"),
                ]
            },
            {
                "q": "你明确不喜欢什么类型的事情？（多选）",
                "multi": True,
                "options": [
                    ("A", "背诵记忆（如历史、法律条文）", "memory"),
                    ("B", "数学计算、逻辑推理", "math"),
                    ("C", "和人打交道、社交应酬", "social"),
                    ("D", "做实验、动手操作", "experiment"),
                    ("E", "写代码、学技术", "tech"),
                    ("F", "我都能接受", "none"),
                ]
            }
        ]
        
        holland_scores = {"R": 0, "I": 0, "A": 0, "S": 0, "E": 0, "C": 0}
        dislikes = []
        
        for idx, question in enumerate(questions, 1):
            print(f"\n{idx}. {question['q']}")
            for opt, text, code in question['options']:
                print(f"   {opt}. {text}")
                
            if question.get('multi'):
                # 多选
                answer = input("请选择（可多选，如：ABC）：").strip().upper()
                for char in answer:
                    for opt, text, code in question['options']:
                        if char == opt:
                            if code == "none":
                                dislikes = []
                            else:
                                dislikes.append(code)
                            break
            else:
                # 单选
                while True:
                    answer = input("请选择：").strip().upper()
                    for opt, text, code in question['options']:
                        if answer == opt:
                            holland_scores[code] += 1
                            break
                    else:
                        print("   ⚠️  无效选择")
                        continue
                    break
                    
        # 确定主导兴趣类型
        sorted_types = sorted(holland_scores.items(), key=lambda x: x[1], reverse=True)
        primary_type = sorted_types[0][0]
        secondary_type = sorted_types[1][0]
        
        type_names = {
            "R": "现实型（Realistic）- 动手操作、技术实践",
            "I": "研究型（Investigative）- 分析研究、探索发现",
            "A": "艺术型（Artistic）- 创意表达、艺术创作",
            "S": "社会型（Social）- 帮助他人、教育服务",
            "E": "企业型（Enterprising）- 领导管理、商业经营",
            "C": "常规型（Conventional）- 规范有序、数据处理"
        }
        
        self.data["interest_profile"]["holland_code"] = f"{primary_type}{secondary_type}"
        self.data["interest_profile"]["primary_type"] = type_names[primary_type]
        self.data["interest_profile"]["secondary_type"] = type_names[secondary_type]
        self.data["interest_profile"]["scores"] = holland_scores
        self.data["interest_profile"]["dislikes"] = dislikes
        
        print(f"\n✅ 兴趣测评完成：")
        print(f"   主导类型：{type_names[primary_type]}")
        print(f"   次要类型：{type_names[secondary_type]}")
        if dislikes:
            print(f"   明确不喜欢：{', '.join(dislikes)}")
        return True
        
    def step_4_ability_assessment(self) -> bool:
        """
        步骤4：能力评估
        """
        print("""
╔══════════════════════════════════════════════════════════════════╗
║  步骤 4/7：能力评估                                               ║
╠══════════════════════════════════════════════════════════════════╣
║  评估各学科能力和软技能                                           ║
║  帮助识别优势和短板                                               ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        
        print("\n请对以下方面进行自我评估（1-5分）：")
        print("1分=很弱  2分=较弱  3分=一般  4分=较强  5分=很强")
        print("-" * 60)
        
        subjects = ["数学", "物理", "化学", "生物", "语文", "英语"]
        subject_scores = {}
        
        for subject in subjects:
            while True:
                try:
                    score = int(input(f"\n{subject}能力（1-5）："))
                    if 1 <= score <= 5:
                        subject_scores[subject] = score
                        break
                    print("   ⚠️  请输入1-5之间的数字")
                except ValueError:
                    print("   ⚠️  请输入有效数字")
                    
        print("\n软技能评估：")
        soft_skills = {
            "逻辑思维": "分析问题的能力",
            "动手操作": "手工、实验、操作设备的能力",
            "沟通表达": "与人交流、演讲、写作的能力",
            "组织协调": "组织活动、管理项目的能力",
            "艺术创作": "绘画、设计、音乐、创意能力",
            "抗压能力": "面对压力和挫折的承受力"
        }
        
        soft_skill_scores = {}
        for skill, desc in soft_skills.items():
            while True:
                try:
                    score = int(input(f"\n{skill} - {desc}（1-5）："))
                    if 1 <= score <= 5:
                        soft_skill_scores[skill] = score
                        break
                    print("   ⚠️  请输入1-5之间的数字")
                except ValueError:
                    print("   ⚠️  请输入有效数字")
                    
        # 识别强项和弱项
        strong_subjects = [s for s, score in subject_scores.items() if score >= 4]
        weak_subjects = [s for s, score in subject_scores.items() if score <= 2]
        
        self.data["ability_assessment"]["subjects"] = subject_scores
        self.data["ability_assessment"]["soft_skills"] = soft_skill_scores
        self.data["ability_assessment"]["strong"] = strong_subjects
        self.data["ability_assessment"]["weak"] = weak_subjects
        
        print(f"\n✅ 能力评估完成：")
        if strong_subjects:
            print(f"   优势学科：{', '.join(strong_subjects)}")
        if weak_subjects:
            print(f"   薄弱学科：{', '.join(weak_subjects)}")
        return True
        
    def step_5_career_goals(self) -> bool:
        """
        步骤5：职业目标
        """
        print("""
╔══════════════════════════════════════════════════════════════════╗
║  步骤 5/7：职业目标                                               ║
╠══════════════════════════════════════════════════════════════════╣
║  了解考生的职业期望和发展目标                                     ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        
        print("\n1. 您最看重职业的哪些方面？（按重要性排序，输入编号如：135）")
        priorities = [
            "收入高、赚钱多",
            "工作稳定、不担心失业",
            "符合兴趣爱好",
            "发展前景好、晋升空间大",
            "工作生活平衡、不加班",
            "社会地位高、受尊重",
            "工作自由、时间灵活"
        ]
        for i, p in enumerate(priorities, 1):
            print(f"   {i}. {p}")
            
        priority_input = input("\n请选择（按重要性排序，如：135）：").strip()
        selected_priorities = []
        for char in priority_input[:3]:  # 取前3个
            try:
                idx = int(char) - 1
                if 0 <= idx < len(priorities):
                    selected_priorities.append(priorities[idx])
            except ValueError:
                pass
        self.data["career_goals"]["priorities"] = selected_priorities
        
        print("\n2. 毕业后规划：")
        print("   1. 本科毕业直接工作")
        print("   2. 考研/保研继续深造")
        print("   3. 出国留学")
        print("   4. 考公务员/事业单位")
        print("   5. 不确定")
        
        while True:
            try:
                plan = int(input("请选择："))
                if 1 <= plan <= 5:
                    plans = ["本科就业", "考研深造", "出国留学", "考公务员", "不确定"]
                    self.data["career_goals"]["plan"] = plans[plan-1]
                    break
            except ValueError:
                pass
            print("   ⚠️  无效选择")
            
        print("\n3. 是否有明确的职业方向？（可选）")
        print("   例：医生、程序员、教师、律师、设计师等")
        career = input("请输入：").strip()
        if career:
            self.data["career_goals"]["target_career"] = career
            
        print(f"\n✅ 职业目标已收集：")
        print(f"   优先看重：{', '.join(selected_priorities[:3])}")
        print(f"   毕业规划：{self.data['career_goals']['plan']}")
        return True
        
    def step_6_family_background(self) -> bool:
        """
        步骤6：家庭背景
        """
        print("""
╔══════════════════════════════════════════════════════════════════╗
║  步骤 6/7：家庭情况                                               ║
╠══════════════════════════════════════════════════════════════════╣
║  了解家庭资源和约束条件                                           ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        
        print("\n1. 家庭经济情况：")
        print("   1. 困难（需要助学贷款/奖学金）")
        print("   2. 一般（能负担学费，其他需节省）")
        print("   3. 中等（学费生活费无压力）")
        print("   4. 较好（可支持考研/出国）")
        print("   5. 富裕（无经济压力）")
        
        while True:
            try:
                level = int(input("请选择："))
                if 1 <= level <= 5:
                    levels = ["困难", "一般", "中等", "较好", "富裕"]
                    self.data["family_background"]["economic"] = levels[level-1]
                    break
            except ValueError:
                pass
            print("   ⚠️  无效选择")
            
        print("\n2. 期望就业城市：")
        print("   1. 一线城市（北上广深）")
        print("   2. 新一线城市（杭州、南京、成都等）")
        print("   3. 省会城市")
        print("   4. 家乡/本地城市")
        print("   5. 不限定")
        print("   6. 其他（请填写）")
        
        city_choice = input("请选择：").strip()
        if city_choice == "6":
            city = input("请填写期望城市：").strip()
        else:
            cities = ["一线城市", "新一线城市", "省会城市", "家乡/本地", "不限定", ""]
            city = cities[int(city_choice)-1] if city_choice.isdigit() and 1 <= int(city_choice) <= 6 else "不限定"
        self.data["family_background"]["target_city"] = city
        
        print("\n3. 是否有家族行业资源可利用？（可选）")
        print("   例：父母在医疗系统、家族经商、有法律资源等")
        resource = input("请输入：").strip()
        if resource:
            self.data["family_background"]["family_resource"] = resource
            
        print(f"\n✅ 家庭情况已收集")
        return True
        
    def step_7_preferences(self) -> bool:
        """
        步骤7：偏好设置
        """
        print("""
╔══════════════════════════════════════════════════════════════════╗
║  步骤 7/7：偏好设置                                               ║
╠══════════════════════════════════════════════════════════════════╣
║  最后的个性化设置                                                 ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        
        print("\n1. 院校层次偏好：")
        print("   1. 优先985/211（名校优先）")
        print("   2. 优先专业实力（专业排名优先）")
        print("   3. 优先地理位置（城市优先）")
        print("   4. 综合平衡")
        
        while True:
            try:
                pref = int(input("请选择："))
                if 1 <= pref <= 4:
                    prefs = ["名校优先", "专业优先", "城市优先", "综合平衡"]
                    self.data["preferences"]["school_priority"] = prefs[pref-1]
                    break
            except ValueError:
                pass
            print("   ⚠️  无效选择")
            
        print("\n2. 专业方向偏好：（可多选）")
        directions = [
            "工科类（计算机、电子、机械等）",
            "理科类（数学、物理、化学等）",
            "医学类（临床、口腔、护理等）",
            "经管类（经济、金融、管理等）",
            "文科类（中文、外语、新闻等）",
            "艺术类（设计、音乐、美术等）",
            "师范类（教育、心理等）",
            "政法类（法学、政治等）"
        ]
        for i, d in enumerate(directions, 1):
            print(f"   {i}. {d}")
        selected = input("请选择（多选，如：135）：").strip()
        selected_dirs = []
        for char in selected:
            try:
                idx = int(char) - 1
                if 0 <= idx < len(directions):
                    selected_dirs.append(directions[idx])
            except ValueError:
                pass
        self.data["preferences"]["major_directions"] = selected_dirs
        
        print("\n3. 是否接受调剂：")
        print("   1. 必须服从调剂（确保录取）")
        print("   2. 可接受部分调剂")
        print("   3. 不服从调剂（优先专业）")
        
        while True:
            try:
                adjust = int(input("请选择："))
                if 1 <= adjust <= 3:
                    adjusts = ["必须服从", "部分接受", "不服从"]
                    self.data["preferences"]["adjustment"] = adjusts[adjust-1]
                    break
            except ValueError:
                pass
            print("   ⚠️  无效选择")
            
        print(f"\n✅ 偏好设置完成")
        return True
        
    def review_and_confirm(self) -> bool:
        """
        信息回顾与确认
        """
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                    📋 信息确认                                    ║
╠══════════════════════════════════════════════════════════════════╣
║  请核对以下信息，确认无误后生成报告                               ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        
        print(f"\n【基本信息】")
        print(f"   姓名：{self.data['basic_info']['name']}")
        print(f"   省份：{self.data['basic_info']['province']}")
        
        print(f"\n【高考信息】")
        print(f"   模式：{self.data['exam_info']['mode']}")
        print(f"   总分：{self.data['exam_info']['total_score']}分")
        print(f"   位次：{self.data['exam_info']['rank']}")
        
        print(f"\n【兴趣类型】")
        print(f"   霍兰德代码：{self.data['interest_profile']['holland_code']}")
        print(f"   主导类型：{self.data['interest_profile']['primary_type']}")
        
        print(f"\n【能力评估】")
        strong = self.data['ability_assessment']['strong']
        if strong:
            print(f"   优势：{', '.join(strong)}")
            
        print(f"\n【职业目标】")
        print(f"   规划：{self.data['career_goals']['plan']}")
        
        print(f"\n【家庭情况】")
        print(f"   经济：{self.data['family_background']['economic']}")
        print(f"   目标城市：{self.data['family_background']['target_city']}")
        
        confirm = input("\n以上信息是否正确？（Y/n）：").strip().lower()
        return confirm != 'n'
        
    def save_data(self, filename=None):
        """
        保存数据到文件
        """
        if filename is None:
            filename = f"/tmp/gaokao_profile_{self.data['basic_info']['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
        self.data["meta"] = {
            "created_at": datetime.now().isoformat(),
            "version": "2.0"
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
            
        print(f"\n💾 数据已保存到：{filename}")
        return filename
        
    def run(self):
        """
        运行完整收集流程
        """
        self.welcome()
        
        steps = [
            ("基本信息", self.step_1_basic_info),
            ("高考信息", self.step_2_exam_info),
            ("兴趣测评", self.step_3_interest_profile),
            ("能力评估", self.step_4_ability_assessment),
            ("职业目标", self.step_5_career_goals),
            ("家庭情况", self.step_6_family_background),
            ("偏好设置", self.step_7_preferences),
        ]
        
        for idx, (name, step_func) in enumerate(steps, 1):
            self.current_step = idx
            if not step_func():
                print(f"\n❌ 步骤 {idx} 未完成，退出收集")
                return False
                
        # 确认信息
        if not self.review_and_confirm():
            print("\n请重新运行程序修改信息")
            return False
            
        # 保存数据
        data_file = self.save_data()
        
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                   ✅ 信息收集完成！                               ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║   接下来可以：                                                    ║
║   1. 运行可视化报告生成器生成完整报告                             ║
║   2. 使用收集的数据进行志愿匹配分析                               ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        
        return data_file


# 直接运行
if __name__ == "__main__":
    collector = GaokaoInfoCollector()
    data_file = collector.run()
    
    if data_file:
        print(f"\n数据文件：{data_file}")
        print("\n提示：您可以使用以下命令生成可视化报告：")
        print(f"  python3 ~/.local/bin/gaokao-visual-report-v2.py")
