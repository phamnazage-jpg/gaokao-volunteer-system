# 使用教程

## 🎯 这个文档写给谁

- 第一次接触本系统的用户
- 想深入了解功能的开发者
- 需要快速找到某个功能的人

## 📚 文档导航

### 🚀 快速上手

- [README.md](../README.md) - 项目总览（**先看这个**）
- [快速使用指南](#快速使用指南) - 5分钟上手

### 📖 深入使用

- [Skills使用](#skills使用) - 3个Skill详细用法
- [脚本使用](#脚本使用) - 命令行工具
- [可视化报告](#可视化报告) - 生成HTML/PDF

### 🏗️ 开发相关

- [开发指南](DEVELOPMENT.md) - 如何贡献
- [架构设计](ARCHITECTURE.md) - 系统架构
- [API参考](#api参考) - 脚本API

### 📋 规范参考

- [错误模式库](../rules/errors/ERRORS.md) - 15种错误
- [省份规则](../rules/provinces.md) - 省份规则索引与真相源入口
- [测试用例](#测试用例) - 验证方法

### 📝 案例与优化

- [真实案例](case-studies/) - 实际使用案例
- [优化日志](optimization-log/) - 改进过程
- [变更日志](../CHANGELOG.md) - 版本历史

---

## 🚀 快速使用指南

### 1. 在Hermes对话中（最简单）

```
# 加载Skill
/skill gaokao-college-advisor

# 然后正常对话
"我是一名湖南考生，578分，物理+化学+生物选科"

# AI会引导你：
# 1. 兴趣测评（霍兰德测试）
# 2. 学科评估
# 3. 家庭情况
# 4. 生成方案

# 然后检查
/skill gaokao-spec-checker
"请检查这个方案..."
```

### 2. 使用命令行（生成报告）

```bash
# 步骤1：信息收集
python3 ~/.local/bin/gaokao-quick-3min.py
# 显示问卷模板

# 步骤2：保存问卷回复到文件
# （用户在对话中完成）

# 步骤3：生成报告
python3 ~/.local/bin/gaokao-visual-report-v2.py
# 输出：HTML + PDF + Markdown

# 步骤4：规范检查
python3 ~/.local/bin/gaokao-checker plan.txt
# 输出：检查报告
```

### 3. 演示完整流程

```bash
bash ~/.local/bin/gaokao-demo-full-workflow.sh
# 自动演示：
# 1. 显示问卷
# 2. 模拟用户回复
# 3. 生成报告
# 4. 输出文件
```

---

## 🤖 Skills使用

### gaokao-college-advisor（方案生成）

**作用**：根据考生信息生成个性化志愿方案

**特点**：

- 基于霍兰德职业兴趣测试
- 考虑学科优劣势
- 物理+化学+生物 选科专业覆盖
- 数据基于2025年位次

**使用流程**：

```
1. 加载Skill
2. 提供基本信息（省份/分数/选科）
3. 回答兴趣测评（5个问题）
4. 回答学科评估
5. 等待方案生成
6. 检查方案（用 spec-checker）
```

### gaokao-spec-checker（规范检查）

**作用**：自动检查志愿方案是否符合本省最新政策

**特点**：

- 支持27个省份自动识别
- 检测8+种常见错误
- 输出致命/严重/警告三级分类
- 提供具体修正建议

**使用场景**：

- 生成方案后立即检查
- 填报前最终核对
- 用户咨询时验证方案

### zhangxuefeng-skillset（张雪峰风格）

**作用**：以张雪峰的风格推荐志愿

**特点**：

- 直接、接地气
- 注重就业导向
- 强调"普通家庭"视角
- 避免"高大上"陷阱

**适用用户**：

- 偏好张雪峰推荐风格
- 普通家庭考生
- 重视就业前景

---

## 🛠️ 脚本使用

### gaokao-checker（规范检查）

```bash
# 基本用法
python3 ~/.local/bin/gaokao-checker plan.txt

# 指定省份
python3 ~/.local/bin/gaokao-checker plan.txt 浙江

# 完整工作流演示
bash ~/.local/bin/gaokao-demo-full-workflow.sh
```

**输出**：自动检测省份，输出针对性检查报告

### gaokao-visual-report-v2.py（可视化）

```bash
# 直接运行（使用示例数据）
python3 ~/.local/bin/gaokao-visual-report-v2.py
# 输出：/tmp/gaokao_report_*.html/pdf/md
```

**修改示例数据**：编辑脚本底部的 `student_data` 和 `volunteer_list`

### gaokao-quick-3min.py（问卷）

```bash
# 显示问卷
python3 ~/.local/bin/gaokao-quick-3min.py
```

**特点**：

- 1分钟极速版（5个问题）
- 3分钟快速版（10个问题）
- 包含霍兰德类型速查表

### gaokao-collect-info.py（7步完整收集）

```bash
# 启动交互式收集
python3 ~/.local/bin/gaokao-collect-info.py
```

**特点**：

- 7步分步引导
- 实时输入验证
- 自动保存为JSON

---

## 📊 可视化报告

### 报告类型

#### HTML报告

- **优点**：精美、可分享、有交互
- **用途**：手机/平板查看、分享链接
- **大小**：约15KB

#### PDF报告

- **优点**：可打印、格式固定
- **用途**：存档、提交
- **大小**：约300KB

#### Markdown报告

- **优点**：可编辑、可转换
- **用途**：二次加工
- **大小**：约8KB

### 报告内容

1. **考生画像雷达图** - 四维度匹配度
2. **院校对比决策表** - 冲稳保可视化
3. **专业匹配度热力图** - 颜色编码
4. **风险检测报告** - 红绿灯警示

---

## 📋 错误模式库

15种已识别错误（详见 `rules/errors/ERRORS.md`）：

### 致命错误（5种）

- E001: 志愿单位错误
- E002: 调剂范围错误
- E003: 投档后规则错误
- E004: 征集志愿次数错误
- E005: 模式错误

### 严重错误（5种）

- S001: 主观概率
- S002: 选科要求一刀切
- S003: 位次数据年份错误
- S004: 2026年位次未说明
- S005: 未提及模式概念

### 一般警告（5种）

- W001: 体检要求缺失
- W002: 专业代码缺失
- W003: 院校代码缺失
- W004: 数据来源未标注
- W005: 风险提示缺失

---

## 🧪 测试用例

### 标准测试

#### 湖南方案（错误版）

```python
plan = """
湖南578分考生志愿方案
本次共填报45个学校志愿：
志愿01：江西财经大学，会计学
录取概率35%
"""
# 应检测出：致命错误
```

#### 湖南方案（修正版）

```python
plan = """
湖南2026高考志愿填报方案（578分）
本次共填报45个院校专业组志愿...
每组最多6个专业+1个组内专业服从...
"""
# 应通过基础检查
```

#### 浙江方案（专业+学校）

```python
plan = """
浙江省，630分
本次共填报80个专业+学校志愿：
每个志愿填1个专业。
"""
# 应识别为"专业+学校"模式
```

### 自动测试

```bash
# 添加测试用例到 tests/cases/
# 编写测试脚本 tests/test_all.py
python3 tests/test_all.py
```

---

## ❓ 常见问题

### Q1：哪个Skill应该先加载？

A：先 `gaokao-college-advisor` 生成方案，再用 `gaokao-spec-checker` 检查。

### Q2：报告生成失败怎么办？

A：检查是否安装了 weasyprint（PDF需要）和 jinja2（HTML需要）。

### Q3：找不到我的省份？

A：当前支持27个省份。如需添加新省份，编辑 `PROVINCE_RULES` 字典。

### Q4：方案被打回怎么办？

A：检查致命错误，优先修正。然后严重错误，最后警告。

### Q5：可以批量处理多个考生吗？

A：可以，参考 `gaokao-visual-report-v2.py` 中的 `student_data` 字典结构，编写循环脚本。

---

## 📞 获取帮助

- **文档**：本目录
- **案例**：`docs/case-studies/`
- **优化**：`docs/optimization-log/`
- **变更**：`CHANGELOG.md`

---

**版本**：v2.0  
**最后更新**：2026-06-11
