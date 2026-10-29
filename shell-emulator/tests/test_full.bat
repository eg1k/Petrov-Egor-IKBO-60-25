@echo off
rem Все команды этапов 1-3 с VFS из нескольких уровней
call "%~dp0_env.bat"
echo Все команды этапов 1-3 с VFS из нескольких уровней
%PYTHON% "%EMULATOR%" --vfs "%VFS%\deep.zip" --script "%SCRIPTS%\startup.txt"
