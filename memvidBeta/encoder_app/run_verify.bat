@echo off
chcp 65001 > nul
title Memvid Verifier

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ ERRORE: Python non trovato!
    echo.
    echo 💡 Possibili soluzioni:
    echo    1. Installa Python da python.org
    echo    2. Aggiungi Python al PATH
    echo    3. Usa: py invece di python
    echo.
    pause
    exit /b 1
)

echo.
echo ═══════════════════════════════════════════════════════════════
echo    🔍 MEMVID COMPLETENESS VERIFIER
echo    Verifica che i file Memvid contengano tutto il testo
echo ═══════════════════════════════════════════════════════════════
echo.

:MENU
echo.
echo 📋 MENU PRINCIPALE:
echo.
echo    1. Verifica singolo file
echo    2. Verifica batch (tutti i file in outputs/)
echo    3. Test rapido sistema
echo    4. Mostra istruzioni
echo    5. Esci
echo.

set /p choice="Scegli un'opzione (1-5): "

if "%choice%"=="1" goto SINGLE
if "%choice%"=="2" goto BATCH
if "%choice%"=="3" goto TEST
if "%choice%"=="4" goto HELP
if "%choice%"=="5" goto EXIT

echo ❌ Scelta non valida!
goto MENU

:SINGLE
echo.
echo ═══════════════════════════════════════════════════════════════
echo    📄 VERIFICA SINGOLO FILE
echo ═══════════════════════════════════════════════════════════════
echo.
echo Inserisci i percorsi dei file (o trascina e rilascia):
echo.

set /p source="File sorgente (PDF/TXT): "
set /p json="File JSON Memvid: "

REM Rimuovi virgolette se presenti
set source=%source:"=%
set json=%json:"=%

echo.
echo ⏳ Verifica in corso...
echo.

python verify_memvid.py "%source%" "%json%"

if errorlevel 1 (
    echo.
    echo ❌ Verifica completata con errori o file incompleto
) else (
    echo.
    echo ✅ Verifica completata con successo!
)

echo.
echo ═══════════════════════════════════════════════════════════════
pause
goto MENU

:BATCH
echo.
echo ═══════════════════════════════════════════════════════════════
echo    📊 VERIFICA BATCH
echo ═══════════════════════════════════════════════════════════════
echo.
echo 🔍 Verifica tutti i file in uploads/ e outputs/...
echo.

python verify_batch.py

if errorlevel 1 (
    echo.
    echo ⚠️  Alcuni file potrebbero essere incompleti
) else (
    echo.
    echo ✅ Tutti i file verificati!
)

echo.
echo ═══════════════════════════════════════════════════════════════
pause
goto MENU

:TEST
echo.
echo ═══════════════════════════════════════════════════════════════
echo    🧪 TEST RAPIDO SISTEMA
echo ═══════════════════════════════════════════════════════════════
echo.
echo 🔍 Esecuzione test di sistema...
echo.

python test_verify.py

echo.
echo ═══════════════════════════════════════════════════════════════
pause
goto MENU

:HELP
echo.
echo ═══════════════════════════════════════════════════════════════
echo    📖 ISTRUZIONI D'USO
echo ═══════════════════════════════════════════════════════════════
echo.
echo 🎯 COSA FA QUESTO TOOL:
echo    Verifica che un file Memvid (JSON) contenga tutto il testo
echo    del documento originale confrontando il numero di parole.
echo.
echo 📁 STRUTTURA FILE:
echo    uploads/         ← File sorgente (PDF, TXT, MD)
echo    outputs/         ← File Memvid generati (JSON, MP4)
echo.
echo 📊 RISULTATI:
echo    ✅ ECCELLENTE (≥99%%)    → File completo al 100%%
echo    ✅ OTTIMO (95-99%%)       → File completo (differenze minime)
echo    ⚠️  BUONO (90-95%%)       → File utilizzabile (qualche perdita)
echo    ⚠️  SUFFICIENTE (80-90%%) → Verificare sezioni critiche
echo    ❌ INSUFFICIENTE (^<80%%)  → Rigenerare file
echo.
echo 💡 OPZIONE 1 - VERIFICA SINGOLO FILE:
echo    • Verifica un file specifico
echo    • Mostra statistiche dettagliate
echo    • Utile per debug di un singolo documento
echo.
echo 💡 OPZIONE 2 - VERIFICA BATCH:
echo    • Verifica automaticamente TUTTI i file
echo    • Genera tabella riassuntiva
echo    • Salva report JSON dettagliato
echo    • Utile per controllo qualità generale
echo.
echo 💡 OPZIONE 3 - TEST RAPIDO:
echo    • Verifica che Python e librerie siano installati
echo    • Controlla struttura directory
echo    • Esegue test su un file di esempio
echo.
echo 🔧 USO DA LINEA DI COMANDO:
echo    python verify_memvid.py "documento.pdf" "documento.json"
echo    python verify_batch.py
echo    python test_verify.py
echo.
echo 📝 NOTE:
echo    • I nomi dei file devono corrispondere (esclusa estensione)
echo    • Supporta PDF, TXT, MD come sorgente
echo    • La verifica richiede pochi secondi per file
echo.
echo ═══════════════════════════════════════════════════════════════
pause
goto MENU

:EXIT
echo.
echo 👋 Arrivederci!
echo.
timeout /t 2 >nul
exit

:ERROR
echo.
echo ❌ Si è verificato un errore!
echo.
echo 💡 Suggerimenti:
echo    • Verifica che Python sia installato
echo    • Verifica che PyPDF2 sia installato: pip install PyPDF2
echo    • Esegui: python test_verify.py per diagnostica completa
echo.
pause
goto MENU
