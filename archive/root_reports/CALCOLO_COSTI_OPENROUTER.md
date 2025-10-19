# Calcolo Costi OpenRouter per Utente

## Panoramica

OpenRouter applica tariffe basate su:
- **Token di input** (prompt inviato)
- **Token di output** (risposta generata)
- **Modello utilizzato** (GPT-4, Claude, ecc.)

## Tariffe OpenRouter per Modello

### Modelli Consigliati per Socrate AI

| Modello | Input ($/1M token) | Output ($/1M token) | Use Case |
|---------|-------------------|---------------------|----------|
| **GPT-4o-mini** | $0.15 | $0.60 | Free tier, query semplici |
| **GPT-4o** | $2.50 | $10.00 | Pro tier, analisi complesse |
| **Claude 3.5 Sonnet** | $3.00 | $15.00 | Enterprise, documenti lunghi |
| **Claude 3 Haiku** | $0.25 | $1.25 | Free/Pro, velocità |
| **Llama 3.1 70B** | $0.35 | $0.40 | Budget-friendly, open source |

### Fonte Prezzi
https://openrouter.ai/models (aggiornato a Ottobre 2025)

## Calcolo Costi per Operazione

### Formula Base

```python
def calcola_costo_query(input_tokens: int, output_tokens: int, modello: str) -> float:
    """
    Calcola costo singola query OpenRouter

    Args:
        input_tokens: Numero token nel prompt (document chunks + query)
        output_tokens: Numero token nella risposta
        modello: Nome modello (es. 'gpt-4o-mini')

    Returns:
        Costo in dollari
    """
    # Prezzi per milione di token
    prezzi = {
        'gpt-4o-mini': {'input': 0.15, 'output': 0.60},
        'gpt-4o': {'input': 2.50, 'output': 10.00},
        'claude-3.5-sonnet': {'input': 3.00, 'output': 15.00},
        'claude-3-haiku': {'input': 0.25, 'output': 1.25},
        'llama-3.1-70b': {'input': 0.35, 'output': 0.40}
    }

    prezzo_modello = prezzi.get(modello, prezzi['gpt-4o-mini'])

    costo_input = (input_tokens / 1_000_000) * prezzo_modello['input']
    costo_output = (output_tokens / 1_000_000) * prezzo_modello['output']

    return costo_input + costo_output
```

### Esempio Pratico: Query su Documento PDF

**Scenario**: Utente chiede "Riassumi il capitolo 3"

1. **Document Chunks** (recuperati da memvid):
   - 3 chunk rilevanti × 400 token = 1,200 token

2. **Query utente**:
   - "Riassumi il capitolo 3" = ~10 token

3. **System prompt**:
   - Istruzioni al modello = ~200 token

4. **Totale Input**: 1,200 + 10 + 200 = **1,410 token**

5. **Output** (risposta):
   - Riassunto di ~300 parole = **~400 token**

**Costo con GPT-4o-mini**:
```
Input:  1,410 / 1,000,000 × $0.15 = $0.0002115
Output:   400 / 1,000,000 × $0.60 = $0.0002400
-------------------------------------------------
TOTALE:                              $0.0004515 (~€0.00042)
```

**Costo con GPT-4o** (stesso esempio):
```
Input:  1,410 / 1,000,000 × $2.50 = $0.003525
Output:   400 / 1,000,000 × $10.00 = $0.004000
-------------------------------------------------
TOTALE:                              $0.007525 (~€0.007)
```

## Stima Utilizzo per Tier

### Free Tier (GPT-4o-mini)

**Limiti suggeriti**: 50 query/mese

| Operazione | Token Input | Token Output | Costo Unitario | Totale Mensile |
|------------|-------------|--------------|----------------|----------------|
| Query semplice | 800 | 200 | $0.00024 | $0.012 |
| Query complessa | 2,000 | 500 | $0.00060 | $0.030 |
| Riassunto | 1,500 | 400 | $0.00045 | $0.0225 |
| **Media (50 query)** | **1,400** | **350** | **$0.00042** | **$0.021** |

**Costo Free Tier per utente**: ~$0.02/mese (€0.019/mese)

### Pro Tier (GPT-4o)

**Limiti suggeriti**: 500 query/mese

| Operazione | Token Input | Token Output | Costo Unitario | Totale Mensile |
|------------|-------------|--------------|----------------|----------------|
| Query semplice | 800 | 200 | $0.004 | $2.00 |
| Query complessa | 3,000 | 800 | $0.0155 | $7.75 |
| Analisi avanzata | 5,000 | 1,500 | $0.0275 | $13.75 |
| **Media (500 query)** | **2,500** | **700** | **$0.0133** | **$6.65** |

**Costo Pro Tier per utente**: ~$6.65/mese (€6.20/mese)

### Enterprise Tier (Claude 3.5 Sonnet)

**Limiti suggeriti**: Illimitate (con fair use)

| Operazione | Token Input | Token Output | Costo Unitario | Costo 1000 query |
|------------|-------------|--------------|----------------|------------------|
| Query semplice | 1,000 | 300 | $0.0075 | $7.50 |
| Analisi documento completo | 10,000 | 2,000 | $0.06 | $60.00 |
| **Media (1000 query/mese)** | **3,500** | **1,000** | **$0.0255** | **$25.50** |

**Costo Enterprise per utente**: ~$25.50/mese (€23.80/mese)

## Calcolo Margine di Profitto

### Free Tier (€0/mese)

```
Entrate:     €0
Costi AI:    -€0.02
Storage R2:  -€0.001
--------------------------
Margine:     -€0.021 (loss leader per acquisizione utenti)
```

**Obiettivo**: Conversione a Pro entro 3 mesi

### Pro Tier (€9.99/mese)

```
Entrate:     €9.99
Costi AI:    -€6.20
Storage R2:  -€0.07 (5GB)
Infra:       -€0.50 (Railway, Redis)
--------------------------
Margine:     €3.22 (32.2% profit margin)
```

### Enterprise Tier (€49.99/mese)

```
Entrate:     €49.99
Costi AI:    -€23.80
Storage R2:  -€0.70 (50GB)
Infra:       -€1.00
--------------------------
Margine:     €24.49 (49% profit margin)
```

## Ottimizzazione Costi AI

### 1. Caching delle Risposte Comuni

```python
# Cache domande frequenti per 24 ore
CACHED_QUERIES = {
    "riassumi": 86400,  # 24 ore
    "cos'è": 43200,     # 12 ore
    "spiega": 21600     # 6 ore
}
```

**Risparmio stimato**: 30-40% su query ripetitive

### 2. Modello Ibrido per Tier

**Free**: Solo GPT-4o-mini
**Pro**: GPT-4o-mini per query semplici, GPT-4o per analisi
**Enterprise**: Claude 3.5 Sonnet + fallback a GPT-4o

**Risparmio stimato**: 15-25% rispetto a uso esclusivo modelli premium

### 3. Chunk Selection Intelligente

Usa embeddings per selezionare solo i chunk più rilevanti:

```python
# Invece di inviare tutti i chunk
CHUNKS_PER_QUERY = {
    'free': 3,        # Max 1,200 token input
    'pro': 5,         # Max 2,000 token input
    'enterprise': 10  # Max 4,000 token input
}
```

**Risparmio stimato**: 40-60% su costi input token

### 4. Output Length Control

```python
# Limita la lunghezza delle risposte
MAX_OUTPUT_TOKENS = {
    'free': 200,
    'pro': 500,
    'enterprise': 2000
}
```

**Risparmio stimato**: 20-30% su costi output token

## Monitoraggio Costi in Real-Time

### Tracking nel Database

Aggiungi colonna a `chat_sessions`:

```python
# In database.py
class ChatSession(Base):
    # ... campi esistenti ...

    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    cost_usd = Column(Float)  # Costo effettivo query
    model_used = Column(String(50))
```

### Dashboard Admin

Metriche da tracciare:
- Costo totale AI per utente (mensile)
- Costo medio per query
- Utenti che superano i limiti
- Trend utilizzo modelli

### Alert Automatici

```python
# Quando utente Free supera soglia
if user.tier == 'free' and user.monthly_ai_cost > 0.05:
    send_upgrade_prompt(user, "Hai usato più del previsto! Passa a Pro per sbloccare più query")
```

## Implementazione nel Codice

### 1. Tracking Costi in `core/openrouter_client.py`

```python
def query_openrouter(prompt: str, model: str, max_tokens: int = 500) -> dict:
    """
    Esegui query su OpenRouter e traccia costi
    """
    response = openrouter.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens
    )

    # Estrai usage
    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens

    # Calcola costo
    cost_usd = calcola_costo_query(input_tokens, output_tokens, model)

    return {
        'answer': response.choices[0].message.content,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'cost_usd': cost_usd,
        'model': model
    }
```

### 2. Salva nel Database

```python
# In api_server.py, endpoint /api/query
result = query_openrouter(prompt, model, max_tokens)

# Update session con costi
update_chat_session(
    session_id=str(chat_session.id),
    response_data={'answer': result['answer']},
    success=True,
    input_tokens=result['input_tokens'],
    output_tokens=result['output_tokens'],
    cost_usd=result['cost_usd'],
    model_used=result['model']
)
```

### 3. Controllo Quota

```python
def check_monthly_ai_quota(user_id: str) -> bool:
    """
    Verifica se utente ha superato la quota mensile
    """
    user = get_user_by_id(user_id)

    # Calcola spesa AI questo mese
    monthly_sessions = get_user_sessions_this_month(user_id)
    total_cost = sum(s.cost_usd for s in monthly_sessions)

    # Soglie per tier
    limits = {
        'free': 0.05,      # $0.05 = ~50 query GPT-4o-mini
        'pro': 10.00,      # $10.00 = ~750 query GPT-4o
        'enterprise': 100.00  # $100 = illimitate praticamente
    }

    return total_cost < limits.get(user.subscription_tier, 0.05)
```

## Proiezioni Scala

### Scenario 1000 Utenti (60% Free, 30% Pro, 10% Enterprise)

```
Free:       600 utenti × €0.02  = €12/mese (costo AI)
Pro:        300 utenti × €6.20  = €1,860/mese (costo AI)
Enterprise: 100 utenti × €23.80 = €2,380/mese (costo AI)
---------------------------------------------------------
TOTALE COSTI AI:                  €4,252/mese

ENTRATE:
Free:       600 × €0     = €0
Pro:        300 × €9.99  = €2,997
Enterprise: 100 × €49.99 = €4,999
---------------------------------------------------------
TOTALE ENTRATE:           €7,996/mese

MARGINE NETTO (solo AI): €3,744/mese (46.8%)
```

### Con Ottimizzazioni (caching, chunk selection, output control)

```
Riduzione costi AI: 40%

COSTI AI OTTIMIZZATI:  €2,551/mese
ENTRATE:               €7,996/mese
---------------------------------------------------------
MARGINE NETTO:         €5,445/mese (68.1%)
```

## Conclusioni

### Costi Unitari per Tier

| Tier | Costo AI Mensile | Entrata Mensile | Margine |
|------|------------------|-----------------|---------|
| Free | €0.02 | €0 | -€0.02 (loss) |
| Pro | €6.20 | €9.99 | €3.79 (38%) |
| Enterprise | €23.80 | €49.99 | €26.19 (52%) |

### Strategia Pricing

1. **Free Tier**: Loss leader per acquisizione
   - Obiettivo: Conversione >20% a Pro entro 3 mesi
   - Costo acquisizione: €0.06 (3 mesi × €0.02)

2. **Pro Tier**: Sweet spot profittabilità
   - Margine sano (38%) con volume
   - Target principale per monetizzazione

3. **Enterprise Tier**: Massimo margine
   - Clienti aziendali, uso intensivo
   - Supporto prioritario giustifica il prezzo

### KPI da Monitorare

- **Costo AI per utente**: Media €6.20 Pro, €23.80 Enterprise
- **Conversion rate Free→Pro**: Target >20%
- **Churn rate**: Target <5% mensile
- **LTV (Lifetime Value)**: Pro €120, Enterprise €600 (12 mesi)
- **CAC (Customer Acquisition Cost)**: Target <€10 per Pro user

---

**Documento Versione**: 1.0
**Ultimo Aggiornamento**: 14 Ottobre 2025
**Prossima Revisione**: Dopo primi 100 utenti paganti
