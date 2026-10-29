@echo off
rem Общие настройки для тестовых скриптов
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set EMULATOR=%~dp0..\emulator.py
set SCRIPTS=%~dp0..\scripts
set VFS=%~dp0..\vfs
if not "%PYTHON%"=="" goto :eof
where python3.14 >nul 2>nul && (set "PYTHON=python3.14") && goto :eof
set PYTHON=python
