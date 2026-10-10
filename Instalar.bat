@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
title Instalador Kahoot Bot
cd /d "%~dp0"

echo ==============================================
echo    INSTALADOR - KAHOOT BOT
echo ==============================================
echo.

REM --- 1. Buscar un Python que FUNCIONE (ignora el atajo falso de Microsoft Store) ---
set "PY="
call :trypy py -3
if not defined PY call :trypy python
if not defined PY call :trypy ""%LOCALAPPDATA%\Programs\Python\Python312\python.exe""
if not defined PY call :trypy ""%LOCALAPPDATA%\Programs\Python\Python313\python.exe""

if not defined PY (
    echo [1/4] Python no encontrado. Instalando Python 3.12...
    where winget >nul 2>nul
    if errorlevel 1 (
        echo.
        echo No se pudo instalar Python automaticamente.
        echo Instalalo desde https://www.python.org/downloads/
        echo ^(marca "Add Python to PATH"^) y ejecuta este instalador otra vez.
        pause
        exit /b 1
    )
    winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
    call :trypy ""%LOCALAPPDATA%\Programs\Python\Python312\python.exe""
    if not defined PY (
        echo.
        echo Python se instalo pero hay que reiniciar este instalador.
        echo Cierra esta ventana y haz doble clic en Instalar.bat otra vez.
        pause
        exit /b 1
    )
) else (
    echo [1/4] Python encontrado.
)

REM --- 2. Entorno virtual ---
echo [2/4] Creando entorno aislado...
if not exist ".venv\Scripts\python.exe" (
    %PY% -m venv .venv
    if errorlevel 1 goto :fail
)

REM --- 3. Dependencias ---
echo [3/4] Instalando librerias (puede tardar un minuto)...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :fail

REM --- 4. Acceso directo en el escritorio ---
echo [4/4] Creando acceso directo en el Escritorio...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\Kahoot Bot.lnk'); $s.TargetPath='%~dp0Iniciar.bat'; $s.WorkingDirectory='%~dp0'; $s.WindowStyle=7; $s.Save()"

echo.
echo ==============================================
echo    LISTO! Abre "Kahoot Bot" desde el Escritorio
echo ==============================================
echo.
set /p RUN="Abrir ahora? (S/N): "
if /i "!RUN!"=="S" call "%~dp0Iniciar.bat"
exit /b 0

:fail
echo.
echo *** Hubo un error en la instalacion. Revisa los mensajes de arriba. ***
pause
exit /b 1

:trypy
%* -c "import venv, sys; sys.exit(0 if sys.version_info >= (3,9) else 1)" >nul 2>nul
if not errorlevel 1 set "PY=%*"
exit /b 0
