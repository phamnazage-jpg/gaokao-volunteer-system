"""
高考志愿填报可视化报告生成器
支持：雷达图、热力图、对比表、风险检测
"""

import json
import sys
from datetime import datetime


def generate_student_radar(student_profile):
    """
    生成考生画像雷达图数据
    """
    scores = {
        "兴趣匹配度": student_profile.get("interest_match", 0),
        "能力匹配度": student_profile.get("ability_match", 0),
        "就业匹配度": student_profile.get("employment_match", 0),
        "家庭适配度": student_profile.get("family_match", 0),
    }
    
    # 综合得分计算
    weighted_score = (
        scores["兴趣匹配度"] * 0.3 +
        scores["能力匹配度"] * 0.3 +
        scores["就业匹配度"] * 0.25 +
        scores["家庭适配度"] * 0.15
    )
    
    # 生成ASCII雷达图
    radar_chart = f"""
┌─────────────────────────────────────────────────────────────────┐
│                    🎯 {student_profile.get('name', '考生')} 画像雷达图                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                        兴趣匹配度                                │
│                             {scores['兴趣匹配度']:>3}/10                             │
│                              │                                   │
│              {min(scores['能力匹配度'], 10):>2}/10 ─────────┼───────── {min(scores['就业匹配度'], 10):>2}/10          │
│                能力匹配度     │     就业匹配度                    │
│                               │                                   │
│                         【{weighted_score:.1f}/10】                           │
│                         综合得分                                │
│                               │                                   │
│                     {scores['家庭适配度']:>3}/10                                   │
│                        家庭适配度                                │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  评分说明：                                                      │
│  • 兴趣匹配：基于霍兰德职业兴趣测试结果                        │
│  • 能力匹配：学科成绩与专业要求的匹配度                        │
│  • 就业匹配：专业就业前景评估                                  │
│  • 家庭适配：经济条件、地域要求的符合度                        │
└─────────────────────────────────────────────────────────────────┘
"""
    return radar_chart, weighted_score


def generate_school_comparison(volunteer_list):
    """
    生成院校对比决策表
    """
    table = """
┌──────────────────────────────────────────────────────────────────────┐
│                    🎯 志愿方案可视化对比                              │
├────────────┬────────────┬──────────┬─────────┬─────────┬───────────┤
│   志愿类型  │    院校    │   专业   │ 录取概率│ 匹配指数│  推荐指数 │
├────────────┼────────────┼──────────┼─────────┼─────────┼───────────┤
"""
    
    for idx, vol in enumerate(volunteer_list, 1):
        v_type = vol.get('type', '稳')
        emoji = {'冲': '🔴', '稳': '🟡', '保': '🟢'}.get(v_type, '⚪')
        
        prob_bar = '█' * int(vol.get('probability', 0) / 10) + '░' * (10 - int(vol.get('probability', 0) / 10))
        match_score = vol.get('match_score', 0)
        stars = '⭐' * int(match_score / 20) + '☆' * (5 - int(match_score / 20))
        
        table += f"""│ {emoji} {v_type:>2} {idx:>2} │ {vol.get('school', '待定'):<10} │ {vol.get('major', '待定'):<8} │ {prob_bar} │   {match_score:>3}   │ {stars} │
├────────────┼────────────┼──────────┼─────────┼─────────┼───────────┤
"""
    
    table += """│                                                                  │
│ 图例：                                                           │
│ 录取概率 █████ 90%+  ████░ 80%+  ███░░ 60%+  ██░░░ 40%+  █░░░░ <20%│
│ 匹配指数  90-100 完美  80-90 高度  70-80 中度  <70 需谨慎          │
└──────────────────────────────────────────────────────────────────┘
"""
    return table


def generate_major_heatmap(majors):
    """
    生成专业匹配度热力图
    """
    heatmap = """
┌──────────────────────────────────────────────────────────────────────┐
│              🔥 兴趣-专业匹配度热力图                                 │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
"""
    
    for major in majors:
        name = major.get('name', '')
        score = major.get('match_score', 0)
        
        # 生成热力条
        if score >= 90:
            bar = '█' * 20
            status = '强烈推荐'
        elif score >= 80:
            bar = '█' * 17 + '░' * 3
            status = '推荐选择'
        elif score >= 70:
            bar = '█' * 14 + '░' * 6
            status = '可以考虑'
        elif score >= 60:
            bar = '█' * 11 + '░' * 9
            status = '谨慎考虑'
        elif score >= 40:
            bar = '█' * 8 + '░' * 12
            status = '不太建议'
        else:
            bar = '█' * 5 + '░' * 15
            status = '不推荐'
        
        heatmap += f"│  {name:<12} {bar}  {score:>3}%  {status:<12} │\n"
    
    heatmap += """│                                                                      │
│ 热力指数：████ 90-100%  ████ 80-90%  ███░ 70-80%  ██░░ 60-70%        │
│            █░░░ 30-60%  ░░░░ <30% (不推荐)                          │
└──────────────────────────────────────────────────────────────────────┘
"""
    return heatmap


def detect_risks(student_profile, volunteer_list):
    """
    智能风险检测
    """
    risks = []
    
    # 检查位次差距
    for vol in volunteer_list:
        if vol.get('type') == '冲':
            if vol.get('probability', 0) < 30:
                risks.append({
                    'level': 'warning',
                    'item': f"{vol.get('school')}录取概率过低",
                    'desc': f"录取概率仅{vol.get('probability')}%，需要增加相近备选"
                })
    
    # 检查学科匹配
    weak_subjects = student_profile.get('weak_subjects', [])
    for vol in volunteer_list:
        required = vol.get('required_subjects', [])
        for subj in required:
            if subj in weak_subjects:
                risks.append({
                    'level': 'danger',
                    'item': f"{vol.get('school')}-{vol.get('major')}学科不匹配",
                    'desc': f"该专业需要{subj}，但考生{subj}为弱项"
                })
    
    # 检查梯度合理性
    types_count = {'冲': 0, '稳': 0, '保': 0}
    for vol in volunteer_list:
        v_type = vol.get('type', '稳')
        types_count[v_type] = types_count.get(v_type, 0) + 1
    
    total = len(volunteer_list)
    if total > 0:
        if types_count['保'] / total < 0.2:
            risks.append({
                'level': 'danger',
                'item': '保底志愿不足',
                'desc': f"保底志愿仅占{types_count['保']/total*100:.0f}%，建议至少30%"
            })
    
    # 生成风险报告
    risk_report = """
┌──────────────────────────────────────────────────────────────────────┐
│              🚦 志愿填报风险检测报告                                  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
"""
    
    danger_list = [r for r in risks if r['level'] == 'danger']
    warning_list = [r for r in risks if r['level'] == 'warning']
    
    if danger_list:
        risk_report += "│  🔴 高风险项目（必须修改）：                                        │\n"
        for risk in danger_list:
            risk_report += f"│     ✗ {risk['item']:<30}                            │\n"
            risk_report += f"│       → {risk['desc']:<50}                │\n"
            risk_report += "│                                                                      │\n"
    
    if warning_list:
        risk_report += "│  🟡 中风险项目（建议调整）：                                        │\n"
        for risk in warning_list:
            risk_report += f"│     ⚠ {risk['item']:<30}                            │\n"
            risk_report += f"│       → {risk['desc']:<50}                │\n"
            risk_report += "│                                                                      │\n"
    
    if not risks:
        risk_report += "│  🟢 恭喜！未检测到高风险项目，当前方案可以安全填报               │\n"
    
    risk_report += """│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
"""
    return risk_report, risks


def generate_volunteer_report(student_data, volunteer_list):
    """
    生成完整可视化报告
    """
    report = f"""
# 高考志愿填报可视化报告

**生成时间**：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}  
**考生姓名**：{student_data.get('name', '未知')}  
**考生省份**：{student_data.get('province', '未知')}  
**高考总分**：{student_data.get('score', 0)}分  
**全省位次**：{student_data.get('rank', 0)}名  

---

## 一、考生画像雷达图

"""
    
    # 生成雷达图
    radar, total_score = generate_student_radar(student_data)
    report += radar
    report += f"\n**综合匹配指数**：{total_score:.1f}/10\n\n"
    
    # 生成院校对比表
    report += "## 二、志愿方案可视化对比\n\n"
    report += generate_school_comparison(volunteer_list)
    report += "\n\n"
    
    # 生成专业热力图
    majors = []
    for vol in volunteer_list:
        majors.append({
            'name': vol.get('major', '未知'),
            'match_score': vol.get('match_score', 0)
        })
    report += "## 三、专业匹配度热力图\n\n"
    report += generate_major_heatmap(majors)
    report += "\n\n"
    
    # 风险检测
    report += "## 四、风险检测报告\n\n"
    risk_report, risks = detect_risks(student_data, volunteer_list)
    report += risk_report
    report += "\n\n"
    
    # 建议总结
    report += """## 五、填报建议总结

基于以上分析，给出以下建议：

| 建议类型 | 具体内容 |
|---------|---------|
| ✅ 推荐选择 | [根据匹配度最高的志愿填写] |
| ⚠️ 谨慎考虑 | [根据风险提示填写] |
| ❌ 不建议 | [根据不匹配项填写] |

---

*本报告由智能志愿填报系统生成，数据基于2025年历史录取信息*
"""
    
    return report


# 示例使用
if __name__ == "__main__":
    # 示例考生数据
    student = {
        'name': '李明',
        'province': '浙江省',
        'score': 612,
        'rank': 15230,
        'interest_match': 85,  # 兴趣匹配度
        'ability_match': 90,   # 能力匹配度
        'employment_match': 88, # 就业匹配度
        'family_match': 95,    # 家庭适配度
        'weak_subjects': ['化学', '语文']
    }
    
    # 示例志愿列表
    volunteers = [
        {
            'school': '浙江大学',
            'major': '计算机类',
            'type': '冲',
            'probability': 35,
            'match_score': 95,
            'required_subjects': ['数学', '物理']
        },
        {
            'school': '杭州电子科技大学',
            'major': '计算机类',
            'type': '稳',
            'probability': 70,
            'match_score': 92,
            'required_subjects': ['数学', '物理']
        },
        {
            'school': '浙江工业大学',
            'major': '软件工程',
            'type': '稳',
            'probability': 80,
            'match_score': 88,
            'required_subjects': ['数学']
        },
        {
            'school': '浙江理工大学',
            'major': '软件工程',
            'type': '保',
            'probability': 95,
            'match_score': 82,
            'required_subjects': ['数学']
        }
    ]
    
    # 生成报告
    report = generate_volunteer_report(student, volunteers)
    
    # 输出到文件
    output_file = f"/tmp/gaokao_visual_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"报告已生成：{output_file}")
    print("\n报告预览：")
    print(report)
