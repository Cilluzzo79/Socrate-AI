"""
Mermaid.js Mindmap Generator - Professional and Reliable
Much better than vis.js for consistent rendering and font control
"""

import re
from typing import Dict, List


# Simple template prompt that Claude can easily follow
MERMAID_MINDMAP_PROMPT = """PRIMA ANALIZZA LA STRUTTURA DEL DOCUMENTO, POI crea la mappa seguendo l'ordine del testo.

STEP 1 - ANALISI STRUTTURA (mentale, non scrivere):
- Identifica i capitoli/sezioni principali NEL LORO ORDINE
- Nota la gerarchia: cosa viene prima, cosa viene dopo
- Riconosci i temi raggruppati insieme dall'autore

STEP 2 - CREAZIONE MAPPA:
Crea una mappa concettuale FEDELE al testo, seguendo ESATTAMENTE questo formato:

=== MAPPA CONCETTUALE ===

TEMA_CENTRALE: [tema principale ESATTO dal testo - 3-6 parole]
DESCRIZIONE_CENTRALE: [definizione precisa in 1 frase]

---

RAMO_1: [Concetto LETTERALE - breve descrizione funzionale]
├─ [Sotto-concetto - cosa fa/rappresenta]
├─ [Sotto-concetto - cosa fa/rappresenta]
└─ [Sotto-concetto - cosa fa/rappresenta]

RAMO_2: [Concetto LETTERALE - breve descrizione funzionale]
├─ [Sotto-concetto - cosa fa/rappresenta]
├─ [Sotto-concetto - cosa fa/rappresenta]
└─ [Sotto-concetto - cosa fa/rappresenta]

RAMO_3: [Concetto LETTERALE - breve descrizione funzionale]
├─ [Sotto-concetto - cosa fa/rappresenta]
├─ [Sotto-concetto - cosa fa/rappresenta]
└─ [Sotto-concetto - cosa fa/rappresenta]

RAMO_4: [Concetto LETTERALE - breve descrizione funzionale]
├─ [Sotto-concetto - cosa fa/rappresenta]
└─ [Sotto-concetto - cosa fa/rappresenta]

---

COLLEGAMENTI:
• RAMO_1 <-> RAMO_2: [relazione ESATTA dal testo - MAX 8 parole]
• RAMO_2 <-> RAMO_3: [relazione ESATTA dal testo - MAX 8 parole]
• RAMO_3 <-> RAMO_4: [relazione ESATTA dal testo - MAX 8 parole]

=== FINE MAPPA ===

REGOLE CRITICHE - MASSIMA FEDELTÀ AL TESTO:

1. FEDELTÀ TERMINOLOGICA ASSOLUTA:
   - USA i termini ESATTI del documento (es. "Legge del Tre", NON "tre principi")
   - Se il testo dice "cosmologia" usa "cosmologia", non "universo"
   - Rispetta nomi propri, concetti tecnici e termini specifici dell'autore

2. ORDINE E STRUTTURA GERARCHICA OBBLIGATORI:
   - I RAMI devono seguire l'ORDINE di presentazione nel documento
   - RAMO_1 = primo concetto/capitolo presentato dall'autore
   - RAMO_2 = secondo concetto/capitolo, e così via in sequenza
   - I sotto-concetti seguono l'ordine in cui appaiono sotto quel tema
   - NON mescolare concetti da sezioni diverse
   - Raggruppa insieme solo ciò che l'autore ha raggruppato

3. NESSUNA INTERPRETAZIONE O PARAFRASI:
   - NON semplificare o generalizzare i concetti
   - NON usare sinonimi se l'autore usa un termine specifico
   - Se il testo dice "ottava cosmica" scrivi "ottava cosmica", non "scala universale"

4. QUALIFICAZIONE CON DESCRITTORI FUNZIONALI:
   - OGNI nodo deve includere un descrittore che spiega COSA FA o COSA RAPPRESENTA
   - Formato: "Termine esatto - breve descrizione funzionale"
   - Esempio CORRETTO: "Legge del Tre - tre forze in ogni fenomeno" ✓
   - Esempio SBAGLIATO: "Legge del Tre" ✗ (troppo generico, non qualificato)
   - Esempio CORRETTO: "Centro intellettuale - elaborazione pensieri logici" ✓
   - Esempio SBAGLIATO: "Centro intellettuale" ✗ (non spiega cosa fa)

5. VERIFICA INCROCIATA:
   - Prima di scrivere ogni ramo, cerca nel contesto il termine esatto
   - Ogni sotto-concetto deve essere effettivamente presente nel testo
   - I collegamenti devono riflettere relazioni esplicitamente menzionate

ESEMPIO CORRETTO (Gurdjieff):
RAMO: Legge del Tre - ogni fenomeno risulta da tre forze
├─ Forza Attiva - inizia il processo
├─ Forza Passiva - resiste al cambiamento
└─ Forza Neutralizzante - riconcilia le opposte

ESEMPIO SBAGLIATO:
RAMO: Tre Principi Fondamentali  [❌ termine non fedele]
├─ Principio positivo  [❌ non è la terminologia usata]
└─ Forza Attiva  [❌ manca descrittore funzionale]
"""


def parse_simple_mindmap(response: str) -> Dict:
    """
    Parse the simple template format into a structured dictionary.
    """
    # Extract central theme
    tema_match = re.search(r'TEMA_CENTRALE:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
    tema_centrale = tema_match.group(1).strip() if tema_match else "Concetto Centrale"

    # Extract central description
    desc_match = re.search(r'DESCRIZIONE_CENTRALE:\s*(.+?)(?:\n---|\\n\\n)', response, re.IGNORECASE | re.DOTALL)
    descrizione = desc_match.group(1).strip() if desc_match else "Mappa concettuale del documento"

    # Extract branches
    branches = []
    ramo_pattern = r'RAMO_(\d+):\s*(.+?)(?=\n(?:RAMO_|\-\-\-|COLLEGAMENTI|===))'

    for match in re.finditer(ramo_pattern, response, re.DOTALL):
        ramo_num = match.group(1)
        ramo_content = match.group(2)

        # Extract branch title (first line)
        lines = ramo_content.strip().split('\n')
        branch_title = lines[0].strip() if lines else f"Ramo {ramo_num}"

        # Extract sub-concepts
        sub_concepts = []
        for line in lines[1:]:
            if any(char in line for char in ['├', '└', '│']):
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
                clean_line = line.strip('•- ')
                connections.append(clean_line)

    return {
        "tema_centrale": tema_centrale,
        "descrizione": descrizione,
        "branches": branches,
        "connections": connections
    }


def escape_mermaid_text(text: str) -> str:
    """Escape special characters for Mermaid syntax"""
    # Remove or escape characters that break Mermaid syntax
    text = text.replace('"', "'")
    text = text.replace('[', '(')
    text = text.replace(']', ')')
    text = text.replace('{', '(')
    text = text.replace('}', ')')
    return text


def generate_mermaid_mindmap_html(data: Dict, document_title: str) -> str:
    """
    Generate a professional HTML visualization using Mermaid.js mindmap.
    """
    tema = escape_mermaid_text(data.get("tema_centrale", "Mappa Concettuale"))
    descrizione = data.get("descrizione", "")
    branches = data.get("branches", [])
    connections = data.get("connections", [])

    # Build Mermaid mindmap syntax
    mermaid_code = "mindmap\n"
    mermaid_code += f"  root(({tema}))\n"

    # Add branches and sub-concepts
    for i, branch in enumerate(branches):
        branch_title = escape_mermaid_text(branch["title"])
        mermaid_code += f"    {branch_title}\n"

        for sub in branch.get("sub_concepts", []):
            sub_text = escape_mermaid_text(sub)
            mermaid_code += f"      {sub_text}\n"

    html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mappa Concettuale - {document_title}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
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
            max-width: 1600px;
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
            background: white;
            border-radius: 15px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            position: relative;
            min-height: 800px;
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
                padding: 20px !important;
                box-shadow: none !important;
                background: white !important;
                border-radius: 0 !important;
                page-break-before: avoid !important;
            }}

            @page {{
                margin: 0.5cm;
                size: landscape;
            }}
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

        /* Mermaid styling - Modern, professional fonts */
        .mindmap-container svg {{
            max-width: 100%;
            height: auto;
        }}

        /* Professional node styling */
        .mindmap-container .node rect,
        .mindmap-container .node circle,
        .mindmap-container .node ellipse,
        .mindmap-container .node polygon {{
            stroke-width: 2px !important;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
        }}

        /* Modern, readable font styling */
        .mindmap-container .nodeLabel {{
            font-size: 15px !important;
            font-weight: 600 !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif !important;
            line-height: 1.4 !important;
            letter-spacing: 0.01em !important;
        }}

        /* Root node styling - slightly larger */
        .mindmap-container .nodeLabel:first-child {{
            font-size: 17px !important;
            font-weight: 700 !important;
        }}

        @media (max-width: 768px) {{
            .header h1 {{ font-size: 1.8rem; }}
            .mindmap-container {{ padding: 20px; }}
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
            <pre class="mermaid">
{mermaid_code}
            </pre>
        </div>

        <div class="connections-box">
            <h2>🔗 Collegamenti tra Concetti</h2>
            {''.join(f'<div class="connection-item">{conn}</div>' for conn in connections)}
        </div>

        <div class="footer">
            Generato da 🤖 Socrate AI • Powered by Claude Sonnet 4.5 & Mermaid.js
        </div>
    </div>

    <script>
        // Initialize Mermaid with modern, professional styling
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            themeVariables: {{
                fontSize: '15px',
                fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
                primaryColor: '#fca5a5',
                primaryTextColor: '#1a1a1a',
                primaryBorderColor: '#ef4444',
                lineColor: '#64748b',
                secondaryColor: '#67e8f9',
                tertiaryColor: '#ddd6fe',
                background: '#ffffff',
                mainBkg: '#fecaca',
                secondBkg: '#a5f3fc',
                tertiaryBkg: '#e9d5ff',
                nodeBorder: '#1a1a1a',
                clusterBkg: '#f8fafc',
                clusterBorder: '#cbd5e1'
            }},
            mindmap: {{
                padding: 40,
                useMaxWidth: true,
                nodeSpacing: 100,
                levelSpacing: 120
            }}
        }});
    </script>
</body>
</html>"""

    return html


def get_mermaid_mindmap_prompt(depth_level: int = 3, central_concept: str = None) -> str:
    """
    Return the mindmap prompt based on depth level and optional central concept.

    Args:
        depth_level: Depth of the mindmap (2-4)
            - 2: Superficiale (3 rami, 2 concetti per ramo)
            - 3: Media (4 rami, 3 concetti per ramo)
            - 4: Dettagliata (5 rami, 3-4 concetti per ramo)
        central_concept: Optional specific concept to focus on (e.g., "Legge del Tre", "Ray di Creazione")
                        If None, creates a general overview map of the entire document
    """
    depth_level = max(2, min(4, depth_level))  # Clamp between 2 and 4

    # Determine focus instruction based on central_concept
    if central_concept:
        focus_instruction = f"""
FOCUS SPECIFICO RICHIESTO:
- Il tema centrale della mappa DEVE essere: "{central_concept}"
- Tutti i rami devono esplorare SOLO aspetti, componenti e dettagli di "{central_concept}"
- Non creare una mappa generale del documento, ma una mappa specifica su questo argomento
- I rami sono le sotto-categorie/aspetti di "{central_concept}" come presentati nel testo
"""
    else:
        focus_instruction = """
MAPPA GENERALE DEL DOCUMENTO:
- Il tema centrale è l'argomento principale dell'intero documento
- I rami sono i capitoli/sezioni/temi principali del documento
- Crea una panoramica completa seguendo la struttura del testo
"""

    if depth_level == 2:
        # Superficiale: 3 rami, 2 concetti per ramo
        return f"""PRIMA ANALIZZA LA STRUTTURA DEL DOCUMENTO, POI crea la mappa seguendo l'ordine del testo.
{focus_instruction}
STEP 1 - ANALISI STRUTTURA (mentale, non scrivere):
- Identifica i 3 temi/capitoli PRINCIPALI nel loro ORDINE di apparizione
- Nota la sequenza logica dell'autore

STEP 2 - CREAZIONE MAPPA:
Crea una mappa concettuale SUPERFICIALE ma FEDELE al testo, seguendo ESATTAMENTE questo formato:

=== MAPPA CONCETTUALE ===

TEMA_CENTRALE: [tema principale ESATTO dal testo - 3-6 parole]
DESCRIZIONE_CENTRALE: [definizione precisa in 1 frase]

---

RAMO_1: [Concetto LETTERALE - breve descrizione funzionale]
├─ [Sotto-concetto - cosa fa/rappresenta]
└─ [Sotto-concetto - cosa fa/rappresenta]

RAMO_2: [Concetto LETTERALE - breve descrizione funzionale]
├─ [Sotto-concetto - cosa fa/rappresenta]
└─ [Sotto-concetto - cosa fa/rappresenta]

RAMO_3: [Concetto LETTERALE - breve descrizione funzionale]
├─ [Sotto-concetto - cosa fa/rappresenta]
└─ [Sotto-concetto - cosa fa/rappresenta]

---

COLLEGAMENTI:
• RAMO_1 <-> RAMO_2: [relazione ESATTA dal testo - MAX 8 parole]
• RAMO_2 <-> RAMO_3: [relazione ESATTA dal testo - MAX 8 parole]

=== FINE MAPPA ===

REGOLE CRITICHE:
1. Mappa SUPERFICIALE: 3 rami principali, 2 concetti per ramo
2. ORDINE OBBLIGATORIO: I rami seguono l'ordine di presentazione nel testo
3. MASSIMA FEDELTÀ TERMINOLOGICA: usa termini esatti del testo
4. QUALIFICAZIONE OBBLIGATORIA: Ogni nodo DEVE avere descrittore funzionale (formato: "Termine - cosa fa/rappresenta")
5. NO parafrasi o interpretazioni - solo contenuti letterali con descrittori
"""

    elif depth_level == 4:
        # Dettagliata: 5 rami, 3-4 concetti per ramo
        return f"""PRIMA ANALIZZA LA STRUTTURA DEL DOCUMENTO, POI crea la mappa seguendo l'ordine del testo.
{focus_instruction}
STEP 1 - ANALISI STRUTTURA (mentale, non scrivere):
- Identifica i 5 temi/capitoli principali nel loro ORDINE di apparizione
- Nota la gerarchia e la sequenza logica dell'autore
- Riconosci quali sotto-concetti appartengono a quale tema

STEP 2 - CREAZIONE MAPPA:
Crea una mappa concettuale DETTAGLIATA e FEDELE al testo, seguendo ESATTAMENTE questo formato:

=== MAPPA CONCETTUALE ===

TEMA_CENTRALE: [tema principale ESATTO dal testo - 3-6 parole]
DESCRIZIONE_CENTRALE: [definizione precisa in 1 frase]

---

RAMO_1: [Concetto LETTERALE - breve descrizione funzionale]
├─ [Sotto-concetto - cosa fa/rappresenta]
├─ [Sotto-concetto - cosa fa/rappresenta]
├─ [Sotto-concetto - cosa fa/rappresenta]
└─ [Sotto-concetto - cosa fa/rappresenta]

RAMO_2: [Concetto LETTERALE - breve descrizione funzionale]
├─ [Sotto-concetto - cosa fa/rappresenta]
├─ [Sotto-concetto - cosa fa/rappresenta]
├─ [Sotto-concetto - cosa fa/rappresenta]
└─ [Sotto-concetto - cosa fa/rappresenta]

RAMO_3: [Concetto LETTERALE - breve descrizione funzionale]
├─ [Sotto-concetto - cosa fa/rappresenta]
├─ [Sotto-concetto - cosa fa/rappresenta]
└─ [Sotto-concetto - cosa fa/rappresenta]

RAMO_4: [Concetto LETTERALE - breve descrizione funzionale]
├─ [Sotto-concetto - cosa fa/rappresenta]
├─ [Sotto-concetto - cosa fa/rappresenta]
└─ [Sotto-concetto - cosa fa/rappresenta]

RAMO_5: [Concetto LETTERALE - breve descrizione funzionale]
├─ [Sotto-concetto - cosa fa/rappresenta]
├─ [Sotto-concetto - cosa fa/rappresenta]
└─ [Sotto-concetto - cosa fa/rappresenta]

---

COLLEGAMENTI:
• RAMO_1 <-> RAMO_2: [relazione ESATTA dal testo - MAX 8 parole]
• RAMO_2 <-> RAMO_3: [relazione ESATTA dal testo - MAX 8 parole]
• RAMO_3 <-> RAMO_4: [relazione ESATTA dal testo - MAX 8 parole]
• RAMO_4 <-> RAMO_5: [relazione ESATTA dal testo - MAX 8 parole]

=== FINE MAPPA ===

REGOLE CRITICHE:
1. Mappa DETTAGLIATA: 5 rami principali, 3-4 concetti per ramo
2. ORDINE OBBLIGATORIO: I rami seguono l'ordine di presentazione nel testo
3. MASSIMA FEDELTÀ TERMINOLOGICA: usa termini esatti del testo
4. QUALIFICAZIONE OBBLIGATORIA: Ogni nodo DEVE avere descrittore funzionale (formato: "Termine - cosa fa/rappresenta")
5. NO parafrasi o interpretazioni - solo contenuti letterali con descrittori
"""

    else:  # depth_level == 3 (default)
        # Media: 4 rami, 3 concetti per ramo
        return f"""PRIMA ANALIZZA LA STRUTTURA DEL DOCUMENTO, POI crea la mappa seguendo l'ordine del testo.
{focus_instruction}
STEP 1 - ANALISI STRUTTURA (mentale, non scrivere):
- Identifica i capitoli/sezioni principali NEL LORO ORDINE
- Nota la gerarchia: cosa viene prima, cosa viene dopo
- Riconosci i temi raggruppati insieme dall'autore

STEP 2 - CREAZIONE MAPPA:
{MERMAID_MINDMAP_PROMPT}"""
