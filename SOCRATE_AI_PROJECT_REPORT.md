# 📋 Report Dettagliato: Socrate AI - Sistema Multi-tenant con Web App e Telegram Bot

**Progetto:** Socrate AI - Knowledge Management System
**Piattaforma:** Railway
**Stack:** Python (Flask + python-telegram-bot), PostgreSQL, React/Vue (Frontend)
**Obiettivo:** Sistema unificato accessibile via Web App e Telegram Bot con autenticazione automatica

---

## 📐 Architettura del Sistema

### **Panoramica High-Level**

```
┌─────────────────────────────────────────────────────────────┐
│                    RAILWAY DEPLOYMENT                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │   Web App    │◄───────►│  Flask API   │                 │
│  │  (Frontend)  │  HTTPS  │   Backend    │                 │
│  │  React/Vue   │         │  (REST API)  │                 │
│  └──────────────┘         └───────┬──────┘                 │
│                                    │                        │
│                            ┌───────▼──────────┐             │
│                            │  Telegram Bot    │             │
│                            │  (PTB Framework) │             │
│                            └───────┬──────────┘             │
│                                    │                        │
│  ┌─────────────────────────────────▼────────────────────┐  │
│  │         PostgreSQL Database (Multi-tenant)           │  │
│  │  • users (telegram_id univoco)                       │  │
│  │  • documents (per user_id)                           │  │
│  │  • chat_sessions (storico)                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │    Railway Volume / S3 Storage                       │  │
│  │    /storage/{user_id}/{document_id}/                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔑 Problema e Soluzione: Autenticazione Automatica

### **Problema**
Gli utenti inesperti non possono configurare manualmente chiavi API o token Telegram.

### **Soluzione: Telegram Login Widget**
Utilizziamo il **widget ufficiale di Telegram** per OAuth senza configurazione:

**Come Funziona:**
1. Utente visita Web App
2. Click su bottone "Login con Telegram"
3. Widget apre automaticamente app Telegram (mobile/desktop)
4. Utente conferma con 1 click
5. Telegram rimanda dati crittografati al backend
6. Backend verifica firma e crea/recupera utente
7. Sessione Web collegata a `telegram_id`

**Vantaggi:**
- ✅ Zero configurazione manuale
- ✅ Sicuro (firma crittografica HMAC-SHA256)
- ✅ UX fluida (1 click)
- ✅ Ufficiale e mantenuto da Telegram

---

## 📊 Database Schema Multi-tenant

### **Tabella: users**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT UNIQUE NOT NULL,  -- Chiave univoca da Telegram
    username VARCHAR(255),
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255),
    photo_url TEXT,
    email VARCHAR(255),  -- Opzionale per future features
    subscription_tier VARCHAR(20) DEFAULT 'free',  -- free, pro, enterprise
    storage_quota_mb INTEGER DEFAULT 500,
    storage_used_mb INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    settings JSONB DEFAULT '{}',  -- Preferenze utente

    INDEX idx_telegram_id (telegram_id),
    INDEX idx_username (username)
);
```

**Campi Chiave:**
- `telegram_id`: ID univoco fornito da Telegram (es: 123456789)
- `subscription_tier`: Gestione piani (free/pro/enterprise)
- `storage_quota_mb`: Limite spazio documenti per tier

---

### **Tabella: documents**
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- File info
    filename VARCHAR(255) NOT NULL,  -- nome_documento_sections.mp4
    original_filename VARCHAR(255),  -- Nome originale upload
    mime_type VARCHAR(50),           -- video/mp4, application/pdf, etc.
    file_size BIGINT,                -- Bytes
    file_path TEXT,                  -- /storage/{user_id}/{doc_id}/file.mp4

    -- Processing status
    status VARCHAR(20) DEFAULT 'processing',  -- uploading, processing, ready, failed
    processing_progress INTEGER DEFAULT 0,    -- 0-100%
    error_message TEXT,

    -- Content metadata
    language VARCHAR(10),            -- it, en, es, etc.
    total_chunks INTEGER,            -- Numero sezioni
    total_tokens INTEGER,            -- Token totali per LLM
    duration_seconds INTEGER,        -- Solo per video
    page_count INTEGER,              -- Solo per PDF

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,

    -- Metadata aggiuntivi
    metadata JSONB DEFAULT '{}',  -- { "transcription_model": "whisper-1", ... }

    -- Indici per performance
    INDEX idx_user_documents (user_id, created_at DESC),
    INDEX idx_status (status),
    INDEX idx_filename (filename)
);
```

**Campi Chiave:**
- `user_id`: Foreign key verso users (isolamento dati)
- `status`: Tracciamento stato processing
- `file_path`: Path nel volume Railway (isolato per user)

---

### **Tabella: chat_sessions**
```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,

    -- Request info
    command_type VARCHAR(20) NOT NULL,  -- quiz, summary, analyze, outline, mindmap
    request_data JSONB NOT NULL,        -- Input parametri

    -- Response info
    response_data JSONB,                -- Output generato
    response_format VARCHAR(10),        -- markdown, html, json

    -- Metadata
    channel VARCHAR(20) NOT NULL,       -- telegram, web_app, api
    llm_model VARCHAR(50),              -- gpt-4, claude-3, etc.
    tokens_used INTEGER,                -- Costo in token
    generation_time_ms INTEGER,         -- Performance tracking

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),

    -- Indici
    INDEX idx_user_sessions (user_id, created_at DESC),
    INDEX idx_document_sessions (document_id, created_at DESC),
    INDEX idx_command_type (command_type)
);
```

**Utilità:**
- Storico completo interazioni
- Analytics su utilizzo
- Debug e troubleshooting
- Billing per tier pro/enterprise

---

## 🏗️ Struttura del Progetto

```
socrate-ai/
├── .env                          # Environment variables
├── .gitignore
├── requirements.txt
├── Procfile                      # Railway: web: gunicorn api_server:app
├── railway.json                  # Railway config
│
├── api_server.py                 # 🔴 MAIN: Flask API + Telegram Auth
├── main.py                       # Entry point (avvia bot + API)
│
├── core/
│   ├── __init__.py
│   ├── database.py               # SQLAlchemy models + connection
│   ├── document_manager.py       # 🔧 DA MODIFICARE: add user_id filter
│   ├── content_generators.py    # LLM prompts (quiz, summary, etc.)
│   └── llm_client.py             # OpenAI/Anthropic wrapper
│
├── telegram_bot/
│   ├── __init__.py
│   ├── bot.py                    # 🔧 DA MODIFICARE: add user context
│   ├── handlers.py               # Command handlers (/quiz, /summary, etc.)
│   └── advanced_handlers.py      # 🔧 DA MODIFICARE: user-scoped operations
│
├── web_app/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css         # Styling (cyberpunk theme)
│   │   ├── js/
│   │   │   ├── auth.js           # Telegram Login Widget handler
│   │   │   ├── dashboard.js      # Document management
│   │   │   └── api.js            # API client
│   │   └── images/
│   │       └── logo.png
│   ├── templates/
│   │   ├── index.html            # Landing page + Login
│   │   ├── dashboard.html        # Main app (upload, tools)
│   │   └── document.html         # Single document view
│   └── __init__.py
│
├── utils/
│   ├── __init__.py
│   ├── file_formatter.py         # HTML/TXT export templates
│   └── storage.py                # File upload/download helpers
│
├── migrations/                   # Alembic DB migrations
│   ├── env.py
│   └── versions/
│       └── 001_initial_schema.py
│
└── tests/
    ├── test_auth.py
    ├── test_document_manager.py
    └── test_api.py
```

---

## 🚀 Implementazione Passo-Passo

### **FASE 1: Setup Database Multi-tenant**

#### **Step 1.1: Crea Database Models**
📁 File: `core/database.py`

```python
from sqlalchemy import create_engine, Column, String, Integer, BigInteger, Text, TIMESTAMP, JSONB, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import uuid
from datetime import datetime
import os

DATABASE_URL = os.getenv('DATABASE_URL')  # Railway PostgreSQL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255))
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255))
    photo_url = Column(Text)
    email = Column(String(255))
    subscription_tier = Column(String(20), default='free')
    storage_quota_mb = Column(Integer, default=500)
    storage_used_mb = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    last_login = Column(TIMESTAMP)
    settings = Column(JSONB, default={})

    # Relationships
    documents = relationship('Document', back_populates='user', cascade='all, delete-orphan')
    chat_sessions = relationship('ChatSession', back_populates='user', cascade='all, delete-orphan')


class Document(Base):
    __tablename__ = 'documents'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255))
    mime_type = Column(String(50))
    file_size = Column(BigInteger)
    file_path = Column(Text)

    status = Column(String(20), default='processing')
    processing_progress = Column(Integer, default=0)
    error_message = Column(Text)

    language = Column(String(10))
    total_chunks = Column(Integer)
    total_tokens = Column(Integer)
    duration_seconds = Column(Integer)
    page_count = Column(Integer)

    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    processing_started_at = Column(TIMESTAMP)
    processing_completed_at = Column(TIMESTAMP)

    metadata = Column(JSONB, default={})

    # Relationships
    user = relationship('User', back_populates='documents')
    chat_sessions = relationship('ChatSession', back_populates='document')


class ChatSession(Base):
    __tablename__ = 'chat_sessions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id', ondelete='SET NULL'))

    command_type = Column(String(20), nullable=False)
    request_data = Column(JSONB, nullable=False)
    response_data = Column(JSONB)
    response_format = Column(String(10))

    channel = Column(String(20), nullable=False)
    llm_model = Column(String(50))
    tokens_used = Column(Integer)
    generation_time_ms = Column(Integer)

    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    user = relationship('User', back_populates='chat_sessions')
    document = relationship('Document', back_populates='chat_sessions')


# Helper functions
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database (create tables)"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized")
```

#### **Step 1.2: Crea Migration Script**
```bash
# Installa Alembic
pip install alembic

# Inizializza
alembic init migrations

# Crea migration
alembic revision --autogenerate -m "Initial schema"

# Applica migration
alembic upgrade head
```

---

### **FASE 2: Implementa Autenticazione Telegram**

#### **Step 2.1: Telegram Login Widget (Frontend)**
📁 File: `web_app/templates/index.html`

```html
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Socrate AI - Knowledge Management System</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="landing-container">
        <div class="hero">
            <h1>🤖 Socrate AI</h1>
            <p class="tagline">Il tuo assistente AI per documenti e video</p>

            <div class="features">
                <div class="feature">
                    <span class="icon">📝</span>
                    <h3>Quiz Interattivi</h3>
                    <p>Genera quiz personalizzati dai tuoi documenti</p>
                </div>
                <div class="feature">
                    <span class="icon">🗺️</span>
                    <h3>Mappe Mentali</h3>
                    <p>Visualizza concetti chiave</p>
                </div>
                <div class="feature">
                    <span class="icon">📊</span>
                    <h3>Analisi Profonde</h3>
                    <p>Tematica, critica, comparativa</p>
                </div>
            </div>

            <div class="cta">
                <h2>Accedi in 1 Click</h2>
                <p>Usa il tuo account Telegram (nessuna configurazione richiesta)</p>

                <!-- TELEGRAM LOGIN WIDGET -->
                <script async src="https://telegram.org/js/telegram-widget.js?22"
                        data-telegram-login="YOUR_BOT_USERNAME"
                        data-size="large"
                        data-auth-url="https://your-app.railway.app/auth/telegram/callback"
                        data-request-access="write">
                </script>
            </div>
        </div>
    </div>
</body>
</html>
```

#### **Step 2.2: Backend Auth Handler**
📁 File: `api_server.py`

```python
from flask import Flask, request, redirect, session, jsonify, render_template
from flask_cors import CORS
import hashlib
import hmac
import os
from core.database import SessionLocal, User, Document
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')
CORS(app)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME')


# ============ ROUTES ============

@app.route('/')
def index():
    """Landing page con Telegram Login Widget"""
    if 'user_id' in session:
        return redirect('/dashboard')
    return render_template('index.html', bot_username=BOT_USERNAME)


@app.route('/auth/telegram/callback')
def telegram_auth_callback():
    """
    Callback da Telegram Login Widget
    Riceve: id, first_name, last_name, username, photo_url, auth_date, hash
    """
    auth_data = request.args.to_dict()

    # 1. Verifica autenticità
    if not verify_telegram_auth(auth_data):
        return "❌ Authentication failed - Invalid signature", 403

    # 2. Get or create user
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=int(auth_data['id'])).first()

        if not user:
            # Crea nuovo utente
            user = User(
                telegram_id=int(auth_data['id']),
                username=auth_data.get('username'),
                first_name=auth_data['first_name'],
                last_name=auth_data.get('last_name'),
                photo_url=auth_data.get('photo_url'),
                last_login=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Aggiorna last_login
            user.last_login = datetime.utcnow()
            db.commit()

        # 3. Crea sessione
        session['user_id'] = str(user.id)
        session['telegram_id'] = user.telegram_id
        session['first_name'] = user.first_name

        # 4. Redirect a dashboard
        return redirect('/dashboard')

    finally:
        db.close()


def verify_telegram_auth(auth_data):
    """
    Verifica firma crittografica da Telegram
    Doc: https://core.telegram.org/widgets/login#checking-authorization
    """
    check_hash = auth_data.pop('hash', None)
    if not check_hash:
        return False

    # Crea stringa di verifica
    data_check_string = '\n'.join([
        f"{k}={v}" for k, v in sorted(auth_data.items())
    ])

    # Calcola hash con chiave segreta
    secret_key = hashlib.sha256(TELEGRAM_BOT_TOKEN.encode()).digest()
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    return calculated_hash == check_hash


@app.route('/logout')
def logout():
    """Logout utente"""
    session.clear()
    return redirect('/')


# ============ API ENDPOINTS ============

@app.route('/api/user/profile')
def get_user_profile():
    """Get profilo utente corrente"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(id=session['user_id']).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({
            'id': str(user.id),
            'telegram_id': user.telegram_id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'photo_url': user.photo_url,
            'subscription_tier': user.subscription_tier,
            'storage_used_mb': user.storage_used_mb,
            'storage_quota_mb': user.storage_quota_mb
        })
    finally:
        db.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

---

### **FASE 3: Modifica Document Manager per Multi-tenancy**

#### **Step 3.1: Aggiorna DocumentManager**
📁 File: `core/document_manager.py` (modifiche)

```python
from core.database import SessionLocal, User, Document
from typing import List, Optional
import uuid

class DocumentManager:
    def __init__(self):
        self.db = SessionLocal()

    def get_documents(self, user_id: str) -> List[dict]:
        """
        Get documenti per uno specifico utente
        🔧 MODIFICATO: Ora filtra per user_id
        """
        documents = self.db.query(Document).filter_by(
            user_id=uuid.UUID(user_id),
            status='ready'
        ).order_by(Document.created_at.desc()).all()

        return [
            {
                'document_id': str(doc.id),
                'name': doc.filename,
                'size': doc.file_size,
                'created_at': doc.created_at.isoformat(),
                'total_chunks': doc.total_chunks
            }
            for doc in documents
        ]

    def get_document_by_id(self, document_id: str, user_id: str) -> Optional[dict]:
        """
        Get singolo documento (con verifica ownership)
        🔧 NUOVO: Controllo user_id per security
        """
        doc = self.db.query(Document).filter_by(
            id=uuid.UUID(document_id),
            user_id=uuid.UUID(user_id)
        ).first()

        if not doc:
            return None

        return {
            'id': str(doc.id),
            'filename': doc.filename,
            'file_path': doc.file_path,
            'total_chunks': doc.total_chunks,
            'status': doc.status
        }

    def create_document(self, user_id: str, filename: str, file_path: str, **kwargs) -> str:
        """
        Crea nuovo documento per utente
        🔧 MODIFICATO: Aggiunto user_id
        """
        doc = Document(
            user_id=uuid.UUID(user_id),
            filename=filename,
            file_path=file_path,
            status='processing',
            **kwargs
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        return str(doc.id)
```

---

### **FASE 4: Web App Dashboard**

#### **Step 4.1: Dashboard HTML**
📁 File: `web_app/templates/dashboard.html`

```html
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>Socrate AI - Dashboard</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="dashboard">
        <aside class="sidebar">
            <div class="user-profile">
                <img src="{{ user.photo_url }}" alt="Profile" class="avatar">
                <h3>{{ user.first_name }}</h3>
                <span class="tier">{{ user.subscription_tier }}</span>
            </div>

            <nav>
                <a href="#documents" class="active">📁 I miei Documenti</a>
                <a href="#tools">🛠️ Strumenti</a>
                <a href="#history">📜 Storico</a>
                <a href="/logout">🚪 Logout</a>
            </nav>
        </aside>

        <main class="content">
            <header>
                <h1>I miei Documenti</h1>
                <button id="upload-btn" class="primary-btn">⬆️ Carica Documento</button>
            </header>

            <div class="storage-info">
                <div class="storage-bar">
                    <div class="storage-used" style="width: {{ (user.storage_used_mb / user.storage_quota_mb * 100) }}%"></div>
                </div>
                <p>{{ user.storage_used_mb }} MB / {{ user.storage_quota_mb }} MB utilizzati</p>
            </div>

            <div id="documents-grid" class="documents-grid">
                <!-- Populated by JS -->
            </div>

            <!-- Upload Modal -->
            <div id="upload-modal" class="modal hidden">
                <div class="modal-content">
                    <h2>Carica Documento</h2>
                    <form id="upload-form">
                        <input type="file" id="file-input" accept=".pdf,.docx,.txt,.mp4">
                        <button type="submit">Carica</button>
                    </form>
                </div>
            </div>
        </main>
    </div>

    <script src="/static/js/dashboard.js"></script>
</body>
</html>
```

#### **Step 4.2: Dashboard JavaScript**
📁 File: `web_app/static/js/dashboard.js`

```javascript
// Carica documenti
async function loadDocuments() {
    const res = await fetch('/api/documents');
    const docs = await res.json();

    const grid = document.getElementById('documents-grid');
    grid.innerHTML = docs.documents.map(doc => `
        <div class="document-card" data-id="${doc.document_id}">
            <div class="doc-icon">📄</div>
            <h3>${doc.name}</h3>
            <p>${(doc.size / 1024 / 1024).toFixed(2)} MB</p>
            <div class="doc-actions">
                <button onclick="openTools('${doc.document_id}')">🛠️ Strumenti</button>
                <button onclick="deleteDoc('${doc.document_id}')">🗑️</button>
            </div>
        </div>
    `).join('');
}

// Upload documento
document.getElementById('upload-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData();
    formData.append('file', document.getElementById('file-input').files[0]);

    const res = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData
    });

    if (res.ok) {
        alert('✅ Documento caricato!');
        loadDocuments();
    }
});

// Inizializza
loadDocuments();
```

---

### **FASE 5: API Endpoints Completi**

#### **Step 5.1: Documents API**
📁 File: `api_server.py` (aggiungi endpoints)

```python
@app.route('/api/documents')
def list_documents():
    """Lista documenti utente"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    doc_manager = DocumentManager()
    docs = doc_manager.get_documents(session['user_id'])

    return jsonify({'documents': docs})


@app.route('/api/documents/upload', methods=['POST'])
def upload_document():
    """Upload nuovo documento"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file provided'}), 400

    # Verifica quota storage
    db = SessionLocal()
    user = db.query(User).filter_by(id=session['user_id']).first()

    file_size_mb = len(file.read()) / 1024 / 1024
    file.seek(0)  # Reset pointer

    if user.storage_used_mb + file_size_mb > user.storage_quota_mb:
        return jsonify({'error': 'Storage quota exceeded'}), 413

    # Salva file
    doc_id = str(uuid.uuid4())
    user_storage_path = f"/storage/{user.id}/{doc_id}/"
    os.makedirs(user_storage_path, exist_ok=True)

    file_path = os.path.join(user_storage_path, file.filename)
    file.save(file_path)

    # Crea record documento
    doc_manager = DocumentManager()
    document_id = doc_manager.create_document(
        user_id=str(user.id),
        filename=file.filename,
        file_path=file_path,
        mime_type=file.mimetype,
        file_size=file_size_mb * 1024 * 1024
    )

    # Aggiorna storage utente
    user.storage_used_mb += file_size_mb
    db.commit()

    return jsonify({
        'document_id': document_id,
        'status': 'processing'
    })
```

---

## 🚢 Deployment su Railway

### **Step 6.1: Configurazione Railway**

📁 File: `Procfile`
```
web: gunicorn api_server:app --bind 0.0.0.0:$PORT
```

📁 File: `railway.json`
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

📁 File: `requirements.txt`
```
flask==3.0.0
python-telegram-bot==20.7
SQLAlchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.13.0
gunicorn==21.2.0
python-dotenv==1.0.0
requests==2.31.0
```

### **Step 6.2: Environment Variables su Railway**

```bash
# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
BOT_USERNAME=SocrateAIBot

# Database (auto-generated da Railway)
DATABASE_URL=postgresql://user:pass@host:5432/railway

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# App
SECRET_KEY=your-secure-random-secret-key
FLASK_ENV=production
PORT=5000
```

### **Step 6.3: Deploy**

```bash
# 1. Installa Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Inizializza progetto
railway init

# 4. Link a progetto Railway
railway link

# 5. Deploy
railway up

# 6. Apri
railway open
```

---

## ✅ Checklist Implementazione

### **Database**
- [ ] Crea modelli SQLAlchemy (User, Document, ChatSession)
- [ ] Setup Alembic migrations
- [ ] Testa creazione tabelle su Railway PostgreSQL
- [ ] Verifica foreign keys e indici

### **Autenticazione**
- [ ] Implementa `verify_telegram_auth()`
- [ ] Crea endpoint `/auth/telegram/callback`
- [ ] Configura Telegram Login Widget nel frontend
- [ ] Testa flow completo: login → redirect → sessione

### **Document Manager**
- [ ] Aggiungi parametro `user_id` a tutti i metodi
- [ ] Implementa ownership check
- [ ] Testa isolamento dati tra utenti
- [ ] Aggiungi logging per debugging

### **Web App**
- [ ] Crea landing page con Login Widget
- [ ] Implementa dashboard con lista documenti
- [ ] Aggiungi upload form con progress bar
- [ ] Integra tool buttons (quiz, summary, etc.)

### **API Endpoints**
- [ ] `/api/documents` (GET - lista)
- [ ] `/api/documents/upload` (POST)
- [ ] `/api/documents/<id>` (GET, DELETE)
- [ ] `/api/quiz/generate` (POST)
- [ ] `/api/summary/generate` (POST)
- [ ] `/api/analyze/generate` (POST)

### **Telegram Bot**
- [ ] Modifica handlers per caricare `user_id` da `telegram_id`
- [ ] Testa comandi con documenti multi-tenant
- [ ] Verifica sync Web ↔ Telegram

### **Deployment**
- [ ] Setup Railway project
- [ ] Configura PostgreSQL database
- [ ] Configura Volume per storage file
- [ ] Set environment variables
- [ ] Deploy e verifica logs
- [ ] Test completo produzione

---

## 📈 Funzionalità Future

1. **Vector Database**: Pinecone/Qdrant per semantic search
2. **Real-time Updates**: WebSocket per status processing documenti
3. **Collaboration**: Condivisione documenti tra utenti
4. **Analytics Dashboard**: Grafici utilizzo per user
5. **API Rate Limiting**: Throttling per tier
6. **Payment Integration**: Stripe per tier Pro/Enterprise
7. **Mobile App**: React Native con stessa API
8. **n8n Integration**: Webhook per automazioni

---

## 📞 Support & Contatti

- **Telegram Bot**: @SocrateAIBot
- **Web App**: https://socrate-ai.railway.app
- **Docs**: https://docs.socrate-ai.com
- **GitHub**: https://github.com/your-org/socrate-ai

---

**Report generato il:** 2025-10-12
**Versione:** 1.0.0
**Status:** Ready for Implementation 🚀
