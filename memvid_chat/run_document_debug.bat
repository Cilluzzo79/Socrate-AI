@echo off
echo ===================================
echo  MEMVID CHAT DOCUMENT DEBUGGER
echo ===================================
echo.

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate

REM Run the debug script
echo Running document debugger...
python debug_documents.py

pause
