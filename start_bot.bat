@echo off
chcp 65001 > nul
echo ==========================================
echo  The Dawn Project - Telegram Bot
echo ==========================================
echo.
echo Checking .env file...

if not exist .env (
    echo [ERROR] .env file not found!
    echo.
    echo Please create .env file based on .env.example
    echo.
    pause
    exit
)

echo [OK] .env file found
echo.

REM Check and activate virtual environment
if exist .venv\Scripts\activate.bat (
    echo [INFO] Virtual environment detected
    echo [INFO] Activating virtual environment...
    call .venv\Scripts\activate.bat
    echo.
)

echo Starting bot...
echo.

REM Run bot
python bot.py

if errorlevel 1 (
    echo.
    echo [ERROR] Bot crashed!
    echo.
    echo Possible reasons:
    echo 1. Dependencies not installed in venv
    echo 2. Invalid data in .env file
    echo 3. Code error (see output above)
    echo.
    echo Try installing dependencies:
    echo .venv\Scripts\python.exe -m pip install -r requirements.txt
    echo.
    pause
)

:end
