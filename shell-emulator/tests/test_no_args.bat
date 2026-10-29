@echo off
rem Запуск без параметров
call "%~dp0_env.bat"
echo Запуск без параметров
%PYTHON% "%EMULATOR%"
