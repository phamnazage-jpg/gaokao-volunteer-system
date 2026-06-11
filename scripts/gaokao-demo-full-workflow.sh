#!/bin/bash
# 高考志愿填报完整流程演示脚本
# 收集 → 解析 → 生成报告

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                                                                   ║"
echo "║          🎓 高考志愿填报智能系统 - 完整流程演示                   ║"
echo "║                                                                   ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# 步骤1：展示问卷
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 步骤1：发送问卷给考生"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "复制以下内容发送给考生："
echo ""
python3 ~/.local/bin/gaokao-quick-3min.py

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📥 步骤2：等待用户回复并解析"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 创建示例用户回复
cat > /tmp/sample_response.txt << 'EOF'
1. 李明
2. 浙江
3. 612
4. 15230
5. R
6. 物理、数学
7. C
8. ③
9. ①
10. ②
EOF

echo "【用户回复示例】："
cat /tmp/sample_response.txt

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 步骤3：自动解析信息"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 << 'PYTHON_EOF'
import sys
sys.path.insert(0, '/home/long/.local/bin')
exec(open('/home/long/.local/bin/gaokao-quick-3min.py').read())

with open('/tmp/sample_response.txt', 'r') as f:
    user_input = f.read()

info = parse_quick_response(user_input)
summary = generate_quick_summary(info)
recommendation = generate_quick_recommendation(info)

print(summary)
print()
print(recommendation)
PYTHON_EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎨 步骤4：生成可视化报告"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 << 'PYTHON_EOF'
import sys
sys.path.insert(0, '/home/long/.local/bin')
exec(open('/home/long/.local/bin/gaokao-visual-report-v2.py').read())

student_data = {
    'name': '李明',
    'province': '浙江',
    'score': 612,
    'rank': 15230,
    'interest_match': 85,
    'ability_match': 90,
    'employment_match': 88,
    'family_match': 80
}

volunteer_list = [
    {'school': '浙江大学', 'major': '计算机类', 'type': '冲', 'probability': 35, 'match_score': 95, 'required_subjects': ['数学', '物理']},
    {'school': '杭州电子科技大学', 'major': '计算机类', 'type': '稳', 'probability': 70, 'match_score': 92, 'required_subjects': ['数学', '物理']},
    {'school': '浙江工业大学', 'major': '软件工程', 'type': '稳', 'probability': 80, 'match_score': 88, 'required_subjects': ['数学']},
    {'school': '浙江理工大学', 'major': '软件工程', 'type': '保', 'probability': 95, 'match_score': 82, 'required_subjects': ['数学']},
    {'school': '中国计量大学', 'major': '自动化', 'type': '保', 'probability': 98, 'match_score': 78, 'required_subjects': ['数学']}
]

files = generate_visual_report(student_data, volunteer_list, output_format='all')

print("✅ 报告已生成：")
for f in files:
    import os
    size = os.path.getsize(f)
    print(f"  📄 {f} ({size/1024:.1f} KB)")

# 复制到示例目录
import shutil
for f in files:
    dest = f"/home/long/Documents/高考志愿报告/示例/{os.path.basename(f)}"
    shutil.copy(f, dest)
    print(f"  ✓ 已复制到: {dest}")
PYTHON_EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 流程完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "完整流程："
echo "  1️⃣  发送问卷（3分钟）"
echo "  2️⃣  用户填写回复"
echo "  3️⃣  自动解析信息"
echo "  4️⃣  生成初步建议"
echo "  5️⃣  生成可视化报告（HTML/PDF/Markdown）"
echo ""
echo "📁 生成的报告位置："
echo "  ~/Documents/高考志愿报告/示例/"
echo ""
echo "💡 可直接在浏览器中打开 HTML 报告查看效果"
echo ""
