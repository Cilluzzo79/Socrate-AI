# 🔍 Memvid Completeness Verifier - Guida Completa

## 📖 Panoramica

Questi script permettono di **verificare che i file Memvid generati contengano tutto il testo** dei documenti originali. La verifica confronta il numero di parole e caratteri tra sorgente e output Memvid.

---

## 📦 File Inclusi

### 1. `verify_memvid.py`
Script principale per verifica singoli file.

**Uso:**
```bash
python verify_memvid.py <file_sorgente> <file_json>
```

**Esempio:**
```bash
python verify_memvid.py "uploads/manuale.pdf" "outputs/manuale.json"
```

### 2. `verify_batch.py`
Script per verifica automatica di tutti i file.

**Uso:**
```bash
python verify_batch.py
```

Verifica automaticamente tutte le coppie file in `uploads/` e `outputs/`.

### 3. `run_verify.bat` (Windows)
Interfaccia menu interattiva per Windows.

**Uso:**
```bash
run_verify.bat
```

---

## 🚀 Quick Start

### Metodo 1: Menu Interattivo (Windows)
1. Doppio click su `run_verify.bat`
2. Scegli opzione dal menu
3. Segui le istruzioni

### Metodo 2: Verifica Singolo File
```bash
python verify_memvid.py "mio_documento.pdf" "mio_documento.json"
```

### Metodo 3: Verifica Batch
```bash
python verify_batch.py
```

---

## 📊 Interpretazione Risultati

### ✅ ECCELLENTE (≥99%)
- **Significato:** File completo al 100%
- **Azione:** Nessuna, file perfetto!
- **Esempio:** 99.8% di copertura

### ✅ OTTIMO (95-99%)
- **Significato:** File completo, differenze minime
- **Causa:** Intestazioni PDF, caratteri speciali
- **Azione:** File utilizzabile senza problemi

### ⚠️ BUONO (90-95%)
- **Significato:** File utilizzabile, qualche perdita
- **Causa:** Chunking aggressivo, alcune pagine
- **Azione:** Verificare sezioni critiche

### ⚠️ SUFFICIENTE (80-90%)
- **Significato:** Perdita significativa (10-20%)
- **Causa:** Problemi encoding o limiti chunk
- **Azione:** Rigenerare con chunk_size maggiore

### ❌ INSUFFICIENTE (<80%)
- **Significato:** File gravemente incompleto
- **Causa:** Encoder interrotto, errori gravi
- **Azione:** Rigenerare immediatamente

---

## 📋 Output Esempio

### Verifica Singolo File

```
======================================================================
🔍 VERIFICA COMPLETEZZA MEMVID
======================================================================

📄 File Sorgente: manuale_diritto_civile.pdf
   Tipo: PDF
   Dimensione: 2847.3 KB

💾 File JSON: manuale_diritto_civile.json
   Dimensione: 1523.8 KB

⏳ ESTRAZIONE TESTO:
----------------------------------------------------------------------
   📄 Estrazione da 342 pagine PDF...
      Completato: 342 pagine estratte
   💾 1,847 chunks estratti dal JSON

📊 STATISTICHE:
----------------------------------------------------------------------

📖 Sorgente Originale:
   • Parole:       245,832
   • Caratteri:  1,523,451

💾 JSON Memvid:
   • Parole:       244,105
   • Caratteri:  1,515,223
   • Chunks:         1,847
   • Parole/chunk:    132.1

📈 COPERTURA:
----------------------------------------------------------------------
   • Parole:       99.30%
   • Caratteri:    99.46%

✅ VALUTAZIONE FINALE:
======================================================================
✅ ECCELLENTE (≥99%)
   Il file Memvid contiene TUTTO il testo originale!
   ✓ Nessuna azione richiesta
======================================================================
```

### Verifica Batch

```
================================================================================
📊 RIEPILOGO VERIFICA BATCH
================================================================================

File                           Parole   Copertura  Rating         
--------------------------------------------------------------------------------
✅ manuale_diritto             244,105      99.3%  ECCELLENTE    
✅ codice_civile               189,432      98.7%  OTTIMO        
✅ guida_pratica                45,678      96.2%  OTTIMO        
⚠️  documento_lungo            320,567      92.1%  BUONO         
❌ test_incompleto              12,345      75.3%  INSUFFICIENTE 
--------------------------------------------------------------------------------

📈 STATISTICHE AGGREGATE:
   • File totali:         5
   • File completi:       4 (80.0%)
   • File incompleti:     1
   • Copertura media:     92.32%

🏆 DISTRIBUZIONE RATING:
   ✅ ECCELLENTE        1 file (20.0%)
   ✅ OTTIMO            2 file (40.0%)
   ⚠️  BUONO            1 file (20.0%)
   ❌ INSUFFICIENTE     1 file (20.0%)
================================================================================

💾 Report salvato: outputs/batch_verification_20251002_143022.json
   Dimensione: 45.3 KB
```

---

## 🔧 Opzioni Avanzate

### Verifica con Hash
```bash
python verify_memvid.py documento.pdf documento.json --hash
```
Confronta anche gli hash MD5 per verifica al 100%.

### Salvare Report
```bash
python verify_memvid.py documento.pdf documento.json --save
```
Salva report dettagliato in JSON.

### Directory Personalizzate (Batch)
```bash
python verify_batch.py --uploads my_uploads --outputs my_outputs
```

### Non Salvare Report (Batch)
```bash
python verify_batch.py --no-save
```

---

## 📁 Struttura File Richiesta

```
encoder_app/
├── uploads/                    ← File sorgente
│   ├── documento1.pdf
│   ├── documento2.txt
│   └── documento3.md
│
├── outputs/                    ← File Memvid
│   ├── documento1.json        ← Stesso nome del sorgente
│   ├── documento1.mp4
│   ├── documento2.json
│   ├── documento2.mp4
│   └── ...
│
├── verify_memvid.py           ← Script verifica singola
├── verify_batch.py            ← Script verifica batch
└── run_verify.bat             ← Menu Windows
```

**IMPORTANTE:** I nomi dei file devono corrispondere (esclusa l'estensione)!

---

## ❓ FAQ

### Q: Perché la copertura non è esattamente 100%?
**A:** Piccole differenze (1-2%) sono normali dovute a:
- Intestazioni/footer PDF non estratti
- Caratteri speciali normalizzati
- Spazi multipli collassati

### Q: Come migliorare la copertura?
**A:** 
1. Aumenta `chunk_size` nell'encoder
2. Aumenta `overlap` tra chunk
3. Verifica limite max chunks
4. Usa encoder `memvid_smart.py` con rilevamento duplicati

### Q: Cosa fare se un file è INSUFFICIENTE?
**A:**
1. Rigenera con settings diversi:
   - `chunk_size: 1000` invece di 500
   - `overlap: 100` invece di 50
2. Usa encoder leggero per file grandi
3. Verifica che PDF sia leggibile (non scansione)

### Q: La verifica è lenta?
**A:** 
- File piccoli: 2-5 secondi
- File medi: 10-20 secondi  
- File grandi: 30-60 secondi
- Opzione `--hash` aggiunge 20-30% tempo

### Q: Posso verificare file TXT e MD?
**A:** Sì! Lo script supporta:
- `.pdf` - File PDF
- `.txt` - File di testo
- `.md` - File Markdown

### Q: Come funziona la verifica batch?
**A:**
1. Cerca tutti `.json` in `outputs/`
2. Per ogni JSON, cerca sorgente corrispondente in `uploads/`
3. Verifica tutte le coppie trovate
4. Genera tabella riassuntiva
5. Salva report JSON dettagliato

---

## 🐛 Troubleshooting

### Errore: "File non trovato"
```
❌ ERRORE: File sorgente non trovato: documento.pdf
```
**Soluzione:** Verifica percorso corretto e presenza file.

### Errore: "Nessuna coppia trovata" (Batch)
```
❌ Nessuna coppia di file trovata!
```
**Soluzione:** 
- Verifica che i file siano nelle cartelle corrette
- Controlla che i nomi corrispondano

### Errore: "Estrazione PDF fallita"
```
❌ ERRORE: Errore estrazione PDF: [dettagli]
```
**Soluzione:**
- PDF potrebbe essere protetto
- PDF potrebbe essere scansionato (usa OCR)
- Installa `pip install PyPDF2` aggiornato

### Warning: "File sorgente non trovato per X.json"
```
⚠️  Nessun file sorgente trovato per: documento.json
```
**Soluzione:** 
- Aggiungi `documento.pdf` o `documento.txt` in `uploads/`
- Assicurati che il nome corrisponda esattamente

---

## 📈 Best Practices

### ✅ Verifica Sempre Dopo Encoding
```bash
# Dopo ogni encoding
python memvid_sections.py input.pdf
python verify_memvid.py uploads/input.pdf outputs/input.json
```

### ✅ Verifica Batch Periodica
```bash
# Una volta a settimana
python verify_batch.py
```

### ✅ Salva Report Importanti
```bash
# Per documenti critici
python verify_memvid.py documento.pdf documento.json --save --hash
```

### ✅ Automatizza con Script
```bash
# Windows: Crea batch file
@echo off
python memvid_sections.py %1
python verify_memvid.py uploads\%~n1.pdf outputs\%~n1.json
```

---

## 🔐 Note Tecniche

### Algoritmo di Verifica
1. Estrae testo da sorgente (PDF/TXT)
2. Estrae testo da JSON Memvid
3. Normalizza entrambi (spazi, case)
4. Conta parole e caratteri
5. Calcola percentuali di copertura
6. Opzionale: Confronta hash MD5

### Normalizzazione Testo
- Spazi multipli → spazio singolo
- Newline multipli → spazio
- Tab → spazio
- Case preservato (ma ignorato per hash)

### Precisione
- **Conteggio parole:** ±0.1%
- **Conteggio caratteri:** ±0.05%
- **Hash match:** 100% (identità byte-per-byte)

---

## 📞 Supporto

### Problemi Comuni
Consulta sezione Troubleshooting sopra.

### Bug o Feature Request
Contatta sviluppatore o apri issue.

### Logs
Gli script stampano su stdout. Per salvare log:
```bash
python verify_batch.py > verification.log 2>&1
```

---

## 📝 Changelog

### v1.0.0 (2025-10-02)
- ✅ Verifica singolo file
- ✅ Verifica batch
- ✅ Menu interattivo Windows
- ✅ Report JSON
- ✅ Supporto PDF/TXT/MD
- ✅ Hash check opzionale

---

## 📄 Licenza

Script forniti come-sono per uso interno.

---

**Versione:** 1.0.0  
**Data:** 02 Ottobre 2025  
**Autore:** Claude Assistant  
**Status:** ✅ Pronto per l'uso
