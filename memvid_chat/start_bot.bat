@echo off
echo ===================================
echo  MEMVID CHAT SYSTEM LAUNCHER
echo ===================================
echo.

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate

REM Start the bot
echo Starting Memvid Chat system...
python main.py

pause
