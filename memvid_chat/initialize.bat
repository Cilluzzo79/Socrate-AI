@echo off
echo ===================================
echo  MEMVID CHAT SYSTEM INITIALIZATION
echo ===================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found. Please install Python 3.8 or higher.
    goto :end
)

REM Check if virtual environment exists
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to create virtual environment.
        goto :end
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install dependencies.
    goto :end
)

REM Initialize database
echo Initializing database...
python -c "from database.models import init_db; init_db()"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to initialize database.
    goto :end
)

REM Sync documents
echo Synchronizing documents...
python -c "from database.operations import sync_documents; sync_documents()"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to synchronize documents.
    goto :end
)

echo.
echo Initialization complete!
echo.
echo To start the bot, run: python main.py
echo.

:end
pause
