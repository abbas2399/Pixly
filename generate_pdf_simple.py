#!/usr/bin/env python3
"""
Simple PDF Generator for Pixly Project Overview
Converts markdown to PDF using markdown2 and reportlab (no system dependencies)

Requirements:
    pip install markdown2 reportlab

Usage:
    python generate_pdf_simple.py
"""

import re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Preformatted
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import markdown2


def parse_markdown_to_flowables(md_content):
    """Convert markdown content to reportlab flowables."""

    # Convert markdown to HTML
    html_content = markdown2.markdown(
        md_content,
        extras=["tables", "fenced-code-blocks", "header-ids"]
    )

    # Setup styles
    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=20,
        spaceBefore=30,
        alignment=TA_LEFT
    ))

    styles.add(ParagraphStyle(
        name='CustomHeading2',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=12,
        spaceBefore=20,
        borderPadding=(0, 0, 5, 0),
        borderColor=colors.HexColor('#3498db'),
        borderWidth=2,
    ))

    styles.add(ParagraphStyle(
        name='CustomHeading3',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#2980b9'),
        spaceAfter=10,
        spaceBefore=15,
    ))

    styles.add(ParagraphStyle(
        name='CustomBodyText',
        parent=styles['BodyText'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=10,
    ))

    styles.add(ParagraphStyle(
        name='CodeStyle',
        parent=styles['Code'],
        fontSize=8,
        leftIndent=20,
        backColor=colors.HexColor('#f8f8f8'),
        borderColor=colors.HexColor('#ddd'),
        borderWidth=1,
        borderPadding=10,
    ))

    # Parse markdown line by line
    flowables = []
    lines = md_content.split('\n')
    i = 0

    in_code_block = False
    code_lines = []
    in_table = False
    table_lines = []

    while i < len(lines):
        line = lines[i]

        # Code blocks
        if line.startswith('```'):
            if in_code_block:
                # End code block
                code_text = '\n'.join(code_lines)
                flowables.append(Preformatted(code_text, styles['CodeStyle']))
                flowables.append(Spacer(1, 0.2*inch))
                code_lines = []
                in_code_block = False
            else:
                # Start code block
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Tables
        if '|' in line and line.strip():
            if not in_table:
                in_table = True
                table_lines = []
            table_lines.append(line)
            i += 1

            # Check if next line is not a table row
            if i < len(lines) and '|' not in lines[i]:
                # Process table
                table_data = []
                for table_line in table_lines:
                    if '---' not in table_line:  # Skip separator rows
                        cells = [cell.strip() for cell in table_line.split('|')[1:-1]]
                        table_data.append(cells)

                if table_data:
                    # Create table
                    t = Table(table_data)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f9f9f9')),
                        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#ddd')),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                    ]))
                    flowables.append(t)
                    flowables.append(Spacer(1, 0.2*inch))

                in_table = False
                table_lines = []
            continue

        # Headings
        if line.startswith('# '):
            text = line[2:].strip()
            flowables.append(Paragraph(text, styles['CustomTitle']))
        elif line.startswith('## '):
            text = line[3:].strip()
            flowables.append(Paragraph(text, styles['CustomHeading2']))
        elif line.startswith('### '):
            text = line[4:].strip()
            flowables.append(Paragraph(text, styles['CustomHeading3']))

        # Horizontal rule
        elif line.strip() == '---':
            flowables.append(Spacer(1, 0.1*inch))

        # Empty line
        elif not line.strip():
            if flowables and not isinstance(flowables[-1], Spacer):
                flowables.append(Spacer(1, 0.1*inch))

        # Regular text
        else:
            # Handle bold
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            # Handle inline code
            text = re.sub(r'`(.*?)`', r'<font color="#c7254e" face="Courier">\1</font>', text)
            # Handle bullet points
            if text.strip().startswith('- '):
                text = '• ' + text.strip()[2:]

            if text.strip():
                flowables.append(Paragraph(text, styles['CustomBodyText']))

        i += 1

    return flowables


def generate_pdf():
    """Generate PDF from markdown file."""

    # File paths
    md_file = Path(__file__).parent / "PIXLY_PROJECT_OVERVIEW.md"
    pdf_file = Path(__file__).parent / "PIXLY_PROJECT_OVERVIEW.pdf"

    # Read markdown content
    print(f"Reading markdown from: {md_file}")
    with open(md_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    # Create PDF
    print(f"Generating PDF: {pdf_file}")
    doc = SimpleDocTemplate(
        str(pdf_file),
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )

    # Convert markdown to flowables
    print("Converting markdown to PDF content...")
    flowables = parse_markdown_to_flowables(markdown_content)

    # Build PDF
    doc.build(flowables)

    print(f"✓ PDF generated successfully: {pdf_file}")
    print(f"  File size: {pdf_file.stat().st_size / 1024:.2f} KB")


if __name__ == "__main__":
    try:
        generate_pdf()
    except ImportError as e:
        print("Error: Required packages not installed.")
        print("Please install dependencies:")
        print("  pip3 install markdown2 reportlab")
        print(f"\nDetails: {e}")
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
