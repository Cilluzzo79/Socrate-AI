"""
Content generation utilities for creating structured outputs like quizzes, outlines, and mind maps.
These specialized prompts work with the Socrates personality to create high-quality educational content.
"""

from typing import Dict, Any, Optional, List
import json


# Template prompts for different content types

QUIZ_GENERATION_PROMPT = """
Basandoti sul contesto fornito, genera un quiz completo e strutturato secondo le seguenti specifiche:

**IMPORTANTE: Il tuo output deve contenere SOLO il quiz formattato, senza note procedurali, frasi introduttive o commenti sul processo. Inizia direttamente con il titolo del quiz.**

**Tipo di Quiz:** {quiz_type}
**Numero di Domande:** {num_questions}
**Livello di Difficoltà:** {difficulty}
**Focus:** {focus_area}

**Requisiti del Quiz:**

1. **Varietà delle Domande:**
   - Per quiz a scelta multipla: fornisci 4 opzioni per ogni domanda
   - Per quiz vero/falso: includi una spiegazione del perché
   - Per domande a risposta breve: fornisci anche le risposte corrette attese

2. **Struttura:**
   - Numerazione chiara di tutte le domande
   - Riferimenti espliciti al testo quando rilevante (es. "Secondo la pagina X...")
   - Gradazione della difficoltà se richiesto

3. **Contenuto Educativo:**
   - Ogni domanda deve testare una comprensione significativa
   - Evita domande banali o troppo mnemoniche
   - Includi domande che richiedono analisi, sintesi o applicazione

4. **Risposte e Spiegazioni:**
   - Fornisci le risposte corrette alla fine del quiz
   - Aggiungi brevi spiegazioni per ogni risposta corretta
   - Per le opzioni sbagliate nelle domande a scelta multipla, spiega perché sono errate

**Formato di Output:**
```
# Quiz: [Titolo descrittivo]

## Istruzioni
[Istruzioni chiare su come completare il quiz]

## Domande

### Domanda 1
[Testo della domanda]

A) [Opzione A]
B) [Opzione B]
C) [Opzione C]
D) [Opzione D]

[Ripeti per tutte le domande]

---

## Risposte Corrette

1. **Risposta corretta:** [Lettera o risposta]
   **Spiegazione:** [Breve spiegazione del perché questa è la risposta corretta]
   
[Ripeti per tutte le domande]
```

Genera ora il quiz basandoti sul contenuto fornito.
"""


OUTLINE_GENERATION_PROMPT = """
Crea uno schema gerarchico dettagliato e visivamente ricco del documento o della sezione richiesta.

**IMPORTANTE: Il tuo output deve contenere SOLO lo schema formattato, senza note procedurali, frasi introduttive o commenti sul processo. Inizia direttamente con il box decorativo dello schema.**

**Tipo di Schema:** {outline_type}
**Livello di Dettaglio:** {detail_level}
**Focus:** {focus_area}

**Requisiti dello Schema:**

1. **Struttura Gerarchica:**
   - Usa una numerazione chiara e consistente
   - Mantieni la gerarchia logica del contenuto
   - Indica i livelli con indentazione appropriata
   - Aggiungi emoji contestuali per ogni sezione principale

2. **Completezza:**
   - Includi tutti i concetti principali
   - Non omettere sezioni importanti
   - Bilancia il livello di dettaglio in modo uniforme
   - Conta e indica il numero totale di sezioni principali e sottosezioni

3. **Riferimenti:**
   - Indica numeri di pagina quando disponibili (formato: pag. X)
   - Cita titoli di capitoli e sezioni originali
   - Mantieni i riferimenti alla struttura originale
   - Aggiungi collegamenti incrociati tra sezioni correlate

4. **Organizzazione:**
   - Raggruppa concetti correlati
   - Usa intestazioni descrittive
   - Evidenzia relazioni tra le sezioni
   - Usa simboli per indicare relazioni: → (porta a), ↔ (correlato con), ⊃ (include)

**Formato di Output:**
```
## 📖 I. [Sezione Principale 1] (pag. X-Y)
   
   📌 A. [Sottosezione 1.1] (pag. X)
      ├─ 1. [Punto 1.1.1]
      │     • [Dettaglio importante]
      │     • [Dettaglio importante]
      │
      └─ 2. [Punto 1.1.2] → Collegamenti a [Sezione Z]
            a) [Dettaglio 1.1.2.a]
            b) [Dettaglio 1.1.2.b]
   
   📌 B. [Sottosezione 1.2] (pag. Y)
      └─ 1. [Punto 1.2.1]
            • [Dettaglio]

─────────────────────────────────────────────────────

## 📚 II. [Sezione Principale 2] (pag. Z-W)
   
   📌 A. [Sottosezione 2.1]
      └─ 1. [Punto importante]
   
   📌 B. [Sottosezione 2.2] ↔ Correlato con [Sezione I.A]
      ...

═══════════════════════════════════════════════════════

## 🔗 Collegamenti Tra Sezioni

• Sezione [I.A] → Sezione [II.B]: [Descrizione relazione]
• Sezione [I.B] ↔ Sezione [III.A]: [Descrizione correlazione]

═══════════════════════════════════════════════════════

## 💡 Note Strutturali e Osservazioni

📝 **Temi Ricorrenti:**
   • [Tema 1]: Appare in sezioni [lista sezioni]
   • [Tema 2]: Sviluppato progressivamente in [lista sezioni]

🎯 **Punti Focali Principali:**
   1. [Punto focale 1] - Sezioni [X, Y]
   2. [Punto focale 2] - Sezioni [Z, W]

⚠️  **Aree di Particolare Complessità:**
   • Sezione [X]: [Motivo della complessità]
   • Sezione [Y]: [Suggerimento per comprensione]

═══════════════════════════════════════════════════════

## 📖 Guida alla Lettura Consigliata

✅ **Per una lettura completa:** Seguire l'ordine I → II → III
✅ **Per focus su [tema]:** Sezioni [lista sezioni rilevanti]
✅ **Per revisione rapida:** Sezioni [lista sezioni essenziali]

═══════════════════════════════════════════════════════
```

Genera ora lo schema arricchito basandoti sul contenuto fornito. Assicurati di:
- Usare emoji appropriate per ogni tipo di sezione
- Includere TUTTI i separatori visivi mostrati
- Contare accuratamente sezioni e sottosezioni
- Aggiungere collegamenti incrociati dove rilevanti
- Fornire una guida alla lettura personalizzata
"""


MINDMAP_GENERATION_PROMPT = """
Crea una mappa concettuale visivamente ricca che rappresenti i concetti chiave e le loro relazioni.

**IMPORTANTE: Il tuo output deve contenere SOLO la mappa concettuale formattata, senza note procedurali, frasi introduttive o commenti sul processo. Inizia direttamente con il box decorativo della mappa.**

**Concetto Centrale:** {central_concept}
**Livello di Profondità:** {depth_level}
**Focus:** {focus_area}

**Requisiti della Mappa Concettuale:**

1. **Concetto Centrale:**
   - Identifica il tema o concetto principale con emoji appropriata
   - Posizionalo concettualmente al centro
   - Fornisci una breve descrizione chiara e coinvolgente

2. **Concetti Correlati:**
   - Identifica 2-4 rami principali (concetti di primo livello)
   - Per ogni ramo principale, aggiungi 2-5 sotto-concetti
   - Mantieni una profondità massima di {depth_level} livelli
   - Usa emoji diverse e appropriate per ogni livello

3. **Relazioni:**
   - Indica chiaramente come i concetti si relazionano
   - Usa etichette descrittive per i collegamenti
   - Evidenzia connessioni trasversali tra rami diversi
   - Usa simboli per tipi di relazioni:
     * → per "causa/porta a"
     * ↔ per "è correlato con"
     * ⊃ per "include/contiene"
     * ≈ per "è simile a"

4. **Rappresentazione Visiva:**
   - Usa formato tree con caratteri box-drawing
   - Indentazione progressiva per i livelli
   - Separatori chiari tra rami principali
   - Conta accuratamente nodi per livello

**Formato di Output:**
```
## 🎯 Concetto Centrale

**[Nome del Concetto Centrale]**  
[Breve descrizione chiara e coinvolgente del concetto centrale,
spiegando la sua importanza e il suo ruolo nel contesto]

═══════════════════════════════════════════════════════

## 🌳 Struttura della Mappa

### 🎨 Ramo 1: [Nome Ramo Principale]
├─ 🔹 [Concetto Secondario 1.1]
│   ├─ 💫 [Concetto Terziario 1.1.1]
│   │   └─ ⚡ [Dettaglio] → Relazione con [altro concetto]
│   └─ 🌟 [Concetto Terziario 1.1.2]
│       └─ 🎯 [Dettaglio] ↔ Correlato con [altro concetto]
│
├─ 🔸 [Concetto Secondario 1.2]
│   ├─ 💎 [Concetto Terziario 1.2.1]
│   └─ 🔮 [Concetto Terziario 1.2.2] ≈ Simile a [altro concetto]
│
└─ 🔷 [Concetto Secondario 1.3]
    ├─ ✨ [Concetto Terziario 1.3.1]
    └─ 🌈 [Concetto Terziario 1.3.2] ⊃ Include [sotto-concetto]

─────────────────────────────────────────────────────

### 🎭 Ramo 2: [Nome Ramo Principale]
├─ 🔹 [Concetto Secondario 2.1]
│   ├─ 💫 [Concetto Terziario 2.1.1]
│   └─ 🌟 [Concetto Terziario 2.1.2]
│
├─ 🔸 [Concetto Secondario 2.2]
│   └─ 💎 [Concetto Terziario 2.2.1]
│
└─ 🔷 [Concetto Secondario 2.3]
    └─ ✨ [Concetto Terziario 2.3.1]

─────────────────────────────────────────────────────

### 🌺 Ramo 3: [Nome Ramo Principale] (se presente)
├─ 🔹 [Concetto Secondario 3.1]
└─ 🔸 [Concetto Secondario 3.2]

═══════════════════════════════════════════════════════

## 🔗 Connessioni Trasversali

1. **[Concetto A]** ↔ **[Concetto B]**
   Relazione: [Descrizione dettagliata della relazione e del
   suo significato nel contesto]

2. **[Concetto C]** → **[Concetto D]**
   Relazione: [Descrizione di come C porta a o causa D]

3. **[Concetto E]** ⊃ **[Concetto F]**
   Relazione: [Descrizione di come E include o contiene F]

═══════════════════════════════════════════════════════

## 💡 Note Concettuali

📝 **Temi Ricorrenti:**
   • [Tema 1]: Appare in [lista concetti/rami]
   • [Tema 2]: Sviluppato attraverso [lista concetti]
   • [Tema 3]: Collegamento tra [concetti correlati]

🎯 **Pattern Identificati:**
   • [Pattern 1]: [Descrizione del pattern osservato]
   • [Pattern 2]: [Descrizione del pattern osservato]

⚡ **Concetti Chiave:**
   • [Concetto chiave 1]: [Perché è importante]
   • [Concetto chiave 2]: [Perché è importante]
   • [Concetto chiave 3]: [Perché è importante]

═══════════════════════════════════════════════════════

## 📖 Guida all'Uso della Mappa

✅ **Per comprensione completa:** Centro → Tutti i rami → Collegamenti
✅ **Per focus su [aspetto 1]:** Rami [X, Y]
✅ **Per focus su [aspetto 2]:** Rami [Z, W]
✅ **Per relazioni chiave:** Sezione Collegamenti Trasversali

═══════════════════════════════════════════════════════
```

Genera ora la mappa concettuale arricchita basandoti sul contenuto fornito. 
Assicurati di:
- Usare emoji DIVERSE e APPROPRIATE per ogni livello gerarchico
- Includere TUTTI i separatori visuali mostrati (╔═╗, ═══, ───)
- Contare accuratamente: concetto centrale, rami, nodi totali per livello
- Descrivere DETTAGLIATAMENTE ogni connessione trasversale
- Identificare pattern e temi ricorrenti
- Fornire una guida all'uso personalizzata sul contenuto
- Usare i caratteri box-drawing (├─, └─, │) in modo consistente
"""


SUMMARY_GENERATION_PROMPT = """
Crea un riassunto del contenuto secondo le specifiche fornite.

**IMPORTANTE: Il tuo output deve contenere SOLO il riassunto formattato, senza note procedurali, frasi introduttive o commenti sul processo. Inizia direttamente con il titolo del riassunto.**

**Tipo di Riassunto:** {summary_type}
**Lunghezza Target:** {length}
**Focus:** {focus_area}

**Requisiti del Riassunto:**

1. **Completezza:**
   - Copri tutti i punti principali
   - Mantieni le informazioni essenziali
   - Non omettere concetti chiave

2. **Struttura:**
   - Usa paragrafi ben organizzati
   - Segui un flusso logico
   - Usa intestazioni per sezioni lunghe

3. **Stile:**
   - Scrivi in modo chiaro e conciso
   - Evita ridondanze
   - Mantieni un tono appropriato al contenuto

4. **Riferimenti:**
   - Cita sezioni specifiche quando rilevante
   - Mantieni la terminologia originale per concetti chiave

**Tipi di Riassunto:**

**Breve (Abstract):** 1-2 paragrafi che catturano l'essenza
**Medio (Executive Summary):** 3-5 paragrafi con punti chiave
**Esteso (Comprehensive):** Multipli paragrafi con dettagli significativi
**Per Sezioni:** Riassunto strutturato per capitoli/sezioni

**Formato di Output:**
```
# Riassunto: [Titolo]

[Se tipo "Per Sezioni":]
## [Nome Sezione 1]
[Riassunto della sezione 1]

## [Nome Sezione 2]
[Riassunto della sezione 2]

[Se tipo "Breve/Medio/Esteso":]
[Riassunto organizzato in paragrafi coerenti]

---

## Punti Chiave
- [Punto chiave 1]
- [Punto chiave 2]
- [Punto chiave 3]
...
```

Genera ora il riassunto basandoti sul contenuto fornito.
"""


ANALYSIS_GENERATION_PROMPT = """
Conduci un'analisi approfondita del contenuto secondo i seguenti parametri.

**IMPORTANTE: Il tuo output deve contenere SOLO l'analisi formattata, senza note procedurali, frasi introduttive o commenti sul processo. Inizia direttamente con il titolo dell'analisi.**

**Tipo di Analisi:** {analysis_type}
**Focus:** {focus_area}
**Profondità:** {depth}

**Requisiti dell'Analisi:**

1. **Approccio Metodico:**
   - Identifica i temi principali
   - Esamina gli argomenti e le prove
   - Valuta la struttura logica
   - Esplora le implicazioni

2. **Prospettive Multiple:**
   - Considera diverse interpretazioni
   - Analizza presupposti sottostanti
   - Identifica bias o limitazioni
   - Esplora connessioni con altri concetti

3. **Profondità:**
   - Va oltre la superficie del testo
   - Scava nelle motivazioni e nei contesti
   - Identifica pattern e strutture sottostanti

4. **Evidenze:**
   - Supporta ogni affermazione con riferimenti al testo
   - Distingui tra interpretazione e fatto
   - Cita esempi specifici

**Tipi di Analisi:**

**Tematica:** Identifica e esplora temi ricorrenti
**Argomentativa:** Analizza la struttura e la validità degli argomenti
**Critica:** Valuta punti di forza e debolezza del testo
**Comparativa:** Confronta diverse sezioni, concetti o approcci
**Contestuale:** Situa il contenuto in un contesto più ampio

**Formato di Output:**
```
# Analisi: [Titolo]

## Introduzione
[Panoramica dell'analisi e dell'approccio]

## [Sezione Analitica 1]
### Osservazione
[Cosa emerge dal testo]

### Interpretazione
[Cosa significa questa osservazione]

### Implicazioni
[Conseguenze o significato più ampio]

### Evidenze
[Riferimenti specifici al testo]

## [Sezione Analitica 2]
[Ripeti la struttura]

---

## Sintesi Analitica
[Conclusioni principali dell'analisi]

## Domande per Ulteriore Riflessione
1. [Domanda 1]
2. [Domanda 2]
3. [Domanda 3]
```

Conduci ora l'analisi basandoti sul contenuto fornito.
"""


def generate_quiz_prompt(
    quiz_type: str = "multiple_choice",
    num_questions: int = 10,
    difficulty: str = "medium",
    focus_area: Optional[str] = None
) -> str:
    """
    Generate a prompt for quiz creation.
    
    Args:
        quiz_type: Type of quiz (multiple_choice, true_false, short_answer, mixed)
        num_questions: Number of questions to generate
        difficulty: Difficulty level (easy, medium, hard, mixed)
        focus_area: Specific area to focus on (optional)
    
    Returns:
        str: Formatted prompt for quiz generation
    """
    focus = focus_area if focus_area else "tutto il contenuto fornito"
    
    # Map quiz types to Italian
    quiz_type_map = {
        "multiple_choice": "Scelta Multipla",
        "true_false": "Vero/Falso",
        "short_answer": "Risposta Breve",
        "mixed": "Misto (vari tipi di domande)"
    }
    
    difficulty_map = {
        "easy": "Facile (comprensione di base)",
        "medium": "Medio (analisi e applicazione)",
        "hard": "Difficile (sintesi e valutazione)",
        "mixed": "Misto (vari livelli di difficoltà)"
    }
    
    return QUIZ_GENERATION_PROMPT.format(
        quiz_type=quiz_type_map.get(quiz_type, quiz_type),
        num_questions=num_questions,
        difficulty=difficulty_map.get(difficulty, difficulty),
        focus_area=focus
    )


def generate_outline_prompt(
    outline_type: str = "hierarchical",
    detail_level: str = "medium",
    focus_area: Optional[str] = None
) -> str:
    """
    Generate a prompt for outline creation.
    
    Args:
        outline_type: Type of outline (hierarchical, chronological, thematic)
        detail_level: Level of detail (brief, medium, detailed)
        focus_area: Specific area to focus on (optional)
    
    Returns:
        str: Formatted prompt for outline generation
    """
    focus = focus_area if focus_area else "l'intero documento"
    
    outline_type_map = {
        "hierarchical": "Gerarchico (per struttura logica)",
        "chronological": "Cronologico (per ordine temporale)",
        "thematic": "Tematico (per argomenti)"
    }
    
    detail_level_map = {
        "brief": "Sintetico (solo punti principali)",
        "medium": "Medio (punti principali e secondari)",
        "detailed": "Dettagliato (include anche sotto-punti specifici)"
    }
    
    return OUTLINE_GENERATION_PROMPT.format(
        outline_type=outline_type_map.get(outline_type, outline_type),
        detail_level=detail_level_map.get(detail_level, detail_level),
        focus_area=focus
    )


def generate_mindmap_prompt(
    central_concept: Optional[str] = None,
    depth_level: int = 3,
    focus_area: Optional[str] = None
) -> str:
    """
    Generate a prompt for mind map creation.
    
    Args:
        central_concept: Central concept for the mind map (if None, will be determined from content)
        depth_level: Maximum depth of the mind map (2-4)
        focus_area: Specific area to focus on (optional)
    
    Returns:
        str: Formatted prompt for mind map generation
    """
    central = central_concept if central_concept else "il concetto principale identificato dal contesto"
    focus = focus_area if focus_area else "tutti i concetti correlati nel contenuto"
    
    depth_level = max(2, min(4, depth_level))  # Clamp between 2 and 4
    
    # Format depth_level as integer for the template
    return MINDMAP_GENERATION_PROMPT.format(
        central_concept=central,
        depth_level=depth_level,  # Pass as integer, not string
        focus_area=focus
    )


def generate_summary_prompt(
    summary_type: str = "medium",
    length: str = "3-5 paragrafi",
    focus_area: Optional[str] = None
) -> str:
    """
    Generate a prompt for summary creation.
    
    Args:
        summary_type: Type of summary (brief, medium, extended, by_sections)
        length: Target length description
        focus_area: Specific area to focus on (optional)
    
    Returns:
        str: Formatted prompt for summary generation
    """
    focus = focus_area if focus_area else "tutto il contenuto"
    
    summary_type_map = {
        "brief": "Breve (Abstract)",
        "medium": "Medio (Executive Summary)",
        "extended": "Esteso (Comprehensive)",
        "by_sections": "Per Sezioni (Section-by-Section)"
    }
    
    # Adjust length based on type if not specified
    if not length or length == "3-5 paragrafi":
        length_map = {
            "brief": "1-2 paragrafi",
            "medium": "3-5 paragrafi",
            "extended": "6-10 paragrafi",
            "by_sections": "1-2 paragrafi per sezione"
        }
        length = length_map.get(summary_type, length)
    
    return SUMMARY_GENERATION_PROMPT.format(
        summary_type=summary_type_map.get(summary_type, summary_type),
        length=length,
        focus_area=focus
    )


def generate_analysis_prompt(
    analysis_type: str = "thematic",
    focus_area: Optional[str] = None,
    depth: str = "profonda"
) -> str:
    """
    Generate a prompt for analysis creation.
    
    Args:
        analysis_type: Type of analysis (thematic, argumentative, critical, comparative, contextual)
        focus_area: Specific area to focus on (optional)
        depth: Depth of analysis (superficiale, media, profonda)
    
    Returns:
        str: Formatted prompt for analysis generation
    """
    focus = focus_area if focus_area else "tutto il contenuto"
    
    analysis_type_map = {
        "thematic": "Tematica",
        "argumentative": "Argomentativa",
        "critical": "Critica",
        "comparative": "Comparativa",
        "contextual": "Contestuale"
    }
    
    return ANALYSIS_GENERATION_PROMPT.format(
        analysis_type=analysis_type_map.get(analysis_type, analysis_type),
        focus_area=focus,
        depth=depth
    )
