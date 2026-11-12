@echo off
rem Демонстрация этапа 1: запуск визуализатора с разными конфигурациями.
rem Интерпретатор можно задать переменной окружения PYTHON.
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set APP=%~dp0..\src\visualizer.py
set CONFIGS=%~dp0configs
if "%PYTHON%"=="" if exist "%~dp0..\.venv\Scripts\python.exe" set "PYTHON=%~dp0..\.venv\Scripts\python.exe"
if "%PYTHON%"=="" (
    where python3.14 >nul 2>nul && (set "PYTHON=python3.14") || (set "PYTHON=python")
)

echo ===== Конфигурация по умолчанию (config.yaml) =====
pushd "%~dp0.."
%PYTHON% "%APP%"
echo [код возврата: %ERRORLEVEL%]
popd
echo.

echo ===== Несуществующий файл конфигурации =====
%PYTHON% "%APP%" -c "%CONFIGS%\no_such_file.yaml"
echo [код возврата: %ERRORLEVEL%]
echo.

for %%F in ("%CONFIGS%\*.yaml") do (
    echo ===== %%~nxF =====
    %PYTHON% "%APP%" -c "%%F"
    call echo [код возврата: %%ERRORLEVEL%%]
    echo.
)
