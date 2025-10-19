# STRATEGIA GRUPPI COLLABORATIVI - SOCRATE AI

**Data**: 18 Ottobre 2025
**Versione**: 1.0
**Status**: 📋 STRATEGIC PLANNING

---

## 🎯 VISION STRATEGICA

### Evoluzione del Prodotto

**Da**: Sistema individuale (1 utente = N documenti privati)
**A**: Sistema collaborativo (1 gruppo = N utenti → M documenti condivisi)

### Obiettivo Principale

Trasformare Socrate AI da **strumento personale** a **piattaforma collaborativa** per team, scuole, famiglie e organizzazioni che condividono knowledge base comuni.

---

## 💡 VANTAGGI STRATEGICI

### 1. Business Model Scalabile

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRICING TIERS PROPOSTI                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FREE (Individual)                                              │
│  ├─ 1 utente                                                    │
│  ├─ 50 MB storage                                               │
│  ├─ 10 query/giorno                                             │
│  └─ Nessun gruppo                                               │
│                                                                 │
│  TEAM ($19/mese o $15/anno) ⭐                                  │
│  ├─ 5 utenti gruppo                                             │
│  ├─ 500 MB storage condiviso                                    │
│  ├─ 500 query/giorno gruppo                                     │
│  ├─ 1 gruppo                                                    │
│  └─ Basic analytics                                             │
│                                                                 │
│  BUSINESS ($49/mese o $39/anno)                                 │
│  ├─ 20 utenti gruppo                                            │
│  ├─ 2 GB storage condiviso                                      │
│  ├─ Query illimitate                                            │
│  ├─ 3 gruppi                                                    │
│  ├─ Advanced analytics                                          │
│  └─ Priority support                                            │
│                                                                 │
│  ENTERPRISE (Custom pricing)                                    │
│  ├─ Utenti illimitati                                           │
│  ├─ Storage personalizzato                                      │
│  ├─ Multi-gruppi illimitati                                     │
│  ├─ SSO/SAML integration                                        │
│  ├─ API dedicata                                                │
│  ├─ SLA 99.9%                                                   │
│  └─ Account manager dedicato                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Ottimizzazione Storage (Risparmio ~70%)

**Scenario Attuale (Individuale)**:
```
User A: manuale_prodotto.pdf (10 MB)
User B: manuale_prodotto.pdf (10 MB) [DUPLICATO]
User C: manuale_prodotto.pdf (10 MB) [DUPLICATO]
User D: manuale_prodotto.pdf (10 MB) [DUPLICATO]
──────────────────────────────────────────
TOTALE: 40 MB occupati
```

**Con Gruppi Collaborativi**:
```
Gruppo "Team Vendite":
└─ manuale_prodotto.pdf (10 MB) [SHARED]
   ├─ User A (accesso)
   ├─ User B (accesso)
   ├─ User C (accesso)
   └─ User D (accesso)
──────────────────────────────────────────
TOTALE: 10 MB occupati (-75% storage!)
```

### 3. Use Cases Perfetti

#### 🏫 **Scuola/Università**
```
Gruppo: "Classe 3A - Liceo Scientifico"
├─ Prof. Rossi (owner)
│  └─ Carica: dispense, esercizi, approfondimenti
├─ 25 studenti (members)
│  └─ Interrogano: "Spiegami il teorema di Pitagora"
│               "Quiz sul Rinascimento"
│               "Riassunto capitolo 5"
└─ Analytics: quali argomenti più interrogati
```

**Vantaggio**: Prof carica 1 volta → 25 studenti accedono
**Monetizzazione**: Scuola paga 1 piano BUSINESS → 100+ studenti

#### 🏢 **Studio Legale/Consulenza**
```
Gruppo: "Studio Associato Bianchi"
├─ Partner (admin)
│  └─ Carica: contratti tipo, normative, sentenze
├─ 8 avvocati (members)
│  └─ Interrogano knowledge base giuridica
├─ 3 praticanti (viewers)
│  └─ Solo lettura/query, no upload
└─ Audit: chi ha consultato quale documento
```

**Vantaggio**: Knowledge base centralizzata, sempre aggiornata
**Monetizzazione**: Piano BUSINESS $49/mese per studio

#### 🏥 **Famiglia**
```
Gruppo: "Famiglia Verdi"
├─ Papà (owner)
│  └─ Carica: manuali elettrodomestici, documenti medici
├─ Mamma (admin)
│  └─ Carica: ricette, guide scuola figli
├─ Figli (members)
│  └─ Interrogano: "Come funziona lavastoviglie?"
│                 "Ricetta torta di mele nonna"
└─ Storage: 200 MB documenti utili
```

**Vantaggio**: Documentazione familiare centralizzata
**Monetizzazione**: Piano TEAM $19/mese = €0.32/giorno per famiglia

#### 🔬 **Team Ricerca**
```
Gruppo: "Laboratorio Fisica Quantistica - UniMI"
├─ Prof. Associato (owner)
│  └─ Carica: paper, dataset, bibliografia
├─ 4 dottorandi (members)
│  └─ Upload: propri paper, appunti
├─ 10 studenti master (viewers)
│  └─ Query: bibliografia per tesi
└─ Deduplication: stesso paper caricato 1 volta
```

**Vantaggio**: Collaborazione scientifica, no duplicati
**Monetizzazione**: Università paga piano ENTERPRISE

---

## 🏗️ ARCHITETTURA DATABASE

### Schema Completo Proposto

```sql
-- ============================================================================
-- USERS (Modificato - aggiunti campi per gruppi)
-- ============================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT UNIQUE NOT NULL,
    email VARCHAR(255),
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    photo_url TEXT,

    -- Subscription personale (per documenti privati)
    subscription_tier VARCHAR(50) DEFAULT 'free',  -- free, pro, premium
    personal_storage_quota_mb FLOAT DEFAULT 50.0,
    personal_storage_used_mb FLOAT DEFAULT 0.0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,

    -- Settings
    user_settings JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_email ON users(email);


-- ============================================================================
-- GROUPS (NUOVO!)
-- ============================================================================

CREATE TABLE groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,  -- URL-friendly: "studio-rossi-partners"
    description TEXT,

    -- Type & Category
    type VARCHAR(50) NOT NULL,  -- school, business, family, research, other
    category VARCHAR(100),      -- Sottocategoria: "legal", "engineering", etc.

    -- Ownership
    owner_user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Subscription & Quotas
    subscription_tier VARCHAR(50) DEFAULT 'free',  -- free, team, business, enterprise
    storage_quota_mb FLOAT DEFAULT 100.0,
    storage_used_mb FLOAT DEFAULT 0.0,
    query_quota_daily INTEGER DEFAULT 50,
    query_count_today INTEGER DEFAULT 0,

    -- Limits
    max_members INTEGER DEFAULT 5,  -- Basato su tier
    current_members INTEGER DEFAULT 1,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_activity_at TIMESTAMP,

    -- Settings & Policies
    settings JSONB DEFAULT '{
        "allow_member_upload": true,
        "require_upload_approval": false,
        "allow_member_invite": false,
        "auto_approve_invites": true,
        "query_visibility": "private"
    }'::jsonb,

    -- Billing
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    billing_email VARCHAR(255),
    next_billing_date DATE,

    -- Status
    status VARCHAR(50) DEFAULT 'active',  -- active, suspended, cancelled

    CONSTRAINT chk_storage_positive CHECK (storage_used_mb >= 0),
    CONSTRAINT chk_members_limit CHECK (current_members <= max_members)
);

CREATE INDEX idx_groups_owner ON groups(owner_user_id);
CREATE INDEX idx_groups_slug ON groups(slug);
CREATE INDEX idx_groups_type ON groups(type);
CREATE INDEX idx_groups_status ON groups(status);


-- ============================================================================
-- GROUP_MEMBERSHIPS (NUOVO!)
-- ============================================================================

CREATE TABLE group_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relations
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Role & Permissions
    role VARCHAR(50) NOT NULL,  -- owner, admin, member, viewer
    permissions JSONB DEFAULT '{
        "can_upload": true,
        "can_delete_own": true,
        "can_delete_any": false,
        "can_invite": false,
        "can_manage_members": false,
        "can_view_analytics": false
    }'::jsonb,

    -- Invitation tracking
    invited_by UUID REFERENCES users(id) ON DELETE SET NULL,
    invitation_code VARCHAR(100) UNIQUE,  -- Codice invito univoco
    invited_at TIMESTAMP,
    joined_at TIMESTAMP DEFAULT NOW(),

    -- Activity
    last_activity_at TIMESTAMP,
    query_count INTEGER DEFAULT 0,
    upload_count INTEGER DEFAULT 0,

    -- Status
    status VARCHAR(50) DEFAULT 'active',  -- active, invited, suspended, left

    UNIQUE(group_id, user_id)
);

CREATE INDEX idx_memberships_group ON group_memberships(group_id);
CREATE INDEX idx_memberships_user ON group_memberships(user_id);
CREATE INDEX idx_memberships_invitation ON group_memberships(invitation_code);
CREATE INDEX idx_memberships_status ON group_memberships(status);


-- ============================================================================
-- DOCUMENTS (Modificato - aggiunto supporto gruppi)
-- ============================================================================

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Ownership
    owner_user_id UUID REFERENCES users(id) ON DELETE CASCADE,  -- Chi ha caricato
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE,      -- NULL = privato

    -- Visibility
    visibility VARCHAR(50) DEFAULT 'private',  -- private, group, public

    -- File info
    filename VARCHAR(500) NOT NULL,
    original_filename VARCHAR(500),
    mime_type VARCHAR(100),
    file_size BIGINT,
    file_path TEXT,  -- R2 key

    -- Processing
    status VARCHAR(50) DEFAULT 'processing',
    processing_progress INTEGER DEFAULT 0,
    error_message TEXT,

    -- Content metadata
    language VARCHAR(10),
    total_chunks INTEGER,
    total_tokens INTEGER,
    duration_seconds INTEGER,
    page_count INTEGER,

    -- Document metadata (includes embeddings)
    doc_metadata JSONB,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processing_completed_at TIMESTAMP,

    -- Sharing (multi-group support)
    shared_with_groups UUID[],  -- Array di group_id per condivisione multipla

    CONSTRAINT chk_visibility CHECK (
        (visibility = 'private' AND group_id IS NULL) OR
        (visibility = 'group' AND group_id IS NOT NULL) OR
        (visibility = 'public')
    )
);

CREATE INDEX idx_documents_owner ON documents(owner_user_id);
CREATE INDEX idx_documents_group ON documents(group_id);
CREATE INDEX idx_documents_visibility ON documents(visibility);
CREATE INDEX idx_documents_status ON documents(status);


-- ============================================================================
-- CHAT_SESSIONS (Modificato - aggiunto tracking gruppo)
-- ============================================================================

CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Context
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    group_id UUID REFERENCES groups(id) ON DELETE SET NULL,  -- NUOVO!

    -- Query
    command_type VARCHAR(50),
    request_data JSONB,
    response_data JSONB,

    -- Success tracking
    success BOOLEAN DEFAULT FALSE,
    error_message TEXT,

    -- Token usage
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd NUMERIC(10, 6),
    model_used VARCHAR(100),

    -- Source
    channel VARCHAR(50),  -- web_app, telegram, api

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,

    -- Privacy
    anonymized BOOLEAN DEFAULT FALSE  -- GDPR: user lascia gruppo → anonimizza
);

CREATE INDEX idx_chat_user ON chat_sessions(user_id);
CREATE INDEX idx_chat_document ON chat_sessions(document_id);
CREATE INDEX idx_chat_group ON chat_sessions(group_id);  -- NUOVO!
CREATE INDEX idx_chat_created ON chat_sessions(created_at);


-- ============================================================================
-- FILE_STORAGE (NUOVO! - Deduplication)
-- ============================================================================

CREATE TABLE file_storage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- File identity
    sha256_hash VARCHAR(64) UNIQUE NOT NULL,  -- Hash univoco file

    -- R2 storage
    r2_key TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100),

    -- Metadata
    original_filename VARCHAR(500),

    -- Reference counting
    reference_count INTEGER DEFAULT 1,  -- Quanti documenti puntano a questo file

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    last_accessed_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT chk_reference_positive CHECK (reference_count >= 0)
);

CREATE INDEX idx_file_storage_hash ON file_storage(sha256_hash);
CREATE INDEX idx_file_storage_r2_key ON file_storage(r2_key);


-- ============================================================================
-- GROUP_INVITATIONS (NUOVO! - Tracking inviti)
-- ============================================================================

CREATE TABLE group_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relations
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
    invited_by UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Invitation
    code VARCHAR(100) UNIQUE NOT NULL,  -- Codice invito: STUDIO-ROSSI-A3F9
    email VARCHAR(255),                 -- Opzionale: invito via email
    telegram_id BIGINT,                 -- Opzionale: invito diretto Telegram

    -- Permissions
    role VARCHAR(50) DEFAULT 'member',

    -- Validity
    expires_at TIMESTAMP,
    max_uses INTEGER DEFAULT 1,
    used_count INTEGER DEFAULT 0,

    -- Status
    status VARCHAR(50) DEFAULT 'pending',  -- pending, used, expired, revoked

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    used_at TIMESTAMP,

    CONSTRAINT chk_uses_limit CHECK (used_count <= max_uses)
);

CREATE INDEX idx_invitations_code ON group_invitations(code);
CREATE INDEX idx_invitations_group ON group_invitations(group_id);
CREATE INDEX idx_invitations_status ON group_invitations(status);


-- ============================================================================
-- GROUP_ACTIVITY_LOG (NUOVO! - Audit trail)
-- ============================================================================

CREATE TABLE group_activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Context
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Action
    action_type VARCHAR(100) NOT NULL,  -- document_uploaded, member_joined, etc.
    entity_type VARCHAR(50),            -- document, member, group, etc.
    entity_id UUID,

    -- Details
    action_data JSONB,  -- Dati specifici azione

    -- Metadata
    ip_address INET,
    user_agent TEXT,

    -- Timestamp
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_activity_group ON group_activity_log(group_id);
CREATE INDEX idx_activity_user ON group_activity_log(user_id);
CREATE INDEX idx_activity_created ON group_activity_log(created_at);
CREATE INDEX idx_activity_type ON group_activity_log(action_type);
```

---

## 🔐 LOGICA PERMESSI

### Matrice Ruoli

| Operazione | Owner | Admin | Member | Viewer |
|-----------|-------|-------|--------|--------|
| **Documenti** |
| Upload documento | ✅ | ✅ | ✅ | ❌ |
| Delete proprio doc | ✅ | ✅ | ✅ | ❌ |
| Delete doc altrui | ✅ | ✅ | ❌ | ❌ |
| Query documento | ✅ | ✅ | ✅ | ✅ |
| **Membri** |
| Invita membro | ✅ | ✅ | ❌ | ❌ |
| Rimuovi membro | ✅ | ✅ | ❌ | ❌ |
| Cambia ruolo | ✅ | ❌ | ❌ | ❌ |
| **Gruppo** |
| Modifica settings | ✅ | ✅ | ❌ | ❌ |
| View analytics | ✅ | ✅ | ❌ | ❌ |
| Delete gruppo | ✅ | ❌ | ❌ | ❌ |
| Gestione billing | ✅ | ❌ | ❌ | ❌ |

### Regole Business

**Un utente può**:
1. Appartenere a **N gruppi** contemporaneamente
2. Avere **documenti privati** + **documenti di gruppo**
3. Creare **1 gruppo free** come owner
4. Essere **invitato in M gruppi** senza limiti

**Un gruppo può**:
1. Avere **storage condiviso** (quota basata su tier)
2. Avere **1 solo owner** (chi paga/gestisce billing)
3. Avere **M admin** (delegati gestione)
4. Impostare **policy upload** (tutti possono / solo admin)

**Un documento può**:
1. Essere **privato** (`visibility=private`, `group_id=NULL`)
2. Essere **di gruppo** (`visibility=group`, `group_id` set)
3. Essere **multi-share** (`shared_with_groups` array per condivisione in N gruppi)
4. Avere **deduplication** (stesso file = 1 storage, N puntatori)

---

## 💰 STRATEGIA MONETIZZAZIONE

### Modello di Pricing Flessibile a Consumo

**FILOSOFIA**: Quota gruppo condivisa + Flessibilità di utilizzo + Opzioni addon/prepagato

#### Caratteristiche Chiave:
1. **Quota Mensile Condivisa**: Tutti i membri attingono dallo stesso pool di query
2. **Flessibilità Temporale**: Uso variabile nel tempo (2 settimane no uso, poi picco)
3. **Addon Query Packs**: Acquisto query extra con validità lunga (3-12 mesi)
4. **Piani Pure Consumption**: Nessun abbonamento, solo acquisto crediti

---

### Pricing Dettagliato

```
┌─────────────────────────────────────────────────────────────────┐
│                    FREE (Individual)                            │
├─────────────────────────────────────────────────────────────────┤
│  Prezzo:             €0/mese                                    │
│  Utenti:             1 individuale                              │
│  Storage:            50 MB                                      │
│  Query:              15 query/mese (pool condiviso)             │
│  Documenti:          Max 5                                      │
│  Gruppi:             Nessuno (può essere invitato in altri)     │
│  Support:            Community forum                            │
│  Addon packs:        Disponibili                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    TEAM (Small Groups) ⭐                       │
├─────────────────────────────────────────────────────────────────┤
│  Prezzo:             €19/mese (€190/anno, save 17%)            │
│  Utenti:             Fino a 5 membri                            │
│  Storage:            500 MB condiviso                           │
│  Query:              500 query/mese (pool gruppo condiviso)     │
│  Documenti:          Max 50                                     │
│  Gruppi:             1 gruppo                                   │
│  Analytics:          Basic (storage, query count per membro)    │
│  Support:            Email (48h response)                       │
│  Inviti:             Illimitati via codice                      │
│  Addon packs:        ✅ Disponibili (100-2000 query extra)      │
│  Costo per query:    €0.038/query inclusa (margine 92%)        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    BUSINESS (Teams)                             │
├─────────────────────────────────────────────────────────────────┤
│  Prezzo:             €49/mese (€490/anno, save 17%)            │
│  Utenti:             Fino a 20 membri                           │
│  Storage:            2 GB condiviso                             │
│  Query:              2,000 query/mese (pool gruppo condiviso)   │
│  Documenti:          Illimitati                                 │
│  Gruppi:             3 gruppi                                   │
│  Analytics:          Advanced (audit log, usage trends/membro)  │
│  Support:            Priority email + chat (12h response)       │
│  Inviti:             Illimitati via email/codice                │
│  Addon packs:        ✅ Disponibili con sconto volume          │
│  Costo per query:    €0.0245/query inclusa (margine 88%)       │
│  Features:           ├─ Roles granulari (owner/admin/member)   │
│                      ├─ Document approval workflow              │
│                      ├─ Export data                             │
│                      └─ Custom branding                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    ENTERPRISE (Organizations)                   │
├─────────────────────────────────────────────────────────────────┤
│  Prezzo:             €199/mese (€1,990/anno, save 17%)         │
│  Utenti:             Illimitati                                 │
│  Storage:            10 GB (scalabile con addon)                │
│  Query:              10,000 query/mese (pool condiviso)         │
│  Documenti:          Illimitati                                 │
│  Gruppi:             Illimitati                                 │
│  Analytics:          Enterprise (dashboard custom, API)         │
│  Support:            ├─ Dedicated account manager               │
│                      ├─ Phone support                           │
│                      ├─ SLA 99.9% uptime                        │
│                      └─ 24/7 priority support                   │
│  Addon packs:        ✅ Prezzi custom negoziabili              │
│  Costo per query:    €0.0199/query inclusa (margine 85%)       │
│  Features:           ├─ SSO/SAML integration                    │
│                      ├─ API dedicata con rate limit custom      │
│                      ├─ On-premise deployment option            │
│                      ├─ Custom model training                   │
│                      ├─ White-label solution                    │
│                      └─ Legal compliance (HIPAA, SOC2)          │
└─────────────────────────────────────────────────────────────────┘
```

---

### Addon Query Packs (Acquisto Una Tantum)

**Disponibili per tutti i piani (FREE, TEAM, BUSINESS, ENTERPRISE)**

```
┌─────────────────────────────────────────────────────────────────┐
│  PACK PICCOLO - 100 Query                                       │
│  ├─ Prezzo: €9                                                  │
│  ├─ Costo/query: €0.09                                          │
│  ├─ Validità: 90 giorni                                         │
│  ├─ Margine: 96%                                                │
│  └─ Ideale per: Occasionali picchi di utilizzo                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PACK MEDIO - 500 Query ⭐                                      │
│  ├─ Prezzo: €39                                                 │
│  ├─ Costo/query: €0.078                                         │
│  ├─ Validità: 90 giorni                                         │
│  ├─ Margine: 96%                                                │
│  └─ Ideale per: Team in crescita, progetti stagionali          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PACK GRANDE - 1,000 Query                                      │
│  ├─ Prezzo: €69                                                 │
│  ├─ Costo/query: €0.069                                         │
│  ├─ Validità: 90 giorni                                         │
│  ├─ Margine: 95%                                                │
│  └─ Ideale per: Gruppi con utilizzo variabile mensile          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PACK XL - 2,000 Query                                          │
│  ├─ Prezzo: €119                                                │
│  ├─ Costo/query: €0.059                                         │
│  ├─ Validità: 90 giorni                                         │
│  ├─ Margine: 95%                                                │
│  └─ Ideale per: Business con campagne intensive                 │
└─────────────────────────────────────────────────────────────────┘
```

**Note Addon Packs**:
- Le query addon si sommano alla quota mensile inclusa
- Validità 90 giorni per evitare spreco
- Si utilizzano DOPO aver esaurito quota mensile
- Possibile acquistare multipli pack contemporaneamente

---

### Piani Pure Consumption (No Abbonamento)

**Per chi vuole massima flessibilità senza impegno mensile**

```
┌─────────────────────────────────────────────────────────────────┐
│  STARTER PREPAGATO - 500 Query                                  │
│  ├─ Prezzo: €29 (una tantum)                                    │
│  ├─ Costo/query: €0.058                                         │
│  ├─ Validità: 3 mesi                                            │
│  ├─ Storage: 200 MB                                             │
│  ├─ Membri: Fino a 3                                            │
│  ├─ Margine: 95%                                                │
│  └─ Ideale per: Uso sporadico, progetti a termine              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  STANDARD PREPAGATO - 1,000 Query ⭐                            │
│  ├─ Prezzo: €49 (una tantum)                                    │
│  ├─ Costo/query: €0.049                                         │
│  ├─ Validità: 6 mesi                                            │
│  ├─ Storage: 500 MB                                             │
│  ├─ Membri: Fino a 5                                            │
│  ├─ Margine: 94%                                                │
│  └─ Ideale per: Team part-time, consulenti freelance           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PRO PREPAGATO - 2,500 Query                                    │
│  ├─ Prezzo: €99 (una tantum)                                    │
│  ├─ Costo/query: €0.039                                         │
│  ├─ Validità: 12 mesi                                           │
│  ├─ Storage: 1 GB                                               │
│  ├─ Membri: Fino a 10                                           │
│  ├─ Margine: 92%                                                │
│  └─ Ideale per: Business stagionale, uso non continuo          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  ENTERPRISE PREPAGATO - 10,000 Query                            │
│  ├─ Prezzo: €299 (una tantum)                                   │
│  ├─ Costo/query: €0.029                                         │
│  ├─ Validità: 12 mesi                                           │
│  ├─ Storage: 5 GB                                               │
│  ├─ Membri: Fino a 50                                           │
│  ├─ Margine: 90%                                                │
│  └─ Ideale per: Grandi progetti con deadline definita          │
└─────────────────────────────────────────────────────────────────┘
```

**Vantaggi Piani Prepagati**:
- Nessun addebito ricorrente
- Validità lunga (fino a 12 mesi)
- Prezzo per query più basso (sconto volume)
- Perfetto per uso non continuativo
- Riattivabile acquistando nuovo pack quando esaurito

---

### Costi LLM e Margini

**Modello utilizzato**: Claude Haiku 4.5 via OpenRouter
- Input: $0.80/1M token (~€0.75)
- Output: $4.00/1M token (~€3.75)

**Calcolo costo medio per query**:
- Media: 1,000 token input + 500 token output
- Costo: (1000 × 0.0000008) + (500 × 0.000004) = **€0.003/query**

**Margini per piano**:

| Piano | Costo/Query Inclusa | Costo LLM | Margine |
|-------|---------------------|-----------|---------|
| FREE | €0 (15 query) | €0.045 | -100% (loss leader) |
| TEAM | €0.038 | €0.003 | **92%** |
| BUSINESS | €0.0245 | €0.003 | **88%** |
| ENTERPRISE | €0.0199 | €0.003 | **85%** |
| Addon Packs | €0.059-0.09 | €0.003 | **94-96%** |
| Prepagati | €0.029-0.058 | €0.003 | **90-95%** |

**Risultato**: Margini eccellenti su tutti i piani paganti (85-96%)!

### Revenue Model Proiezioni

**Scenario Conservativo (100 clienti, 12 mesi)**:

```
Customer Mix:
├─ 60 FREE:       60 × €0       = €0/mese
├─ 30 TEAM:       30 × €19      = €570/mese
├─ 8 BUSINESS:    8 × €49       = €392/mese
└─ 2 ENTERPRISE:  2 × €299      = €598/mese
───────────────────────────────────────────
TOTALE MRR:                       €1,560/mese
TOTALE ARR:                       €18,720/anno
```

**Costi Operativi Stimati**:
```
Railway hosting:         ~€100/mese
Cloudflare R2:           ~€50/mese
LLM API (OpenRouter):    ~€200/mese
Stripe fees (3%):        ~€47/mese
───────────────────────────────────────────
TOTALE COSTI:            €397/mese
MARGINE LORDO:           €1,163/mese (74.6%)
```

**Scenario Ottimistico (500 clienti, 12 mesi)**:

```
Customer Mix:
├─ 300 FREE:      300 × €0      = €0/mese
├─ 150 TEAM:      150 × €19     = €2,850/mese
├─ 40 BUSINESS:   40 × €49      = €1,960/mese
└─ 10 ENTERPRISE: 10 × €299     = €2,990/mese
───────────────────────────────────────────
TOTALE MRR:                       €7,800/mese
TOTALE ARR:                       €93,600/anno

Costi:                            ~€1,500/mese
MARGINE LORDO:                    €6,300/mese (80.8%)
```

### Strategia Go-To-Market

**Fase 1: Beta Testing (Month 1-2)**
- 50 utenti early adopters FREE
- Raccolta feedback UX
- Validazione use cases (scuola, business, famiglia)

**Fase 2: Freemium Launch (Month 3-6)**
- Lancio tier FREE + TEAM
- Growth hacking: referral program (invita 3 amici → +100MB storage)
- Content marketing: blog post su use cases

**Fase 3: B2B Expansion (Month 7-12)**
- Lancio tier BUSINESS + ENTERPRISE
- Outreach diretto: scuole, studi professionali
- Partnership: integrazioni Notion, Slack, Google Workspace

---

## 🚀 ROADMAP IMPLEMENTAZIONE

### Fase 1: Foundation (Settimane 1-2)

**Database & Backend**:
- [ ] Migrazione schema database (tabelle `groups`, `group_memberships`)
- [ ] API CRUD gruppi:
  - `POST /api/groups` - Crea gruppo
  - `GET /api/groups/{id}` - Dettagli gruppo
  - `PUT /api/groups/{id}` - Modifica settings
  - `DELETE /api/groups/{id}` - Elimina gruppo (con grace period)
- [ ] API membership:
  - `POST /api/groups/{id}/members` - Invita membro
  - `DELETE /api/groups/{id}/members/{user_id}` - Rimuovi membro
  - `PUT /api/groups/{id}/members/{user_id}/role` - Cambia ruolo

**Logica Permessi**:
- [ ] Decorator `@require_group_permission(action)`
- [ ] Middleware validazione quota gruppo
- [ ] Helper `user_can(user_id, action, group_id)`

**Testing**:
- [ ] Unit tests API gruppi
- [ ] Integration tests permissions
- [ ] Load test: 100 gruppi, 1000 utenti

**Deliverable**: Backend completo per gestione gruppi

---

### Fase 2: Document Sharing (Settimana 3)

**Upload Documenti Gruppo**:
- [ ] Modifica `POST /api/documents/upload`:
  - Parametro `group_id` opzionale
  - Validazione quota storage gruppo
  - Aggiornamento `storage_used_mb` gruppo
- [ ] Modifica `delete_document()`:
  - Decremento quota gruppo
  - Verifica permessi (owner o admin)

**Query Documenti Gruppo**:
- [ ] Modifica `POST /api/query`:
  - Filtro documenti per `group_id`
  - Tracking query in `chat_sessions.group_id`
  - Validazione quota query gruppo

**Storage Quota Management**:
- [ ] Endpoint `GET /api/groups/{id}/storage` - Usage stats
- [ ] Soft limit warning (90% quota)
- [ ] Hard limit enforcement (100% quota)

**Testing**:
- [ ] Test upload/query gruppo
- [ ] Test quota enforcement
- [ ] Test permission denied scenarios

**Deliverable**: Documenti condivisi funzionanti

---

### Fase 3: Inviti & Onboarding (Settimana 4)

**Sistema Inviti**:
- [ ] Generazione codici invito univoci
  - Format: `{GROUP_SLUG}-{RANDOM_6CHARS}`
  - Es: `studio-rossi-A3F9K2`
- [ ] API inviti:
  - `POST /api/groups/{id}/invitations` - Crea invito
  - `POST /api/invitations/{code}/accept` - Accetta invito
  - `GET /api/invitations/{code}` - Info invito

**Onboarding Flow**:
- [ ] UI: Welcome screen "Individuale vs Gruppo"
- [ ] UI: "Crea nuovo gruppo" form
- [ ] UI: "Entra con codice invito" form
- [ ] Email: Template invito (opzionale)

**Telegram Integration** (Bonus):
- [ ] Comando `/creategroup <nome>`
- [ ] Comando `/invite` - Genera codice
- [ ] Comando `/join <codice>` - Join gruppo

**Testing**:
- [ ] Test flusso completo onboarding
- [ ] Test codici invito (validità, scadenza)
- [ ] Test edge cases (invito scaduto, gruppo pieno)

**Deliverable**: Onboarding gruppo completo

---

### Fase 4: Dashboard UI (Settimana 5)

**Dashboard Gruppi**:
- [ ] UI: Sezione "I miei gruppi"
  - Card per ogni gruppo
  - Badge ruolo (owner/admin/member)
  - Storage bar progress
- [ ] UI: Dettaglio gruppo
  - Lista membri con ruoli
  - Lista documenti gruppo
  - Storage & query usage

**Upload Flow**:
- [ ] UI: Selettore "Carica in:"
  - Radio button: [Privato] [Gruppo X] [Gruppo Y]
  - Mostra quota disponibile gruppo
- [ ] UI: Drag & drop con destinazione gruppo

**Member Management**:
- [ ] UI: Lista membri con azioni (owner/admin only)
  - Cambia ruolo
  - Rimuovi membro
  - Resend invito
- [ ] UI: "Invita membri" button
  - Genera codice → Copy to clipboard
  - Share via: [Email] [Telegram] [WhatsApp]

**Testing**:
- [ ] Test UI responsiveness (mobile/desktop)
- [ ] Test accessibilità (WCAG 2.1)
- [ ] User testing: 10 beta testers

**Deliverable**: UI completa per gruppi

---

### Fase 5: Analytics & Admin (Settimana 6)

**Admin Dashboard**:
- [ ] UI: Analytics gruppo (owner/admin only)
  - Storage breakdown (per tipo file)
  - Query trends (grafico ultimi 30gg)
  - Top 5 documenti più interrogati
  - Active members (MAU)

**Audit Log**:
- [ ] UI: Timeline attività gruppo
  - "Mario ha caricato documento.pdf"
  - "Lucia ha interrogato contratto.pdf"
  - "Admin ha invitato nuovo membro"
- [ ] Filtri: per membro, per azione, per data

**Export Data** (GDPR compliance):
- [ ] Endpoint `GET /api/groups/{id}/export`
  - ZIP con: documenti, metadata, chat history
  - Anonimizzazione opzionale
- [ ] UI: Button "Esporta dati gruppo"

**Settings Gruppo**:
- [ ] UI: Settings page
  - Nome & descrizione gruppo
  - Policy upload (tutti/solo admin)
  - Query visibility (privata/pubblica al gruppo)
  - Approval workflow (opzionale)

**Testing**:
- [ ] Test export dati (completezza)
- [ ] Test analytics accuracy
- [ ] Load test: 1000 eventi audit log

**Deliverable**: Admin features complete

---

### Fase 6: Billing & Subscriptions (Settimane 7-8)

**Stripe Integration**:
- [ ] Setup Stripe account + products
- [ ] Webhook handler `/api/webhooks/stripe`
  - `invoice.paid` → Attiva subscription
  - `invoice.payment_failed` → Sospendi gruppo
  - `customer.subscription.deleted` → Cancella subscription
- [ ] Endpoint billing:
  - `POST /api/groups/{id}/checkout` - Create Stripe session
  - `POST /api/groups/{id}/billing-portal` - Manage subscription

**Subscription Management**:
- [ ] UI: "Upgrade piano" flow
  - Comparazione tiers
  - Stripe Checkout redirect
  - Success/cancel pages
- [ ] UI: "Gestisci abbonamento"
  - Link Stripe billing portal
  - Mostra prossimo rinnovo
  - Cancellazione con conferma

**Quota Enforcement**:
- [ ] Soft limit warnings (email/notifica):
  - Storage 80% → "Considera upgrade"
  - Query 80% quota → "Limite giornaliero quasi raggiunto"
- [ ] Hard limit block:
  - Storage 100% → No upload
  - Query 100% → No query (reset giornaliero)

**Upgrade/Downgrade**:
- [ ] Logica proration Stripe
- [ ] Adjustment quota immediato
- [ ] Email conferma cambio piano

**Testing**:
- [ ] Test Stripe webhooks (Stripe CLI)
- [ ] Test upgrade/downgrade flows
- [ ] Test quota enforcement accuracy

**Deliverable**: Monetizzazione attiva

---

### Fase 7: Advanced Features (Opzionale, Settimane 9-10)

**Deduplication Storage**:
- [ ] Implementa tabella `file_storage`
- [ ] SHA-256 hashing upload
- [ ] Reference counting
- [ ] Cleanup job (reference_count=0)

**Approval Workflow**:
- [ ] Stato documento: `pending_approval`
- [ ] Notifica admin: nuovo documento da approvare
- [ ] Endpoint: `POST /api/documents/{id}/approve`

**Advanced Analytics**:
- [ ] Query heatmap (orari picco)
- [ ] Document similarity (clustering)
- [ ] Member engagement score

**API Pubblica** (Enterprise):
- [ ] API keys per gruppi
- [ ] Rate limiting per tier
- [ ] Documentazione OpenAPI/Swagger

**Testing**:
- [ ] Test deduplication accuracy
- [ ] Test approval workflow
- [ ] API security testing

**Deliverable**: Features premium

---

## ⚠️ SFIDE & SOLUZIONI

### 1. Complessità Permessi

**Sfida**: Gestire permessi granulari tra ruoli e azioni.

**Soluzioni**:
```python
# Decorator pattern per permission checking
@require_group_permission('upload_document')
def upload_document(group_id: str, user_id: str):
    # Solo se user ha permesso 'can_upload' nel gruppo
    pass

# Helper function
def user_can(user_id: str, action: str, group_id: str) -> bool:
    membership = get_membership(user_id, group_id)
    if not membership:
        return False

    # Check role-based permissions
    if membership.role == 'owner':
        return True
    if membership.role == 'admin':
        return action not in ['delete_group', 'manage_billing']
    if membership.role == 'member':
        return action in ['upload_document', 'query_document']
    if membership.role == 'viewer':
        return action in ['query_document']

    return False
```

---

### 2. Storage Deduplication

**Sfida**: Stesso file caricato da utenti diversi in gruppi diversi.

**Soluzione**:
```python
def upload_document_with_dedup(file_data: bytes, filename: str, group_id: str):
    # 1. Calculate SHA-256 hash
    file_hash = hashlib.sha256(file_data).hexdigest()

    # 2. Check if file already exists in storage
    existing_file = db.query(FileStorage).filter_by(sha256_hash=file_hash).first()

    if existing_file:
        # File exists! Increment reference count
        existing_file.reference_count += 1
        file_storage_id = existing_file.id
        logger.info(f"Dedup: reusing existing file {file_hash[:8]}")
    else:
        # New file: upload to R2
        r2_key = generate_unique_r2_key(filename)
        upload_to_r2(r2_key, file_data)

        # Create FileStorage record
        new_file = FileStorage(
            sha256_hash=file_hash,
            r2_key=r2_key,
            file_size=len(file_data),
            reference_count=1
        )
        db.add(new_file)
        file_storage_id = new_file.id

    # 3. Create Document record pointing to FileStorage
    doc = Document(
        file_storage_id=file_storage_id,
        group_id=group_id,
        filename=filename,
        # ... other fields
    )
    db.add(doc)
    db.commit()
```

**Risparmio Stimato**:
- Gruppo con 10 membri che caricano stesso PDF (20 MB)
- Senza dedup: 10 × 20 MB = 200 MB
- Con dedup: 1 × 20 MB = 20 MB
- **Risparmio: 90%**

---

### 3. Query Quota Gruppo

**Sfida**: Come contare query per gruppo? Aggregate di tutti membri o separato?

**Soluzione Proposta**: **Quota condivisa gruppo**

```python
def check_query_quota(group_id: str) -> bool:
    group = db.query(Group).filter_by(id=group_id).first()

    # Reset contatore se nuovo giorno
    if group.last_quota_reset < datetime.now().date():
        group.query_count_today = 0
        group.last_quota_reset = datetime.now().date()
        db.commit()

    # Check quota
    if group.query_count_today >= group.query_quota_daily:
        return False  # Quota exceeded

    # Increment counter
    group.query_count_today += 1
    db.commit()
    return True

# Usage in query endpoint
@app.route('/api/query', methods=['POST'])
@require_auth
def query_endpoint():
    document = get_document(document_id)

    if document.group_id:
        # Check group quota
        if not check_query_quota(document.group_id):
            return jsonify({
                'error': 'Quota query giornaliera esaurita',
                'help': 'Upgrade piano o attendi reset domani'
            }), 429
    else:
        # Check personal quota
        if not check_user_quota(user_id):
            return jsonify({'error': 'Quota personale esaurita'}), 429

    # Execute query...
```

---

### 4. Privacy & GDPR

**Sfida**: User lascia gruppo → diritto oblio query personali?

**Soluzione**:

```python
def user_leaves_group(user_id: str, group_id: str):
    # 1. Remove membership
    membership = get_membership(user_id, group_id)
    db.delete(membership)

    # 2. Anonimizzare chat_sessions (GDPR right to be forgotten)
    sessions = db.query(ChatSession).filter_by(
        user_id=user_id,
        group_id=group_id
    ).all()

    for session in sessions:
        session.user_id = None  # Anonimizza
        session.anonymized = True

    # 3. Documenti caricati dall'utente: 2 opzioni
    #    Opzione A: Trasferire ownership all'owner gruppo
    #    Opzione B: Eliminare documenti (se policy gruppo lo richiede)

    user_docs = db.query(Document).filter_by(
        owner_user_id=user_id,
        group_id=group_id
    ).all()

    group = db.query(Group).filter_by(id=group_id).first()

    for doc in user_docs:
        if group.settings.get('keep_documents_on_leave', True):
            # Opzione A: Trasferisci ownership
            doc.owner_user_id = group.owner_user_id
        else:
            # Opzione B: Elimina documento
            delete_document(doc.id)

    db.commit()

    logger.info(f"User {user_id} left group {group_id} - GDPR compliance applied")
```

**Export Dati Utente** (GDPR Article 20):

```python
@app.route('/api/user/export-data', methods=['POST'])
@require_auth
def export_user_data():
    user_id = get_current_user_id()

    # 1. Collect user data
    user = get_user(user_id)
    memberships = get_user_memberships(user_id)
    documents = get_user_documents(user_id)
    sessions = get_user_chat_sessions(user_id)

    # 2. Create ZIP archive
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        # User profile
        zip_file.writestr('user_profile.json', json.dumps(user.to_dict()))

        # Memberships
        zip_file.writestr('groups.json', json.dumps([m.to_dict() for m in memberships]))

        # Documents metadata
        zip_file.writestr('documents.json', json.dumps([d.to_dict() for d in documents]))

        # Chat history
        zip_file.writestr('chat_history.json', json.dumps([s.to_dict() for s in sessions]))

    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'socrate_data_{user_id}.zip'
    )
```

---

### 5. Ownership Transfer

**Sfida**: Owner gruppo cancella account → gruppo orfano?

**Soluzione**: **Grace Period + Transfer**

```python
def delete_user_account(user_id: str):
    # 1. Check if user is owner of any group
    owned_groups = db.query(Group).filter_by(owner_user_id=user_id).all()

    if owned_groups:
        # User is owner! Cannot delete immediately

        # Option A: Transfer ownership to another admin
        for group in owned_groups:
            admins = db.query(GroupMembership).filter_by(
                group_id=group.id,
                role='admin'
            ).all()

            if admins:
                # Transfer to first admin
                new_owner = admins[0]
                group.owner_user_id = new_owner.user_id
                new_owner.role = 'owner'
                logger.info(f"Ownership transferred: {group.id} → {new_owner.user_id}")
            else:
                # No admin available: suspend group with 30-day grace period
                group.status = 'pending_deletion'
                group.deletion_scheduled_at = datetime.now() + timedelta(days=30)

                # Notify all members
                notify_group_members(
                    group.id,
                    "Owner ha eliminato account. Gruppo sarà cancellato tra 30gg. "
                    "Qualcuno diventi admin per assumere ownership."
                )

        db.commit()

        return {
            'success': False,
            'error': 'Devi trasferire ownership gruppi prima di eliminare account',
            'groups': [g.id for g in owned_groups]
        }

    # 2. User is not owner: safe to delete
    # Leave all groups first
    memberships = get_user_memberships(user_id)
    for membership in memberships:
        user_leaves_group(user_id, membership.group_id)

    # 3. Delete user
    db.delete(user)
    db.commit()

    return {'success': True}
```

---

## 🎨 UX FLOW COMPLETO

### Flow 1: Registrazione + Crea Gruppo

```
┌─────────────────────────────────────────────────────────────────┐
│  1. TELEGRAM LOGIN                                              │
│     User clicks "Login con Telegram" → Auth callback           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. WELCOME SCREEN                                              │
│     ┌───────────────────────────────────────────────────────┐   │
│     │  Benvenuto su Socrate AI! 👋                         │   │
│     │                                                       │   │
│     │  Come vuoi usare Socrate?                            │   │
│     │                                                       │   │
│     │  [🧑 Uso Individuale]  [👥 Uso in Gruppo]            │   │
│     └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                    │                          │
                    │                          │
          ┌─────────┴───────┐      ┌──────────┴──────────┐
          │                 │      │                     │
          ▼                 ▼      ▼                     ▼
     INDIVIDUALE        GRUPPO   GRUPPO               GRUPPO
     (skip setup)       (create) (join code)          (future: browse)
          │                 │
          ▼                 ▼
     Dashboard      ┌─────────────────────────────────────────────┐
                    │  3. CREA GRUPPO                             │
                    │     ┌─────────────────────────────────────┐ │
                    │     │ Nome gruppo: _____________________  │ │
                    │     │                                     │ │
                    │     │ Tipo gruppo:                        │ │
                    │     │ ○ 🏫 Scuola/Università              │ │
                    │     │ ○ 🏢 Lavoro/Business                │ │
                    │     │ ○ 🏡 Famiglia                       │ │
                    │     │ ○ 🔬 Ricerca                        │ │
                    │     │ ○ 📚 Altro                          │ │
                    │     │                                     │ │
                    │     │ Piano:                              │ │
                    │     │ ○ FREE (5 utenti, 100MB)           │ │
                    │     │ ○ TEAM €19/mese (20 utenti, 500MB) │ │
                    │     │                                     │ │
                    │     │         [Crea Gruppo]               │ │
                    │     └─────────────────────────────────────┘ │
                    └─────────────────────────────────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────────────┐
                    │  4. SETUP COMPLETATO!                       │
                    │     ✅ Gruppo "Studio Rossi" creato        │
                    │                                             │
                    │     Invita membri con questo codice:        │
                    │     ┌─────────────────────────────────────┐ │
                    │     │  STUDIO-ROSSI-A3F9K2                │ │
                    │     │  [📋 Copia] [📧 Email] [✉️ Telegram] │ │
                    │     └─────────────────────────────────────┘ │
                    │                                             │
                    │              [Vai alla Dashboard]           │
                    └─────────────────────────────────────────────┘
                                      │
                                      ▼
                                  Dashboard
```

---

### Flow 2: Join Gruppo con Codice

```
┌─────────────────────────────────────────────────────────────────┐
│  1. WELCOME SCREEN (dopo login)                                 │
│     [🧑 Uso Individuale]  [👥 Uso in Gruppo]                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. GRUPPO: HAI UN CODICE?                                      │
│     ┌───────────────────────────────────────────────────────┐   │
│     │  Hai ricevuto un codice invito?                       │   │
│     │                                                       │   │
│     │  [Sì, ho un codice]  [No, creo nuovo gruppo]        │   │
│     └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. INSERISCI CODICE                                            │
│     ┌───────────────────────────────────────────────────────┐   │
│     │  Codice invito: ___________________________          │   │
│     │                                                       │   │
│     │              [Verifica Codice]                        │   │
│     └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (valida codice)
┌─────────────────────────────────────────────────────────────────┐
│  4. CONFERMA JOIN                                               │
│     ┌───────────────────────────────────────────────────────┐   │
│     │  ✅ Codice valido!                                    │   │
│     │                                                       │   │
│     │  Gruppo: 🏢 Studio Rossi & Partners                  │   │
│     │  Membri: 12/20                                        │   │
│     │  Storage: 340 MB / 500 MB                             │   │
│     │                                                       │   │
│     │  Entrerai come: Member                               │   │
│     │  Potrai: ✅ Upload documenti  ✅ Query documenti      │   │
│     │                                                       │   │
│     │         [Unisciti al Gruppo]  [Annulla]              │   │
│     └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. BENVENUTO NEL GRUPPO!                                       │
│     🎉 Ora fai parte di "Studio Rossi & Partners"             │
│                                                                 │
│     Documenti disponibili: 24                                   │
│     Membri: 13                                                  │
│                                                                 │
│              [Vai alla Dashboard]                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                          Dashboard
```

---

### Flow 3: Upload Documento a Gruppo

```
Dashboard
   │
   ▼
┌─────────────────────────────────────────────────────────────────┐
│  [+ Carica Documento]                                           │
└─────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────┐
│  CARICA IN:                                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ ○ 📁 I miei documenti privati (45 MB / 50 MB)           │  │
│  │                                                          │  │
│  │ ● 👥 Gruppo: Studio Rossi (340 MB / 500 MB)            │  │
│  │                                                          │  │
│  │ ○ 👥 Gruppo: Famiglia Verdi (12 MB / 100 MB)           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  [Sfoglia File] o [Trascina qui]                                │
└─────────────────────────────────────────────────────────────────┘
   │
   ▼ (seleziona file: contratto_vendita.pdf - 2.3 MB)
┌─────────────────────────────────────────────────────────────────┐
│  CONFERMA UPLOAD                                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ File: contratto_vendita.pdf (2.3 MB)                     │  │
│  │ Destinazione: 👥 Studio Rossi & Partners                │  │
│  │                                                          │  │
│  │ Dopo upload:                                             │  │
│  │ Storage gruppo: 342.3 MB / 500 MB (68%)                 │  │
│  │                                                          │  │
│  │ Visibile a: 13 membri                                   │  │
│  │                                                          │  │
│  │         [Carica]  [Annulla]                             │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────┐
│  UPLOAD IN CORSO...                                             │
│  ████████████████░░░░░░░░░░ 65%                                 │
│  Elaborazione in background (tempo stimato: 2 min)             │
└─────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────┐
│  ✅ DOCUMENTO PRONTO!                                           │
│     contratto_vendita.pdf è ora disponibile nel gruppo         │
│                                                                 │
│     [Interroga Documento]  [Torna alla Dashboard]              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 METRICHE DI SUCCESSO

### KPI Chiave

**Adoption Metrics**:
```
┌─────────────────────────────────────────────────────────────────┐
│  % Utenti che creano/join gruppo (target: >40%)                │
│  ────────────────────────────────────────────────────────────── │
│  Baseline:    0% (pre-feature)                                 │
│  Month 1:     Target 20%                                        │
│  Month 3:     Target 40%                                        │
│  Month 6:     Target 60%                                        │
│                                                                 │
│  Come misurare:                                                 │
│  (users con group_membership) / (total users)                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Avg membri per gruppo (target: 5-8)                           │
│  ────────────────────────────────────────────────────────────── │
│  Indica se i gruppi sono attivamente popolati                  │
│                                                                 │
│  Come misurare:                                                 │
│  SUM(current_members) / COUNT(groups)                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Retention rate gruppi a 90gg (target: >70%)                   │
│  ────────────────────────────────────────────────────────────── │
│  % gruppi ancora attivi dopo 90gg dalla creazione              │
│                                                                 │
│  Come misurare:                                                 │
│  (groups active at day 90) / (groups created 90 days ago)      │
└─────────────────────────────────────────────────────────────────┘
```

**Engagement Metrics**:
```
┌─────────────────────────────────────────────────────────────────┐
│  Query per gruppo/giorno (target: >20)                         │
│  ────────────────────────────────────────────────────────────── │
│  Indica utilizzo attivo knowledge base                          │
│                                                                 │
│  Query:                                                         │
│  SELECT                                                         │
│    group_id,                                                    │
│    COUNT(*) / COUNT(DISTINCT DATE(created_at)) as avg_daily    │
│  FROM chat_sessions                                             │
│  WHERE group_id IS NOT NULL                                     │
│  GROUP BY group_id                                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Documenti condivisi per gruppo (target: >5)                   │
│  ────────────────────────────────────────────────────────────── │
│  Indica ricchezza knowledge base                                │
│                                                                 │
│  Query:                                                         │
│  SELECT group_id, COUNT(*) as doc_count                         │
│  FROM documents                                                 │
│  WHERE group_id IS NOT NULL                                     │
│  GROUP BY group_id                                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  MAU gruppo (Monthly Active Users) (target: >60% membri)       │
│  ────────────────────────────────────────────────────────────── │
│  % membri che hanno fatto almeno 1 query/upload nel mese       │
│                                                                 │
│  Query:                                                         │
│  SELECT                                                         │
│    g.id,                                                        │
│    COUNT(DISTINCT gm.user_id) as total_members,                │
│    COUNT(DISTINCT cs.user_id) as active_users,                 │
│    (COUNT(DISTINCT cs.user_id)::float /                        │
│     COUNT(DISTINCT gm.user_id)) * 100 as mau_pct               │
│  FROM groups g                                                  │
│  JOIN group_memberships gm ON g.id = gm.group_id               │
│  LEFT JOIN chat_sessions cs ON                                 │
│    cs.group_id = g.id AND                                       │
│    cs.created_at >= NOW() - INTERVAL '30 days'                 │
│  GROUP BY g.id                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Revenue Metrics**:
```
┌─────────────────────────────────────────────────────────────────┐
│  Conversion FREE → TEAM (target: >15%)                         │
│  ────────────────────────────────────────────────────────────── │
│  % gruppi FREE che upgradano a TEAM dopo 30gg                  │
│                                                                 │
│  Triggers upgrade:                                              │
│  - Storage 80% pieno                                            │
│  - 5 membri raggiunto                                           │
│  - Query quota superata 3 volte                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Conversion TEAM → BUSINESS (target: >5%)                      │
│  ────────────────────────────────────────────────────────────── │
│  % gruppi TEAM che upgradano a BUSINESS dopo 90gg              │
│                                                                 │
│  Triggers upgrade:                                              │
│  - >10 membri necessari                                         │
│  - Storage 500MB insufficiente                                  │
│  - Richiesta analytics avanzate                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  MRR Growth (target: >20% month-over-month)                    │
│  ────────────────────────────────────────────────────────────── │
│  Monthly Recurring Revenue crescita                             │
│                                                                 │
│  Formula:                                                       │
│  ((MRR_current - MRR_previous) / MRR_previous) * 100           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Churn Rate (target: <5% monthly)                              │
│  ────────────────────────────────────────────────────────────── │
│  % gruppi paganti che cancellano subscription                   │
│                                                                 │
│  Formula:                                                       │
│  (cancelled_subscriptions / active_subscriptions_start) * 100  │
│                                                                 │
│  Exit interview: perché cancelli?                               │
│  - Troppo costoso (price sensitivity)                           │
│  - Feature mancanti                                             │
│  - Problemi tecnici                                             │
│  - Non più necessario                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🤔 DECISIONI STRATEGICHE APERTE

Prima di iniziare implementazione, necessarie decisioni su:

### 1. Priorità Billing

**Domanda**: Lanciare subito con Stripe o prima MVP free per testare adoption?

**Opzioni**:
- **A**: MVP free-only (4-6 settimane) → Validare product-market fit → Poi billing
- **B**: Billing da subito (8 settimane) → Iniziare revenue immediatamente

**Raccomandazione**: **Opzione A** - Validare prima demand

---

### 2. Limiti Free Tier

**Domanda**: Quanti utenti per gruppo FREE?

**Opzioni**:
- **A**: 3 utenti (stretto, incentiva upgrade veloce)
- **B**: 5 utenti (bilanciato, permette test reale)
- **C**: 10 utenti (generoso, rischio bassa conversion)

**Raccomandazione**: **5 utenti** - Sweet spot per famiglie/piccoli team

---

### 3. Multi-Gruppo User FREE

**Domanda**: User FREE può creare 1 gruppo ma essere membro di N gruppi altrui?

**Opzioni**:
- **A**: Sì, illimitati (growth virality)
- **B**: Max 3 gruppi totali (limita free-riders)

**Raccomandazione**: **Opzione A** - Incentiva inviti

---

### 4. Document Ownership

**Domanda**: User lascia gruppo → suoi documenti caricati restano o vengono eliminati?

**Opzioni**:
- **A**: Restano, ownership trasferita a owner gruppo
- **B**: Eliminati automaticamente
- **C**: Scelta utente al momento del leave

**Raccomandazione**: **Opzione A** (default) con **C** come override

---

### 5. Onboarding Prioritario

**Domanda**: Ottimizzare UX per "crea gruppo" o "join gruppo"?

**Opzioni**:
- **A**: Focus su "crea gruppo" (bottom-up growth)
- **B**: Focus su "join gruppo" (top-down via owner esistenti)

**Raccomandazione**: **50/50** - A/B test su cohort

---

### 6. Analytics Privacy

**Domanda**: Admin gruppo può vedere query individuali membri o solo aggregati?

**Opzioni**:
- **A**: Solo aggregati (privacy-first)
- **B**: Query individuali ma senza contenuto risposta
- **C**: Full visibility (trasparenza totale)

**Raccomandazione**: **Opzione B** con toggle in settings gruppo

---

## ✅ PROSSIMI PASSI

### Immediate Action Items

1. **Decisioni strategiche**: Rispondere alle 6 domande aperte sopra
2. **Database migration plan**: Revieware schema proposto, eventuali modifiche
3. **Wireframes UI**: Mockup dashboard gruppi, onboarding flow
4. **Tech stack decisions**:
   - Billing: Stripe vs Paddle vs Lemonsqueezy?
   - Analytics: Posthog vs Mixpanel vs custom?
5. **Timeline commitment**: Confermare 6-8 settimane roadmap

---

## 📚 RIFERIMENTI

### Competitor Analysis

**Notion**:
- Workspace collaboration model
- Tiered pricing simile (Free, Plus, Business, Enterprise)
- Permission granulari

**Obsidian Sync**:
- Vault condivisi
- End-to-end encryption option
- Self-hosted alternative

**Dropbox**:
- Folder sharing model
- Storage-based pricing
- Team admin dashboard

### Inspirazione Features

- **Slack**: Invite codes, onboarding flow
- **GitHub**: Organization roles (owner/admin/member)
- **Notion**: Template gallery per gruppi

---

**Report creato**: 18 Ottobre 2025
**Autore**: Claude Code AI Assistant
**Versione**: 1.0 - Strategic Planning
**Status**: 📋 Awaiting Stakeholder Decisions

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
