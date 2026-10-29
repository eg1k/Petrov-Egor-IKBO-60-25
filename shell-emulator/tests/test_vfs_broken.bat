@echo off
rem VFS: файл не является ZIP-архивом
call "%~dp0_env.bat"
echo VFS: файл не является ZIP-архивом
%PYTHON% "%EMULATOR%" --vfs "%VFS%\broken.zip"
