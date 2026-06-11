# 安装指南

## 📦 系统要求

### 必要环境

- **操作系统**: Linux / macOS / Windows (WSL2)
- **Python**: >= 3.10
- **Git**: >= 2.0
- **磁盘空间**: >= 500MB

### 推荐环境

- **Python**: 3.11+
- **操作系统**: Ubuntu 22.04+ / macOS 14+
- **内存**: >= 4GB

---

## 🚀 快速安装

### 方式1：直接克隆项目

```bash
# 进入项目目录
cd /home/long/project/gaokao-volunteer-system

# 确认目录结构
ls -la
```

### 方式2：复制到Skills目录（在Hermes中使用）

```bash
# 复制4个Skills到Hermes
ln -s /home/long/project/gaokao-volunteer-system/skills/gaokao-college-advisor ~/.hermes/skills/
ln -s /home/long/project/gaokao-volunteer-system/skills/gaokao-spec-checker ~/.hermes/skills/
ln -s /home/long/project/gaokao-volunteer-system/skills/zhangxuefeng-skillset ~/.hermes/skills/
ln -s /home/long/project/gaokao-volunteer-system/skills/gaokao-counselor-long ~/.hermes/skills/
```

### 方式3：复制脚本到可执行路径

```bash
# 创建软链接到 ~/.local/bin
ln -s /home/long/project/gaokao-volunteer-system/scripts/gaokao-checker ~/.local/bin/
ln -s /home/long/project/gaokao-volunteer-system/scripts/gaokao-quick-3min.py ~/.local/bin/
ln -s /home/long/project/gaokao-volunteer-system/scripts/gaokao-visual-report-v2.py ~/.local/bin/

# 确保可执行
chmod +x ~/.local/bin/gaokao-checker
```

---

## 🐍 Python依赖安装

### 安装必要包

```bash
# 基础依赖
pip3 install --user --break-system-packages \
    weasyprint \
    jinja2 \
    markdown

# 可选依赖（用于开发和测试）
pip3 install --user --break-system-packages \
    pytest \
    black \
    flake8
```

### 验证安装

```bash
# 检查Python版本
python3 --version

# 检查必要包
python3 -c "import weasyprint; print('weasyprint OK')"
python3 -c "import jinja2; print('jinja2 OK')"

# 检查脚本
which gaokao-checker
gaokao-checker --help
```

---

## ⚙️ 配置

### 1. 配置Hermes（可选）

如果你使用Hermes，需要确保Skills能被加载：

```bash
# 检查Hermes配置
hermes skills list

# 如果Skills未显示，可能需要刷新
hermes skills reload
```

### 2. 配置邮件（可选）

如果需要邮件发送功能：

```bash
# 配置环境变量
export QQ_EMAIL_PASSWORD="your-password"

# 或写入 ~/.bashrc
echo 'export QQ_EMAIL_PASSWORD="your-password"' >> ~/.bashrc
```

### 3. 配置浏览器（可选）

用于生成PDF：

```bash
# 安装wkhtmltopdf
sudo apt-get install wkhtmltopdf
```

---

## 🧪 验证安装

### 运行测试

```bash
# 进入项目目录
cd /home/long/project/gaokao-volunteer-system

# 运行自动化测试
python3 tests/test_all.py

# 预期输出：所有测试通过
```

### 手动测试

```bash
# 测试规范检查器
python3 ~/.local/bin/gaokao-checker tests/cases/hunan-578.md

# 测试可视化报告
python3 ~/.local/bin/gaokao-visual-report-v2.py

# 测试问卷
python3 ~/.local/bin/gaokao-quick-3min.py
```

---

## 🐛 常见问题

### Q1: 找不到 `gaokao-checker` 命令

**原因**: 路径未添加到PATH

**解决**:

```bash
# 添加到PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 验证
which gaokao-checker
```

### Q2: `pip3 install` 失败

**原因**: 权限问题或系统包限制

**解决**:

```bash
# 使用 --user 参数
pip3 install --user weasyprint jinja2 markdown

# 或使用虚拟环境
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

### Q3: Skills 在 Hermes 中不显示

**原因**: Hermes 未扫描到

**解决**:

```bash
# 刷新Skills列表
hermes skills reload

# 或重启 Hermes
```

### Q4: PDF 生成失败

**原因**: weasyprint 依赖缺失

**解决**:

```bash
# 安装系统依赖
sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0

# 重新安装 weasyprint
pip3 install --user --break-system-packages --force-reinstall weasyprint
```

### Q5: Git 提交失败

**原因**: 身份未配置

**解决**:

```bash
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

---

## 🔄 更新

### 更新项目

```bash
# 进入项目目录
cd /home/long/project/gaokao-volunteer-system

# 拉取最新代码（如果有远程仓库）
git pull

# 查看更新日志
cat CHANGELOG.md | head -50
```

### 更新依赖

```bash
# 更新Python包
pip3 install --user --break-system-packages --upgrade \
    weasyprint jinja2 markdown
```

---

## 📋 卸载

### 完全卸载

```bash
# 删除Skills软链接
rm ~/.hermes/skills/gaokao-college-advisor
rm ~/.hermes/skills/gaokao-spec-checker
rm ~/.hermes/skills/zhangxuefeng-skillset
rm ~/.hermes/skills/gaokao-counselor-long

# 删除脚本软链接
rm ~/.local/bin/gaokao-checker
rm ~/.local/bin/gaokao-quick-3min.py
rm ~/.local/bin/gaokao-visual-report-v2.py

# 删除项目目录
rm -rf /home/long/project/gaokao-volunteer-system

# 卸载Python包（可选）
pip3 uninstall weasyprint jinja2 markdown
```

---

## 📞 获取帮助

- **文档**: [TUTORIAL.md](docs/TUTORIAL.md)
- **开发**: [DEVELOPMENT.md](docs/DEVELOPMENT.md)
- **测试**: `python3 tests/test_all.py`
- **FAQ**: [FAQ.md](FAQ.md)

---

**版本**: v2.0  
**最后更新**: 2026-06-11
