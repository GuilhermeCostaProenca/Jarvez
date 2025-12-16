@echo off
setlocal
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ================================
echo        JARVEZ BOOTSTRAP
echo ================================
echo.

if exist ".env" (
    echo [Jarvez] Carregando .env...
    for /f "usebackq tokens=1* delims==" %%a in (`findstr /r "^[A-Za-z_][A-Za-z0-9_]*=" .env`) do set "%%a=%%b"
)

if not defined JARVEZ_DB_PATH set "JARVEZ_DB_PATH=%CD%\data\jarvez.db"

if not exist "logs" mkdir "logs"

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
start "" /min cmd /c "call .venv\Scripts\activate.bat && python -u -m jarvez.brain > logs\brain.log 2>&1"

echo [Jarvez] Waiting brain bootstrap...
timeout /t 2 /nobreak >nul

echo.
echo [Jarvez] Starting API/panel at http://127.0.0.1:8888 ...
start "" /min cmd /c "call .venv\Scripts\activate.bat && python -m uvicorn jarvez.api.server:app --host 127.0.0.1 --port 8888 --log-level info > logs\panel.log 2>&1"

echo.
echo [Jarvez] Launching body (Godot)...

if exist "godot_body\bin\JarvezOrb.exe" (
    start "" "godot_body\bin\JarvezOrb.exe"
    echo [Jarvez] Body launched.
) else (
    echo [ALERTA] JarvezOrb.exe nao encontrado em:
    echo    godot_body\bin\JarvezOrb.exe
    echo Abra o projeto Godot (godot_body) no editor e gere o executavel, ou instale o Godot 4 e rode a cena principal.
    if exist "%ProgramFiles%\Godot\Godot.exe" (
        start "" "%ProgramFiles%\Godot\Godot.exe" "godot_body\project.godot"
    )
)

echo.
echo [Jarvez] Bootstrap finished.
echo (Este terminal pode ser fechado)
pause
endlocal
