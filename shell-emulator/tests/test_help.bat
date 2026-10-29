@echo off
rem Справка по параметрам
call "%~dp0_env.bat"
echo Справка по параметрам
%PYTHON% "%EMULATOR%" --help
pause
