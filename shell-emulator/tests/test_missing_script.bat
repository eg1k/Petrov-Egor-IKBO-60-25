@echo off
rem Стартовый скрипт не существует
call "%~dp0_env.bat"
echo Стартовый скрипт не существует
%PYTHON% "%EMULATOR%" --script "%SCRIPTS%\no_such_file.txt"
