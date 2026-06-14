"""
高考志愿填报可视化报告生成器 V2.0
支持：雷达图、热力图、对比表、风险检测
新增：HTML导出、PDF导出、精美样式
"""

from datetime import datetime

# 尝试导入可选依赖
try:
    from jinja2 import Template

    HAS_JINJA = True
except ImportError:
    HAS_JINJA = False
    print("警告: jinja2 未安装，HTML模板功能将受限")

try:
    from weasyprint import HTML  # type: ignore[import-untyped]

    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False
    print("警告: weasyprint 未安装，PDF导出功能不可用")


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
        scores["兴趣匹配度"] * 0.3
        + scores["能力匹配度"] * 0.3
        + scores["就业匹配度"] * 0.25
        + scores["家庭适配度"] * 0.15
    )

    # 生成ASCII雷达图
    radar_chart = f"""
┌─────────────────────────────────────────────────────────────────┐
│                    🎯 {student_profile.get("name", "考生")} 画像雷达图                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                        兴趣匹配度                                │
│                             {scores["兴趣匹配度"]:>3}/10                             │
│                              │                                   │
│              {min(scores["能力匹配度"], 10):>2}/10 ─────────┼───────── {min(scores["就业匹配度"], 10):>2}/10          │
│                能力匹配度     │     就业匹配度                    │
│                               │                                   │
│                         【{weighted_score:.1f}/10】                           │
│                         综合得分                                │
│                               │                                   │
│                      {scores["家庭适配度"]:>3}/10                                   │
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
    return radar_chart, weighted_score, scores


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
        v_type = vol.get("type", "稳")
        emoji = {"冲": "🔴", "稳": "🟡", "保": "🟢"}.get(v_type, "⚪")

        prob_bar = "█" * int(vol.get("probability", 0) / 10) + "░" * (
            10 - int(vol.get("probability", 0) / 10)
        )
        match_score = vol.get("match_score", 0)
        stars = "⭐" * int(match_score / 20) + "☆" * (5 - int(match_score / 20))

        table += f"""│ {emoji} {v_type:>2} {idx:>2} │ {vol.get("school", "待定"):<10} │ {vol.get("major", "待定"):<8} │ {prob_bar} │   {match_score:>3}   │ {stars} │
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
        name = major.get("name", "")
        score = major.get("match_score", 0)

        # 生成热力条
        if score >= 90:
            bar = "█" * 20
            status = "强烈推荐"
        elif score >= 80:
            bar = "█" * 17 + "░" * 3
            status = "推荐选择"
        elif score >= 70:
            bar = "█" * 14 + "░" * 6
            status = "可以考虑"
        elif score >= 60:
            bar = "█" * 11 + "░" * 9
            status = "谨慎考虑"
        elif score >= 40:
            bar = "█" * 8 + "░" * 12
            status = "不太建议"
        else:
            bar = "█" * 5 + "░" * 15
            status = "不推荐"

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
        if vol.get("type") == "冲":
            if vol.get("probability", 0) < 30:
                risks.append({
                    "level": "warning",
                    "item": f"{vol.get('school')}录取概率过低",
                    "desc": f"录取概率仅{vol.get('probability')}%，需要增加相近备选",
                })

    # 检查学科匹配
    weak_subjects = student_profile.get("weak_subjects", [])
    for vol in volunteer_list:
        required = vol.get("required_subjects", [])
        for subj in required:
            if subj in weak_subjects:
                risks.append({
                    "level": "danger",
                    "item": f"{vol.get('school')}-{vol.get('major')}学科不匹配",
                    "desc": f"该专业需要{subj}，但考生{subj}为弱项",
                })

    # 检查梯度合理性
    types_count = {"冲": 0, "稳": 0, "保": 0}
    for vol in volunteer_list:
        v_type = vol.get("type", "稳")
        types_count[v_type] = types_count.get(v_type, 0) + 1

    total = len(volunteer_list)
    if total > 0:
        if types_count["保"] / total < 0.2:
            risks.append({
                "level": "danger",
                "item": "保底志愿不足",
                "desc": f"保底志愿仅占{types_count['保'] / total * 100:.0f}%，建议至少30%",
            })

    # 生成风险报告
    risk_report = """
┌──────────────────────────────────────────────────────────────────────┐
│              🚦 志愿填报风险检测报告                                  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
"""

    danger_list = [r for r in risks if r["level"] == "danger"]
    warning_list = [r for r in risks if r["level"] == "warning"]

    if danger_list:
        risk_report += (
            "│  🔴 高风险项目（必须修改）：                                        │\n"
        )
        for risk in danger_list:
            risk_report += f"│     ✗ {risk['item']:<30}                            │\n"
            risk_report += f"│       → {risk['desc']:<50}                │\n"
            risk_report += "│                                                                      │\n"

    if warning_list:
        risk_report += (
            "│  🟡 中风险项目（建议调整）：                                        │\n"
        )
        for risk in warning_list:
            risk_report += f"│     ⚠ {risk['item']:<30}                            │\n"
            risk_report += f"│       → {risk['desc']:<50}                │\n"
            risk_report += "│                                                                      │\n"

    if not risks:
        risk_report += (
            "│  🟢 恭喜！未检测到高风险项目，当前方案可以安全填报               │\n"
        )

    risk_report += """│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
"""
    return risk_report, risks


def generate_html_report(student_data, volunteer_list, output_file=None):
    """
    生成HTML可视化报告
    """
    if not HAS_JINJA:
        print("错误: 需要安装 jinja2 才能生成HTML报告")
        print("运行: pip3 install --user jinja2")
        return None

    # 计算雷达图数据
    radar_data = {
        "interest": student_data.get("interest_match", 0),
        "ability": student_data.get("ability_match", 0),
        "employment": student_data.get("employment_match", 0),
        "family": student_data.get("family_match", 0),
    }
    radar_data["average"] = sum(radar_data.values()) / 4

    # HTML模板
    html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>高考志愿填报方案 - {{ name }}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans SC", sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header .subtitle { font-size: 1.2em; opacity: 0.9; }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        .info-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .info-card .label { color: #666; font-size: 0.9em; margin-bottom: 5px; }
        .info-card .value { font-size: 1.5em; font-weight: bold; color: #667eea; }
        .section {
            padding: 40px;
            border-bottom: 1px solid #eee;
        }
        .section:last-child { border-bottom: none; }
        .section-title {
            font-size: 1.8em;
            color: #333;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .chart-container {
            background: #f8f9fa;
            padding: 30px;
            border-radius: 12px;
            margin: 20px 0;
        }
        .school-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        .school-table th, .school-table td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        .school-table th {
            background: #667eea;
            color: white;
        }
        .school-table tr:hover { background: #f8f9fa; }
        .badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
        }
        .badge-red { background: #ffebee; color: #c62828; }
        .badge-yellow { background: #fff3e0; color: #ef6c00; }
        .badge-green { background: #e8f5e9; color: #2e7d32; }
        .heatmap { display: flex; flex-direction: column; gap: 10px; }
        .heat-item {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .heat-bar {
            flex: 1;
            height: 20px;
            background: linear-gradient(90deg, #ff6b6b 0%, #ffd93d 50%, #6bcf7f 100%);
            border-radius: 10px;
            position: relative;
        }
        .heat-marker {
            position: absolute;
            top: -5px;
            width: 30px;
            height: 30px;
            background: #667eea;
            border-radius: 50%;
            transform: translateX(-50%);
            box-shadow: 0 2px 10px rgba(102,126,234,0.5);
        }
        .risk-list { list-style: none; }
        .risk-item {
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .risk-danger { background: #ffebee; border-left: 4px solid #c62828; }
        .risk-warning { background: #fff3e0; border-left: 4px solid #ef6c00; }
        .risk-safe { background: #e8f5e9; border-left: 4px solid #2e7d32; }
        .footer {
            background: #333;
            color: white;
            padding: 30px;
            text-align: center;
        }
        @media print {
            body { background: white; }
            .container { box-shadow: none; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 高考志愿填报方案</h1>
            <p class="subtitle">{{ name }} | {{ province }} | {{ score }}分 | 位次: {{ rank }}</p>
            <p style="margin-top: 10px; opacity: 0.8;">生成时间: {{ generated_at }}</p>
        </div>
        
        <div class="info-grid">
            <div class="info-card">
                <div class="label">考生姓名</div>
                <div class="value">{{ name }}</div>
            </div>
            <div class="info-card">
                <div class="label">高考总分</div>
                <div class="value">{{ score }}分</div>
            </div>
            <div class="info-card">
                <div class="label">全省位次</div>
                <div class="value">{{ rank }}</div>
            </div>
            <div class="info-card">
                <div class="label">综合匹配</div>
                <div class="value">{{ radar.average }}/10</div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">📊 考生画像分析</h2>
            <div class="chart-container">
                <canvas id="radarChart" width="400" height="300"></canvas>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">🎯 志愿方案对比</h2>
            <table class="school-table">
                <thead>
                    <tr>
                        <th>类型</th>
                        <th>院校</th>
                        <th>专业</th>
                        <th>录取概率</th>
                        <th>匹配度</th>
                    </tr>
                </thead>
                <tbody>
                    {% for vol in volunteers %}
                    <tr>
                        <td>
                            {% if vol.type == '冲' %}
                            <span class="badge badge-red">🔴 冲</span>
                            {% elif vol.type == '稳' %}
                            <span class="badge badge-yellow">🟡 稳</span>
                            {% else %}
                            <span class="badge badge-green">🟢 保</span>
                            {% endif %}
                        </td>
                        <td>{{ vol.school }}</td>
                        <td>{{ vol.major }}</td>
                        <td>
                            <div style="background: #eee; border-radius: 10px; overflow: hidden;">
                                <div style="background: linear-gradient(90deg, #ff6b6b, #ffd93d, #6bcf7f); 
                                            height: 20px; width: {{ vol.probability }}%;
                                            display: flex; align-items: center; justify-content: center;
                                            color: white; font-size: 0.8em; font-weight: bold;">
                                    {{ vol.probability }}%
                                </div>
                            </div>
                        </td>
                        <td>{{ vol.match_score }}分</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2 class="section-title">🔥 专业匹配度热力图</h2>
            <div class="heatmap">
                {% for major in majors %}
                <div class="heat-item">
                    <span style="width: 120px; font-weight: bold;">{{ major.name }}</span>
                    <div class="heat-bar">
                        <div class="heat-marker" style="left: {{ major.match_score }}%;"></div>
                    </div>
                    <span style="width: 60px; text-align: right; font-weight: bold;">{{ major.match_score }}%</span>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">🚦 风险检测报告</h2>
            {% if risks %}
            <ul class="risk-list">
                {% for risk in risks %}
                <li class="risk-item {% if risk.level == 'danger' %}risk-danger{% elif risk.level == 'warning' %}risk-warning{% else %}risk-safe{% endif %}">
                    {% if risk.level == 'danger' %}✗{% elif risk.level == 'warning' %}⚠{% else %}✓{% endif %}
                    <div>
                        <strong>{{ risk.item }}</strong>
                        <p style="color: #666; margin-top: 5px;">{{ risk.desc }}</p>
                    </div>
                </li>
                {% endfor %}
            </ul>
            {% else %}
            <div class="risk-item risk-safe">
                ✓ <strong>恭喜！当前方案未检测到高风险，可以安全填报</strong>
            </div>
            {% endif %}
        </div>
        
        <div class="footer">
            <p>© 2026 高考志愿填报智能系统</p>
            <p style="margin-top: 10px; opacity: 0.7;">本报告仅供参考，请以官方信息为准</p>
        </div>
    </div>
    
    <script>
        // 雷达图
        const ctx = document.getElementById('radarChart').getContext('2d');
        new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['兴趣匹配', '能力匹配', '就业匹配', '家庭适配'],
                datasets: [{
                    label: '匹配度',
                    data: [{{ radar.interest }}, {{ radar.ability }}, {{ radar.employment }}, {{ radar.family }}],
                    backgroundColor: 'rgba(102, 126, 234, 0.2)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(102, 126, 234, 1)',
                    pointSize: 6
                }]
            },
            options: {
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20
                        }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    </script>
</body>
</html>"""

    template = Template(html_template)

    # 准备数据
    majors = [
        {"name": vol["major"], "match_score": vol["match_score"]}
        for vol in volunteer_list
    ]
    _, risks = detect_risks(student_data, volunteer_list)

    html_content = template.render(
        name=student_data.get("name", "考生"),
        province=student_data.get("province", "未知"),
        score=student_data.get("score", 0),
        rank=student_data.get("rank", 0),
        radar=radar_data,
        volunteers=volunteer_list,
        majors=majors,
        risks=risks,
        generated_at=datetime.now().strftime("%Y年%m月%d日 %H:%M"),
    )

    # 保存HTML
    if output_file is None:
        output_file = f"/tmp/gaokao_report_{student_data.get('name', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✓ HTML报告已生成: {output_file}")
    return output_file


def generate_pdf_from_html(html_file, pdf_file=None):
    """
    将HTML转换为PDF
    """
    if not HAS_WEASYPRINT:
        print("错误: 需要安装 weasyprint 才能生成PDF")
        print("运行: pip3 install --user weasyprint")
        return None

    if pdf_file is None:
        pdf_file = html_file.replace(".html", ".pdf")

    try:
        HTML(filename=html_file).write_pdf(pdf_file)
        print(f"✓ PDF报告已生成: {pdf_file}")
        return pdf_file
    except Exception as e:
        print(f"✗ PDF生成失败: {e}")
        return None


def generate_visual_report(student_data, volunteer_list, output_format="all"):
    """
    生成完整可视化报告（支持多种格式）

    参数:
        student_data: 考生数据
        volunteer_list: 志愿列表
        output_format: 输出格式 ('md', 'html', 'pdf', 'all')

    返回:
        生成的文件路径列表
    """
    results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"gaokao_report_{student_data.get('name', 'unknown')}_{timestamp}"

    # 1. 生成Markdown报告
    if output_format in ["md", "all"]:
        md_content = f"""# 高考志愿填报方案报告

**生成时间**: {datetime.now().strftime("%Y年%m月%d日 %H:%M")}  
**考生姓名**: {student_data.get("name", "考生")}  
**考生省份**: {student_data.get("province", "未知")}  
**高考总分**: {student_data.get("score", 0)}分  
**全省位次**: {student_data.get("rank", 0)}名  

---

## 一、考生画像雷达图

"""
        radar_chart, weighted_score, scores = generate_student_radar(student_data)
        md_content += radar_chart
        md_content += f"\n**综合匹配指数**: {weighted_score:.1f}/10\n\n"

        md_content += "## 二、志愿方案可视化对比\n\n"
        md_content += generate_school_comparison(volunteer_list)

        md_content += "## 三、专业匹配度热力图\n\n"
        majors = [
            {"name": vol["major"], "match_score": vol["match_score"]}
            for vol in volunteer_list
        ]
        md_content += generate_major_heatmap(majors)

        md_content += "## 四、风险检测报告\n\n"
        risk_report, _ = detect_risks(student_data, volunteer_list)
        md_content += risk_report

        md_file = f"/tmp/{base_name}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"✓ Markdown报告已生成: {md_file}")
        results.append(md_file)

    # 2. 生成HTML报告
    html_file = None
    if output_format in ["html", "pdf", "all"]:
        html_file = f"/tmp/{base_name}.html"
        html_file = generate_html_report(student_data, volunteer_list, html_file)
        if html_file:
            results.append(html_file)

    # 3. 生成PDF报告
    if output_format in ["pdf", "all"] and html_file:
        pdf_file = f"/tmp/{base_name}.pdf"
        pdf_file = generate_pdf_from_html(html_file, pdf_file)
        if pdf_file:
            results.append(pdf_file)

    return results


# 示例使用
if __name__ == "__main__":
    # 示例考生数据
    student = {
        "name": "李明",
        "province": "浙江省",
        "score": 612,
        "rank": 15230,
        "interest_match": 85,
        "ability_match": 90,
        "employment_match": 88,
        "family_match": 95,
        "weak_subjects": ["化学", "语文"],
    }

    # 示例志愿列表
    volunteers = [
        {
            "school": "浙江大学",
            "major": "计算机类",
            "type": "冲",
            "probability": 35,
            "match_score": 95,
            "required_subjects": ["数学", "物理"],
        },
        {
            "school": "杭州电子科技大学",
            "major": "计算机类",
            "type": "稳",
            "probability": 70,
            "match_score": 92,
            "required_subjects": ["数学", "物理"],
        },
        {
            "school": "浙江工业大学",
            "major": "软件工程",
            "type": "稳",
            "probability": 80,
            "match_score": 88,
            "required_subjects": ["数学"],
        },
        {
            "school": "浙江理工大学",
            "major": "软件工程",
            "type": "保",
            "probability": 95,
            "match_score": 82,
            "required_subjects": ["数学"],
        },
    ]

    print("=" * 60)
    print("高考志愿填报可视化报告生成器 V2.0")
    print("=" * 60)
    print()

    # 生成所有格式
    files = generate_visual_report(student, volunteers, output_format="all")

    print()
    print("=" * 60)
    print("生成完成！文件列表：")
    print("=" * 60)
    for f in files:
        print(f"  • {f}")
    print()
    print("提示：")
    print("  • HTML文件可直接在浏览器中打开")
    print("  • PDF文件可直接打印或分享")
    print("  • Markdown文件可编辑和转换")
