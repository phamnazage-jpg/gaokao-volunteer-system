# 高考志愿填报系统 - 双模式使用指南

## 架构模式

本系统采用**双模式架构**：
1. **Skill模式**：Hermes对话中使用
2. **Standalone模式**：独立脚本工具

## 模式对比

| 维度 | Skill模式 | Standalone模式 |
|------|-----------|----------------|
| **使用场景** | 日常咨询对话 | 批量生成报告/演示 |
| **启动方式** | `/skill gaokao-college-advisor` | `python3 ~/.local/bin/gaokao-*.py` |
| **交互方式** | 对话式问答 | 命令行/脚本执行 |
| **输出** | 对话回复 | 文件（HTML/PDF/Markdown） |
| **适合用户** | 单次咨询 | 批量处理/存档 |

## 使用建议

### 选择Skill模式当：
- 考生/家长直接咨询
- 需要实时问答互动
- 信息收集不完整，需要追问
- 快速给出建议

### 选择Standalone模式当：
- 需要生成可打印的报告文件
- 批量生成多份方案
- 演示完整流程
- 需要HTML/PDF/Markdown输出

## 快速参考

### Skill模式入口
```
/skill gaokao-college-advisor
# 然后直接对话咨询
```

### Standalone模式入口
```bash
# 生成可视化报告（HTML/PDF/Markdown）
python3 ~/.local/bin/gaokao-visual-report-v2.py

# 获取问卷模板
python3 ~/.local/bin/gaokao-quick-3min.py

# 完整流程演示
bash ~/.local/bin/gaokao-demo-full-workflow.sh
```

## 输出文件位置

Standalone模式生成的文件默认保存到：
- `/tmp/gaokao_report_姓名_日期.*` - 临时文件
- `~/Documents/高考志愿报告/示例/` - 示例/备份文件

## 最佳实践

1. **先用Skill模式收集信息** → 对话获取考生信息
2. **再用Standalone生成报告** → 导出HTML/PDF给考生带走
3. **保留双模式灵活性** → 根据场景选择最合适的

## 维护注意

- Skill文件：`~/.hermes/skills/gaokao-college-advisor/`
- 脚本文件：`~/.local/bin/gaokao-*.py`
- 两者需保持内容一致性
- 更新Skill时检查脚本是否需要同步更新
