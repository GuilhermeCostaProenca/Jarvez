@echo off
setlocal
cd /d "%~dp0"

rem Activate venv if present
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

rem Launch brain (hidden/minimized)
start "" /min python -u -m jarvez.brain

rem Give the brain a moment to boot the WS
timeout /t 2 /nobreak >nul

rem Launch the Godot-built body (expected at godot_body\bin\JarvezOrb.exe)
if exist "godot_body\bin\JarvezOrb.exe" (
    start "" "godot_body\bin\JarvezOrb.exe"
) else (
    echo [Jarvez] Godot body not found at godot_body\bin\JarvezOrb.exe
)

endlocal
