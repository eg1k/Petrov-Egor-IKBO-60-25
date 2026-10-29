@echo off
rem Задан только путь к VFS
call "%~dp0_env.bat"
echo Задан только путь к VFS
%PYTHON% "%EMULATOR%" --vfs "%~dp0..\vfs\minimal.zip"
