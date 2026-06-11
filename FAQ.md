# 常见问题

## 🔍 通用问题

### Q1: 这个项目是做什么的？

**A**: 这是一个高考志愿填报辅助系统，包括：

- 4个Hermes Skills（顾问、检查员、龙老师、张雪峰风格）
- 27个省份自动适配
- 可视化报告生成
- 自动规范检查

### Q2: 适合什么人群？

**A**:

- ✅ 2026届高考考生和家长
- ✅ 需要专业志愿规划的普通家庭
- ✅ 数据敏感型决策者
- ✅ Hermes用户

### Q3: 和张雪峰老师的关系？

**A**:

- 我们有专门的 `zhangxuefeng-skillset` 模仿他的风格
- 我们还有 `gaokao-counselor-long`（龙老师），是"张雪峰思路+AI技术"的融合

---

## 🛠️ 安装问题

### Q4: 如何安装？

**A**: 详见 [INSTALL.md](INSTALL.md)

快速路径：

```bash
# Skills已在 ~/.hermes/skills/
# 脚本已在 ~/.local/bin/
```

### Q5: 需要哪些Python包？

**A**:

```bash
pip3 install --user --break-system-packages \
    weasyprint jinja2 markdown
```

### Q6: 安装失败怎么办？

**A**:

1. 检查Python版本（>= 3.10）
2. 使用 `--user` 参数避免权限问题
3. 或使用虚拟环境
4. 查看 [INSTALL.md#常见问题](INSTALL.md#常见问题)

---

## 🏃 使用问题

### Q7: 如何在Hermes中使用？

**A**:

```
# 加载技能
/skill gaokao-counselor-long

# 然后对话
"我是湖南考生，578分..."
```

### Q8: 如何命令行使用？

**A**:

```bash
# 规范检查
gaokao-checker plan.txt

# 生成报告
python3 ~/.local/bin/gaokao-visual-report-v2.py

# 显示问卷
python3 ~/.local/bin/gaokao-quick-3min.py
```

### Q9: 支持哪些省份？

**A**: 共27个省

- 院校专业组模式：湖南、广东、湖北等14省
- 专业+学校模式：浙江、山东、河北等8省
- 传统模式：河南、四川、新疆等5省

详见 [rules/provinces.md](rules/provinces.md)

### Q10: 数据准确吗？

**A**:

- 基于2025年实际录取位次
- 2026年招生计划待官方公布（6月15-20日）
- 2026年位次待出分后确定（6月25日）
- **仅供参考，以官方为准**

---

## 🧪 功能问题

### Q11: 如何保证方案合规？

**A**:

- 所有方案通过 `gaokao-spec-checker` 自动检查
- 检测致命/严重/警告三级错误
- 基于官方数据核实

### Q12: 能100%保证录取吗？

**A**: **不能**

- 录取受多种因素影响
- 我们只能提高科学性和规范性
- 最终录取由考试院和高校决定

### Q13: PDF报告生成失败？

**A**:

1. 检查 weasyprint 是否安装
2. 检查系统依赖（libpango）
3. 查看 [INSTALL.md#q4-pdf-生成失败](INSTALL.md#q4-pdf-生成失败)

---

## 📝 文档问题

### Q14: 有哪些文档？

**A**:

- [README.md](README.md) - 项目说明
- [INSTALL.md](INSTALL.md) - 安装指南
- [CONTRIBUTING.md](CONTRIBUTING.md) - 贡献指南
- [CHANGELOG.md](CHANGELOG.md) - 变更日志
- [docs/TUTORIAL.md](docs/TUTORIAL.md) - 使用教程
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) - 开发指南
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - 架构设计

### Q15: 如何查看更多案例？

**A**:

- [docs/case-studies/](docs/case-studies/)
- [docs/optimization-log/](docs/optimization-log/)
- [rules/errors/ERRORS.md](rules/errors/ERRORS.md)

---

## 🔧 技术问题

### Q16: 项目结构是什么样的？

**A**:

```
gaokao-volunteer-system/
├── skills/          # Hermes Skills
├── scripts/         # 独立脚本
├── rules/           # 规则库
├── docs/            # 文档
├── tests/           # 测试
└── data/            # 数据示例
```

详见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

### Q17: 如何运行测试？

**A**:

```bash
# 全部测试
python3 tests/test_all.py

# 单省份测试
python3 skills/gaokao-spec-checker/scripts/spec_checker_v2.py
```

### Q18: 如何添加新省份？

**A**:

1. 编辑 `PROVINCE_RULES` 字典
2. 添加省份文档
3. 添加测试用例
4. 更新文档

详见 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## ⚖️ 法律/合规问题

### Q19: 数据版权归谁？

**A**:

- 2025年录取数据来源于各省教育考试院公开信息
- 招生政策来源于教育部/各省官方文件
- 项目本身为学习研究性质

### Q20: 使用本项目是否保证成功？

**A**: **明确声明**

- 本项目仅供学习参考
- 实际填报请以**各省教育考试院官方信息为准**
- 最终决策由考生及家长做出
- 我们不承担志愿填报结果的责任

### Q21: 可以商用吗？

**A**:

- 当前版本为学习研究性质
- 如需商用，请咨询相关法律意见
- 注意各省教育政策的商用限制

---

## 💡 优化建议

### Q22: 如何提出功能建议？

**A**:

1. 记录到 `docs/optimization-log/future-plan.md`
2. 在Git提交中说明
3. 测试验证后提交PR

### Q23: 发现新错误模式怎么办？

**A**:

1. 记录到 `rules/errors/ERRORS.md`
2. 添加测试用例
3. 更新检查器（如需要）
4. 提交变更

### Q24: 有真实案例可以分享吗？

**A**:

- 欢迎分享！
- 使用模板：`docs/case-studies/TEMPLATE.md`
- 脱敏处理后提交

---

## 📞 联系与帮助

### Q25: 遇到问题如何获取帮助？

**A**:

1. 查看 [TUTORIAL.md](docs/TUTORIAL.md)
2. 运行 `python3 tests/test_all.py` 验证
3. 检查 [INSTALL.md#常见问题](INSTALL.md#常见问题)
4. 查看本项目文档

### Q26: 如何报告Bug？

**A**:

```bash
# 1. 复现问题
# 2. 检查是否已知问题（rules/errors/ERRORS.md）
# 3. 记录问题详情
# 4. 提交修复（CONTRIBUTING.md）
```

---

## ❓ 其他问题

### Q27: 为什么叫"龙老师"？

**A**: 谐音"long"（long-term project），寓意长期积累、持续服务。

### Q28: 未来会收费吗？

**A**: 当前版本为学习研究性质。未来如商业化，会明确告知。

### Q29: 会支持27省以外的省份吗？

**A**: 会的，欢迎贡献。详见 [CONTRIBUTING.md](CONTRIBUTING.md)

### Q30: 2027年及以后还维护吗？

**A**: 计划维护。届时需更新：

- 2026年录取数据
- 2027年招生计划
- 各省政策变化

---

**还有问题？**

- 查看完整文档：[docs/](docs/)
- 检查测试：[tests/](tests/)
- 查看案例：[docs/case-studies/](docs/case-studies/)

---

**版本**: v2.0  
**最后更新**: 2026-06-11
