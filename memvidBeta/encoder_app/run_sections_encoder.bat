@echo off
echo ===================================
echo  MEMVID SECTIONS ENCODER
echo ===================================
echo.

:: Ottieni il percorso del file
set /p file_path=Inserisci il percorso completo del file da elaborare: 

:: Configurazione predefinita
set chunk_size=1200
set overlap=200
set format=mp4
set max_pages=
set max_chunks=

echo.
echo Configurazione (puoi selezionare più opzioni):
echo 1. Usa configurazione predefinita (chunk: 1200, overlap: 200, formato: mp4)
echo 2. Configurazione personalizzata
echo 3. Solo JSON (nessun video MP4)
echo 4. Elaborazione parziale (solo prime pagine per PDF grandi)
echo 5. Imposta manualmente il numero massimo di chunk
echo 0. Fine selezione e avvia elaborazione
echo.

:menu
set /p option_choice=Seleziona un'opzione o 0 per avviare: 

if "%option_choice%"=="0" goto start_processing

if "%option_choice%"=="1" (
    echo Configurazione predefinita selezionata.
    set chunk_size=1200
    set overlap=200
    set format=mp4
    goto menu
)

if "%option_choice%"=="2" (
    echo.
    set /p chunk_size=Dimensione chunk [100-2000]: 
    set /p overlap=Sovrapposizione [0-500]: 
    echo Configurazione personalizzata impostata.
    goto menu
)

if "%option_choice%"=="3" (
    set format=json
    echo Formato JSON selezionato.
    goto menu
)

if "%option_choice%"=="4" (
    set /p max_pages=Numero massimo di pagine da elaborare: 
    echo Elaborazione parziale impostata a %max_pages% pagine.
    goto menu
)

if "%option_choice%"=="5" (
    set /p max_chunks=Numero massimo di chunk da elaborare: 
    echo Limite chunk impostato a %max_chunks%.
    goto menu
)

echo Opzione non valida, riprova.
goto menu

:start_processing
echo.
echo Riepilogo configurazione:
echo - File: "%file_path%"
echo - Dimensione chunk: %chunk_size%
echo - Sovrapposizione: %overlap%
echo - Formato: %format%
if not "%max_pages%"=="" echo - Pagine max: %max_pages%
if not "%max_chunks%"=="" echo - Chunk max: %max_chunks%
echo.

:: Costruzione del comando
set cmd=python memvid_sections.py "%file_path%" --chunk-size %chunk_size% --overlap %overlap% --format %format%
if not "%max_pages%"=="" set cmd=%cmd% --max-pages %max_pages%
if not "%max_chunks%"=="" set cmd=%cmd% --max-chunks %max_chunks%

echo Esecuzione comando: %cmd%
echo.
echo L'elaborazione sta per iniziare. Potrebbe richiedere diversi minuti.
echo Premi un tasto per continuare...
pause > nul

:: Esecuzione
%cmd%

echo.
echo Elaborazione completata! Premi un tasto per chiudere.
pause > nul
