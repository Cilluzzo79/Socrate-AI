# SOCRATE AI - VISION GRUPPI COLLABORATIVI

**Ciao Francesca, questo è il progetto che sto sviluppando. Cosa ne pensi? Hai altre idee?**

---

## 🎯 L'IDEA IN SINTESI

Trasformare Socrate AI da **sistema individuale** a **piattaforma collaborativa per gruppi**, dove team, classi, famiglie e organizzazioni possono:

- **Condividere documenti** in uno spazio comune
- **Interrogare insieme** la stessa knowledge base
- **Ottimizzare storage** (1 file condiviso vs N copie duplicate)
- **Collaborare efficacemente** con permessi e ruoli

---

## 💡 VANTAGGI STRATEGICI

### 1. **Business Model Scalabile**

**Pricing Proposto**:
```
FREE (Individual):
- 1 utente
- 50 MB storage
- 10 query/giorno
- Nessun gruppo

TEAM ($19/mese o $15/anno):
- 5 utenti gruppo
- 500 MB condiviso
- 500 query/giorno gruppo
- 1 gruppo
- Basic analytics

BUSINESS ($49/mese o $39/anno):
- 20 utenti gruppo
- 2 GB condiviso
- Query illimitate
- 3 gruppi
- Advanced analytics
- Priority support

ENTERPRISE (Custom):
- Utenti illimitati
- Storage custom
- Multi-gruppi illimitati
- SSO/SAML
- API dedicata
- SLA 99.9%
- Account manager
```

**Revenue Model Esempio (100 clienti)**:
- 60 FREE: $0
- 30 TEAM: 30 × $19 = **$570/mese**
- 8 BUSINESS: 8 × $49 = **$392/mese**
- 2 ENTERPRISE: 2 × $299 = **$598/mese**

**MRR Totale: $1,560/mese = $18,720/anno**

Con margine del **78%** dopo costi infrastruttura (Railway, R2, LLM API).

### 2. **Ottimizzazione Storage** ✅

**Prima (individuale)**:
```
User A: manuale.pdf (5 MB)
User B: manuale.pdf (5 MB) [DUPLICATO]
User C: manuale.pdf (5 MB) [DUPLICATO]
TOTALE: 15 MB
```

**Dopo (gruppo)**:
```
Gruppo XYZ: manuale.pdf (5 MB) [SHARED]
- User A può accedere
- User B può accedere
- User C può accedere
TOTALE: 5 MB (-67% storage!)
```

### 3. **Use Cases Perfetti**

**🏫 Scuola/Università**:
- Prof carica dispense → studenti interrogano
- Storage condiviso classe
- History query per vedere cosa chiedono gli studenti
- Esami: verificare preparazione studenti tramite domande

**🏢 Studio Legale/Consulenza**:
- Partner carica contratti/normative/giurisprudenza
- Team accede knowledge base comune
- Audit trail: chi ha interrogato cosa e quando
- Ricerca rapida in migliaia di pagine di documenti

**👨‍👩‍👧‍👦 Famiglia**:
- Manuali elettrodomestici condivisi
- Documenti medici/assicurativi accessibili a tutti
- Ricette, guide fai-da-te
- Storia familiare, genealogia

**🔬 Team Ricerca**:
- Paper scientifici condivisi
- Libreria bibliografia comune
- Collaborazione analisi dati
- Note di ricerca accessibili a tutto il team

**🏭 Corporate/Azienda**:
- Manuali operativi condivisi
- Policy aziendali interrogabili
- Onboarding nuovi dipendenti (knowledge base pronta)
- Documentazione tecnica accessibile

---

## 🏗️ ARCHITETTURA PROPOSTA

### Nuovo Schema Database

```sql
-- Gruppi
CREATE TABLE groups (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE,
    type VARCHAR(50), -- school, business, family, research, other
    subscription_tier VARCHAR(50) DEFAULT 'free',
    storage_quota_mb INTEGER DEFAULT 500,
    storage_used_mb FLOAT DEFAULT 0,
    query_quota_daily INTEGER DEFAULT 500,
    created_at TIMESTAMP DEFAULT NOW(),
    owner_user_id UUID REFERENCES users(id),
    settings JSONB DEFAULT '{}'
);

-- Memberships (relazione users ↔ groups)
CREATE TABLE group_memberships (
    id UUID PRIMARY KEY,
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member', -- owner, admin, member, viewer
    joined_at TIMESTAMP DEFAULT NOW(),
    invited_by UUID REFERENCES users(id),
    permissions JSONB DEFAULT '{"can_upload": true, "can_delete": false}'
);

-- Documenti (modificato)
ALTER TABLE documents ADD COLUMN group_id UUID REFERENCES groups(id);
ALTER TABLE documents ADD COLUMN visibility VARCHAR(20) DEFAULT 'private'; -- private, group, public
ALTER TABLE documents ADD COLUMN shared_with_groups UUID[]; -- per multi-share

-- Chat sessions (modificato per analytics)
ALTER TABLE chat_sessions ADD COLUMN group_id UUID REFERENCES groups(id);
```

### Logica Permessi

**Matrice Ruoli**:

| Ruolo    | Upload Doc | Delete Doc | Invite User | Query Doc | View Analytics |
|----------|-----------|-----------|-------------|-----------|----------------|
| **Owner**    | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Admin**    | ✅ | ✅ (solo propri) | ✅ | ✅ | ✅ |
| **Member**   | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Viewer**   | ❌ | ❌ | ❌ | ✅ | ❌ |

### Regole Business

1. **Un utente può**:
   - Appartenere a **N gruppi** contemporaneamente
   - Avere **documenti privati** + **documenti di gruppo**
   - Creare **1 gruppo free** come owner

2. **Un gruppo può**:
   - Avere **storage condiviso** (quota basata su tier)
   - Avere **1 owner** (chi paga/gestisce) + **M admin/member/viewer**
   - Impostare **policy upload** (tutti possono / solo admin)

3. **Un documento può**:
   - Essere **privato** (solo user_id, no group_id)
   - Essere **di gruppo** (group_id set, visibile a tutti membri)
   - Essere **multi-share** (condiviso in N gruppi diversi - array)

---

## 🎨 UX FLOW PROPOSTO

### Registrazione Nuovo Utente

```
1. Login Telegram
   ↓
2. Welcome screen:
   "Come vuoi usare Socrate AI?"

   [🧑 Uso Individuale]     [👥 Team/Gruppo]

   ↓                         ↓
3a. INDIVIDUALE:          3b. TEAM/GRUPPO:
   → Dashboard            "Hai già un codice invito?"
     normale
                          [✅ Sì, ho un codice]  [➕ No, creo nuovo gruppo]

                          ↓                      ↓
                          4a. Con codice:        4b. Nuovo gruppo:
                          → Inserisci           → "Nome gruppo": _______
                            codice              → "Tipo": [Scuola] [Lavoro]
                          → Join gruppo           [Famiglia] [Ricerca] [Altro]
                            esistente           → "Piano": [FREE] [TEAM] [BUSINESS]
                                                → Crea gruppo
                          ↓                      ↓
                          Dashboard con sezione "Gruppi"
```

### Upload Documento

```
Dashboard
   ↓
[+ Carica Documento]
   ↓
"Dove vuoi caricare questo documento?"

┌─────────────────────────────────────┐
│ 📁 I miei documenti privati         │ ← Solo tu puoi accedere
├─────────────────────────────────────┤
│ 👥 Gruppo: Studio Rossi & Partners │ ← 15 membri possono accedere
├─────────────────────────────────────┤
│ 👥 Gruppo: Classe 3A Liceo          │ ← 28 membri possono accedere
└─────────────────────────────────────┘
   ↓
Seleziona gruppo → Upload + Processing
   ↓
✅ Documento caricato e visibile a tutti i membri del gruppo!
```

### Query su Documento Condiviso

```
Dashboard Gruppo
   ↓
Vedi documenti condivisi:
- Manuale_Operativo.pdf (caricato da: Marco, 12 gg fa)
- Contratto_Tipo.pdf (caricato da: Admin, 3 mesi fa)
- Policy_Privacy.pdf (caricato da: Giulia, 1 settimana fa)
   ↓
Clicca documento → [💬 Fai una domanda]
   ↓
"Quali sono le clausole sulla riservatezza?"
   ↓
✅ Risposta AI + fonti (chunk specifici del PDF)

[Admin può vedere]:
- Chi ha interrogato questo documento
- Quali domande sono state fatte
- Quando e quante volte
```

---

## 🚀 ROADMAP IMPLEMENTAZIONE

### Fase 1: Foundation (2 settimane)
**Obiettivo**: MVP gruppi base funzionante

- [ ] Schema database:
  - Tabella `groups`
  - Tabella `group_memberships`
  - Modifica `documents` (+ group_id, visibility)

- [ ] API Backend:
  - `POST /api/groups` - Crea gruppo
  - `GET /api/groups` - Lista gruppi utente
  - `POST /api/groups/{id}/invite` - Genera codice invito
  - `POST /api/groups/join` - Join con codice
  - `GET /api/groups/{id}/members` - Lista membri

- [ ] Logica Permessi:
  - Middleware verifica membership
  - Check role per operazioni (upload/delete/invite)

- [ ] Storage:
  - Quota gruppo (storage_used_mb)
  - Upload documenti a gruppo (group_id)

**Deliverable**: Sistema gruppi FREE tier (max 5 membri, 500 MB)

---

### Fase 2: Document Sharing & Query (1 settimana)
**Obiettivo**: Condivisione documenti e interrogazione

- [ ] Upload con selezione destinazione:
  - Radio buttons: "Privato" / "Gruppo X" / "Gruppo Y"
  - Validazione quota storage gruppo

- [ ] Query su documenti gruppo:
  - Endpoint `/api/query` → check group_id
  - Salva chat_session con group_id (analytics)

- [ ] UI Dashboard Gruppo:
  - Lista documenti gruppo
  - Chi ha caricato + quando
  - Bottone query per ogni documento

**Deliverable**: Upload e query documenti condivisi funzionanti

---

### Fase 3: Inviti & Onboarding (1 settimana)
**Obiettivo**: Flow completo inviti membri

- [ ] Sistema Codici Invito:
  - Generazione codice univoco (es: `STUD-XY8H-2K9L`)
  - Validazione + expiry (7 giorni)
  - Limit inviti per gruppo (tier-based)

- [ ] Onboarding Migliorato:
  - Welcome screen "Individuale vs Gruppo"
  - Flow "Crea gruppo" con form completo
  - Flow "Entra in gruppo" con codice

- [ ] Notifiche:
  - Email/Telegram quando invitato
  - Conferma join gruppo

**Deliverable**: Sistema inviti completo e testato

---

### Fase 4: Analytics & Admin Panel (1 settimana)
**Obiettivo**: Dashboard admin gruppo

- [ ] Analytics Gruppo:
  - Storage usage (grafico torta per documento)
  - Query count giornaliere/settimanali/mensili
  - Top 5 documenti più interrogati
  - Top 5 query più frequenti

- [ ] Admin Panel:
  - Lista membri con ruoli
  - Change role (member → admin, etc.)
  - Remove member
  - Transfer ownership

- [ ] Settings Gruppo:
  - Rinomina gruppo
  - Change tipo (scuola/lavoro/famiglia)
  - Policy upload (all members / admin only)
  - Delete gruppo (con conferma + grace period)

**Deliverable**: Dashboard admin completa

---

### Fase 5: Billing & Subscription (2 settimane) - OPZIONALE
**Obiettivo**: Monetizzazione tier paganti

- [ ] Integrazione Stripe:
  - Checkout session TEAM/BUSINESS
  - Webhook subscription events
  - Cancel/Resume subscription

- [ ] Enforcement Limiti:
  - Check quota storage prima upload
  - Check query quota giornaliera
  - Soft limit (warning) vs hard limit (block)

- [ ] Upgrade/Downgrade Flow:
  - Da FREE a TEAM (pagamento)
  - Da TEAM a BUSINESS (upgrade)
  - Downgrade con grace period

- [ ] Invoice & Billing:
  - Email fatture automatiche
  - Storico pagamenti
  - Export invoices PDF

**Deliverable**: Sistema billing completo (lancio commerciale)

---

**TOTALE MVP (Fase 1-4): 5 settimane**
**TOTALE con Billing (Fase 1-5): 7 settimane**

---

## ⚠️ SFIDE DA CONSIDERARE

### 1. **Complessità Permessi**

**Domande aperte**:
- Owner elimina gruppo → cosa succede ai documenti?
  - **Proposta**: Grace period 30gg + notifica membri + opzione trasferimento ownership

- Utente lascia gruppo → suoi documenti caricati?
  - **Proposta**: Documenti restano proprietà gruppo (cambio owner_user_id ad Admin o Owner)

- Member carica documento "sensibile" → admin può eliminarlo?
  - **Proposta**: Sì, owner/admin possono eliminare qualsiasi documento (policy gruppo)

### 2. **Storage Deduplication**

**Problema**: Stesso file PDF caricato in 2 gruppi diversi → occupa 2× storage?

**Soluzione Proposta**: Hash-based deduplication
```sql
CREATE TABLE files_storage (
    id UUID PRIMARY KEY,
    sha256_hash VARCHAR(64) UNIQUE,
    r2_key VARCHAR(255),
    file_size BIGINT,
    reference_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- documents ora punta a files_storage
ALTER TABLE documents ADD COLUMN file_storage_id UUID REFERENCES files_storage(id);
```

**Logica**:
1. Upload file → calcola SHA-256
2. Check se hash già esiste in `files_storage`
3. Se esiste: `reference_count++`, crea document record (no upload R2)
4. Se nuovo: upload R2, crea `files_storage`, `reference_count = 1`
5. Delete document: `reference_count--`, se = 0 → elimina da R2

**Risparmio storage**: 60-80% (stima conservativa)

### 3. **Query Quota Gruppo**

**Problema**: Come contare query? Per singolo user o somma gruppo?

**Proposta**:
```
Tier TEAM:
- 500 query/giorno GRUPPO (somma di tutti membri)
- Reset 00:00 UTC giornaliero
- Soft limit 80% → warning admin
- Hard limit 100% → block query (upgrade prompt)

Counter:
CREATE TABLE group_daily_usage (
    group_id UUID,
    date DATE,
    query_count INTEGER DEFAULT 0,
    PRIMARY KEY (group_id, date)
);

-- Increment on ogni query
UPDATE group_daily_usage
SET query_count = query_count + 1
WHERE group_id = ? AND date = CURRENT_DATE;
```

### 4. **Privacy & GDPR**

**Obblighi Legali**:
- User può richiedere export dati (GDPR Art. 20)
- User può richiedere cancellazione (GDPR Art. 17 "Right to be forgotten")

**Proposta**:
- Endpoint `/api/user/export-data` → ZIP con:
  - Tutti documenti caricati (PDF)
  - Tutte query fatte (JSON)
  - Membership gruppi (JSON)

- Endpoint `/api/user/delete-account`:
  - Anonimizza chat_sessions (user_id → NULL)
  - Remove da group_memberships
  - Se owner gruppo → trasferimento ownership ad admin o delete gruppo
  - Elimina documenti privati
  - Mantiene documenti gruppo (cambio ownership)

---

## 📊 METRICHE DI SUCCESSO (KPI)

### Adoption Metrics

**Target 6 mesi dopo lancio**:
```
- % utenti che creano/join gruppo:     >40%
- Avg membri per gruppo:                5-8
- Retention rate gruppi a 90gg:        >70%
- Gruppi attivi (>1 query/settimana):  >60%
```

### Engagement Metrics

```
- Query per gruppo/giorno:              >20
- Documenti condivisi per gruppo:       >5
- MAU (Monthly Active Users) gruppo:    >60% membri
- Avg session duration:                 >5 min
```

### Revenue Metrics (con billing)

```
- Conversion FREE → TEAM:               >15%
- Conversion TEAM → BUSINESS:           >5%
- MRR growth month-over-month:          >20%
- Churn rate mensile:                   <5%
- LTV (Lifetime Value) medio:           >$500
```

### Technical Metrics

```
- Storage deduplication savings:        >50%
- Avg query response time:              <2s
- API uptime:                           >99.5%
- Document processing success rate:     >95%
```

---

## 💰 ANALISI COSTI vs REVENUE

### Costi Mensili (stima 100 gruppi attivi)

```
Infrastructure:
- Railway (web + worker):                 $100
- Cloudflare R2 (50 GB storage):          $50
- PostgreSQL (Railway):                   incluso
- Redis (Railway):                        incluso

LLM API:
- OpenRouter Claude Haiku 4.5:           $200
  (100 gruppi × 500 query/mese × $0.004/query)

Total Hosting:                            $350/mese
```

### Revenue Mensili (100 gruppi)

**Scenario Conservativo**:
```
- 40 FREE:              $0
- 40 TEAM ($19):        $760
- 15 BUSINESS ($49):    $735
- 5 ENTERPRISE ($199):  $995

MRR Total:              $2,490
Costi:                  -$350
Profit:                 $2,140/mese (86% margin!)
```

**Scenario Ottimistico** (200 gruppi, conversioni migliori):
```
- 80 FREE:              $0
- 80 TEAM ($19):        $1,520
- 30 BUSINESS ($49):    $1,470
- 10 ENTERPRISE ($199): $1,990

MRR Total:              $4,980
Costi:                  -$600 (scaling)
Profit:                 $4,380/mese (88% margin!)
```

**Proiezione 12 mesi**:
- Anno 1: $25,000 - $50,000 revenue (stima conservativa)
- Anno 2: $100,000+ (con marketing e scaling)

---

## 🎯 PROSSIMI PASSI

### Domande per Francesca (e per te!)

Prima di iniziare l'implementazione, vorrei il tuo feedback su:

1. **Priorità tier**:
   - Lanciamo subito FREE per validare adoption?
   - O implementiamo billing da subito per iniziare revenue?

2. **Limite free tier**:
   - Quanti utenti per gruppo FREE? (suggerirei 3-5 per incentivare upgrade)

3. **Multi-gruppo**:
   - User FREE può essere membro di N gruppi altrui ma creare solo 1 gruppo?
   - O limite 1 gruppo totale (owner o member)?

4. **Document ownership**:
   - Se user lascia gruppo, suoi documenti caricati restano o vengono eliminati?
   - (Io suggerirei: restano proprietà gruppo)

5. **Onboarding prioritario**:
   - Iniziamo con "crea gruppo" o "join gruppo" (codice invito)?
   - O entrambi in parallelo?

6. **Analytics privacy**:
   - Admin gruppo può vedere query individuali membri ("Giulia ha chiesto: ...")
   - O solo aggregati ("Documento interrogato 15 volte questa settimana")?

7. **Target market iniziale**:
   - Quale use case vuoi targetizzare per primo?
   - Scuole? Studi professionali? Famiglie? Corporate?

8. **Naming gruppi**:
   - Ti piace "Gruppi" o preferisci altro? ("Team", "Workspace", "Organizzazioni")

9. **Funzionalità extra**:
   - Hai altre idee che non ho considerato?
   - Funzionalità che secondo te sono must-have?

10. **Timeline**:
    - Quando vorresti lanciare la versione gruppi?
    - Quanto tempo possiamo dedicare allo sviluppo?

---

## 🚀 CONCLUSIONE

### Perché Questa è una Grande Idea

1. **Product-Market Fit Naturale**:
   - Documentazione è quasi sempre collaborativa (team, scuole, famiglie)
   - Socrate risolve problema reale: accesso rapido a info sepolte in PDF

2. **Modello Freemium Solido**:
   - Free tier per adoption
   - Upgrade naturale quando team cresce
   - Value proposition chiaro (più membri = più valore)

3. **Difendibilità Competitiva**:
   - Network effects (più membri → più documenti → più valore)
   - Switching cost alto (knowledge base costruita nel tempo)
   - Dati proprietari (query patterns, usage analytics)

4. **Scalabilità Tecnica**:
   - Infrastruttura già pronta (Railway + R2 + Celery)
   - Deduplication storage (crescita costi sublineare)
   - LLM API economica (Claude Haiku 4.5)

5. **Revenue Scalabile**:
   - Margini altissimi (85%+)
   - ARR predictable (subscription)
   - Upsell naturale (FREE → TEAM → BUSINESS)

---

### La Mia Raccomandazione

**Approccio MVP Lean (5 settimane)**:

1. **Fase 1-2 (3 settimane)**: Schema DB + API + Upload/Query gruppo
2. **Fase 3 (1 settimana)**: Sistema inviti + onboarding
3. **Fase 4 (1 settimana)**: Analytics base + admin panel

**Lancio FREE tier** per validare:
- Product-market fit reale
- Quali use case funzionano meglio (scuole vs business vs famiglie)
- Feedback utenti su UX

**Poi Fase 5 (2 settimane)**: Billing + subscription (solo dopo feedback positivo)

**Totale: 7 settimane da MVP completo a prodotto commerciale** 🚀

---

## 📞 CONTATTI & FEEDBACK

**Ciao Francesca!**

Questa è la mia vision per Socrate AI v2.0 con gruppi collaborativi.

**Cosa ne pensi?**
- Ti piace l'idea generale?
- Quali use case ti entusiasmano di più?
- Hai suggerimenti per migliorare l'UX?
- Vedi altri casi d'uso che non ho considerato?
- Hai feedback sul pricing proposto?

**Hai altre idee?**
- Funzionalità che secondo te sono essenziali?
- Integrazioni utili (Notion, Slack, Teams, Google Drive)?
- Marketing strategy (come faresti conoscere Socrate)?
- Partnership strategiche (scuole, università, associazioni)?

**Mi piacerebbe discuterne insieme e raccogliere il tuo feedback prima di iniziare l'implementazione!**

Dimmi cosa ne pensi! 💬

---

**Documento creato**: 18 Ottobre 2025
**Autore**: Mauro (con supporto Claude Code)
**Status**: Vision & Planning
**Next Step**: Feedback & Validation → Inizio sviluppo MVP

🤖 Generated with [Claude Code](https://claude.com/claude-code)
