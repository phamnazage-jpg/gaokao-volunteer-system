# 开发指南

## 🎯 项目目标

为高考考生提供**专业、准确、规范化**的志愿填报辅助。

## 🚀 快速开始

### 场景1：在Hermes对话中使用（推荐）

```
/skill gaokao-college-advisor
"我是湖南考生，578分..."

# 生成方案后立即检查
/skill gaokao-spec-checker
"请检查这个方案..."
```

### 场景2：命令行使用

```bash
# 1. 信息收集（3分钟问卷）
python3 ~/.local/bin/gaokao-quick-3min.py

# 2. 生成可视化报告
python3 ~/.local/bin/gaokao-visual-report-v2.py

# 3. 规范检查
python3 ~/.local/bin/gaokao-checker plan.txt

# 4. 完整流程演示
bash ~/.local/bin/gaokao-demo-full-workflow.sh
```

### 场景3：项目开发

```bash
# 进入项目
cd /home/long/projects/gaokao-volunteer-system

# 提交变更
git add .
git commit -m "feat: 新增功能"

# 同步到Hermes
cp skills/gaokao-spec-checker/scripts/spec_checker_v2.py \
   ~/.hermes/skills/gaokao-spec-checker/scripts/
```

## 🏗️ 架构

### 分层架构

```
┌─────────────────┐
│  用户对话层     │  Hermes Skills
├─────────────────┤
│  业务逻辑层     │  Python脚本
├─────────────────┤
│  数据规则层     │  rules/ 目录
├─────────────────┤
│  持久化层       │  docs/, data/
└─────────────────┘
```

### 核心组件

1. **gaokao-college-advisor** - 方案生成
2. **gaokao-spec-checker** - 规范检查
3. **zhangxuefeng-skillset** - 风格化推荐
4. **独立脚本** - 数据处理、可视化
5. **规则库** - 省份、年度、错误规则

## 📝 开发规范

### 代码规范

- Python 3.10+（使用类型提示）
- 遵循 PEP 8
- 函数和类必须有 docstring
- 关键逻辑添加中文注释

### 命名规范

- 目录：lowercase-hyphen
- 文件：lowercase_underscore 或 lowercase-hyphen
- 类：PascalCase
- 函数/变量：snake_case

### 提交规范

```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 格式调整
refactor: 重构
test: 测试
chore: 构建/工具变更
```

## 🧪 测试

### 手动测试

```bash
# 1. 测试湖南方案
python3 ~/.local/bin/gaokao-checker tests/cases/hunan-578.md

# 2. 测试浙江方案
python3 ~/.local/bin/gaokao-checker tests/cases/zhejiang-630.md
```

### 测试用例位置

- `tests/cases/` - 各省测试用例
- 每省至少1个标准用例
- 至少1个错误用例（用于验证检测能力）

## 📦 部署

### 同步到Hermes

```bash
# Skills
cp -r skills/gaokao-college-advisor/ ~/.hermes/skills/
cp -r skills/gaokao-spec-checker/ ~/.hermes/skills/
cp -r skills/zhangxuefeng-skillset/ ~/.hermes/skills/

# 脚本
cp scripts/gaokao-checker ~/.local/bin/
cp scripts/gaokao-visual-report-v2.py ~/.local/bin/
```

### 部署检查清单

- [ ] 所有技能可用（`/skill`命令加载）
- [ ] 脚本可执行（`chmod +x`）
- [ ] 路径正确（`which gaokao-checker`）
- [ ] 测试通过
- [ ] 文档更新

## 🐛 调试

### 常见问题

1. **Skill不加载** → 检查 SKILL.md frontmatter
2. **脚本不执行** → 检查 `chmod +x`
3. **检查器报错** → 检查省份是否在 PROVINCE_RULES

### 调试工具

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 参考资料

- 阳光高考：https://gaokao.chsi.com.cn/
- 湖南省教育考试院：http://jyt.hunan.gov.cn/
- 各省2026年高考政策文件

## 🤝 贡献指南

### 贡献方式

1. 发现错误 → 添加到 `rules/errors/ERRORS.md`
2. 优化方案 → 更新对应Skill
3. 添加省份 → 扩展 `PROVINCE_RULES`
4. 真实案例 → 记录到 `docs/case-studies/`

### 贡献流程

1. 修改文件
2. 运行测试
3. 提交（`git commit`）
4. 同步到Hermes
5. 记录到 `CHANGELOG.md`

---

**版本**：v2.0  
**最后更新**：2026-06-11
