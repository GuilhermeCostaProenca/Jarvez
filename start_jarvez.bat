@echo off
setlocal
cd /d "%~dp0"

echo ================================
echo        JARVEZ BOOTSTRAP
echo ================================
echo.

rem Activate venv if present
if exist ".venv\Scripts\activate.bat" (
    echo [Jarvez] Activating virtualenv...
    call ".venv\Scripts\activate.bat"
) else (
    echo [ERRO] Virtualenv nao encontrado em .venv
    pause
    exit /b 1
)

echo.
echo [Jarvez] Starting brain...
start "" /min python -u -m jarvez.brain

echo [Jarvez] Waiting brain bootstrap...
timeout /t 2 /nobreak >nul

echo.
echo [Jarvez] Launching body (Godot)...

if exist "godot_body\bin\JarvezOrb.exe" (
    start "" "godot_body\bin\JarvezOrb.exe"
    echo [Jarvez] Body launched.
) else (
    echo [ERRO] JarvezOrb.exe nao encontrado em:
    echo godot_body\bin\JarvezOrb.exe
    echo.
    pause
    exit /b 1
)

echo.
echo [Jarvez] Bootstrap finished.
echo (Este terminal pode ser fechado)
pause
endlocal
