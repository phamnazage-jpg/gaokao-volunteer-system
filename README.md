# 高考志愿填报智能系统

[![CI](https://github.com/phamnazage-jpg/gaokao-volunteer-system/actions/workflows/ci.yml/badge.svg)](https://github.com/phamnazage-jpg/gaokao-volunteer-system/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/phamnazage-jpg/gaokao-volunteer-system/graph/badge.svg)](https://codecov.io/gh/phamnazage-jpg/gaokao-volunteer-system)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)

> 一套完整的、专业的、可扩展的高考志愿填报辅助系统

## 📋 项目简介

本项目旨在为高考考生提供**专业、准确、规范化**的志愿填报辅助，包括：

- 方案生成（基于霍兰德兴趣模型 + 学科评估 + 个性化推荐）
- 方案检查（基于各省2026年最新政策规范的自动检查）
- 可视化报告（HTML/PDF/Markdown多格式输出）
- 信息收集（1分钟/3分钟/7步三套问卷）
- 多省份支持（已支持27个省份自动适配）

## 🏗️ 目录结构

```
gaokao-volunteer-system/
├── README.md                 # 本文件（项目说明）
├── CHANGELOG.md              # 变更日志
│
├── docs/                     # 文档
│   ├── versions/             # 版本历史
│   ├── case-studies/         # 真实案例研究
│   └── optimization-log/     # 优化过程记录
│
├── rules/                    # 规则库
│   ├── provinces/            # 省份规则（按省份）
│   ├── years/                # 年度规则（按年份）
│   └── errors/               # 错误模式库
│
├── skills/                   # Hermes Skills
│   ├── gaokao-college-advisor/   # 高考志愿填报顾问
│   ├── gaokao-spec-checker/      # 规范检查员
│   └── zhangxuefeng-skillset/    # 张雪峰风格
│
├── scripts/                  # 独立脚本
│   ├── gaokao-visual-report-v2.py    # 可视化报告V2
│   ├── gaokao-quick-3min.py          # 3分钟问卷
│   ├── gaokao-collect-info.py        # 完整收集
│   ├── gaokao-checker                # 规范检查（多省份）
│   └── legacy/                       # 历史版本
│
├── data/                     # 数据
│   ├── templates/            # 模板
│   └── examples/             # 示例
│
└── tests/                    # 测试
    └── cases/                # 测试用例
```

## 🎯 核心组件

### 1. gaokao-college-advisor（方案生成）

- **功能**：基于考生信息生成志愿填报方案
- **特点**：霍兰德兴趣测试 + 个性化匹配 + 2025年位次数据
- **位置**：`skills/gaokao-college-advisor/`

### 2. gaokao-spec-checker（方案检查）

- **功能**：自动检查志愿方案是否符合本省最新政策
- **特点**：多省份自动适配 + 致命/严重/警告三级分类
- **位置**：`skills/gaokao-spec-checker/`
- **已支持**：27个省份（详见 `rules/provinces/`）

### 3. zhangxuefeng-skillset（张雪峰风格）

- **功能**：以张雪峰风格推荐志愿
- **特点**：直接、接地气、注重就业导向
- **位置**：`skills/zhangxuefeng-skillset/`

### 4. 独立脚本（可选补充）

- **gaokao-visual-report-v2.py**：生成HTML/PDF/MD报告
- **gaokao-quick-3min.py**：3分钟快速问卷
- **gaokao-collect-info.py**：7步完整收集
- **gaokao-checker**：多省份规范检查

## 🚀 快速开始

### 在Hermes对话中使用（推荐）

```
/skill gaokao-college-advisor
# 生成方案

/skill gaokao-spec-checker
# 检查方案
```

### 命令行使用

```bash
# 规范检查
python3 ~/.local/bin/gaokao-checker plan.txt

# 生成报告
python3 ~/.local/bin/gaokao-visual-report-v2.py

# 显示问卷
python3 ~/.local/bin/gaokao-quick-3min.py
```

## 📊 已支持省份

| 模式       | 省份数 | 列表                                                                                 |
| ---------- | :----: | ------------------------------------------------------------------------------------ |
| 院校专业组 |   14   | 湖南、广东、湖北、安徽、江西、甘肃、黑龙江、江苏、福建、广西、北京、上海、天津、海南 |
| 专业+学校  |   8    | 浙江、山东、河北、重庆、辽宁、贵州、青海、吉林                                       |
| 传统       |   5    | 河南、四川、新疆、云南、西藏                                                         |

**总计27省，可自动识别省份并加载对应规则**

## 📝 开发规范

### 代码规范

- Python：PEP 8 + 中文注释
- Markdown：清晰标题层次
- 命名：lowercase-hyphen 或 lowercase_underscore

### 文档规范

- 每个组件有 README
- 关键决策记录到 `docs/case-studies/`
- 优化过程记录到 `docs/optimization-log/`
- 错误模式记录到 `rules/errors/`

### 测试规范

- 每个新功能要有测试用例
- 测试用例放在 `tests/cases/`
- 错误模式要加入 `rules/errors/`

## 🔄 持续优化

### 优化日志

详见 `docs/optimization-log/`，记录每次优化的：

- 优化点
- 改进效果
- 用户反馈
- 后续计划

### 已知不足

- 27省中的部分规则可能不准确
- 2026年招生计划待官方公布
- 部分省份特殊批次未覆盖
- 算法精度有待提高

### 未来规划

详见 `docs/optimization-log/future-plan.md`

## 📚 相关资源

- 阳光高考：https://gaokao.chsi.com.cn/
- 湖南省教育考试院：http://jyt.hunan.gov.cn/jyt/sjyt/hnsjyksy/
- 各省教育考试院（详见各省份规则文档）

## 📄 版权信息

本项目为个人开发项目，仅供学习参考使用。

实际志愿填报请以**各省教育考试院**官方信息为准。

---

**生成时间**：2026年6月11日  
**当前版本**：v2.0
