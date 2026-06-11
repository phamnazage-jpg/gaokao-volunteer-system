# 多格式报告导出指南

## 技术栈

```python
# 必需依赖
jinja2        # HTML模板引擎
weasyprint    # HTML转PDF
markdown      # Markdown处理
```

## 安装命令

```bash
pip3 install --user jinja2 weasyprint markdown

# Ubuntu/Debian 系统依赖
sudo apt-get install libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0
```

## 核心模式

### 1. 三元生成函数

```python
def generate_report(data, output_format='all'):
    """支持多格式导出：Markdown + HTML + PDF"""
    results = []
    
    # Markdown（基础格式，可编辑）
    if output_format in ['md', 'all']:
        md = generate_markdown(data)
        results.append(save_file(md, '.md'))
    
    # HTML（可视化，可交互）
    if output_format in ['html', 'pdf', 'all']:
        html = generate_html(data, template.html)
        results.append(save_file(html, '.html'))
    
    # PDF（可打印，可分享）
    if output_format in ['pdf', 'all']:
        pdf = html_to_pdf(html_file)  # 从HTML转换
        results.append(pdf)
    
    return results
```

### 2. HTML模板结构

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <!-- 外联CDN资源（Chart.js等） -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    /* 内联CSS确保PDF兼容性 */
    @media print {
      /* PDF专用样式 */
    }
  </style>
</head>
<body>
  {{ content }}
  <canvas id="chart"></canvas>
  <script>
    new Chart(document.getElementById('chart'), {...});
  </script>
</body>
</html>
```

### 3. 从HTML生成PDF

```python
from weasyprint import HTML, CSS

def html_to_pdf(html_file, pdf_file=None):
    """单页HTML转PDF"""
    if pdf_file is None:
        pdf_file = html_file.replace('.html', '.pdf')
    
    HTML(filename=html_file).write_pdf(pdf_file)
    return pdf_file
```

## 坑点记录

- **WeasyPrint系统依赖**：需要安装 pango/harfbuzz，否则报错
- **中文字体**：PDF可能缺中文字体，需安装 fonts-noto-cjk
- **Chart.js离线**：使用CDN依赖网络，完全离线需内联

## 示例输出

```bash
$ python3 gaokao-visual-report-v2.py

✓ Markdown报告：/tmp/report.md    (8 KB)
✓ HTML报告：/tmp/report.html      (14 KB)
✓ PDF报告：/tmp/report.pdf        (336 KB)
```
