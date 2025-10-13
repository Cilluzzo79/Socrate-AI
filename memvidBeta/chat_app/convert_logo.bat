@echo off
echo.
echo ========================================
echo   SOCRATE AI - LOGO CONVERTER
echo ========================================
echo.

cd /d "%~dp0"
cd utils

python convert_logo.py

echo.
echo ========================================
echo.
echo Premi un tasto per chiudere...
pause > nul
