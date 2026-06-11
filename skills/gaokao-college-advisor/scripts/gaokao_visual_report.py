#!/usr/bin/env python3
"""
高考志愿填报可视化报告生成器 V2.0
支持 Markdown/HTML/PDF 多格式导出
用法: python3 gaokao_visual_report.py [student_data.json]
"""

import json
import sys
from pathlib import Path

# 导入主生成逻辑
from gaokao_visual_report_v2 import generate_visual_report

def main():
    if len(sys.argv) < 2:
        print("用法: python3 gaokao_visual_report.py <student_data.json>")
        print("生成示例: python3 gaokao_visual_report.py --demo")
        sys.exit(1)
    
    if sys.argv[1] == '--demo':
        # 使用示例数据
        student = {
            'name': '李明',
            'province': '浙江省',
            'score': 612,
            'rank': 15230,
            'interest_match': 85,
            'ability_match': 90,
            'employment_match': 88,
            'family_match': 95,
            'weak_subjects': ['化学', '语文']
        }
        volunteers = [
            {'school': '浙江大学', 'major': '计算机类', 'type': '冲', 'probability': 35, 'match_score': 95, 'required_subjects': ['数学', 'physical']},
            {'school': '杭州电子科技大学', 'major': '计算机类', 'type': '稳', 'probability': 70, 'match_score': 92, 'required_subjects': ['数学', 'physical']},
        ]
    else:
        # 从JSON文件加载
        with open(sys.argv[1], 'r') as f:
            data = json.load(f)
            student = data['student']
            volunteers = data['volunteers']
    
    files = generate_visual_report(student, volunteers, output_format='all')
    
    print("\n✓ 生成完成:")
    for f in files:
        print(f"  • {f}")

if __name__ == '__main__':
    main()
