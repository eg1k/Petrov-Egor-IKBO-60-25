@echo off
rem Задан только стартовый скрипт
call "%~dp0_env.bat"
echo Задан только стартовый скрипт
%PYTHON% "%EMULATOR%" --script "%SCRIPTS%\startup.txt"
