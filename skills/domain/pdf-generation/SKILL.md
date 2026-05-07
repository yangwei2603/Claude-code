---
name: pdf-generation
description: >
  基于 reportlab 的高质量 PDF 文档自动生成技能。
  覆盖：正式报告、合同文档、数据报表、红头文件、签报材料。
  当用户提及：生成 PDF、PDF 报告、正式 PDF、合同 PDF、
  签报材料、红头文件、报表导出、PDF 排版 时触发。
triggers:
  - 生成 PDF
  - PDF 报告
  - 正式 PDF
  - 合同 PDF
  - 签报材料
  - 红头文件
  - 报表导出
  - PDF 排版
agent_created: true
version: 1.0
created: 2026-05-07
---

# PDF 文档生成 Skill

## 能力范围

- **正式报告**：数据分析报告、财务分析报告、项目汇报 PDF
- **合同文档**：合同正文 PDF 输出（含骑缝章预留位）
- **数据报表**：复杂表格 PDF、财务报表导出
- **红头文件**：企业标准红头格式
- **签报材料**：内部审批签报 PDF

## 环境要求

```bash
# 已预装在 .venv 中
pip install reportlab
```

## 核心 API 速查

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# 注册中文字体（macOS 自带 STHeiti，无需额外安装）
pdfmetrics.registerFont(TTFont('STHeiti', '/System/Library/Fonts/STHeiti Medium.ttc', subfontIndex=0))
pdfmetrics.registerFont(TTFont('STHeiti-Bold', '/System/Library/Fonts/STHeiti Medium.ttc', subfontIndex=1))

# 创建文档
doc = SimpleDocTemplate(
    "output.pdf",
    pagesize=A4,
    rightMargin=2*cm, leftMargin=2*cm,
    topMargin=2*cm, bottomMargin=2*cm
)

# 样式
styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontName='STHeiti-Bold',
    fontSize=18,
    textColor=HexColor('#1A1A1A'),
    alignment=TA_CENTER,
    spaceAfter=20
)

body_style = ParagraphStyle(
    'CustomBody',
    parent=styles['Normal'],
    fontName='STHeiti',
    fontSize=11,
    leading=20,
    textColor=HexColor('#333333')
)

# 内容构建
story = []
story.append(Paragraph("报告标题", title_style))
story.append(Spacer(1, 0.5*cm))
story.append(Paragraph("正文内容...", body_style))

# 表格
data = [['表头1', '表头2', '表头3'],
        ['数据1', '数据2', '数据3']]
table = Table(data, colWidths=[4*cm, 4*cm, 4*cm])
table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#004D99')),
    ('TEXTCOLOR', (0, 0), (-1, 0), white),
    ('FONTNAME', (0, 0), (-1, 0), 'STHeiti-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 11),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
    ('FONTNAME', (0, 1), (-1, -1), 'STHeiti'),
    ('FONTSIZE', (0, 1), (-1, -1), 10),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('TOPPADDING', (0, 0), (-1, -1), 8),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
]))
story.append(table)

# 生成
doc.build(story)
```

## 标准化报告模板

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def create_pdf_report(filepath, title, subtitle, author, date, sections):
    """
    sections: [
        {"heading": "一、执行摘要", "content": "..."},
        {"heading": "二、数据分析", "content": "...", "table": [...]},
    ]
    """
    # 注册字体
    pdfmetrics.registerFont(TTFont('STHeiti', '/System/Library/Fonts/STHeiti Medium.ttc', subfontIndex=0))
    pdfmetrics.registerFont(TTFont('STHeiti-Bold', '/System/Library/Fonts/STHeiti Medium.ttc', subfontIndex=1))
    
    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm
    )
    
    # 样式定义
    title_style = ParagraphStyle(
        'Title', fontName='STHeiti-Bold', fontSize=20,
        textColor=HexColor('#1A1A1A'), alignment=TA_CENTER, spaceAfter=8
    )
    subtitle_style = ParagraphStyle(
        'Subtitle', fontName='STHeiti', fontSize=12,
        textColor=HexColor('#666666'), alignment=TA_CENTER, spaceAfter=20
    )
    meta_style = ParagraphStyle(
        'Meta', fontName='STHeiti', fontSize=10,
        textColor=HexColor('#999999'), alignment=TA_CENTER, spaceAfter=30
    )
    h2_style = ParagraphStyle(
        'H2', fontName='STHeiti-Bold', fontSize=14,
        textColor=HexColor('#004D99'), spaceBefore=20, spaceAfter=10
    )
    body_style = ParagraphStyle(
        'Body', fontName='STHeiti', fontSize=11,
        textColor=HexColor('#333333'), leading=20, spaceAfter=10
    )
    
    story = []
    
    # 封面区
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph(title, title_style))
    if subtitle:
        story.append(Paragraph(subtitle, subtitle_style))
    story.append(Paragraph(f"编制：{author}　　日期：{date}", meta_style))
    story.append(Spacer(1, 1*cm))
    
    # 内容区
    for sec in sections:
        story.append(Paragraph(sec['heading'], h2_style))
        if 'content' in sec:
            story.append(Paragraph(sec['content'], body_style))
        
        if 'table' in sec and sec['table']:
            headers = sec['table'][0]
            rows = sec['table'][1:]
            data = [headers] + [[str(v) for v in r] for r in rows]
            
            col_width = (16*cm) / len(headers)
            t = Table(data, colWidths=[col_width]*len(headers))
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#004D99')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('FONTNAME', (0, 0), (-1, 0), 'STHeiti-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
                ('FONTNAME', (0, 1), (-1, -1), 'STHeiti'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.5*cm))
    
    # 页脚声明
    story.append(Spacer(1, 2*cm))
    footer_style = ParagraphStyle(
        'Footer', fontName='STHeiti', fontSize=9,
        textColor=HexColor('#999999'), alignment=TA_CENTER
    )
    story.append(Paragraph("— 本报告由 AI 辅助生成，仅供内部参考 —", footer_style))
    
    doc.build(story)
    return filepath
```

## 红头文件模板

```python
def create_redhead_document(filepath, doc_title, doc_number, body_text, issuer, date):
    """企业红头文件格式"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.enums import TA_CENTER
    
    pdfmetrics.registerFont(TTFont('STHeiti', '/System/Library/Fonts/STHeiti Medium.ttc', subfontIndex=0))
    pdfmetrics.registerFont(TTFont('STHeiti-Bold', '/System/Library/Fonts/STHeiti Medium.ttc', subfontIndex=1))
    
    doc = SimpleDocTemplate(filepath, pagesize=A4,
        rightMargin=2.5*cm, leftMargin=2.5*cm,
        topMargin=3*cm, bottomMargin=2*cm)
    
    red_style = ParagraphStyle(
        'RedHead', fontName='STHeiti-Bold', fontSize=22,
        textColor=HexColor('#CC0000'), alignment=TA_CENTER, spaceAfter=4
    )
    number_style = ParagraphStyle(
        'DocNum', fontName='STHeiti', fontSize=11,
        textColor=HexColor('#CC0000'), alignment=TA_CENTER, spaceAfter=30
    )
    
    story = []
    story.append(Paragraph("春秋航空股份有限公司", red_style))
    story.append(Paragraph(doc_number, number_style))
    
    # 红色分隔线效果（用表格模拟）
    line = Table([['']], colWidths=[16*cm], rowHeights=[2])
    line.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#CC0000')),
    ]))
    story.append(line)
    story.append(Spacer(1, 1*cm))
    
    # 正文...
    
    doc.build(story)
```

## 输出规范

- 文件命名：`{主题}_报告_{YYYYMMDD}.pdf`
- 存储路径：`projects/pdf-output/` 或分析目录同级
- 页面：A4，边距 2cm
- 字体：正文 STHeiti 11pt，标题 STHeiti-Bold 14-20pt
- 配色：主色 #004D99（深蓝），红头 #CC0000，强调色 #E84040 / #00B06F

## 与其他 Skill 衔接

```
data-analysis → 生成 report_analysis_YYYYMMDD.md
     ↓
pdf-generation → 读取 Markdown → 生成正式 PDF 报告
     ↓
file-organizer → 自动归档到指定目录
```
