@echo off
echo.
echo ========================================
echo   UPDATE FORMATTER WITH LOGO
echo ========================================
echo.

cd /d "%~dp0"
cd utils

python update_formatter_logo.py

echo.
pause
