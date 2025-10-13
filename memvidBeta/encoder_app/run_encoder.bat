@echo off
echo ====================================
echo Memvid Sections Encoder - Windows
echo ====================================
echo.

REM Vai nella directory corretta
cd /d D:\railway\memvid\memvidBeta\encoder_app

echo Directory di lavoro: %CD%
echo.

REM Chiedi il file da elaborare
set /p FILE_PATH="Inserisci il percorso completo del file PDF: "

REM Verifica che il file esista
if not exist "%FILE_PATH%" (
    echo ERRORE: File non trovato!
    pause
    exit /b 1
)

echo.
echo File da elaborare: %FILE_PATH%
echo.

REM Esegui Python con percorso assoluto
python memvid_sections.py "%FILE_PATH%" --chunk-size 1200 --overlap 200 --format mp4

echo.
echo ====================================
echo Elaborazione completata!
echo ====================================
pause
