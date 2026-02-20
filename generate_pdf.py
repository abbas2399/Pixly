#!/usr/bin/env python3
"""
PDF Generator for Pixly Project Overview
Converts the markdown documentation to a professional PDF document.

Requirements:
    pip install markdown2 weasyprint

Usage:
    python generate_pdf.py
"""

import markdown2
from weasyprint import HTML, CSS
from pathlib import Path

def generate_pdf():
    """Generate PDF from markdown file."""

    # File paths
    md_file = Path(__file__).parent / "PIXLY_PROJECT_OVERVIEW.md"
    pdf_file = Path(__file__).parent / "PIXLY_PROJECT_OVERVIEW.pdf"

    # Read markdown content
    print(f"Reading markdown from: {md_file}")
    with open(md_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    # Convert markdown to HTML with extras
    print("Converting markdown to HTML...")
    html_content = markdown2.markdown(
        markdown_content,
        extras=[
            "tables",
            "fenced-code-blocks",
            "header-ids",
            "break-on-newline"
        ]
    )

    # Create full HTML document with styling
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Pixly Project Overview</title>
        <style>
            @page {{
                size: A4;
                margin: 2cm;
                @bottom-right {{
                    content: "Page " counter(page) " of " counter(pages);
                    font-size: 10pt;
                    color: #666;
                }}
            }}

            body {{
                font-family: 'Helvetica', 'Arial', sans-serif;
                line-height: 1.6;
                color: #333;
                font-size: 11pt;
            }}

            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                margin-top: 30px;
                margin-bottom: 20px;
                font-size: 28pt;
                page-break-after: avoid;
            }}

            h2 {{
                color: #34495e;
                border-bottom: 2px solid #3498db;
                padding-bottom: 8px;
                margin-top: 25px;
                margin-bottom: 15px;
                font-size: 20pt;
                page-break-after: avoid;
            }}

            h3 {{
                color: #2980b9;
                margin-top: 20px;
                margin-bottom: 12px;
                font-size: 16pt;
                page-break-after: avoid;
            }}

            h4 {{
                color: #3498db;
                margin-top: 15px;
                margin-bottom: 10px;
                font-size: 14pt;
            }}

            p {{
                margin: 10px 0;
                text-align: justify;
            }}

            ul, ol {{
                margin: 10px 0;
                padding-left: 30px;
            }}

            li {{
                margin: 5px 0;
            }}

            strong {{
                color: #2c3e50;
                font-weight: 600;
            }}

            code {{
                background-color: #f4f4f4;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 2px 5px;
                font-family: 'Courier New', monospace;
                font-size: 10pt;
                color: #c7254e;
            }}

            pre {{
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                overflow-x: auto;
                margin: 15px 0;
                page-break-inside: avoid;
            }}

            pre code {{
                background: none;
                border: none;
                padding: 0;
                color: #333;
            }}

            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 15px 0;
                page-break-inside: avoid;
            }}

            th {{
                background-color: #3498db;
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: 600;
            }}

            td {{
                border: 1px solid #ddd;
                padding: 10px;
            }}

            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}

            hr {{
                border: none;
                border-top: 1px solid #ddd;
                margin: 20px 0;
            }}

            blockquote {{
                border-left: 4px solid #3498db;
                padding-left: 15px;
                margin: 15px 0;
                color: #555;
                font-style: italic;
            }}

            a {{
                color: #3498db;
                text-decoration: none;
            }}

            .page-break {{
                page-break-before: always;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Generate PDF
    print(f"Generating PDF: {pdf_file}")
    HTML(string=full_html).write_pdf(pdf_file)

    print(f"✓ PDF generated successfully: {pdf_file}")
    print(f"  File size: {pdf_file.stat().st_size / 1024:.2f} KB")

if __name__ == "__main__":
    try:
        generate_pdf()
    except ImportError as e:
        print("Error: Required packages not installed.")
        print("Please install dependencies:")
        print("  pip install markdown2 weasyprint")
        print(f"\nDetails: {e}")
    except Exception as e:
        print(f"Error generating PDF: {e}")
        raise
