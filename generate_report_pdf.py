"""
Generates Simulation_Project_Report.pdf from Simulation_Project_Report.md
using ReportLab for clean, professional PDF output.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus.flowables import HRFlowable
import re

# ── Page setup ────────────────────────────────────────────────────────────────
PDF_PATH = "Simulation_Project_Report.pdf"
MD_PATH  = "Simulation_Project_Report.md"

doc = SimpleDocTemplate(
    PDF_PATH,
    pagesize=A4,
    leftMargin=2.5*cm, rightMargin=2.5*cm,
    topMargin=2.5*cm,  bottomMargin=2.5*cm,
    title="Reorganisation of an Outpatient Radiology Department",
    author="Simulation Modelling and Analysis 2025-2026",
)

# ── Styles ────────────────────────────────────────────────────────────────────
BASE   = getSampleStyleSheet()
BLUE   = colors.HexColor("#1a3a5c")
LBLUE  = colors.HexColor("#2e6da4")
GRAY   = colors.HexColor("#555555")
LGRAY  = colors.HexColor("#f5f5f5")
RULE   = colors.HexColor("#cccccc")

def style(name, parent="Normal", **kw):
    s = ParagraphStyle(name, parent=BASE[parent])
    for k, v in kw.items():
        setattr(s, k, v)
    return s

S_TITLE   = style("Title2",   "Title",   fontSize=22, textColor=BLUE,
                  spaceAfter=6, leading=28, alignment=TA_CENTER)
S_SUBTITLE= style("Sub",      "Normal",  fontSize=11, textColor=GRAY,
                  spaceAfter=4, alignment=TA_CENTER)
S_H1      = style("H1",       "Heading1",fontSize=14, textColor=BLUE,
                  spaceBefore=18, spaceAfter=6, leading=18)
S_H2      = style("H2",       "Heading2",fontSize=12, textColor=LBLUE,
                  spaceBefore=12, spaceAfter=4, leading=15)
S_H3      = style("H3",       "Heading3",fontSize=11, textColor=LBLUE,
                  spaceBefore=8,  spaceAfter=3, leading=14, fontName="Helvetica-BoldOblique")
S_BODY    = style("Body",     "Normal",  fontSize=10, leading=14,
                  spaceAfter=6, alignment=TA_JUSTIFY)
S_BULLET  = style("Bullet",   "Normal",  fontSize=10, leading=14,
                  spaceAfter=3, leftIndent=16, bulletIndent=6)
S_MATH    = style("Math",     "Normal",  fontSize=10, leading=14,
                  spaceAfter=6, leftIndent=30, fontName="Courier",
                  textColor=colors.HexColor("#333333"))
S_CAPTION = style("Caption",  "Normal",  fontSize=9,  leading=12,
                  spaceAfter=4, textColor=GRAY, alignment=TA_CENTER)
S_TH      = style("TH",       "Normal",  fontSize=8,  leading=11,
                  textColor=colors.white, fontName="Helvetica-Bold", alignment=TA_CENTER)
S_TD      = style("TD",       "Normal",  fontSize=8,  leading=11, alignment=TA_CENTER)
S_TD_L    = style("TDL",      "Normal",  fontSize=8,  leading=11, alignment=TA_LEFT)
S_QUOTE   = style("Quote",    "Normal",  fontSize=10, leading=14,
                  leftIndent=20, rightIndent=20, spaceAfter=6,
                  borderPad=6, textColor=BLUE, fontName="Helvetica-Oblique")

# ── Helper: render inline markdown (bold/italic/code) ─────────────────────────
def md_inline(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*',     r'<i>\1</i>', text)
    text = re.sub(r'`(.+?)`',       r'<font name="Courier">\1</font>', text)
    text = re.sub(r'\$(.+?)\$',     lambda m: '<font name="Courier">'+m.group(1)+'</font>', text)
    text = text.replace('—', '&#8212;').replace('≥', '&#8805;').replace('≤', '&#8804;')
    return text

# ── Table builder ─────────────────────────────────────────────────────────────
def build_table(header, rows):
    th_cells = [Paragraph(md_inline(h), S_TH) for h in header]
    data = [th_cells]
    for i, row in enumerate(rows):
        cells = []
        for j, cell in enumerate(row):
            s = S_TD_L if j == 0 else S_TD
            cells.append(Paragraph(md_inline(cell), s))
        data.append(cells)

    col_count = len(header)
    page_w = A4[0] - 5*cm
    col_w = [page_w / col_count] * col_count
    # Give first col more space if it's a label column
    if col_count >= 4:
        col_w[0] = page_w * 0.22
        rest = (page_w - col_w[0]) / (col_count - 1)
        col_w[1:] = [rest] * (col_count - 1)

    t = Table(data, colWidths=col_w, repeatRows=1)
    style_cmds = [
        ("BACKGROUND",  (0,0), (-1,0), BLUE),
        ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LGRAY]),
        ("GRID",        (0,0), (-1,-1), 0.4, RULE),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",  (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING",(0,0),(-1,-1), 5),
    ]
    t.setStyle(TableStyle(style_cmds))
    return t

# ── Parse markdown → ReportLab flowables ──────────────────────────────────────
def parse_md(md_text):
    flowables = []
    lines = md_text.splitlines()
    i = 0

    # Cover page
    flowables.append(Spacer(1, 3*cm))
    flowables.append(Paragraph("Reorganisation of an Outpatient<br/>Radiology Department", S_TITLE))
    flowables.append(Spacer(1, 0.4*cm))
    flowables.append(HRFlowable(width="80%", thickness=2, color=BLUE, spaceAfter=10))
    flowables.append(Paragraph("Simulation Modelling and Analysis (F000941) &nbsp;|&nbsp; 2025–2026", S_SUBTITLE))
    flowables.append(PageBreak())

    while i < len(lines):
        line = lines[i].rstrip()

        # Skip YAML frontmatter
        if line.strip() == "---":
            i += 1
            while i < len(lines) and lines[i].strip() != "---":
                i += 1
            i += 1
            continue

        # Skip main title (already on cover)
        if line.startswith("# Reorganisation"):
            i += 1
            continue
        if line.startswith("## Simulation Modelling"):
            i += 1
            continue
        if line.strip() == "---":
            flowables.append(HRFlowable(width="100%", thickness=0.5, color=RULE, spaceAfter=6))
            i += 1
            continue

        # Headings
        if line.startswith("#### "):
            flowables.append(Paragraph(md_inline(line[5:]), S_H3))
            i += 1; continue
        if line.startswith("### "):
            flowables.append(Paragraph(md_inline(line[4:]), S_H3))
            i += 1; continue
        if line.startswith("## "):
            flowables.append(Paragraph(md_inline(line[3:]), S_H1))
            i += 1; continue
        if line.startswith("# "):
            flowables.append(Paragraph(md_inline(line[2:]), S_H1))
            i += 1; continue

        # Block quote (recommendation box)
        if line.startswith("> "):
            flowables.append(Paragraph(md_inline(line[2:]), S_QUOTE))
            i += 1; continue

        # Block math ($$...$$)
        if line.strip().startswith("$$"):
            math_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("$$"):
                math_lines.append(lines[i].strip())
                i += 1
            i += 1
            flowables.append(Paragraph(" ".join(math_lines), S_MATH))
            continue

        # Markdown table
        if line.startswith("|"):
            header_line = line
            i += 1
            # skip separator row
            if i < len(lines) and re.match(r'\|[\s\-:|]+\|', lines[i]):
                i += 1
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            # parse
            def parse_row(l):
                return [c.strip() for c in l.strip().strip("|").split("|")]
            header = parse_row(header_line)
            data   = [parse_row(r) for r in rows]
            flowables.append(Spacer(1, 4))
            flowables.append(build_table(header, data))
            flowables.append(Spacer(1, 6))
            continue

        # Bullet list
        if re.match(r'^[-*]\s', line):
            text = re.sub(r'^[-*]\s+', '', line)
            flowables.append(Paragraph("&#8226;&nbsp;&nbsp;" + md_inline(text), S_BULLET))
            i += 1; continue

        # Numbered list
        if re.match(r'^\d+\.\s', line):
            text = re.sub(r'^\d+\.\s+', '', line)
            num  = re.match(r'^(\d+)\.', line).group(1)
            flowables.append(Paragraph(f"<b>{num}.</b>&nbsp;&nbsp;" + md_inline(text), S_BULLET))
            i += 1; continue

        # Empty line
        if not line.strip():
            flowables.append(Spacer(1, 4))
            i += 1; continue

        # Normal paragraph
        flowables.append(Paragraph(md_inline(line), S_BODY))
        i += 1

    return flowables

# ── Main ──────────────────────────────────────────────────────────────────────
with open(MD_PATH, encoding="utf-8") as f:
    md_text = f.read()

flowables = parse_md(md_text)
doc.build(flowables)
print(f"PDF saved: {PDF_PATH}")
