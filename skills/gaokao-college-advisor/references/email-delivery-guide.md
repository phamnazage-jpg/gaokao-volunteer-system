# Email Delivery Configuration Guide
# 邮件发送配置指南

## Gmail Configuration (Current)

### 发件邮箱设置
- **Email**: phamnazage@gmail.com
- **Display Name**: 高考志愿填报顾问
- **IMAP/SMTP**: Enabled

### Himalaya Configuration File

Location: `~/.config/himalaya/config.toml`

```toml
[accounts.gmail]
email = "phamnazage@gmail.com"
display-name = "高考志愿填报顾问"
default = true

[accounts.gmail.backend]
type = "imap"
host = "imap.gmail.com"
port = 993
login = "phamnazage@gmail.com"

[accounts.gmail.backend.encryption]
type = "tls"

[accounts.gmail.backend.auth]
type = "password"
cmd = "echo $GMAIL_APP_PASSWORD"

[accounts.gmail.message.send.backend]
type = "smtp"
host = "smtp.gmail.com"
port = 587
login = "phamnazage@gmail.com"

[accounts.gmail.message.send.backend.encryption]
type = "start-tls"

[accounts.gmail.message.send.backend.auth]
type = "password"
cmd = "echo $GMAIL_APP_PASSWORD"

[accounts.gmail.folder.aliases]
inbox = "INBOX"
sent = "[Gmail]/Sent Mail"
drafts = "[Gmail]/Drafts"
trash = "[Gmail]/Trash"
```

### Getting Gmail App Password

1. Go to https://myaccount.google.com
2. Navigate to **Security**
3. Enable **2-Step Verification** (required)
4. Go to **App passwords** (https://myaccount.google.com/apppasswords)
5. Select **Mail** as the app
6. Select **Other (Custom name)**: "Himalaya CLI"
7. Click **Generate**
8. Copy the 16-character password

### Environment Variable Setup

```bash
# Set before sending emails
export GMAIL_APP_PASSWORD="your-16-char-app-password"

# To make permanent
export GMAIL_APP_PASSWORD="your-16-char-app-password" >> ~/.bashrc
```

### Sending Test Email

```bash
cat << 'EOF' | himalaya template send
From: phamnazage@gmail.com
To: phamnazage@gmail.com
Cc: phamnazage@gmail.com
Subject: 【测试】高考志愿填报系统
Content-Type: text/plain; charset=utf-8

This is a test email from the Gaokao consulting system.
EOF
```

## Email Template

```
Subject: 【高考志愿填报方案】[考生姓名] - 2026年高考志愿填报建议

尊敬的[考生姓名]家长/同学：

您好！

根据您提供的高考分数和位次信息，我已完成详细的志愿填报方案分析。
请查收附件中的完整报告（PDF格式）。

【方案概要】
- 推荐冲刺院校：X所
- 推荐稳妥院校：X所  
- 推荐保底院校：X所
- 整体录取概率评估：[评估结果]

【重要提醒】
1. 本方案基于2025年历史录取数据，2026年实际录取情况可能有所变化
2. 请务必在正式填报前登录省教育考试院官网核实最新招生计划
3. 建议准备2-3个备选方案，根据实际出分情况灵活调整

【后续服务】
如有任何疑问，欢迎随时回复邮件咨询。我会在24小时内回复。

祝考生金榜题名，前程似锦！

高考志愿填报顾问
phamnazage@gmail.com
2026年XX月XX日
```

## Troubleshooting

### "Please log in via your web browser"
- Check Gmail security alerts
- Visit https://accounts.google.com/DisplayUnlockCaptcha
- Allow less secure apps if necessary

### Authentication Failed
- Verify using App Password (not regular Gmail password)
- Re-generate app password if needed
- Check environment variable is set correctly

### Connection Issues
- Verify IMAP is enabled in Gmail settings
- Check firewall/proxy settings
- Try alternative ports if needed
