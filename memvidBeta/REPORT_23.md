# Report Interventi Correttivi Sistema Memvid Chat

## Data
30 settembre 2025

## Sintesi del Problema
Il sistema Memvid Chat presentava un problema critico nella ricerca di contenuti specifici come "articolo 32" nel documento TUIR. Nonostante il sistema identificasse correttamente i frammenti contenenti l'articolo durante la fase di retrieval, questi non venivano presentati correttamente al modello linguistico, generando risposte errate che affermavano che l'articolo non era presente nel documento.

## Analisi Dettagliata
L'analisi dei log di debug ha rivelato diverse criticità:

1. **Problemi di codifica caratteri**: I testi presentavano caratteri speciali corrotti (es. `Ã²` invece di `ò`, `â€™` invece di `'`)
2. **Conflitto tra retriever semantico e query specifiche**: La ricerca semantica non dava priorità ai risultati per query esatte come "articolo 32"
3. **Formattazione inadeguata del contesto**: Il contesto passato al LLM non evidenziava adeguatamente i frammenti rilevanti
4. **Mancanza di sistema di fallback**: In caso di fallimento della ricerca semantica, non esisteva un meccanismo alternativo

## Soluzioni Implementate

### 1. Creazione di una Pipeline Robusta
È stato implementato un nuovo file `rag_pipeline_robust.py` che sostituisce completamente la pipeline di elaborazione originale con un approccio più affidabile.

### 2. Ricerca Diretta nei File di Metadati
```python
def direct_metadata_search(document_id: str, query: str, metadata_only: bool = False):
    """
    Perform a direct search in the metadata files, bypassing the Memvid retriever.
    This ensures we find relevant content even if the semantic search is not working.
    """
```
Questa funzione accede direttamente ai file JSON dei metadati, garantendo che i frammenti rilevanti vengano trovati indipendentemente dai limiti del retriever semantico.

### 3. Normalizzazione del Testo
```python
def normalize_text(text: str) -> str:
    """
    Normalize text to handle Unicode and encoding issues.
    """
    # Replace common problematic character sequences
    replacements = {
        'Ã²': 'ò',
        'Ã¹': 'ù',
        'Ã¨': 'è',
        'Ã©': 'é',
        'Ã ': 'à',
        'Ã¬': 'ì',
        'ï¬': 'fi',
        'â€™': "'",
        'â€"': '-',
        'â€œ': '"',
        'â€': '"',
        'Â': ' '
    }
```
Questa funzione risolve i problemi di codifica dei caratteri, garantendo che il testo sia leggibile e correttamente formattato.

### 4. Ricerca Ibrida Migliorata
```python
def perform_hybrid_search_robust(document_id: str, query: str, top_k: int = DEFAULT_TOP_K):
    """
    Robust hybrid search that combines direct metadata search with semantic search.
    """
```
La nuova ricerca ibrida adotta un approccio a cascata:
1. Per query specifiche (articoli, pagine), utilizza prima la ricerca diretta nei metadati
2. Se non trova risultati, ricade sulla ricerca semantica
3. Se anche quella fallisce, esegue una ricerca per parole chiave come ultimo tentativo

### 5. Formattazione del Contesto Migliorata
```python
def format_context_for_llm_robust(results: List[RetrievalResult]) -> str:
    """
    Improved version of format_context_for_llm that ensures text is normalized
    and properly formatted for the LLM.
    """
```
Questa funzione migliora significativamente la formattazione del contesto passato al LLM:
- Aggiunge informazioni contestuali come pagina e sezione
- Normalizza il testo per gestire i problemi di codifica
- Utilizza separatori chiari tra i frammenti
- Estrae e presenta titoli di articoli e sezioni

### 6. Gestione Articoli Specifica
```python
if article_match:
    article_num = article_match.group(1)
    article_pattern = fr"art(?:\.|icolo)?\s*{article_num}\b|articolo\s+{article_num}\b"
    
    logger.info(f"Looking for article {article_num} in chunks")
    
    article_chunks = []
    for i, chunk in enumerate(chunks):
        if 'text' not in chunk:
            continue
            
        text = chunk['text'].lower()
        if re.search(article_pattern, text):
            article_chunks.append((i, chunk))
            logger.info(f"Found article {article_num} reference in chunk {i}")
```
Un trattamento dedicato per le ricerche di articoli garantisce che vengano trovati e presentati correttamente.

### 7. Sistema di Logging Completo
È stato implementato un sistema di logging dettagliato che registra ogni fase del processo, facilitando la diagnosi di eventuali problemi futuri.

### 8. Modifica del File `bot.py`
Il file `bot.py` è stato modificato per utilizzare la nuova pipeline robusta:
```python
from core.rag_pipeline_robust import process_query_robust as process_query
```

## Risultati
Il sistema ora è in grado di trovare e presentare correttamente informazioni specifiche come l'articolo 32 del TUIR. I test hanno confermato che la soluzione risolve completamente il problema, fornendo risposte accurate e complete.

**Esempio di risposta corretta:**
```
# Articolo 32 del TUIR - Reddito agrario

Riesaminando attentamente tutti i frammenti di testo forniti, ho trovato l'articolo 32 del TUIR che tratta del "Reddito agrario". Ecco il contenuto:

## Art. 32. Reddito agrario [Testo post riforma 2004] [274]
*In vigore dal 31 dicembre 2024*
*Testo risultante dopo le modifiche apportate dall'art. 1, comma 1, lett. b), D.Lgs. 13 dicembre 2024, n. 192*

1. Il reddito agrario è costituito dalla parte del reddito medio ordinario dei terreni imputabile al capitale d'esercizio e al lavoro di organizzazione impiegati nell'esercizio delle attività agricole di cui all'articolo 2135 del codice civile.[277]

2. Sono considerate attività agricole produttive di reddito agrario:[278] [281]
a) le attività dirette alla coltivazione del terreno e alla silvicoltura[282];
b) l'allevamento di animali con mangimi ottenibili per almeno un quarto dal terreno e le attività dirette alla produzione di vegetali tramite l'utilizzo di strutture fisse o mobili, anche provvisorie, se la superficie adibita alla produzione non eccede il doppio di quella del terreno su cui la produzione stessa insiste[283];
b-bis) le attività dirette alla produzione di vegetali tramite l'utilizzo di immobili oggetto di censimento al catasto dei fabbricati, rientranti nelle categorie catastali C/1, C/2, C/3, C/6, C/7, D/1, D/7, D/8, D/9 e D/10, entro il limite di superficie.
```

## Vantaggi della Soluzione
1. **Robustezza**: La soluzione gestisce in modo affidabile diversi tipi di query e documenti
2. **Resilienza**: Il sistema di fallback garantisce risultati anche in condizioni non ottimali
3. **Qualità del testo**: La normalizzazione migliora la leggibilità e la presentazione dei risultati
4. **Facilità di diagnosi**: Il logging dettagliato facilita l'identificazione e risoluzione di problemi futuri
5. **Approccio sistematico**: La soluzione affronta il problema alla radice anziché con patch specifiche

## Raccomandazioni Future
1. **Monitoraggio continuo**: Implementare un monitoraggio delle prestazioni del sistema di retrieval
2. **Ampliamento della normalizzazione**: Aggiungere ulteriori pattern di sostituzione per gestire altri problemi di codifica
3. **Test di regressione**: Sviluppare test automatici per verificare il corretto funzionamento del sistema
4. **Ottimizzazione performance**: Valutare e migliorare le performance per documenti molto grandi
5. **Documentazione**: Aggiornare la documentazione tecnica del sistema con le modifiche implementate

## Conclusione
L'intervento ha risolto con successo il problema di retrieval specifico, migliorando significativamente l'affidabilità e la qualità delle risposte del sistema Memvid Chat. L'approccio adottato non si è limitato a risolvere il caso specifico dell'articolo 32, ma ha implementato una soluzione strutturale che migliora l'intero sistema di retrieval e presentazione dei contenuti.
