"""
Professional Outline Visualizer - Interactive HTML with accordion layout
Creates beautiful, study-friendly outline visualizations
"""

import re
from typing import Dict, List, Tuple
import base64
from pathlib import Path


def parse_outline_text(outline_text: str) -> Dict:
    """
    Parse outline text into structured sections.
    Handles various outline formats (hierarchical, chronological, thematic).
    """
    sections = []
    current_section = None
    current_subsection = None

    lines = outline_text.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect main sections (usually start with I, II, 1, 2, or have markdown headers)
        if re.match(r'^#+\s+', line) or re.match(r'^[IVX]+\.|^\d+\.|^[A-Z]\)', line):
            # Main section
            title = re.sub(r'^#+\s+|^[IVX]+\.|^\d+\.|^[A-Z]\)\s*', '', line)
            if current_section:
                sections.append(current_section)
            current_section = {
                'title': title,
                'subsections': [],
                'content': []
            }
            current_subsection = None

        # Detect subsections (indented or with letters/numbers)
        elif re.match(r'^\s+[a-z]\)|^\s+\d+\)|^\s+-\s+\*\*', line):
            # Subsection
            title = re.sub(r'^\s+[a-z]\)|^\s+\d+\)|^\s+-\s+\*\*|\*\*\s*', '', line).strip()
            if current_section:
                if current_subsection:
                    current_section['subsections'].append(current_subsection)
                current_subsection = {
                    'title': title,
                    'content': []
                }

        # Regular content
        elif current_section:
            content_line = line.strip('- •*')
            if current_subsection:
                current_subsection['content'].append(content_line)
            else:
                current_section['content'].append(content_line)

    # Add last section
    if current_subsection and current_section:
        current_section['subsections'].append(current_subsection)
    if current_section:
        sections.append(current_section)

    return {'sections': sections}


def encode_logo(logo_path: str = None) -> str:
    """
    Encode logo image to base64 for embedding in HTML.
    Returns a data URI or placeholder SVG.
    """
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
        except Exception as e:
            print(f"Error loading logo: {e}")

    # Default SVG logo placeholder
    return """data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 60'%3E%3Ctext x='10' y='40' font-family='Arial Black' font-size='32' fill='%2306b6d4'%3ESocrate AI%3C/text%3E%3C/svg%3E"""


def generate_outline_html(outline_data: Dict, document_title: str, outline_type: str, detail_level: str, logo_path: str = None) -> str:
    """
    Generate beautiful interactive HTML for outline visualization.

    Args:
        outline_data: Structured outline data
        document_title: Title of the document
        outline_type: Type of outline (hierarchical, chronological, thematic)
        detail_level: Level of detail (brief, medium, detailed)
        logo_path: Optional path to logo image
    """

    sections = outline_data.get('sections', [])
    logo_data_uri = encode_logo(logo_path)

    # Map types to Italian
    type_map = {
        'hierarchical': 'Gerarchico',
        'chronological': 'Cronologico',
        'thematic': 'Tematico'
    }
    detail_map = {
        'brief': 'Sintetico',
        'medium': 'Medio',
        'detailed': 'Dettagliato'
    }

    type_display = type_map.get(outline_type, outline_type)
    detail_display = detail_map.get(detail_level, detail_level)

    # Generate table of contents
    toc_html = ""
    for i, section in enumerate(sections):
        toc_html += f'<a href="#section-{i}" class="toc-item" onclick="scrollToSection({i})">{section["title"]}</a>\n'

    # Generate sections HTML
    sections_html = ""
    for i, section in enumerate(sections):
        sections_html += f"""
        <div class="section" id="section-{i}">
            <div class="section-header" onclick="toggleSection({i})">
                <h2>
                    <span class="section-number">{i + 1}</span>
                    {section['title']}
                    <span class="toggle-icon">▼</span>
                </h2>
            </div>
            <div class="section-content" id="content-{i}">
        """

        # Main section content
        if section.get('content'):
            sections_html += '<div class="section-main-content">\n'
            for content_line in section['content']:
                if content_line:
                    sections_html += f'<p>• {content_line}</p>\n'
            sections_html += '</div>\n'

        # Subsections
        for j, subsection in enumerate(section.get('subsections', [])):
            sections_html += f"""
            <div class="subsection">
                <h3 onclick="toggleSubsection({i}, {j})">
                    {subsection['title']}
                    <span class="toggle-icon-small">▶</span>
                </h3>
                <div class="subsection-content" id="subcontent-{i}-{j}">
            """
            for content_line in subsection.get('content', []):
                if content_line:
                    sections_html += f'<p>• {content_line}</p>\n'
            sections_html += '</div>\n</div>\n'

        sections_html += '</div>\n</div>\n'

    html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Schema - {document_title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%);
            color: #e2e8f0;
            line-height: 1.6;
        }}

        .header {{
            background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%);
            padding: 30px;
            box-shadow: 0 4px 20px rgba(6, 182, 212, 0.3);
            position: sticky;
            top: 0;
            z-index: 100;
        }}

        .header-content {{
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            gap: 20px;
        }}

        .logo {{
            height: 50px;
            width: auto;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
        }}

        .header-text {{
            flex: 1;
        }}

        .header h1 {{
            font-size: 1.8rem;
            color: white;
            margin-bottom: 5px;
        }}

        .header-meta {{
            color: rgba(255, 255, 255, 0.9);
            font-size: 0.9rem;
        }}

        .print-button {{
            background: white;
            color: #06b6d4;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }}

        .print-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}

        .container {{
            display: flex;
            max-width: 1400px;
            margin: 0 auto;
            min-height: calc(100vh - 110px);
        }}

        .sidebar {{
            width: 280px;
            background: #1e293b;
            padding: 20px;
            overflow-y: auto;
            position: sticky;
            top: 110px;
            height: calc(100vh - 110px);
            border-right: 2px solid #334155;
        }}

        .sidebar h3 {{
            color: #06b6d4;
            margin-bottom: 15px;
            font-size: 1.1rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .toc-item {{
            display: block;
            padding: 10px 15px;
            margin-bottom: 5px;
            background: #0f172a;
            border-radius: 8px;
            color: #cbd5e1;
            text-decoration: none;
            transition: all 0.2s ease;
            border-left: 3px solid transparent;
        }}

        .toc-item:hover, .toc-item.active {{
            background: #1e40af;
            border-left-color: #06b6d4;
            transform: translateX(5px);
            color: white;
        }}

        .main-content {{
            flex: 1;
            padding: 30px;
            overflow-y: auto;
        }}

        .section {{
            background: #1e293b;
            margin-bottom: 20px;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }}

        .section:hover {{
            box-shadow: 0 6px 20px rgba(6, 182, 212, 0.2);
        }}

        .section-header {{
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            padding: 20px;
            cursor: pointer;
            user-select: none;
            transition: all 0.3s ease;
        }}

        .section-header:hover {{
            background: linear-gradient(135deg, #2563eb 0%, #60a5fa 100%);
        }}

        .section-header h2 {{
            color: white;
            font-size: 1.4rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .section-number {{
            display: inline-block;
            width: 35px;
            height: 35px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 50%;
            text-align: center;
            line-height: 35px;
            margin-right: 15px;
            font-size: 1rem;
        }}

        .toggle-icon {{
            transition: transform 0.3s ease;
            font-size: 0.8em;
        }}

        .section-header.collapsed .toggle-icon {{
            transform: rotate(-90deg);
        }}

        .section-content {{
            padding: 25px;
            max-height: 2000px;
            overflow: hidden;
            transition: max-height 0.5s ease, padding 0.3s ease;
        }}

        .section-content.collapsed {{
            max-height: 0;
            padding: 0 25px;
        }}

        .section-main-content {{
            margin-bottom: 20px;
        }}

        .section-main-content p {{
            color: #cbd5e1;
            margin-bottom: 10px;
            padding-left: 10px;
        }}

        .subsection {{
            background: #0f172a;
            margin: 15px 0;
            border-radius: 8px;
            overflow: hidden;
            border-left: 4px solid #06b6d4;
        }}

        .subsection h3 {{
            color: #06b6d4;
            padding: 15px;
            cursor: pointer;
            user-select: none;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.2s ease;
        }}

        .subsection h3:hover {{
            background: rgba(6, 182, 212, 0.1);
        }}

        .toggle-icon-small {{
            transition: transform 0.3s ease;
            font-size: 0.7em;
        }}

        .subsection h3.collapsed .toggle-icon-small {{
            transform: rotate(0deg);
        }}

        .subsection h3:not(.collapsed) .toggle-icon-small {{
            transform: rotate(90deg);
        }}

        .subsection-content {{
            padding: 0 15px 15px 15px;
            max-height: 1000px;
            overflow: hidden;
            transition: max-height 0.4s ease, padding 0.3s ease;
        }}

        .subsection-content.collapsed {{
            max-height: 0;
            padding: 0 15px;
        }}

        .subsection-content p {{
            color: #94a3b8;
            margin-bottom: 8px;
            padding-left: 10px;
        }}

        .footer {{
            text-align: center;
            padding: 30px;
            color: #64748b;
            background: #0f172a;
            margin-top: 40px;
        }}

        @media print {{
            body {{
                background: white;
                color: black;
            }}

            .header {{
                position: static;
                background: white;
                border-bottom: 2px solid #ccc;
            }}

            .header h1, .header-meta {{
                color: black;
            }}

            .print-button, .sidebar, .footer {{
                display: none;
            }}

            .container {{
                display: block;
            }}

            .main-content {{
                padding: 20px;
            }}

            .section {{
                background: white;
                border: 1px solid #ccc;
                page-break-inside: avoid;
                box-shadow: none;
            }}

            .section-header {{
                background: #f3f4f6 !important;
                color: black !important;
            }}

            .section-header h2 {{
                color: black !important;
            }}

            .section-content {{
                display: block !important;
                max-height: none !important;
                padding: 20px !important;
            }}

            .subsection {{
                background: #f9fafb;
                border-left-color: #999;
            }}

            .subsection h3 {{
                color: #333 !important;
            }}

            .subsection-content {{
                display: block !important;
                max-height: none !important;
                padding: 15px !important;
            }}

            .toggle-icon, .toggle-icon-small {{
                display: none;
            }}
        }}

        @media (max-width: 768px) {{
            .sidebar {{
                display: none;
            }}

            .header-content {{
                flex-direction: column;
                align-items: flex-start;
            }}

            .logo {{
                height: 40px;
            }}

            .main-content {{
                padding: 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <img src="{logo_data_uri}" alt="Logo" class="logo">
            <div class="header-text">
                <h1>📑 Schema: {document_title}</h1>
                <div class="header-meta">
                    Tipo: {type_display} • Dettaglio: {detail_display}
                </div>
            </div>
            <button class="print-button" onclick="window.print()">🖨️ Stampa / PDF</button>
        </div>
    </div>

    <div class="container">
        <nav class="sidebar">
            <h3>📋 Indice</h3>
            {toc_html}
        </nav>

        <main class="main-content">
            {sections_html}
        </main>
    </div>

    <div class="footer">
        Generato da 🤖 Socrate AI • Powered by Claude Sonnet 4.5
    </div>

    <script>
        function toggleSection(index) {{
            const content = document.getElementById(`content-${{index}}`);
            const header = content.previousElementSibling;
            content.classList.toggle('collapsed');
            header.classList.toggle('collapsed');
        }}

        function toggleSubsection(sectionIndex, subIndex) {{
            const content = document.getElementById(`subcontent-${{sectionIndex}}-${{subIndex}}`);
            const header = content.previousElementSibling;
            content.classList.toggle('collapsed');
            header.classList.toggle('collapsed');
        }}

        function scrollToSection(index) {{
            const section = document.getElementById(`section-${{index}}`);
            section.scrollIntoView({{ behavior: 'smooth', block: 'start' }});

            // Highlight active TOC item
            document.querySelectorAll('.toc-item').forEach(item => item.classList.remove('active'));
            event.target.classList.add('active');

            // Expand section if collapsed
            const content = document.getElementById(`content-${{index}}`);
            const header = content.previousElementSibling;
            if (content.classList.contains('collapsed')) {{
                content.classList.remove('collapsed');
                header.classList.remove('collapsed');
            }}
        }}

        // Expand all sections by default
        document.addEventListener('DOMContentLoaded', function() {{
            // All sections start expanded
        }});
    </script>
</body>
</html>"""

    return html


def get_outline_visualizer_prompt() -> str:
    """Return prompt for generating well-structured outlines."""
    return """Per favore genera uno schema ben strutturato e organizzato.

FORMATO RICHIESTO:
- Usa titoli chiari per le sezioni principali (preceduti da # o numeri romani I, II, III)
- Usa sotto-titoli per le sottosezioni (preceduti da a), b), c) o numeri)
- Usa punti elenco per i dettagli (- o •)
- Mantieni una gerarchia chiara e consistente

Esempio di formato:
# I. Sezione Principale
- Punto importante della sezione
- Altro punto rilevante

    a) Prima sottosezione
    - Dettaglio della sottosezione
    - Altro dettaglio

    b) Seconda sottosezione
    - Contenuto specifico
    - Informazione rilevante

# II. Seconda Sezione Principale
...
"""
