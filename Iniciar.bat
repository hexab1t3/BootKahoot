@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo Primero ejecuta Instalar.bat
    pause
    exit /b 1
)
REM "keyboard" necesita permisos de administrador para detectar la tecla K
net session >nul 2>&1
if errorlevel 1 (
    powershell -NoProfile -Command "Start-Process -FilePath '%~dp0Iniciar.bat' -Verb RunAs"
    exit /b
)
start "" ".venv\Scripts\pythonw.exe" "KahootBotGUI.py"
