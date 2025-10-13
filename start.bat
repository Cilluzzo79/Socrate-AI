@echo off
echo ===================================
echo  MEMVID DOCUMENT ENCODER LAUNCHER
echo ===================================
echo.

:: Controlla se Python è installato
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERRORE: Python non è stato trovato nel sistema.
    echo Installare Python 3.8 o superiore da https://www.python.org/
    echo.
    pause
    exit /b
)

:: Visualizza la versione di Python
python --version
echo.

:: Esegui la diagnostica
echo Esecuzione della diagnostica...
python debug.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo Vuoi installare le dipendenze mancanti? (S/N)
    set /p INSTALL=
    if /i "%INSTALL%"=="S" (
        echo.
        echo Installazione delle dipendenze...
        pip install -r requirements.txt
        echo.
        echo Ri-esecuzione della diagnostica...
        python debug.py
        if %ERRORLEVEL% neq 0 (
            echo.
            echo ERRORE: Non è stato possibile installare tutte le dipendenze.
            echo Controllare i messaggi di errore sopra.
            echo.
            pause
            exit /b
        )
    ) else (
        echo.
        echo Avvio annullato.
        pause
        exit /b
    )
)

:: Avvia l'applicazione
echo.
echo Avvio dell'applicazione Memvid Document Encoder...
echo (L'interfaccia web si aprirà nel browser)
echo.
python run.py

pause
