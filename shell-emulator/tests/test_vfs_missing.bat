@echo off
rem VFS: архив не существует
call "%~dp0_env.bat"
echo VFS: архив не существует
%PYTHON% "%EMULATOR%" --vfs "%VFS%\no_such.zip"
