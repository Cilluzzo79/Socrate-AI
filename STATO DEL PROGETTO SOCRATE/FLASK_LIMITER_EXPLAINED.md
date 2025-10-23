# 🛡️ Flask-Limiter: Cos'è e Come Funziona

**Data**: 23 Ottobre 2025
**Autore**: Claude Code con Backend-Master-Analyst
**Versione**: 1.0

---

## 📖 Cos'è Flask-Limiter?

**Flask-Limiter** è una libreria Python che implementa **rate limiting** (limitazione del tasso di richieste) per applicazioni Flask.

### Analogia Semplice
Immagina un ristorante con una porta d'ingresso:
- **Senza Rate Limiting**: Tutti possono entrare contemporaneamente → caos, tavoli pieni, cuochi sopraffatti
- **Con Rate Limiting**: "Massimo 50 clienti all'ora" → servizio ordinato, qualità mantenuta

Flask-Limiter è il "buttafuori digitale" che conta quante richieste fa ogni utente e dice "STOP" quando superano il limite.

---

## 🎯 A Cosa Serve?

### 1. **Prevenire Abusi e Attacchi DoS**
**Scenario**: Un attaccante fa 10.000 richieste al secondo per bloccare il server.

**Senza Rate Limiting**:
```
Attaccante → 10.000 richieste/sec → Server crashato ❌
```

**Con Flask-Limiter**:
```python
@limiter.limit("5 per minute")
def generate_mindmap():
    # ... codice ...
```
```
Attaccante → 10.000 richieste/sec
Flask-Limiter → Blocca dopo 5 richieste ✅
Risposta: HTTP 429 "Too Many Requests"
```

### 2. **Controllo Costi API (OpenAI/Anthropic)**
**Problema**: Gli endpoint tools chiamano LLM che costano soldi.

**Esempio**:
- 1 mindmap = $0.10 (costo OpenAI)
- Senza limiti: 1000 richieste/minuto = **$100/minuto** = $6.000/ora 💸
- Con `"5 per minute"`: Max $0.50/minuto = **$30/ora** (controllabile)

### 3. **Proteggere Risorse Server**
**Endpoint `/api/tools/mindmap`**:
- Chiama RAG con top_k=15 chunks
- Genera prompt LLM (1000+ tokens)
- Aspetta risposta LLM (10-30 secondi)
- Parsing + HTML generation

**Senza Limiti**: 100 richieste simultanee → 100 workers → RAM esaurita → crash
**Con "5 per minute"**: Max 5 operazioni concorrenti → risorse gestibili

---

## ⚙️ Come Funziona nel Codice

### Configurazione Globale (`api_server.py` linee 60-66)
```python
limiter = Limiter(
    app=app,
    key_func=get_remote_address,  # Identifica utente per IP
    default_limits=["200 per day", "50 per hour"],  # Limite generale
    storage_uri="memory://",  # Dove salvare i contatori
    strategy="fixed-window"  # Algoritmo di conteggio
)
```

#### Parametri Spiegati:

**1. `key_func=get_remote_address`**
- **Cosa fa**: Identifica ogni utente tramite indirizzo IP
- **Esempio**:
  - User A (IP: 192.168.1.1) → contatore separato
  - User B (IP: 10.0.0.5) → contatore separato
- **Alternativa**: Usare `user_id` per utenti autenticati

**2. `default_limits=["200 per day", "50 per hour"]`**
- Limiti applicati a TUTTI gli endpoint (se non specificato diversamente)
- **200 richieste al giorno** → 8.3 richieste/ora in media
- **50 richieste all'ora** → limit più str etto per picchi
- Flask-Limiter applica il **più restrittivo**

**3. `storage_uri="memory://"`**
- **Development**: Usa RAM del server (dati persi al riavvio)
- **Production**: Usare Redis (`storage_uri=os.getenv('REDIS_URL')`)
  - Redis = database in-memory condiviso tra workers
  - Persiste contatori anche con restart

**4. `strategy="fixed-window"`**
- **Fixed Window**: Conta richieste in finestre di tempo fisse
  - Esempio con "5 per minute":
    - 10:00:00 - 10:00:59 → finestra 1 (max 5 richieste)
    - 10:01:00 - 10:01:59 → finestra 2 (reset a 0, max 5 richieste)

- **Alternativa "Sliding Window"**: Più precisa ma più costosa computazionalmente

---

### Esempio Endpoint-Specific Limit
```python
@app.route('/api/tools/<document_id>/mindmap', methods=['POST'])
@limiter.limit("5 per minute")  # Override: più stretto del default
@require_auth
def generate_mindmap_tool(document_id):
    # Questo endpoint costa molto (LLM call)
    # Quindi limita a 5 richieste/minuto invece di 50/ora
```

**Cascata di Limiti**:
1. ✅ **Default global**: 200/day, 50/hour
2. ✅ **Endpoint-specific**: 5/minute (più stretto)
3. **Risultato**: Flask-Limiter applica il più restrittivo a ogni momento

**Esempio Timeline**:
```
User fa 5 richieste mindmap in 60 secondi:
  - Richiesta 1-5: ✅ OK (sotto 5/min)
  - Richiesta 6 (a 50 secondi): ❌ HTTP 429 "Rate limit exceeded"
  - Richiesta 7 (a 61 secondi, nuova finestra): ✅ OK
```

---

## 📊 Strategia Rate Limiting per Socrate AI

### Limiti Implementati

| Endpoint | Limit | Ragione |
|----------|-------|---------|
| **Global (default)** | 200/day, 50/hour | Protezione base |
| `/api/tools/mindmap` | 5/minute | LLM cost elevato |
| `/api/tools/outline` | 5/minute | LLM cost elevato |
| `/api/tools/quiz` | 5/minute | LLM cost elevato |
| `/api/tools/summary` | 10/minute | Meno costoso |
| `/api/tools/analyze` | 10/minute | User-driven |

### Perché "5 per minute" per Tools?

**Calcolo Costi**:
- 1 mindmap call = ~2000 input tokens + 1500 output tokens
- GPT-4o costo: $2.50/M input + $10/M output
- **Cost per call**: $0.02 (input) + $0.015 (output) = **~$0.035**

**Con 5 per minute**:
- Max cost/minuto: 5 × $0.035 = $0.175
- Max cost/ora: $10.50
- Max cost/giorno: $252

**Senza limiti** (scenario abuse):
- Attacker: 100 calls/min × $0.035 = **$3.50/min** = **$5,040/giorno** 💸💸💸

**Conclusione**: Rate limiting **critico** per controllo costi!

---

## 🚨 Cosa Succede Quando Si Supera il Limite?

### Response HTTP 429
```json
{
  "error": "429 Too Many Requests",
  "message": "Rate limit exceeded: 5 per 1 minute"
}
```

### Headers Informativi
Flask-Limiter aggiunge headers utili:
```http
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1698156780
Retry-After: 45
```

- `X-RateLimit-Remaining`: Quante richieste restano
- `Retry-After`: Secondi da aspettare prima di riprovare

---

## 🔧 Configurazione Production (Railway)

### 1. Aggiungere Redis Service
```bash
railway add redis
```

### 2. Update `api_server.py`
```python
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.getenv('REDIS_URL', 'memory://'),  # ✅ Redis in prod
    strategy="fixed-window"
)
```

### 3. Environment Variables Railway
```
REDIS_URL=redis://redis.railway.internal:6379
```

**Vantaggi Redis**:
- ✅ Contatori condivisi tra workers Gunicorn
- ✅ Persistenza tra restart
- ✅ Performance migliore per high traffic

---

## 📈 Monitoring Rate Limits

### Log delle Violazioni
Flask-Limiter logga automaticamente:
```python
logger.warning(f"Rate limit exceeded for {get_remote_address()}")
```

### Metriche da Monitorare
1. **Numero di 429 responses** → Troppe? Aumentare limiti o ottimizzare
2. **IP con più violazioni** → Possibili attaccanti da bloccare
3. **Endpoint più limitati** → Indicano bottleneck

---

## ✅ Benefici Implementati

| Beneficio | Impatto |
|-----------|---------|
| **Prevenzione DoS** | ✅ Server protetto da attacchi |
| **Controllo Costi LLM** | ✅ Max $252/giorno invece di illimitato |
| **Stabilità Server** | ✅ Risorse RAM/CPU controllate |
| **Fair Usage** | ✅ Nessun utente monopolizza risorse |
| **Security Posture** | ✅ Riduzione superficie attacco |

---

## 🎓 Best Practices

### 1. **Limiti Più Stretti per Operazioni Costose**
```python
# ✅ GOOD
@limiter.limit("5 per minute")  # LLM call costoso
def generate_mindmap():

# ❌ BAD
@limiter.limit("1000 per minute")  # Troppo permissivo
```

### 2. **User-Based Limits per Utenti Autenticati**
```python
def get_user_id_for_limit():
    return session.get('user_id', get_remote_address())

limiter = Limiter(key_func=get_user_id_for_limit)
```

### 3. **Whitelist per Admin/Internal**
```python
@limiter.exempt  # Nessun limite per questo endpoint
def admin_endpoint():
    pass
```

### 4. **Limiti Dinamici per Tier**
```python
def dynamic_limit():
    user_tier = get_user_tier()
    if user_tier == 'premium':
        return "20 per minute"
    return "5 per minute"

@limiter.limit(dynamic_limit)
def generate_mindmap():
    pass
```

---

## 🔍 Debugging Rate Limits

### Test Locale
```bash
# Invia 10 richieste rapide
for i in {1..10}; do
  curl -X POST http://localhost:5000/api/tools/doc123/mindmap
  sleep 1
done
```

**Output atteso**:
- Request 1-5: ✅ 200 OK
- Request 6: ❌ 429 Too Many Requests
- Request 7 (dopo 60 sec): ✅ 200 OK

### Disable in Development
```python
# api_server.py
if os.getenv('FLASK_ENV') == 'development':
    limiter.enabled = False  # Disabilita rate limiting in dev
```

---

## 📝 Summary

**Flask-Limiter** è essenziale per:
1. **Sicurezza**: Previene abusi e DoS
2. **Costi**: Controlla spese API LLM
3. **Stabilità**: Protegge risorse server
4. **Fairness**: Garantisce accesso equo

**Configurazione Socrate AI**:
- ✅ Limite global: 200/day, 50/hour
- ✅ Tools costosi: 5/minute
- ✅ Storage: Memory (dev), Redis (prod)
- ✅ Strategy: Fixed-window

**Next Steps**:
1. Deploy con limiti attivi
2. Monitorare metriche 429
3. Aggiustare limiti basandosi su usage patterns
4. Migrare a Redis in production per persistence

---

**Versione**: 1.0
**Last Update**: 23 Ottobre 2025
