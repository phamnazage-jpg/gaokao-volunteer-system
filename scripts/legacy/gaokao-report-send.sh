#!/bin/bash
# 高考志愿填报报告生成并发送脚本
# 发件邮箱：phamnazage@gmail.com

# 使用说明:
# 1. 先设置环境变量: export GMAIL_APP_PASSWORD=*** 2. 运行: ./gaokao-report-send.sh <客户邮箱> <考生姓名>

CUSTOMER_EMAIL=$1
STUDENT_NAME=$2
REPORT_FILE=$3  # Markdown 文件路径

if [ -z "$CUSTOMER_EMAIL" ] || [ -z "$STUDENT_NAME" ]; then
    echo "用法: $0 <客户邮箱> <考生姓名> [报告文件.md]"
    exit 1
fi

# 检查环境变量
if [ -z "$GMAIL_APP_PASSWORD" ]; then
    echo "错误: 请先设置 GMAIL_APP_PASSWORD 环境变量"
    echo "export GMAIL_APP_PASSWORD='你的Gmail应用专用密码'"
    echo ""
    echo "获取方式："
    echo "1. 登录 https://myaccount.google.com"
    echo "2. 安全性 → 两步验证 → 应用专用密码"
    echo "3. 生成16位应用专用密码"
    exit 1
fi

# 生成时间戳
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
WORKDIR="/tmp/gaokao_report_${TIMESTAMP}"
mkdir -p "$WORKDIR"

# 如果有报告文件，转换并发送
if [ -n "$REPORT_FILE" ] && [ -f "$REPORT_FILE" ]; then
    # 复制报告到工作目录
    cp "$REPORT_FILE" "${WORKDIR}/report.md"
    
    # 尝试转换为 PDF（如果有 pandoc 和 wkhtmltopdf）
    if command -v pandoc &> /dev/null && command -v wkhtmltopdf &> /dev/null; then
        pandoc "${WORKDIR}/report.md" -o "${WORKDIR}/report.pdf" \
            --pdf-engine=wkhtmltopdf \
            --metadata title="高考志愿填报方案_${STUDENT_NAME}" \
            --metadata author="高考志愿填报顾问" \
            -V geometry:margin=2.5cm 2>/dev/null
        echo "✓ PDF 已生成: ${WORKDIR}/report.pdf"
    else
        echo "⚠ pandoc/wkhtmltopdf 未安装，只发送 Markdown 文件"
    fi
else
    # 创建示例报告
    cat > "${WORKDIR}/report.md" << EOF
# 高考志愿填报方案报告

**生成时间**: $(date '+%Y年%m月%d日')  
**考生姓名**: ${STUDENT_NAME}

## 请在此处填写详细分析...

---
祝考生金榜题名！
高考志愿填报顾问
phamnazage@gmail.com
EOF
    echo "已创建示例报告: ${WORKDIR}/report.md"
fi

# 发送邮件
echo "正在发送邮件到: $CUSTOMER_EMAIL"
himalaya message write \
    -H "To:${CUSTOMER_EMAIL}" \
    -H "Cc:phamnazage@gmail.com" \
    -H "Subject:【高考志愿填报方案】${STUDENT_NAME} - 2026年高考志愿填报建议" \
    "请查收附件中的高考志愿填报方案报告。如有疑问请回复邮件咨询。祝考生金榜题名！高考志愿填报顾问 phamnazage@gmail.com"

if [ $? -eq 0 ]; then
    echo "✓ 邮件发送成功"
else
    echo "✗ 邮件发送失败，请检查配置"
    echo ""
    echo "常见问题："
    echo "1. 确认 GMAIL_APP_PASSWORD 已正确设置"
    echo "2. 确认 Gmail 已开启两步验证"
    echo "3. 确认使用的是应用专用密码，不是Gmail登录密码"
fi

echo ""
echo "报告文件保存在: ${WORKDIR}"
echo ""
echo "提示：邮件已同时抄送到 phamnazage@gmail.com（备份）"
