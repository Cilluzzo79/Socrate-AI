@echo off
echo ===================================
echo  MEMVID CHAT TELEGRAM DEBUGGER
echo ===================================
echo.

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate

REM Run the debug script
echo Running Telegram document selection debugger...
python debug_telegram_select.py

echo.
echo Debug completed! Check telegram_debug.log for details.
echo.

pause
