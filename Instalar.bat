@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
title Instalador Kahoot Bot
cd /d "%~dp0"

echo ==============================================
echo    INSTALADOR - KAHOOT BOT  (v3)
echo ==============================================
echo.

REM --- 1. Buscar un Python que FUNCIONE (ignora el atajo falso de Microsoft Store) ---
set "PY="
call :trypy
REM Solo vale si Python imprime "KOK" (el atajo falso de la Store no imprime eso)
set "_o="
del "%TEMP%\kpy.txt" >nul 2>nul
%* -c "import venv,sys;print('KOK' if sys.version_info>=(3,9) else 'NO')" >"%TEMP%\kpy.txt" 2>nul
if exist "%TEMP%\kpy.txt" set /p _o=<"%TEMP%\kpy.txt"
if "!_o!"=="KOK" set "PY=%*"
exit /b 0
