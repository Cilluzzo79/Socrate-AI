@echo off
REM Start Socrate AI in async development mode
REM Requires: Redis running on localhost:6379

echo ======================================
echo SOCRATE AI - ASYNC DEVELOPMENT MODE
echo ======================================
echo.

REM Check if Redis is running
echo [1/4] Checking Redis...
redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Redis not running!
    echo.
    echo Please start Redis first:
    echo   Option 1: docker run -d -p 6379:6379 redis:7-alpine
    echo   Option 2: docker-compose -f docker-compose.dev.yml up redis -d
    echo.
    pause
    exit /b 1
)
echo [OK] Redis is running

REM Check Python environment
echo.
echo [2/4] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)
echo [OK] Python found

REM Initialize database
echo.
echo [3/4] Initializing database...
python init_db.py
if errorlevel 1 (
    echo [ERROR] Database initialization failed!
    pause
    exit /b 1
)

REM Start services
echo.
echo [4/4] Starting services...
echo.
echo This will open 3 windows:
echo   1. Celery Worker (async task processor)
echo   2. Flask API Server (web interface)
echo   3. This console (for monitoring)
echo.

REM Start Celery worker in new window
start "Celery Worker" cmd /k "celery -A celery_config worker --loglevel=info --concurrency=2"

REM Wait a bit for worker to start
timeout /t 3 /nobreak >nul

REM Start Flask API in new window
start "Flask API" cmd /k "python api_server.py"

REM Wait for Flask to start
timeout /t 3 /nobreak >nul

echo.
echo ======================================
echo ALL SERVICES STARTED!
echo ======================================
echo.
echo Web UI:        http://localhost:5000
echo Health Check:  http://localhost:5000/api/health
echo.
echo Celery Worker: Running in separate window
echo Flask API:     Running in separate window
echo.
echo Press Ctrl+C in those windows to stop services
echo.
echo To test async processing:
echo   python test_async_processing.py
echo.
pause
