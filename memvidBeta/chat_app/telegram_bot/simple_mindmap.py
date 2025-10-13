"""
Simple Linear Mindmap Generator - Template-based approach
Much more reliable than complex JSON generation
"""

import re
import json
from typing import Dict, List, Tuple


# Simple template prompt that Claude can easily follow
SIMPLE_MINDMAP_PROMPT = """Crea una mappa concettuale CONCISA per studiare, seguendo ESATTAMENTE questo formato:

=== MAPPA CONCETTUALE ===

TEMA_CENTRALE: [tema principale in 3-6 parole chiave]
DESCRIZIONE_CENTRALE: [spiega in 1 frase]

---

RAMO_1: [Concetto chiave - MAX 5 parole]
├─ [Parola chiave o frase brevissima - MAX 5 parole]
├─ [Parola chiave o frase brevissima - MAX 5 parole]
└─ [Parola chiave o frase brevissima - MAX 5 parole]

RAMO_2: [Concetto chiave - MAX 5 parole]
├─ [Parola chiave o frase brevissima - MAX 5 parole]
├─ [Parola chiave o frase brevissima - MAX 5 parole]
└─ [Parola chiave o frase brevissima - MAX 5 parole]

RAMO_3: [Concetto chiave - MAX 5 parole]
├─ [Parola chiave o frase brevissima - MAX 5 parole]
├─ [Parola chiave o frase brevissima - MAX 5 parole]
└─ [Parola chiave o frase brevissima - MAX 5 parole]

RAMO_4: [Concetto chiave - MAX 5 parole]
├─ [Parola chiave o frase brevissima - MAX 5 parole]
└─ [Parola chiave o frase brevissima - MAX 5 parole]

RAMO_5: [Concetto chiave - MAX 5 parole]
├─ [Parola chiave o frase brevissima - MAX 5 parole]
└─ [Parola chiave o frase brevissima - MAX 5 parole]

---

COLLEGAMENTI:
• RAMO_1 <-> RAMO_2: [breve relazione - MAX 8 parole]
• RAMO_2 <-> RAMO_3: [breve relazione - MAX 8 parole]
• RAMO_4 <-> RAMO_5: [breve relazione - MAX 8 parole]

=== FINE MAPPA ===

REGOLE CRITICHE PER LO STUDIO:
1. USA SOLO PAROLE CHIAVE E FRASI BREVISSIME (3-5 parole massimo)
2. NO frasi complete o spiegazioni lunghe
3. Pensa a come uno studente memorizzerebbe visivamente
4. Ogni nodo deve essere IMMEDIATAMENTE leggibile e memorizzabile
5. Usa contenuti REALI dal documento ma in forma ultra-sintetica
"""


def parse_simple_mindmap(response: str) -> Dict:
    """
    Parse the simple template format into a structured dictionary.
    Much more reliable than JSON parsing.
    """

    # Extract central theme
    tema_match = re.search(r'TEMA_CENTRALE:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
    tema_centrale = tema_match.group(1).strip() if tema_match else "Concetto Centrale"

    # Extract central description
    desc_match = re.search(r'DESCRIZIONE_CENTRALE:\s*(.+?)(?:\n---|\n\n)', response, re.IGNORECASE | re.DOTALL)
    descrizione = desc_match.group(1).strip() if desc_match else "Mappa concettuale del documento"

    # Extract branches (RAMO_1, RAMO_2, etc.)
    branches = []
    ramo_pattern = r'RAMO_(\d+):\s*(.+?)(?=\n(?:RAMO_|\-\-\-|COLLEGAMENTI|===))'

    for match in re.finditer(ramo_pattern, response, re.DOTALL):
        ramo_num = match.group(1)
        ramo_content = match.group(2)

        # Extract branch title (first line)
        lines = ramo_content.strip().split('\n')
        branch_title = lines[0].strip() if lines else f"Ramo {ramo_num}"

        # Extract sub-concepts (lines with ├─ or └─)
        sub_concepts = []
        for line in lines[1:]:
            # Match lines with tree characters
            if any(char in line for char in ['├', '└', '│']):
                # Clean the line
                clean_line = re.sub(r'[├└│─\s]+', '', line, count=1).strip()
                if clean_line and len(clean_line) > 3:
                    sub_concepts.append(clean_line)

        branches.append({
            "title": branch_title,
            "sub_concepts": sub_concepts
        })

    # Extract connections
    connections = []
    conn_section = re.search(r'COLLEGAMENTI:\s*(.+?)(?=\n===|$)', response, re.DOTALL | re.IGNORECASE)
    if conn_section:
        conn_lines = conn_section.group(1).strip().split('\n')
        for line in conn_lines:
            if '<->' in line or '→' in line or '->' in line:
                # Extract connection
                clean_line = line.strip('•- ')
                connections.append(clean_line)

    return {
        "tema_centrale": tema_centrale,
        "descrizione": descrizione,
        "branches": branches,
        "connections": connections
    }


def generate_simple_mindmap_html(data: Dict, document_title: str) -> str:
    """
    Generate a beautiful HTML visualization using Chart.js tree chart.
    """

    tema = data.get("tema_centrale", "Mappa Concettuale")
    descrizione = data.get("descrizione", "")
    branches = data.get("branches", [])
    connections = data.get("connections", [])

    # Build Chart.js hierarchical data
    chart_nodes = []
    chart_edges = []

    # Central node - MASSIMA GRANDEZZA
    chart_nodes.append({
        "id": "central",
        "label": tema,
        "level": 0,
        "color": {
            "background": "#0891b2",
            "border": "#0e7490",
            "highlight": {
                "background": "#06b6d4",
                "border": "#0891b2"
            }
        },
        "font": {
            "size": 120,
            "color": "#000000",
            "face": "Arial Black",
            "bold": True
        }
    })

    # Branch nodes
    for i, branch in enumerate(branches):
        branch_id = f"branch_{i}"
        # Colori con più contrasto e testo nero
        colors = [
            {"bg": "#fca5a5", "border": "#dc2626", "highlight": "#ef4444"},  # Rosso
            {"bg": "#67e8f9", "border": "#0891b2", "highlight": "#06b6d4"},  # Cyan
            {"bg": "#d8b4fe", "border": "#7c3aed", "highlight": "#a855f7"},  # Viola
            {"bg": "#93c5fd", "border": "#1d4ed8", "highlight": "#3b82f6"},  # Blu
            {"bg": "#fcd34d", "border": "#d97706", "highlight": "#f59e0b"}   # Giallo
        ]
        branch_color = colors[i % 5]

        chart_nodes.append({
            "id": branch_id,
            "label": branch["title"],
            "level": 1,
            "color": {
                "background": branch_color["bg"],
                "border": branch_color["border"],
                "highlight": {
                    "background": branch_color["highlight"],
                    "border": branch_color["border"]
                }
            },
            "font": {
                "size": 90,
                "color": "#000000",
                "face": "Arial Black",
                "bold": True
            }
        })
        chart_edges.append({"from": "central", "to": branch_id})

        # Sub-concept nodes
        for j, sub in enumerate(branch.get("sub_concepts", [])):
            sub_id = f"sub_{i}_{j}"
            chart_nodes.append({
                "id": sub_id,
                "label": sub,
                "level": 2,
                "color": {
                    "background": branch_color["bg"],
                    "border": branch_color["border"],
                    "highlight": {
                        "background": branch_color["highlight"],
                        "border": branch_color["border"]
                    }
                },
                "font": {
                    "size": 70,
                    "color": "#000000",
                    "face": "Arial",
                    "bold": True
                }
            })
            chart_edges.append({"from": branch_id, "to": sub_id})

    html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mappa Concettuale - {document_title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%);
            color: #e2e8f0;
            min-height: 100vh;
            padding: 20px;
            margin: 0;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            background: linear-gradient(135deg, #06b6d4 0%, #a855f7 100%);
            padding: 40px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(6, 182, 212, 0.3);
        }}

        .header h1 {{
            font-size: 2.5rem;
            color: white;
            margin-bottom: 10px;
        }}

        .header .subtitle {{
            font-size: 1.2rem;
            color: rgba(255, 255, 255, 0.9);
        }}

        .description-box {{
            background: #1e293b;
            border: 2px solid #06b6d4;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }}

        .description-box h2 {{
            color: #06b6d4;
            margin-bottom: 10px;
            font-size: 1.3rem;
        }}

        .description-box p {{
            line-height: 1.6;
            color: #cbd5e1;
        }}

        .mindmap-container {{
            background: #1e293b;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            position: relative;
        }}

        .print-button {{
            position: absolute;
            top: 30px;
            right: 30px;
            background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(6, 182, 212, 0.4);
            transition: all 0.3s ease;
            z-index: 1000;
        }}

        .print-button:hover {{
            background: linear-gradient(135deg, #0891b2 0%, #06b6d4 100%);
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(6, 182, 212, 0.5);
        }}

        @media print {{
            * {{
                margin: 0 !important;
                padding: 0 !important;
            }}

            html, body {{
                margin: 0 !important;
                padding: 0 !important;
                height: 100% !important;
                background: white !important;
            }}

            .header, .description-box, .connections-box, .footer, .print-button {{
                display: none !important;
            }}

            .container {{
                margin: 0 !important;
                padding: 0 !important;
                max-width: 100% !important;
            }}

            .mindmap-container {{
                margin: 0 !important;
                padding: 0 !important;
                box-shadow: none !important;
                background: white !important;
                border-radius: 0 !important;
                page-break-before: avoid !important;
            }}

            #network {{
                height: 100vh !important;
                width: 100vw !important;
                border: none !important;
                border-radius: 0 !important;
                background: white !important;
                page-break-before: avoid !important;
            }}

            @page {{
                margin: 0;
                size: landscape;
            }}
        }}

        #network {{
            height: 2400px;
            border: 2px solid #334155;
            border-radius: 10px;
            background: #0f172a;
        }}

        .connections-box {{
            background: #1e293b;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }}

        .connections-box h2 {{
            color: #06b6d4;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }}

        .connection-item {{
            background: #0f172a;
            padding: 12px 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid #a855f7;
            color: #cbd5e1;
        }}

        .footer {{
            text-align: center;
            padding: 20px;
            color: #64748b;
            margin-top: 30px;
        }}

        @media (max-width: 768px) {{
            .header h1 {{ font-size: 1.8rem; }}
            #network {{ height: 500px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🗺️ Mappa Concettuale</h1>
            <div class="subtitle">{document_title}</div>
        </div>

        <div class="description-box">
            <h2>🎯 {tema}</h2>
            <p>{descrizione}</p>
        </div>

        <div class="mindmap-container">
            <button class="print-button" onclick="window.print()">🖨️ Stampa / Salva PDF</button>
            <div id="network"></div>
        </div>

        <div class="connections-box">
            <h2>🔗 Collegamenti tra Concetti</h2>
            {''.join(f'<div class="connection-item">{conn}</div>' for conn in connections)}
        </div>

        <div class="footer">
            Generato da 🤖 Socrate AI • Powered by Claude Sonnet 4.5
        </div>
    </div>

    <script>
        // Create network graph with vis.js
        const container = document.getElementById('network');

        const nodes = new vis.DataSet({json.dumps(chart_nodes, ensure_ascii=False)});

        const edges = new vis.DataSet({json.dumps(chart_edges, ensure_ascii=False)});

        const data = {{ nodes: nodes, edges: edges }};

        const options = {{
            nodes: {{
                shape: 'box',
                margin: 50,
                widthConstraint: {{ minimum: 500, maximum: 1200 }},
                heightConstraint: {{ minimum: 120 }},
                borderWidth: 6,
                shadow: true
            }},
            edges: {{
                width: 2,
                color: {{ color: '#475569', highlight: '#06b6d4' }},
                smooth: {{
                    type: 'cubicBezier',
                    forceDirection: 'vertical',
                    roundness: 0.4
                }}
            }},
            layout: {{
                hierarchical: {{
                    direction: 'UD',
                    sortMethod: 'directed',
                    nodeSpacing: 800,
                    levelSeparation: 800,
                    treeSpacing: 600,
                    blockShifting: true,
                    edgeMinimization: true,
                    parentCentralization: true
                }}
            }},
            physics: {{
                enabled: false
            }},
            autoResize: true,
            interaction: {{
                dragNodes: true,
                dragView: true,
                zoomView: true,
                hover: true
            }}
        }};

        const network = new vis.Network(container, data, options);

        // Add click interaction
        network.on('click', function(params) {{
            if (params.nodes.length > 0) {{
                const nodeId = params.nodes[0];
                const node = nodes.get(nodeId);
                // Determina il tipo di nodo per il messaggio
                let tipoNodo = nodeId === 'central' ? 'Tema centrale' :
                              (nodeId.startsWith('branch_') ? 'Questo ramo' : 'Questo concetto');
                alert(tipoNodo + ' dice:\\n\\n' + node.label);
            }}
        }});
    </script>
</body>
</html>"""

    return html


def get_simple_mindmap_prompt() -> str:
    """Return the simple template prompt."""
    return SIMPLE_MINDMAP_PROMPT
