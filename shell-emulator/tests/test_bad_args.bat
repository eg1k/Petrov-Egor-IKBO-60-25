@echo off
rem Неизвестный параметр командной строки
call "%~dp0_env.bat"
echo Неизвестный параметр командной строки
%PYTHON% "%EMULATOR%" --unknown value
pause
