@echo off
rem Заданы оба параметра
call "%~dp0_env.bat"
echo Заданы оба параметра
%PYTHON% "%EMULATOR%" --vfs "%~dp0..\vfs\minimal.zip" --script "%SCRIPTS%\minimal.txt"
