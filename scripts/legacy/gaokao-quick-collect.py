"""
高考志愿填报信息收集 - 对话集成版
用于在AI对话中快速收集考生信息
"""

# 标准问题模板
COLLECTION_TEMPLATE = """
您好！我是高考志愿填报智能助手。

为了给您提供最精准的志愿推荐，我需要了解以下信息：

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【步骤1/7】基本信息（必填）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 考生姓名：__________
2. 所在省份：__________（如：浙江省）
3. 高考模式：__________
   ①传统文理 ②3+3模式 ③3+1+2模式

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【步骤2/7】高考信息（必填）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4. 高考总分：__________分
5. 全省位次：__________名（一分一段表查询）
6. 选科组合：__________（如：物理+化学+地理）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【步骤3/7】兴趣测评（霍兰德模型）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
7. 课余时间最喜欢做什么？
   A. 拆解/组装东西（电器、模型）→ 现实型
   B. 看书/研究问题/探索原理 → 研究型
   C. 画画/设计/创作 → 艺术型
   D. 和朋友玩/组织活动 → 社会型
   E. 做小生意/策划活动 → 企业型
   F. 整理/做规划/记账 → 常规型

8. 如果完全不用担心钱，最想做什么？
   （同上6个选项）

9. 明确不喜欢什么？（多选）
   A. 背诵记忆 B. 数学计算 C. 和人打交道
   D. 做实验 E. 写代码 F. 都能接受

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【步骤4/7】能力评估（1-5分）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
10. 学科能力自评：
    数学：__ 物理：__ 化学：__ 
    语文：__ 英语：__ 
    （1分=很弱 3分=一般 5分=很强）

11. 你最擅长的学科：__________
    你最薄弱的学科：__________

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【步骤5/7】职业目标（必填）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
12. 职业优先级排序（输入编号如：135）：
    1.收入高 2.工作稳定 3.符合兴趣
    4.前景好 5.工作平衡 6.社会地位 7.工作自由

13. 毕业规划：__________
    ①本科就业 ②考研深造 ③出国留学 ④考公务员 ⑤不确定

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【步骤6/7】家庭背景
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
14. 家庭经济情况：__________
    ①困难 ②一般 ③中等 ④较好 ⑤富裕

15. 期望就业城市：__________
    ①一线城市 ②新一线城市 ③省会 ④家乡 ⑤不限定

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【步骤7/7】偏好设置
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
16. 院校层次偏好：__________
    ①名校优先 ②专业优先 ③城市优先 ④综合平衡

17. 是否服从调剂：__________
    ①必须服从 ②部分接受 ③不服从

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 填写提示：
• 可复制以上内容，填写后发回
• 信息越详细，推荐越精准
• 关键数据（分数、位次）请核对准确

请尽量回答所有问题，我们开始吧！
"""


def parse_collected_info(text: str) -> dict:
    """
    解析用户填写的信息
    """
    info = {
        "basic_info": {},
        "exam_info": {},
        "interest_profile": {},
        "ability_assessment": {},
        "career_goals": {},
        "family_background": {},
        "preferences": {}
    }
    
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 尝试解析 "数字. 项目：答案" 格式
        if '：' in line or ':' in line:
            parts = line.replace(':', '：').split('：', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                
                # 根据关键词分类存储
                if any(k in key for k in ['姓名', '省份']):
                    info['basic_info'][key] = value
                elif any(k in key for k in ['总分', '位次', '选科', '模式']):
                    info['exam_info'][key] = value
                elif any(k in key for k in ['兴趣', '喜欢', '不喜欢']):
                    info['interest_profile'][key] = value
                elif any(k in key for k in ['学科', '能力', '擅长', '薄弱']):
                    info['ability_assessment'][key] = value
                elif any(k in key for k in ['职业', '规划', '毕业']):
                    info['career_goals'][key] = value
                elif any(k in key for k in ['家庭', '经济', '城市']):
                    info['family_background'][key] = value
                elif any(k in key for k in ['偏好', '院校', '调剂']):
                    info['preferences'][key] = value
    
    return info


def validate_info(info: dict) -> list:
    """
    验证信息完整性
    返回缺失的必填项
    """
    missing = []
    
    # 必填项检查
    required_fields = {
        '姓名': 'basic_info',
        '省份': 'basic_info',
        '总分': 'exam_info',
        '位次': 'exam_info',
    }
    
    for field, section in required_fields.items():
        section_data = info.get(section, {})
        if not any(field in k for k in section_data.keys()):
            missing.append(field)
    
    return missing


def generate_summary(info: dict) -> str:
    """
    生成信息汇总摘要
    """
    summary = ["\n" + "="*50]
    summary.append("📋 考生信息汇总")
    summary.append("="*50)
    
    # 基本信息
    basic = info.get('basic_info', {})
    if basic:
        summary.append(f"\n【基本信息】")
        for k, v in basic.items():
            summary.append(f"  {k}：{v}")
    
    # 高考信息
    exam = info.get('exam_info', {})
    if exam:
        summary.append(f"\n【高考信息】")
        for k, v in exam.items():
            summary.append(f"  {k}：{v}")
    
    # 兴趣测评
    interest = info.get('interest_profile', {})
    if interest:
        summary.append(f"\n【兴趣类型】")
        for k, v in interest.items():
            summary.append(f"  {k}：{v}")
    
    # 能力评估
    ability = info.get('ability_assessment', {})
    if ability:
        summary.append(f"\n【能力评估】")
        for k, v in ability.items():
            summary.append(f"  {k}：{v}")
    
    # 职业目标
    career = info.get('career_goals', {})
    if career:
        summary.append(f"\n【职业目标】")
        for k, v in career.items():
            summary.append(f"  {k}：{v}")
    
    summary.append("\n" + "="*50)
    
    # 验证结果
    missing = validate_info(info)
    if missing:
        summary.append(f"\n⚠️  缺少必填项：{', '.join(missing)}")
    else:
        summary.append("\n✅ 必填信息完整！")
    
    return '\n'.join(summary)


# 快捷使用函数
def quick_collect():
    """
    快速收集模板输出
    """
    return COLLECTION_TEMPLATE


def process_response(user_input: str) -> str:
    """
    处理用户输入，返回解析结果
    """
    info = parse_collected_info(user_input)
    summary = generate_summary(info)
    return summary


# 示例使用
if __name__ == "__main__":
    # 输出收集模板
    print(COLLECTION_TEMPLATE)
    
    # 示例：模拟用户填写
    sample_input = """
1. 考生姓名：李明
2. 所在省份：浙江省
4. 高考总分：612分
5. 全省位次：15230名
6. 选科组合：物理+化学+地理
7. 课余时间最喜欢做什么？A
11. 最擅长的学科：物理
11. 最薄弱的学科：化学
12. 职业优先级排序：135
13. 毕业规划：①本科就业
14. 家庭经济情况：③中等
"""
    
    print("\n" + "="*50)
    print("解析示例输入：")
    print("="*50)
    result = process_response(sample_input)
    print(result)
