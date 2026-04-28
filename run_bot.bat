@echo off
REM Simple bot launcher without Russian text

if exist .venv\Scripts\python.exe (
    echo Running with virtual environment...
    .venv\Scripts\python.exe bot.py
) else (
    echo Running with system Python...
    python bot.py
)

pause
