# Strategia di Storage e Monetizzazione
## Piattaforma Multi-tenant Socrate AI

**Data**: 14 Ottobre 2025
**Versione**: 1.0
**Autore**: Team Architettura Sistema

---

## Riepilogo Esecutivo

Questo documento descrive l'architettura di storage e la strategia di monetizzazione implementata per la piattaforma multi-tenant Socrate AI. La soluzione sfrutta Cloudflare R2 per uno storage scalabile e conveniente, con un sistema di quote utente progettato per mantenere le operazioni all'interno del tier gratuito generando entrate attraverso abbonamenti premium.

---

## 1. Architettura di Storage

### 1.1 Scelta Tecnologica: Cloudflare R2

**Soluzione Selezionata**: Cloudflare R2 (object storage compatibile S3)

**Motivazioni della Scelta**:
- **Zero costi di egress**: A differenza di AWS S3, R2 non applica tariffe per il recupero dati
- **10GB tier gratuito**: Sufficiente per la base utenti iniziale (100-200 utenti)
- **API compatibile S3**: Migrazione facile verso altri provider se necessario
- **Integrazione CDN globale**: Accesso veloce tramite la rete edge di Cloudflare
- **Conformità GDPR**: Endpoint Europa selezionato per sovranità dei dati
- **SLA 99.9% uptime**: Affidabilità di livello enterprise

**Alternative Considerate**:
1. **Storage BLOB in database** ❌
   - Non scalabile per file di grandi dimensioni
   - Aumenta le dimensioni del database e i costi di backup
   - Prestazioni query lente

2. **AWS S3** ❌
   - Costi di egress ($0.09/GB dopo 100GB)
   - Costerebbe $9/mese per 100GB di traffico
   - Più costoso su larga scala

3. **Filesystem locale** ❌
   - I container Railway sono effimeri
   - Nessuno storage condiviso tra servizi Web e Worker
   - Perdita dati al riavvio del container

### 1.2 Organizzazione Storage

**Struttura File**:
```
R2_BUCKET: socrate-ai-storage
├── users/{user_id}/
│   └── docs/{document_id}/
│       ├── {filename}.pdf
│       ├── {filename}_sections_metadata.json
│       └── {filename}_sections_index.json
```

**Generazione Chiavi** (core/s3_storage.py:171):
```python
def generate_file_key(user_id: str, document_id: str, filename: str) -> str:
    """Genera chiave S3: users/{user_id}/docs/{doc_id}/{filename}"""
    safe_filename = "".join(c for c in filename if c.isalnum() or c in ('._- ')).strip()
    return f"users/{user_id}/docs/{document_id}/{safe_filename}"
```

**Vantaggi**:
- Isolamento utenti per conformità GDPR
- Calcolo semplice dello storage per utente
- Eliminazione efficiente quando gli utenti lasciano la piattaforma
- Audit trail organizzati

### 1.3 Dettagli Implementazione

**Flusso Upload** (api_server.py:338-418):
1. L'utente carica il file via REST API (multipart/form-data)
2. Flask legge il contenuto del file in memoria
3. Genera ID documento univoco (UUID)
4. Upload su R2: `users/{user_id}/docs/{doc_id}/{filename}`
5. Memorizza la chiave R2 in PostgreSQL `documents.file_path`
6. Attiva task Celery per elaborazione asincrona

**Flusso Elaborazione** (tasks.py:68-95):
1. Il worker Celery recupera i metadati del documento da PostgreSQL
2. Download del file da R2 usando la chiave memorizzata
3. Salvataggio in directory temporanea (`tempfile.mkdtemp()`)
4. Esecuzione encoder memvid sul file temporaneo
5. Upload dei metadati/indice elaborati su R2
6. Aggiornamento stato documento nel database
7. Eliminazione file temporanei (`shutil.rmtree(temp_dir)`)

**Sezioni Codice Principali**:
- Upload: api_server.py:359-369
- Download: tasks.py:69-95
- Client R2: core/s3_storage.py:24-43
- Pulizia: tasks.py:244-249

---

## 2. Analisi Costi

### 2.1 Prezzi Cloudflare R2

**Tier Gratuito**:
- Storage: 10 GB/mese
- Operazioni Classe A (scritture): 1 milione/mese
- Operazioni Classe B (letture): 10 milioni/mese
- Egress: **Illimitato** (nessun costo)

**Tier a Pagamento** (oltre il tier gratuito):
- Storage: $0.015/GB/mese (~€0.014/GB)
- Classe A: $4.50 per milione di operazioni
- Classe B: $0.36 per milione di operazioni

### 2.2 Costi Previsti su Scala

**Scenario 1: Dentro il Tier Gratuito (0-200 utenti)**
- Media 50MB per utente
- Totale: 10GB storage
- **Costo mensile**: €0 (tier gratuito)

**Scenario 2: Piccola Scala (200-500 utenti)**
- Media 50MB per utente
- Totale: 25GB storage
- Eccedenza: 15GB a pagamento
- **Costo mensile**: €0.21 (15GB × €0.014)

**Scenario 3: Media Scala (500-1000 utenti)**
- Media 50MB per utente
- Totale: 50GB storage
- Eccedenza: 40GB a pagamento
- **Costo mensile**: €0.56 (40GB × €0.014)

**Scenario 4: Grande Scala (1000-5000 utenti)**
- Media 50MB per utente
- Totale: 250GB storage
- Eccedenza: 240GB a pagamento
- **Costo mensile**: €3.36 (240GB × €0.014)

**Costo Operazioni** (trascurabile):
- 1000 utenti × 10 upload/mese = 10.000 scritture
- 1000 utenti × 100 query/mese = 100.000 letture
- Ampiamente dentro il tier gratuito (1M scritture, 10M letture)

---

## 3. Strategia di Monetizzazione

### 3.1 Sistema Quote Utente

**Implementato in database.py:82-83**:
```python
subscription_tier = Column(String(20), default='free')  # free, pro, enterprise
storage_quota_mb = Column(Integer, default=500)
storage_used_mb = Column(Integer, default=0)
```

**Struttura Tier**:

| Tier       | Quota Storage | Prezzo Mensile | Utenti Target         |
|------------|---------------|----------------|-----------------------|
| Free       | 100 MB        | €0             | Utenti trial          |
| Pro        | 5 GB          | €9.99/mese     | Utenti regolari       |
| Enterprise | 50 GB         | €49.99/mese    | Power user/aziende    |

### 3.2 Proiezioni Entrate

**Obiettivo: 1000 Utenti Attivi**

**Scenario Conservativo (80% free, 15% pro, 5% enterprise)**:
- Free: 800 utenti × €0 = €0
- Pro: 150 utenti × €9.99 = €1.498,50
- Enterprise: 50 utenti × €49.99 = €2.499,50
- **Entrate Mensili Totali**: €3.998
- **Costo Storage R2**: ~€0.56 (40GB totali)
- **Margine Netto Storage**: 99.99%

**Scenario Ottimistico (60% free, 30% pro, 10% enterprise)**:
- Free: 600 utenti × €0 = €0
- Pro: 300 utenti × €9.99 = €2.997
- Enterprise: 100 utenti × €49.99 = €4.999
- **Entrate Mensili Totali**: €7.996
- **Costo Storage R2**: ~€3.36 (240GB totali)
- **Margine Netto Storage**: 99.96%

**Insight Chiave**: I costi di storage rimangono trascurabili anche su larga scala grazie a:
1. Zero costi di egress (gli utenti interrogano i documenti frequentemente)
2. Tariffe R2 basse (€0.014/GB)
3. Limiti di quota utente prevengono abusi

### 3.3 Applicazione Quote

**Implementazione Attuale**:
- Tracciamento quote nel database (database.py:82-83)
- Validazione pre-upload in document_operations.py (da implementare)

**Funzionalità Richieste**:
1. **Controllo pre-upload**:
   ```python
   def check_storage_quota(user_id: str, file_size: int) -> bool:
       user = get_user_by_id(user_id)
       if (user.storage_used_mb + file_size / 1024 / 1024) > user.storage_quota_mb:
           raise ValueError("Quota storage superata")
   ```

2. **Aggiornamento quota all'upload**:
   ```python
   user.storage_used_mb += file_size / 1024 / 1024
   db.commit()
   ```

3. **Riduzione quota alla cancellazione**:
   ```python
   user.storage_used_mb -= doc.file_size / 1024 / 1024
   db.commit()
   ```

4. **Visualizzazione dashboard utente**:
   - Barra di progresso che mostra l'utilizzo dello storage
   - Pulsante "Passa a Pro" quando ci si avvicina al limite

### 3.4 Flussi di Entrate Aggiuntivi

**Funzionalità Premium** (oltre lo storage):
- Elaborazione prioritaria (coda più veloce)
- Modelli AI avanzati (GPT-4, Claude Opus)
- Branding personalizzato (white-label)
- Accesso API per integrazioni
- Capacità di elaborazione batch
- Ritenzione estesa (free: 30 giorni, pro: 1 anno, enterprise: illimitato)

**Pricing Basato sull'Uso** (futuro):
- Crediti query AI (es. 100 free/mese, poi €0.10 per query)
- Minuti encoding video (free: 10 min/mese, poi €0.50/min)

---

## 4. Gestione Rischi

### 4.1 Rischi Storage

**Rischio 1: Crescita Utenti Rapida**
- **Scenario**: 10.000 utenti free × 100MB = 1TB storage
- **Costo**: €14/mese (sostenibile)
- **Mitigazione**: Funnel di conversione verso tier a pagamento, limiti quota aggressivi per tier free

**Rischio 2: Abuso Storage**
- **Scenario**: Utenti caricano file di grandi dimensioni ripetutamente
- **Mitigazione**:
  - Limiti dimensione file (free: 50MB, pro: 500MB, enterprise: 5GB)
  - Rate limiting (10 upload/ora)
  - Rilevamento automatico duplicati

**Rischio 3: Aumento Prezzi R2**
- **Scenario**: Cloudflare aumenta i prezzi
- **Mitigazione**: API compatibile S3 consente migrazione ad AWS S3, Google Cloud Storage, o MinIO self-hosted

**Rischio 4: Perdita Dati**
- **Scenario**: Outage R2 o corruzione dati
- **Mitigazione**:
  - SLA 99.9% di Cloudflare
  - Backup giornalieri su provider secondario (opzionale, per tier enterprise)
  - Metadati critici memorizzati in PostgreSQL (backup ridondante)

### 4.2 Rischi Conformità

**Conformità GDPR**:
- ✅ Endpoint Europa selezionato
- ✅ Isolamento utenti per struttura cartelle
- ✅ Eliminazione dati facile (elimina tutti i file in `users/{user_id}/`)
- ✅ Capacità export dati (download tutti i file via API S3)

**Ritenzione Dati**:
- Implementare pulizia automatica dopo 30 giorni (tier free)
- Tier enterprise: ritenzione controllata dall'utente

---

## 5. Roadmap Implementazione

### Fase 1: Funzionalità Core ✅ (COMPLETATA)
- [x] Creazione bucket R2
- [x] Integrazione client S3 (core/s3_storage.py)
- [x] Endpoint upload (api_server.py:338-418)
- [x] Download nel worker (tasks.py:68-95)
- [x] Elaborazione file temporanei e pulizia
- [x] Configurazione deployment Railway

### Fase 2: Sistema Quote (PROSSIMO SPRINT)
- [ ] Implementare controllo quota pre-upload
- [ ] Tracciamento utilizzo storage su upload/delete
- [ ] Visualizzazione storage dashboard utente
- [ ] Flusso "Passa a Pro"

### Fase 3: Monetizzazione (SPRINT 3)
- [ ] Integrazione pagamenti Stripe
- [ ] Gestione abbonamenti
- [ ] Logica upgrade/downgrade tier
- [ ] Generazione fatture

### Fase 4: Funzionalità Avanzate (Q1 2026)
- [ ] Limiti dimensione file per tier
- [ ] Rate limiting
- [ ] Rilevamento duplicati
- [ ] Politiche pulizia automatica
- [ ] Dashboard admin per monitoraggio storage

### Fase 5: Ottimizzazione Scala (Q2 2026)
- [ ] Integrazione CDN per accesso più veloce
- [ ] Replica multi-regione (per enterprise)
- [ ] Archiviazione cold storage (file acceduti raramente)
- [ ] Ottimizzazione compressione

---

## 6. Monitoraggio & Allarmi

### 6.1 Metriche Chiave da Tracciare

**Metriche Storage**:
- Storage totale utilizzato (GB)
- Storage per utente (MB)
- Tasso crescita storage (GB/mese)
- Utilizzo tier gratuito (%)

**Metriche Utente**:
- Totale utenti per tier (free/pro/enterprise)
- Tasso conversione (free → pagamento)
- Tasso abbandono (churn rate)
- Entrata media per utente (ARPU)

**Metriche Costo**:
- Fattura mensile R2
- Costo storage per utente
- Margine lordo per tier

**Metriche Performance**:
- Tasso successo upload
- Tempo medio upload
- Tempo elaborazione worker
- Errori download

### 6.2 Soglie Allarme

**Allarmi Critici**:
- Storage R2 > 8GB (80% del tier gratuito)
- Tasso fallimento upload > 5%
- Profondità coda worker > 100 task

**Allarmi Warning**:
- Storage R2 > 7GB (70% del tier gratuito)
- Tempo medio elaborazione > 2 minuti
- Profondità coda worker > 50 task

---

## 7. Analisi Competitiva

### 7.1 Confronto con Competitor

| Funzionalità      | Socrate AI    | Notion AI     | ChatPDF       | Adobe Acrobat |
|-------------------|---------------|---------------|---------------|---------------|
| Storage Gratuito  | 100 MB        | Illimitato*   | 3 documenti   | 100 MB        |
| Storage Pagamento | 5 GB (€9.99)  | Illimitato*   | Illimitato (€5)| 100 GB (€18)|
| AI Documenti      | ✅ Custom     | ✅ GPT-4      | ✅ GPT-3.5    | ✅ Proprietario|
| Elaboraz. Video   | ✅            | ❌            | ❌            | ❌            |
| Open Source       | ✅ (memvid)   | ❌            | ❌            | ❌            |

*Notion: Nessun limite storage esplicito, ma si applicano rate limits e limiti query AI

**Vantaggi Competitivi**:
1. **Elaborazione video**: Funzionalità unica non offerta dai competitor AI documenti
2. **Encoder open source**: Trasparenza e personalizzabilità
3. **Zero lock-in**: API compatibile S3, export dati facile
4. **Tier gratuito generoso**: 100MB consente utilizzo reale prima del paywall

**Posizionamento Prezzi**:
- **Tier free**: Più generoso di ChatPDF (limite 3 documenti)
- **Tier pro**: Competitivo con ChatPDF (€9.99 vs €5), ma offre video
- **Tier enterprise**: Significativamente più economico di Adobe (€49.99 vs €18/utente/mese per team)

---

## 8. Conclusioni

### 8.1 Riepilogo Strategico

L'architettura di storage implementata raggiunge tre obiettivi critici:

1. **Scalabilità**: L'API compatibile S3 consente crescita da 100 utenti a 100.000+ senza cambiamenti architetturali
2. **Convenienza**: Zero costi egress e bassi costi storage (€0.014/GB) garantiscono margini di profitto >99.9% sullo storage
3. **Monetizzazione**: Sistema quote a livelli crea percorsi chiari di upgrade mantenendo i costi storage trascurabili

### 8.2 Fattori Chiave di Successo

**Tecnici**:
- ✅ Storage indipendente dai container (risolve filesystem effimero Railway)
- ✅ Elaborazione asincrona con Celery (separa upload da encoding)
- ✅ Pulizia file temporanei (previene gonfiamento disco)
- ✅ Isolamento utenti (conformità GDPR, eliminazione facile)

**Business**:
- ✅ Tier gratuito guida adozione (100MB = ~2-3 documenti)
- ✅ Proposta valore chiara per upgrade (5GB Pro = ~100 documenti)
- ✅ Costi storage rimangono <1% delle entrate su scala
- ✅ Zero lock-in costruisce fiducia (export compatibile S3)

### 8.3 Prossimi Passi

**Azioni Immediate**:
1. Implementare applicazione quote nell'endpoint upload
2. Aggiungere visualizzazione utilizzo storage alla dashboard utente
3. Configurare monitoraggio per utilizzo storage R2
4. Testare flusso completo upload → elaborazione → download

**Breve Termine (1 mese)**:
1. Integrare Stripe per gestione abbonamenti
2. Implementare flusso "Passa a Pro"
3. Creare dashboard admin per metriche storage
4. Configurare allarmi automatici per soglie storage

**Lungo Termine (3-6 mesi)**:
1. A/B test tier prezzi (€9.99 vs €14.99 per Pro)
2. Analizzare funnel conversione e ottimizzare flusso free → pagamento
3. Esplorare pricing basato sull'uso per query AI
4. Considerare opzione MinIO self-hosted per clienti enterprise

---

## 9. Appendice Tecnica

### 9.1 Variabili Configurazione

**Variabili Ambiente Railway** (entrambi i servizi Web e Worker):
```bash
R2_ACCESS_KEY_ID=<cloudflare_r2_access_key>
R2_SECRET_ACCESS_KEY=<cloudflare_r2_secret_key>
R2_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
R2_BUCKET_NAME=socrate-ai-storage
```

### 9.2 Riferimenti Codice

**Operazioni Storage**:
- Upload: api_server.py:359-369
- Download: tasks.py:69-95
- Eliminazione: core/s3_storage.py:112-138
- Verifica esistenza: core/s3_storage.py:141-168

**Modelli Database**:
- Quote utente: database.py:82-83
- Storage documenti: database.py:112-113
- Tracciamento utilizzo: document_operations.py (da implementare)

**Task Worker**:
- Flusso elaborazione: tasks.py:22-278
- Logica pulizia: tasks.py:244-249

### 9.3 Checklist Testing

**Testing Manuale**:
- [ ] Upload PDF 1MB (tier free)
- [ ] Upload PDF 100MB (vicino alla quota)
- [ ] Upload PDF 101MB (dovrebbe fallire)
- [ ] Eliminazione documento (quota dovrebbe diminuire)
- [ ] Worker scarica da R2 con successo
- [ ] File elaborati caricati su R2
- [ ] File temporanei puliti

**Load Testing**:
- [ ] 10 upload concorrenti
- [ ] 100 documenti in coda worker
- [ ] Latenza lettura/scrittura R2 sotto carico

**Security Testing**:
- [ ] Utente A non può accedere ai documenti di Utente B
- [ ] Credenziali R2 invalide falliscono con grazia
- [ ] Attacchi path traversal bloccati

---

**Versione Documento**: 1.0
**Ultimo Aggiornamento**: 14 Ottobre 2025
**Prossima Revisione**: Novembre 2025 (dopo implementazione sistema quote)
