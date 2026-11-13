@echo off
rem Демонстрация этапа 1: запуск визуализатора с разными конфигурациями.
rem Интерпретатор можно задать переменной окружения PYTHON.
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set APP=%~dp0..\src\visualizer.py
set CONFIGS=%~dp0configs
rem Диаграммы не открываются в браузере (--no-show), а только сохраняются в папку output
if "%PYTHON%"=="" if exist "%~dp0..\.venv\Scripts\python.exe" set "PYTHON=%~dp0..\.venv\Scripts\python.exe"
if "%PYTHON%"=="" (
    where python3.14 >nul 2>nul && (set "PYTHON=python3.14") || (set "PYTHON=python")
)

echo ===== Конфигурация по умолчанию (config.yaml) =====
pushd "%~dp0.."
%PYTHON% "%APP%" --no-show
echo [код возврата: %ERRORLEVEL%]
popd
echo.

echo ===== Несуществующий файл конфигурации =====
%PYTHON% "%APP%" --no-show -c "%CONFIGS%\no_such_file.yaml"
echo [код возврата: %ERRORLEVEL%]
echo.

for %%F in ("%CONFIGS%\*.yaml") do (
    echo ===== %%~nxF =====
    %PYTHON% "%APP%" --no-show -c "%%F"
    call echo [код возврата: %%ERRORLEVEL%%]
    echo.
)

echo ===== Модульные тесты =====
%PYTHON% -m unittest discover -s "%~dp0." -v
echo [код возврата: %ERRORLEVEL%]
