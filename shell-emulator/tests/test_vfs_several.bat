@echo off
rem VFS: несколько файлов, включая двоичный
call "%~dp0_env.bat"
echo VFS: несколько файлов, включая двоичный
%PYTHON% "%EMULATOR%" --vfs "%VFS%\several.zip" --script "%SCRIPTS%\vfs_save.txt"
