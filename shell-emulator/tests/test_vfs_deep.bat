@echo off
rem VFS: не менее 3 уровней файлов и папок
call "%~dp0_env.bat"
echo VFS: не менее 3 уровней файлов и папок
%PYTHON% "%EMULATOR%" --vfs "%VFS%\deep.zip" --script "%SCRIPTS%\vfs_save.txt"
