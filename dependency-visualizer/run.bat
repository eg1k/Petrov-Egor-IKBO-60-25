@echo off
rem Запуск визуализатора. Аргументы передаются программе, например: run.bat -c config.yaml
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set ROOT=%~dp0
if not exist "%ROOT%.venv\Scripts\python.exe" (
    echo Создание виртуального окружения .venv...
    python -m venv "%ROOT%.venv" || exit /b 1
    "%ROOT%.venv\Scripts\python.exe" -m pip install -q -r "%ROOT%requirements.txt" || exit /b 1
)
"%ROOT%.venv\Scripts\python.exe" "%ROOT%src\visualizer.py" %*
