# 🤖 Socrate Bot - Guida Completa ai Comandi Avanzati

## Introduzione

Benvenuto nella guida completa di Socrate, il tuo assistente personale per l'analisi approfondita dei documenti tramite Telegram. Questa versione potenziata include nuovi comandi specializzati per generare contenuti strutturati come quiz, schemi, mappe concettuali e analisi dettagliate.

## 📋 Indice

1. [Comandi Base](#comandi-base)
2. [Comandi Avanzati](#comandi-avanzati)
3. [Esempi di Utilizzo](#esempi-di-utilizzo)
4. [Suggerimenti e Best Practices](#suggerimenti-e-best-practices)
5. [Risoluzione Problemi](#risoluzione-problemi)

---

## Comandi Base

### /start
**Descrizione:** Avvia il bot e mostra il messaggio di benvenuto.

**Quando usarlo:** 
- Prima volta che usi il bot
- Per vedere quali documenti hai selezionato
- Per un riepilogo rapido dei comandi disponibili

---

### /select
**Descrizione:** Apre un menu per selezionare il documento con cui vuoi lavorare.

**Come funziona:**
1. Mostra tutti i documenti Memvid disponibili
2. Clicca sul documento desiderato
3. Il bot confermerà la selezione

**Nota:** Devi selezionare un documento prima di usare qualsiasi altro comando.

---

### /settings
**Descrizione:** Permette di modificare i parametri di funzionamento del bot.

**Impostazioni disponibili:**
- **Top K** (3-10): Numero di frammenti da recuperare per ogni query
- **Temperature** (0.0-1.0): Controlla la creatività delle risposte
- **Max Tokens** (500-3000): Lunghezza massima delle risposte
- **Beta Mode** (On/Off): Attiva funzionalità avanzate e statistiche dettagliate

**Suggerimento:** Per analisi più approfondite, aumenta il Top K a 7-10.

---

### /reset
**Descrizione:** Cancella la storia della conversazione corrente e inizia una nuova sessione.

**Quando usarlo:**
- Vuoi cambiare argomento completamente
- La conversazione è diventata troppo lunga
- Vuoi ripartire da zero con lo stesso documento

---

### /help
**Descrizione:** Mostra un riepilogo di tutti i comandi disponibili.

---

## Comandi Avanzati

### 🎯 /quiz - Generazione Quiz

**Descrizione:** Genera un quiz personalizzato sul documento selezionato.

**Processo di configurazione:**

1. **Tipo di Quiz:**
   - **📝 Scelta Multipla:** Domande con 4 opzioni di risposta
   - **✓/✗ Vero/Falso:** Affermazioni da verificare
   - **✍️ Risposta Breve:** Domande aperte
   - **🎲 Misto:** Combinazione di vari tipi

2. **Numero di Domande:**
   - 5 domande (rapido)
   - 10 domande (standard)
   - 15 domande (approfondito)
   - 20 domande (completo)

3. **Livello di Difficoltà:**
   - **😊 Facile:** Comprensione di base
   - **🤔 Medio:** Analisi e applicazione
   - **🧠 Difficile:** Sintesi e valutazione
   - **🎲 Misto:** Vari livelli

**Cosa riceverai:**
- Tutte le domande formattate chiaramente
- Risposte corrette alla fine del quiz
- Spiegazioni per ogni risposta
- Riferimenti al testo quando rilevante

**Esempio d'uso:**
```
/quiz
→ Scegli "Scelta Multipla"
→ Scegli "10 domande"
→ Scegli "Medio"
→ Ricevi il quiz completo con risposte
```

---

### 📑 /outline - Creazione Schema

**Descrizione:** Genera uno schema gerarchico strutturato del documento.

**Tipi di Schema:**

1. **📋 Gerarchico:** Organizzato per struttura logica
   - Ideale per: Manuali, libri di testo, documentazione tecnica
   - Mantiene la gerarchia capitoli/sezioni originale

2. **⏱️ Cronologico:** Organizzato per ordine temporale
   - Ideale per: Resoconti storici, biografie, processi sequenziali
   - Segue la linea temporale degli eventi

3. **🎯 Tematico:** Organizzato per argomenti
   - Ideale per: Raccolte di saggi, articoli, documenti multi-argomento
   - Raggruppa concetti correlati

**Livelli di Dettaglio:**
- **📝 Sintetico:** Solo punti principali
- **📄 Medio:** Punti principali e secondari
- **📚 Dettagliato:** Include anche sotto-punti specifici

**Output:**
Schema numerato con intestazioni chiare, indentazione per mostrare la gerarchia, riferimenti a pagine quando disponibili.

---

### 🧠 /mindmap - Mappa Concettuale

**Descrizione:** Crea una mappa mentale/concettuale dei concetti chiave e delle loro relazioni.

**Profondità della Mappa:**
- **🌿 Leggera (2 livelli):** Vista d'insieme rapida
- **🌳 Media (3 livelli):** Bilanciamento tra ampiezza e profondità
- **🌲 Profonda (4 livelli):** Massimo dettaglio

**Cosa Include:**
- Concetto centrale del documento
- 4-8 concetti di primo livello
- Sotto-concetti per ogni ramo principale
- Relazioni tra i concetti (cause, correlazioni, similitudini)
- Connessioni trasversali tra rami diversi

**Formato Output:**
```
🎯 Concetto Centrale
└── Ramo 1
    ├── Sotto-concetto 1.1
    │   └── Dettaglio → [relazione con...]
    └── Sotto-concetto 1.2

🔗 Connessioni Trasversali
```

**Suggerimento:** Usa la mappa media (3 livelli) per la maggior parte dei casi - offre un buon equilibrio.

---

### 📝 /summary - Generazione Riassunto

**Descrizione:** Crea un riassunto del documento secondo il formato richiesto.

**Tipi di Riassunto:**

1. **📄 Breve (Abstract):**
   - Lunghezza: 1-2 paragrafi
   - Contenuto: Essenza del documento
   - Ideale per: Overview rapida

2. **📋 Medio (Executive Summary):**
   - Lunghezza: 3-5 paragrafi
   - Contenuto: Punti chiave con alcuni dettagli
   - Ideale per: Comprensione generale

3. **📚 Esteso (Comprehensive):**
   - Lunghezza: 6-10 paragrafi
   - Contenuto: Copertura dettagliata
   - Ideale per: Studio approfondito

4. **📑 Per Sezioni:**
   - Lunghezza: 1-2 paragrafi per sezione
   - Contenuto: Riassunto strutturato per capitoli
   - Ideale per: Documenti lunghi con chiara struttura

**Output Incluso:**
- Riassunto formattato
- Lista dei punti chiave
- Riferimenti a sezioni specifiche

---

### 🔬 /analyze - Analisi Approfondita

**Descrizione:** Conduce un'analisi dettagliata del documento secondo la metodologia scelta.

**Tipi di Analisi:**

1. **🎨 Tematica:**
   - Identifica temi ricorrenti
   - Esplora come si sviluppano nel testo
   - Mostra le interconnessioni tra temi
   - **Ideale per:** Opere letterarie, saggi, documenti filosofici

2. **💭 Argomentativa:**
   - Analizza la struttura degli argomenti
   - Identifica premesse e conclusioni
   - Valuta la logica e le evidenze
   - **Ideale per:** Testi persuasivi, articoli accademici, proposte

3. **🔍 Critica:**
   - Valuta punti di forza e debolezza
   - Identifica assunzioni implicite
   - Esamina bias e limitazioni
   - **Ideale per:** Valutazione di teorie, revisione critica

4. **⚖️ Comparativa:**
   - Confronta diverse sezioni o concetti
   - Evidenzia similitudini e differenze
   - Analizza approcci alternativi
   - **Ideale per:** Studi comparativi, review di letteratura

5. **🌐 Contestuale:**
   - Situa il contenuto in contesto più ampio
   - Esamina implicazioni e applicazioni
   - Collega a temi universali
   - **Ideale per:** Comprensione profonda, applicazione pratica

**Struttura Output:**
```
# Analisi: [Tipo]

## Introduzione
[Panoramica dell'approccio]

## Osservazioni
[Cosa emerge dal testo]

## Interpretazione
[Significato delle osservazioni]

## Implicazioni
[Conseguenze più ampie]

## Sintesi
[Conclusioni principali]

## Domande per Riflessione
[Spunti per approfondire]
```

---

## Esempi di Utilizzo

### Scenario 1: Preparazione per un Esame

**Obiettivo:** Studiare un manuale di diritto

```
1. /select → Seleziona "Codice Civile"
2. /summary → Scegli "Per Sezioni" per avere overview completa
3. /outline → Scegli "Gerarchico - Dettagliato" per struttura completa
4. /quiz → Genera "Misto - 20 domande - Difficile" per testare la conoscenza
5. [Domande specifiche] → "Spiegami l'articolo 32" o "Differenze tra X e Y"
```

### Scenario 2: Analisi di un Testo Filosofico

**Obiettivo:** Comprendere profondamente un saggio

```
1. /select → Seleziona il documento
2. /mindmap → Crea mappa "Profonda" per visualizzare concetti
3. /analyze → Scegli "Tematica" per identificare temi principali
4. /analyze → Scegli "Critica" per valutazione approfondita
5. [Discussione] → Fai domande specifiche sui temi emersi
```

### Scenario 3: Review Rapida di Documento Aziendale

**Obiettivo:** Estrarre punti chiave velocemente

```
1. /select → Seleziona il report
2. /summary → Scegli "Breve" per overview
3. /outline → Scegli "Sintetico" per struttura rapida
4. [Domande mirate] → Approfondisci sezioni specifiche
```

---

## Suggerimenti e Best Practices

### Per Quiz Efficaci

✅ **DO:**
- Usa quiz misti per varietà
- Inizia con difficoltà media, poi aumenta
- Genera quiz su sezioni specifiche chiedendo prima "Crea un quiz sulla sezione X"
- Rivedi le spiegazioni delle risposte, non solo le risposte corrette

❌ **DON'T:**
- Non generare troppi quiz facili - non testano vera comprensione
- Non saltare la revisione delle spiegazioni
- Non fare quiz troppo lunghi se hai poco tempo (5-10 domande sono sufficienti)

### Per Schemi e Mappe

✅ **DO:**
- Usa schemi gerarchici per documenti ben strutturati
- Usa mappe concettuali per visualizzare relazioni complesse
- Salva gli schemi generati per riferimento futuro
- Usa mappe di profondità media come punto di partenza

❌ **DON'T:**
- Non usare mappe troppo profonde per documenti brevi
- Non ignorare le connessioni trasversali nelle mappe
- Non aspettarti che schema e mappa siano identici - hanno scopi diversi

### Per Riassunti

✅ **DO:**
- Inizia con riassunto medio per comprensione generale
- Usa riassunto per sezioni per documenti molto lunghi
- Integra riassunti con domande specifiche
- Confronta riassunto con schema per completezza

❌ **DON'T:**
- Non fare affidamento solo sul riassunto breve per documenti complessi
- Non saltare i punti chiave elencati alla fine
- Non usare riassunto esteso quando ti serve solo overview

### Per Analisi

✅ **DO:**
- Scegli tipo di analisi adatto al documento
- Leggi le "Domande per Riflessione" alla fine
- Usa analisi multiple (es. tematica + critica) per comprensione completa
- Combina analisi con domande di follow-up

❌ **DON'T:**
- Non usare analisi critica su documenti puramente informativi
- Non ignorare la sezione "Implicazioni"
- Non aspettarti che una sola analisi copra tutti gli aspetti

### Ottimizzazione Settings

**Per Analisi Veloci:**
- Top K: 3-5
- Temperature: 0.3-0.5
- Max Tokens: 1000-1500

**Per Analisi Approfondite:**
- Top K: 7-10
- Temperature: 0.5-0.7
- Max Tokens: 2000-3000

**Per Contenuti Creativi (mappe, analisi tematiche):**
- Top K: 5-7
- Temperature: 0.7-0.9
- Max Tokens: 1500-2500

---

## Risoluzione Problemi

### "Nessun documento selezionato"
**Soluzione:** Usa /select prima di qualsiasi altro comando

### "Risposta troppo lunga"
**Soluzione:** 
- Il bot divide automaticamente in parti
- In alternativa, riduci Max Tokens in /settings
- Chiedi riassunti più brevi o sezioni specifiche

### "Quiz con domande poco rilevanti"
**Problema:** Il documento potrebbe essere troppo lungo
**Soluzione:**
- Fai domande prima su sezioni specifiche
- Poi genera quiz specificando: "Crea un quiz sulla sezione X"

### "Analisi non abbastanza profonda"
**Soluzione:**
- Aumenta Top K a 8-10 in /settings
- Aumenta Max Tokens a 2500-3000
- Fai domande di follow-up specifiche

### "Errore durante generazione"
**Soluzione:**
- Verifica connessione internet
- Prova a ridurre il numero di domande/lunghezza
- Usa /reset e riprova
- Controlla che il documento sia stato caricato correttamente

---

## 💡 Consigli Finali

1. **Sperimenta:** Prova diversi tipi di comandi sullo stesso documento per vedere cosa funziona meglio

2. **Combina Comandi:** Usa più comandi in sequenza per comprensione completa
   - Esempio: summary → outline → quiz → analyze

3. **Sfrutta Beta Mode:** Attiva in /settings per vedere statistiche dettagliate e capire come ottimizzare

4. **Salva i Risultati:** Copia e salva quiz, schemi e analisi per riferimento futuro

5. **Interagisci:** Dopo ogni comando, fai domande di approfondimento sui risultati

6. **Feedback:** Se qualcosa non funziona come ti aspetti, riprova con parametri diversi

---

## 🎓 Risorse Aggiuntive

- Per supporto tecnico: Controlla i log del bot
- Per miglioramenti: Le tue richieste aiutano a migliorare Socrate
- Per aggiornamenti: Usa /help per vedere nuove funzionalità

---

**Versione Guida:** 2.0  
**Ultimo Aggiornamento:** Ottobre 2025  
**Autore:** Sistema Memvid Chat - Socrate Bot

---

*Buono studio con Socrate! 📚🤖*
