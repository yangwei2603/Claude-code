---
name: docx-generation
description: >
  基于 python-docx 的高质量 Word 文档自动生成技能。
  覆盖：正式报告、合同文档、会议纪要、工作周报、数据分析报告。
  当用户提及：生成 Word、生成 docx、Word 报告、正式文档、
  合同模板、会议纪要导出、周报导出、报告排版 时触发。
triggers:
  - 生成 Word
  - 生成 docx
  - Word 报告
  - 正式文档
  - 合同模板
  - 会议纪要导出
  - 周报导出
  - 报告排版
agent_created: true
version: 1.0
created: 2026-05-07
---

# DOCX 文档生成 Skill

## 能力范围

- **正式报告**：数据分析报告、财务分析报告、项目汇报
- **合同文档**：基于模板的合同填充
- **会议纪要**：结构化纪要导出
- **工作周报**：自动化周报生成
- **数据表格**：复杂表格（合并单元格、多级表头）

## 环境要求

```bash
# 已预装在 .venv 中
pip install python-docx
```

## 核心 API 速查

```python
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

doc = Document()

# 中文字体设置
doc.styles['Normal'].font.name = '微软雅黑'
doc.styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

# 标题
title = doc.add_heading('报告标题', level=1)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

# 正文段落
p = doc.add_paragraph()
p.add_run('正文内容').font.size = Pt(12)

# 表格
table = doc.add_table(rows=3, cols=3)
table.style = 'Table Grid'
hdr_cells = table.rows[0].cells
hdr_cells[0].text = '表头1'

# 保存
doc.save('output.docx')
```

## 标准化报告模板

```python
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

def create_formal_report(title, subtitle, author, date, sections):
    """
    sections: [
        {"heading": "一、执行摘要", "content": "..."},
        {"heading": "二、数据分析", "content": "...", "table": [...]},
    ]
    """
    doc = Document()
    
    # 全局字体
    style = doc.styles['Normal']
    style.font.name = '微软雅黑'
    style.font.size = Pt(12)
    style._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    
    # 封面标题
    t = doc.add_paragraph()
    run = t.add_run(title)
    run.font.size = Pt(22)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # 副标题
    if subtitle:
        st = doc.add_paragraph()
        run = st.add_run(subtitle)
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
        st.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # 元信息
    meta = doc.add_paragraph()
    meta.add_run(f"编制：{author}    日期：{date}").font.size = Pt(10)
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph()  # 空行
    
    # 内容区
    for sec in sections:
        # 二级标题
        h = doc.add_heading(sec['heading'], level=2)
        h.runs[0].font.color.rgb = RGBColor(0x00, 0x4D, 0x99)
        
        # 正文
        if 'content' in sec:
            doc.add_paragraph(sec['content'])
        
        # 表格
        if 'table' in sec and sec['table']:
            headers = sec['table'][0]
            rows = sec['table'][1:]
            tbl = doc.add_table(rows=1+len(rows), cols=len(headers))
            tbl.style = 'Table Grid'
            
            # 表头（蓝色背景）
            for i, h_text in enumerate(headers):
                cell = tbl.rows[0].cells[i]
                cell.text = h_text
                cell.paragraphs[0].runs[0].font.bold = True
                cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                from docx.oxml import parse_xml
                cell._element.get_or_add_tcPr().append(
                    parse_xml(r'<w:shd {} w:fill="004D99"/>'.format(
                        'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
                    ))
                )
            
            # 数据行
            for r_idx, row_data in enumerate(rows):
                for c_idx, val in enumerate(row_data):
                    tbl.rows[r_idx+1].cells[c_idx].text = str(val)
        
        doc.add_paragraph()  # 段间距
    
    # 页脚
    doc.add_paragraph()
    footer = doc.add_paragraph()
    footer.add_run("— 本报告由 AI 辅助生成，仅供内部参考 —").font.size = Pt(9)
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.runs[0].font.color.rgb = RGBColor(0x99, 0x99, 0x99)
    
    return doc
```

## 输出规范

- 文件命名：`{主题}_报告_{YYYYMMDD}.docx`
- 存储路径：`projects/docx-output/` 或分析目录同级
- 字体：正文 微软雅黑 12pt，标题 微软雅黑 14-22pt
- 配色：主色 #004D99（深蓝），强调色 #E84040（红）/ #00B06F（绿）

## 与其他 Skill 衔接

```
data-analysis → 生成 report_analysis_YYYYMMDD.md
     ↓
docx-generation → 读取 Markdown → 生成正式 Word 报告
     ↓
file-organizer → 自动归档到指定目录
```
