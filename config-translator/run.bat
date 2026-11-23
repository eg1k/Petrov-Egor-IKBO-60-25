@echo off
python -X utf8 "%~dp0src\main.py" %*
exit /b %errorlevel%
