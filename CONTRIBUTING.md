# 贡献指南

感谢您对高考志愿填报项目的关注！我们欢迎任何形式的贡献。

---

## 🤝 如何贡献

### 1. 发现新问题

- 在真实咨询中发现新的错误模式
- 提出流程优化建议
- 报告Bug

### 2. 改进现有功能

- 修复已知Bug
- 优化算法
- 完善文档

### 3. 添加新功能

- 增加省份支持
- 添加新检查规则
- 开发新工具

### 4. 分享经验

- 记录真实案例
- 总结优化经验
- 编写教程

---

## 📋 贡献流程

### 步骤1：Fork项目（或本地分支）

```bash
# 创建分支
git checkout -b feature/你的功能名称

# 或
git checkout -b fix/bug描述
```

### 步骤2：进行修改

#### 如果是修复错误模式

```bash
# 1. 编辑错误模式库
nano rules/errors/ERRORS.md

# 2. 添加测试用例
cp tests/cases/template.md tests/cases/你的测试.md

# 3. 更新规则文件
# 修改 skills/gaokao-spec-checker/scripts/spec_checker_v2.py

# 4. 添加测试
# 修改 tests/test_all.py
```

#### 如果是优化Skill

```bash
# 1. 编辑Skill文件
nano skills/gaokao-college-advisor/SKILL.md

# 2. 更新案例
cp skills/gaokao-college-advisor/cases/TEMPLATE.md \
   skills/gaokao-college-advisor/cases/新案例.md

# 3. 运行测试
python3 tests/test_all.py
```

### 步骤3：提交更改

```bash
# 查看修改
git status

# 添加文件
git add .

# 提交（遵循提交规范）
git commit -m "fix: 修复XXX错误模式

- 问题：XXX
- 原因：XXX
- 修复：XXX
- 测试：新增测试用例test_xxx"
```

### 步骤4：同步到项目

```bash
# 切换到主分支
git checkout main

# 合并分支
git merge feature/你的功能名称

# 推送（如果有远程）
git push origin main
```

---

## 📝 提交规范

### 提交类型

| 类型       | 用途     | 示例                     |
| ---------- | -------- | ------------------------ |
| `feat`     | 新功能   | `feat: 新增山东规则`     |
| `fix`      | Bug修复  | `fix: 修正浙江模式检测`  |
| `docs`     | 文档更新 | `docs: 更新README`       |
| `style`    | 代码格式 | `style: 格式化Python`    |
| `refactor` | 重构     | `refactor: 优化检查逻辑` |
| `test`     | 测试相关 | `test: 新增湖南测试用例` |
| `chore`    | 其他     | `chore: 更新gitignore`   |

### 提交信息格式

```
<类型>: <简短描述>

<详细说明（可选）>

- <变更点1>
- <变更点2>
- <测试情况>
```

### 示例

```bash
# 好的提交
git commit -m "feat: 新增山西规则支持

- 添加山西省到PROVINCE_RULES
- 包含院校专业组模式45个志愿
- - - - - - - - - - - - - - - - - - -
测试：本地测试通过
数据：待官方核实"

# 不好的提交
git commit -m "修改了一些内容"
```

---

## 🎯 贡献类型详解

### 添加新省份

1. **编辑规则文件**

   ```python
   # skills/gaokao-spec-checker/scripts/spec_checker_v2.py
   PROVINCE_RULES["新省份"] = {
       "mode": "院校专业组",
       "max_volunteers": 45,
       "max_majors_per_group": 6,
       ...
   }
   ```

2. **添加文档**

   ```markdown
   # rules/provinces/新省份.md

   ## 山西省2026年高考规则

   - 志愿数：45个
   - 模式：院校专业组
     ...
   ```

3. **添加测试**

   ```python
   # tests/cases/新省份-XXX.md
   - 标准方案
   - 错误方案
   ```

4. **更新说明**
   - [ ] CHANGELOG.md
   - [ ] README.md（省份列表）

### 发现新错误模式

1. **记录错误**

   ```markdown
   # rules/errors/ERRORS.md

   ### E###：<错误名称>

   - **症状**：<描述>
   - **正确**：<应该是>
   - **场景**：<何时出现>
   - **修复**：<如何修正>
   - **首次发现**：YYYY-MM-DD
   - **报告人**：@用户名
   ```

2. **更新检查器**（如果需要代码检测）

   ```python
   # skills/gaokao-spec-checker/scripts/spec_checker_v2.py
   # 在_check_xxx方法中添加检测逻辑
   ```

3. **添加测试**
   ```python
   # 在tests/test_all.py中添加测试函数
   ```

### 真实案例

1. **复制模板**

   ```bash
   cp docs/case-studies/TEMPLATE.md \
      docs/case-studies/case-###.md
   ```

2. **填写案例**

   ```markdown
   ## 案例###：<简述>

   **咨询时间**：YYYY-MM-DD

   **用户信息**：...
   **方案生成**：...
   **后续动作**：...
   **教训总结**：...
   ```

---

## 🧪 测试要求

### 提交前必须

- [ ] 所有自动化测试通过
- [ ] 手动测试通过
- [ ] 文档已更新
- [ ] 提交信息符合规范

### 运行测试

```bash
# 全部测试
python3 tests/test_all.py

# 单省份测试
python3 skills/gaokao-spec-checker/scripts/spec_checker_v2.py

# 手动验证
python3 ~/.local/bin/gaokao-checker tests/cases/hunan-578.md
```

---

## 🎨 代码规范

### Python规范

- 遵循 PEP 8
- 函数必须有 docstring
- 关键逻辑添加中文注释
- 类型提示（Python 3.10+）

### Markdown规范

- 标题层次清晰
- 表格对齐
- 代码块标注语言

### 命名规范

- 目录：`lowercase-hyphen`
- 文件：`lowercase_underscore` 或 `lowercase-hyphen`
- 类：`PascalCase`
- 函数/变量：`snake_case`

---

## 📞 联系方式

### 报告问题

- 在文件中记录错误模式
- 提交PR修复
- 更新FAQ

### 讨论功能

- 在优化日志中记录
- 更新未来规划
- 提交讨论Issue

---

## 📜 行为准则

### 我们欢迎

- ✅ 建设性的批评
- ✅ 真诚的建议
- ✅ 真实的案例
- ✅ 严谨的态度

### 我们不接受

- ❌ 人身攻击
- ❌ 虚假信息
- ❌ 不专业的态度
- ❌ 数据造假

---

## 🏆 贡献者荣誉

### 贡献类型

| 类型     | 说明           | 标记 |
| -------- | -------------- | ---- |
| 错误发现 | 发现新错误模式 | 🔍   |
| 代码贡献 | 修复Bug/新功能 | 💻   |
| 文档编写 | 完善文档       | 📝   |
| 案例分享 | 真实咨询案例   | 📖   |
| 测试验证 | 测试和验证     | ✅   |

---

**感谢每一位贡献者！**

---

**版本**: v2.0  
**最后更新**: 2026-06-11
