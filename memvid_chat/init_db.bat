@echo off
echo Initializing database...

python -c "from database.models import init_db; init_db()"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to initialize database.
    pause
    exit /b 1
)

echo Database initialized successfully.
echo.
echo Synchronizing documents...

python -c "from database.operations import sync_documents; sync_documents()"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to synchronize documents.
    pause
    exit /b 1
)

echo Documents synchronized successfully.
echo.
echo Initialization complete!
echo.
pause
