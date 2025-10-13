# Memvid Chat: Guida all'Installazione e Utilizzo

Questa guida dettagliata ti accompagnerà attraverso il processo di installazione, configurazione e utilizzo del sistema Memvid Chat.

## Indice
1. [Requisiti di Sistema](#requisiti-di-sistema)
2. [Installazione](#installazione)
3. [Configurazione](#configurazione)
4. [Avvio del Bot](#avvio-del-bot)
5. [Utilizzo](#utilizzo)
6. [Risoluzione dei Problemi](#risoluzione-dei-problemi)
7. [Domande Frequenti](#domande-frequenti)

## Requisiti di Sistema

- **Python**: Versione 3.8 o superiore
- **Sistema Operativo**: Windows, macOS o Linux
- **Connessione Internet**: Per la comunicazione con le API Telegram e OpenRouter
- **Account Telegram**: Per interagire con il bot
- **API Key OpenRouter**: Per l'accesso a Claude 3.7 Sonnet
- **Memvid**: Documenti processati in formato Memvid

## Installazione

### Windows

1. Clona o scarica il repository nella tua directory preferita
2. Apri il Prompt dei Comandi come amministratore
3. Naviga nella directory del progetto
4. Esegui lo script di inizializzazione:

```batch
initialize.bat
```

### Linux/macOS

1. Clona o scarica il repository nella tua directory preferita
2. Apri il terminale
3. Naviga nella directory del progetto
4. Rendi eseguibile lo script di inizializzazione:

```bash
chmod +x initialize.sh
```

5. Esegui lo script:

```bash
./initialize.sh
```

## Configurazione

### File di Configurazione

Il file di configurazione principale è `.env` nella cartella `config`. Copia il file `.env.example` in `.env` e modifica le seguenti impostazioni:

- `TELEGRAM_BOT_TOKEN`: Token del tuo bot Telegram (ottienilo da [@BotFather](https://t.me/BotFather))
- `OPENROUTER_API_KEY`: Chiave API di OpenRouter
- `MEMVID_OUTPUT_DIR`: Percorso alla directory contenente i file Memvid (MP4 e JSON)
- `ADMIN_USER_IDS`: (Opzionale) ID degli utenti amministratori, separati da virgole

### Configurazione Avanzata

Per una configurazione più dettagliata, puoi modificare anche i seguenti parametri:

- `MODEL_NAME`: Nome del modello da utilizzare su OpenRouter
- `MAX_TOKENS`: Numero massimo di token nella risposta
- `TEMPERATURE`: Temperatura per la generazione della risposta
- `DEFAULT_TOP_K`: Numero di chunk da recuperare per default
- `DEBUG_MODE`: Attiva la modalità di debug per log dettagliati

## Avvio del Bot

### Windows

Esegui lo script:

```batch
start_bot.bat
```

### Linux/macOS

1. Rendi eseguibile lo script:

```bash
chmod +x start_bot.sh
```

2. Esegui lo script:

```bash
./start_bot.sh
```

## Utilizzo

### Comandi del Bot

- `/start`: Inizia la conversazione con il bot
- `/select`: Seleziona un documento per la chat
- `/settings`: Modifica le impostazioni di chat
- `/reset`: Resetta la conversazione corrente
- `/help`: Mostra le istruzioni d'aiuto

### Flusso di Utilizzo Tipico

1. Avvia il bot con `/start`
2. Seleziona un documento con `/select`
3. Fai domande sul documento
4. Se necessario, regola le impostazioni con `/settings`
5. Per cambiare documento, usa di nuovo `/select`

### Modalità Beta

La modalità beta può essere attivata dalle impostazioni e offre:

- Informazioni dettagliate sull'utilizzo dei token
- Accesso a parametri avanzati di generazione
- Visualizzazione dei metadati di risposta

## Risoluzione dei Problemi

### Il bot non risponde

- Verifica che il token del bot sia corretto
- Assicurati che il bot sia in esecuzione
- Controlla i log per errori

### Errori di retrieval

- Verifica che i documenti Memvid esistano nella directory configurata
- Controlla che i file MP4 abbiano i corrispondenti file JSON
- Esegui la sincronizzazione dei documenti con `python -c "from database.operations import sync_documents; sync_documents()"`

### Errori di generazione

- Verifica che la chiave API OpenRouter sia valida
- Controlla la connessione internet
- Verifica che il modello specificato sia disponibile su OpenRouter

## Domande Frequenti

### Posso aggiungere nuovi documenti mentre il bot è in esecuzione?

Sì, puoi aggiungere nuovi documenti Memvid alla directory configurata. Esegui `/select` per aggiornare l'elenco dei documenti disponibili.

### Come posso vedere le statistiche di utilizzo?

Attiva la modalità beta nelle impostazioni del bot. Dopo ogni risposta, verranno mostrate informazioni dettagliate sull'utilizzo dei token.

### Posso usare il bot in chat di gruppo?

Attualmente, il bot è progettato per chat individuali. L'utilizzo in chat di gruppo non è supportato ufficialmente.

### Come posso cambiare il modello LLM?

Modifica il parametro `MODEL_NAME` nel file `.env` e riavvia il bot.

### Posso elaborare nuovi documenti con il bot?

La versione attuale non supporta l'elaborazione diretta di documenti. Devi utilizzare prima l'applicazione Memvid Document Encoder per convertire i documenti in formato Memvid.
