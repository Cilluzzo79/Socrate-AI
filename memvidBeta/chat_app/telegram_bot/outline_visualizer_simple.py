"""
Simple Outline Visualizer - Direct text rendering with beautiful styling
Preserves all original formatting while adding interactivity
"""

import re
from pathlib import Path
import base64


def encode_logo(logo_path: str = None) -> str:
    """Encode logo to base64 or return SVG placeholder."""
    if logo_path and Path(logo_path).exists():
        try:
            with open(logo_path, 'rb') as f:
                logo_data = base64.b64encode(f.read()).decode('utf-8')
                ext = Path(logo_path).suffix.lower()
                mime_type = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.svg': 'image/svg+xml'
                }.get(ext, 'image/png')
                return f"data:{mime_type};base64,{logo_data}"
        except:
            pass

    return """data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 60'%3E%3Ctext x='10' y='40' font-family='Arial Black' font-size='32' fill='%2306b6d4'%3ESocrate AI%3C/text%3E%3C/svg%3E"""


def generate_simple_outline_html(outline_text: str, document_title: str, outline_type: str, detail_level: str, logo_path: str = None) -> str:
    """
    Generate beautiful HTML that preserves the original outline formatting.
    No parsing required - just wrap the text in beautiful styling.
    """

    logo_uri = encode_logo(logo_path)

    # Convert outline text to HTML, preserving structure
    html_content = ""
    lines = outline_text.split('\n')

    for line in lines:
        # Skip empty lines
        if not line.strip():
            html_content += '<br>\n'
            continue

        # Detect hierarchy level by indentation
        stripped = line.lstrip()
        indent_level = len(line) - len(stripped)

        # Apply styling based on patterns
        css_class = "content-line"

        # Main sections (##, Roman numerals, emojis)
        if re.match(r'^##\s+|^📖|^📚|^📝|^[IVX]+\.\s+', stripped):
            css_class = "section-main"
        # Subsections
        elif re.match(r'^###\s+|^📌|^📍|^[A-Z]\.\s+|^\d+\.\d+', stripped):
            css_class = "section-sub"
        # List items
        elif re.match(r'^[-•*►▸├└│]\s+', stripped):
            css_class = "list-item"
        # Decorative separators
        elif re.match(r'^[=\-_]{3,}$', stripped):
            css_class = "separator"

        # Add indentation
        indent_px = min(indent_level * 2, 100)  # Cap at 100px

        # Escape HTML
        escaped = stripped.replace('<', '&lt;').replace('>', '&gt;')

        html_content += f'<div class="{css_class}" style="padding-left: {indent_px}px">{escaped}</div>\n'

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Schema Interattivo - {document_title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', 'Consolas', 'Monaco', monospace;
            background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%);
            color: #e2e8f0;
            line-height: 1.8;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: #15151f;
            border-radius: 20px;
            border: 2px solid rgba(6, 182, 212, 0.3);
            box-shadow: 0 0 40px rgba(6, 182, 212, 0.2);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #06b6d4 0%, #a855f7 100%);
            padding: 40px;
            text-align: center;
            position: relative;
        }}

        .header img {{
            height: 50px;
            margin-bottom: 20px;
        }}

        .header h1 {{
            font-size: 2rem;
            color: white;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}

        .header-meta {{
            color: rgba(255, 255, 255, 0.9);
            font-size: 1rem;
        }}

        .content {{
            padding: 40px;
            font-size: 15px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        }}

        .section-main {{
            font-size: 1.4em;
            font-weight: bold;
            color: #06b6d4;
            margin-top: 30px;
            margin-bottom: 15px;
            padding: 15px;
            background: rgba(6, 182, 212, 0.1);
            border-left: 4px solid #06b6d4;
            border-radius: 4px;
        }}

        .section-sub {{
            font-size: 1.2em;
            font-weight: bold;
            color: #a855f7;
            margin-top: 20px;
            margin-bottom: 10px;
            padding: 10px;
            background: rgba(168, 85, 247, 0.1);
            border-left: 3px solid #a855f7;
            border-radius: 4px;
        }}

        .list-item {{
            color: #cbd5e1;
            margin: 8px 0;
            padding: 8px 15px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 4px;
            transition: all 0.2s;
        }}

        .list-item:hover {{
            background: rgba(6, 182, 212, 0.05);
            transform: translateX(5px);
        }}

        .content-line {{
            color: #94a3b8;
            margin: 6px 0;
            padding: 6px 10px;
        }}

        .separator {{
            color: rgba(6, 182, 212, 0.3);
            margin: 20px 0;
            text-align: center;
        }}

        .print-button {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(6, 182, 212, 0.4);
            transition: all 0.3s;
            z-index: 1000;
        }}

        .print-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(6, 182, 212, 0.5);
        }}

        @media print {{
            body {{
                background: white;
                color: black;
            }}

            .container {{
                border: none;
                box-shadow: none;
                background: white;
            }}

            .print-button {{
                display: none;
            }}

            .section-main {{
                color: #000;
                background: #f0f0f0;
            }}

            .section-sub {{
                color: #333;
                background: #f8f8f8;
            }}

            .list-item, .content-line {{
                color: #000;
            }}
        }}

        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.5rem;
            }}

            .content {{
                padding: 20px;
                font-size: 13px;
            }}
        }}
    </style>
</head>
<body>
    <button class="print-button" onclick="window.print()">🖨️ Stampa / Salva PDF</button>

    <div class="container">
        <div class="header">
            <img src="{logo_uri}" alt="Logo">
            <h1>📋 Schema Interattivo</h1>
            <div class="header-meta">
                <strong>{document_title}</strong><br>
                Tipo: {outline_type} • Dettaglio: {detail_level}
            </div>
        </div>

        <div class="content">
            {html_content}
        </div>
    </div>

    <script>
        // Add smooth scroll behavior
        document.querySelectorAll('.section-main, .section-sub').forEach(el => {{
            el.style.cursor = 'pointer';
            el.addEventListener('click', function() {{
                // Highlight on click
                this.style.background = 'rgba(6, 182, 212, 0.2)';
                setTimeout(() => {{
                    this.style.background = '';
                }}, 300);
            }});
        }});
    </script>
</body>
</html>"""
