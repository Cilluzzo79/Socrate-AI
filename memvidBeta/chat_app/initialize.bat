@echo off
echo ===================================
echo  MEMVID CHAT SYSTEM INITIALIZER
echo ===================================
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv .venv

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Initialize database
echo Initializing database...
python -c "from database.models import init_db; init_db()"
python -c "from database.operations import sync_documents; sync_documents()"

echo.
echo Initialization completed successfully!
echo You can now run start_bot.bat to start the system.
echo.

pause
