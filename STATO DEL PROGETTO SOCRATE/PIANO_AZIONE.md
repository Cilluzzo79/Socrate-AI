# Piano d'Azione Socrate AI
**Creato**: 15 Ottobre 2025

---

## 📍 PUNTO ATTUALE

**Fase**: 2 - Storage e Costi (80%)
**Ultimo deploy**: 15 ottobre 2025 (mattina)
**Prossimo step**: Test upload file end-to-end

---

## 🎯 PIANO SETTIMANALE

### Settimana 1 (15-21 Ottobre) - Completare Fase 2
**Obiettivo**: Sistema upload + processing funzionante al 100%

#### Giorno 1-2 (15-16 Ottobre) ⬅️ SIAMO QUI
- [ ] **Test upload file su produzione**
  - Verificare upload su https://web-production-38b1c.up.railway.app/
  - Debug eventuali errori R2
  - Confermare file arriva su Cloudflare

- [ ] **Verificare processing completo**
  - Worker preleva task da Redis
  - Download file da R2
  - Memvid encoder funziona
  - Upload metadata su R2
  - Status documento diventa "ready"

- [ ] **Fix bug emersi**
  - Correggere errori upload/download
  - Sistemare processing se fallisce
  - Aggiornare logs per debug

#### Giorno 3-4 (17-18 Ottobre)
- [ ] **Implementare quote storage**
  - Pre-upload check: verificare spazio disponibile
  - Bloccare upload se quota superata
  - Mostrare storage usage in dashboard
  - Test con file grandi (vicino al limite)

- [ ] **Migliorare dashboard**
  - Progress bar upload più accurata
  - Notifiche upload completato
  - Gestione errori più chiara
  - Link per scaricare file processati

#### Giorno 5-7 (19-21 Ottobre)
- [ ] **Test completi end-to-end**
  - Test con PDF di varie dimensioni (1MB, 10MB, 50MB)
  - Test con diversi formati supportati
  - Test upload multipli simultanei
  - Test con utenti diversi (isolamento)

- [ ] **Documentare problemi risolti**
  - Aggiornare STATO_PROGETTO.md
  - Documentare fix implementati
  - Creare troubleshooting guide

- [ ] **✅ CHECKPOINT: Fase 2 completata al 100%**

---

### Settimana 2 (22-28 Ottobre) - Iniziare Fase 3: Query AI

#### Giorno 1-3 (22-24 Ottobre)
- [ ] **Implementare Memvid Query Engine**
  - Creare `core/memvid_query.py`
  - Funzione `find_relevant_chunks()`
  - Integrare embeddings (sentence-transformers)
  - Test similarity search

#### Giorno 4-5 (25-26 Ottobre)
- [ ] **Implementare OpenRouter Client**
  - Creare `core/openrouter_client.py`
  - Setup API key OpenRouter
  - Test chiamata base con GPT-4o-mini
  - Gestione errori e retry

#### Giorno 6-7 (27-28 Ottobre)
- [ ] **Integrare Query nel backend**
  - Completare endpoint `/api/query`
  - Collegare memvid query + OpenRouter
  - Salvare chat_sessions in database
  - Test query base

---

### Settimana 3 (29 Ottobre - 4 Novembre) - Query AI Frontend

#### Giorno 1-3
- [ ] **Creare interfaccia chat**
  - Chat UI in dashboard
  - Input query
  - Mostra risposta AI
  - Mostra sources (pagine documento)

#### Giorno 4-5
- [ ] **Test query AI completi**
  - Test con domande semplici
  - Test con domande complesse
  - Test accuratezza risposte
  - Ottimizzare numero chunk

#### Giorno 6-7
- [ ] **Tracking costi**
  - Mostrare token usati per query
  - Calcolare costo in EUR
  - Salvare in database
  - Dashboard costi utente

- [ ] **✅ CHECKPOINT: Fase 3 completata**

---

### Settimana 4 (5-11 Novembre) - Monetizzazione Base

#### Giorno 1-3
- [ ] **Setup Stripe**
  - Account Stripe
  - Configurare prodotti (Free, Pro, Enterprise)
  - Webhook subscription
  - Test checkout flow

#### Giorno 4-5
- [ ] **Implementare tier limits**
  - Bloccare funzioni per tier
  - Upgrade flow (free → pro)
  - Mostrare feature locked

#### Giorno 6-7
- [ ] **Test pagamenti**
  - Test checkout completo
  - Test upgrade subscription
  - Test webhook eventi
  - Verificare invoice generation

---

## 🎯 MILESTONE PRINCIPALI

### Milestone 1: Sistema Base Funzionante (Fine Ottobre)
**Deliverable:**
- ✅ Upload + processing documenti
- ✅ Query AI funzionante
- ✅ Dashboard utente base
- ✅ Tracking costi

### Milestone 2: Monetizzazione Attiva (Metà Novembre)
**Deliverable:**
- ✅ Stripe integrato
- ✅ Tier free/pro/enterprise
- ✅ Quote enforcement
- ✅ Payment flow completo

### Milestone 3: Beta Launch (Fine Novembre)
**Deliverable:**
- ✅ 50 beta tester
- ✅ Feedback raccolto
- ✅ Bug principali fixati
- ✅ Documentazione utente

### Milestone 4: Public Launch (Dicembre 2025)
**Deliverable:**
- ✅ Landing page
- ✅ Marketing materiale
- ✅ Terms of Service + Privacy Policy
- ✅ Customer support setup

---

## 📊 METRICHE DI SUCCESSO

### Fase 2 (Storage) - Criteri Completamento
- [ ] Upload success rate > 95%
- [ ] Processing success rate > 90%
- [ ] Average processing time < 60s
- [ ] Zero errori R2 critici
- [ ] Storage quota funzionante

### Fase 3 (Query AI) - Criteri Completamento
- [ ] Query response time < 5s
- [ ] Risposta accurata in 80% dei casi
- [ ] Token usage ottimizzato (< 2000 per query)
- [ ] Costo medio query < €0.01
- [ ] Zero errori OpenRouter critici

### Fase 4 (Monetizzazione) - Criteri Completamento
- [ ] Payment success rate > 98%
- [ ] Stripe webhook reliability > 99%
- [ ] Upgrade flow completato in < 2 minuti
- [ ] Zero errori fatturazione

---

## 🔄 REVIEW SETTIMANALE

### Ogni Lunedì
1. **Rivedere progressi settimana precedente**
   - Cosa abbiamo completato?
   - Cosa è rimasto indietro?
   - Problemi emersi?

2. **Aggiornare piano settimana corrente**
   - Riprioritizzare task
   - Aggiungere nuovi task emersi
   - Rimuovere task non più rilevanti

3. **Update STATO_PROGETTO.md**
   - Aggiornare percentuale completamento fasi
   - Documentare problemi risolti
   - Aggiornare "DOVE SIAMO ADESSO"

---

## 🚨 RISCHI E MITIGAZIONI

### Rischio 1: R2 Upload Instabile
**Probabilità**: Media
**Impatto**: Alto
**Mitigazione**:
- Implementare retry logic con backoff
- Fallback a storage locale temporaneo
- Alert quando error rate > 5%

### Rischio 2: OpenRouter Costi Fuori Controllo
**Probabilità**: Media
**Impatto**: Alto
**Mitigazione**:
- Limite max token per query
- Cache query comuni
- Monitoraggio daily cost con alert

### Rischio 3: Worker Overload
**Probabilità**: Bassa
**Impatto**: Medio
**Mitigazione**:
- Auto-scaling worker su Railway
- Queue size monitoring
- Priority queue per tier premium

### Rischio 4: Stripe Integration Bug
**Probabilità**: Bassa
**Impatto**: Alto
**Mitigazione**:
- Test extensivi in test mode
- Webhook logging completo
- Manual fallback procedure

---

## 📝 NOTE IMPLEMENTAZIONE

### Priorità Features
**Must Have (prima del launch):**
- Upload documenti
- Processing memvid
- Query AI base
- Payment Stripe
- Storage quota

**Nice to Have (post-launch):**
- Video processing
- Quiz generation
- Multi-document query
- Custom prompts
- Team accounts

### Tech Debt da Affrontare
- [ ] Migrare da logging base a structured logging
- [ ] Implementare Alembic per database migrations
- [ ] Aggiungere unit tests (coverage > 70%)
- [ ] Setup CI/CD con GitHub Actions
- [ ] Implementare rate limiting API

---

**Ultima revisione**: 15 Ottobre 2025
**Prossima revisione**: 21 Ottobre 2025 (fine Settimana 1)
