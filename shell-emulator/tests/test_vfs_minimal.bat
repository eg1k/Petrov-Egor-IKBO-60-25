@echo off
rem VFS: минимальная (один файл)
call "%~dp0_env.bat"
echo VFS: минимальная (один файл)
%PYTHON% "%EMULATOR%" --vfs "%VFS%\minimal.zip" --script "%SCRIPTS%\vfs_save.txt"
