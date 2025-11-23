@echo off
echo ========================================
echo   Trailing Stop Bot - BNB/USDT
echo ========================================
echo.

cd /d "%~dp0"

echo Iniciando GUI del bot...
python trailing_stop_bot_gui.py

if errorlevel 1 (
    echo.
    echo Error al ejecutar el bot.
    echo Verifica que Python y las dependencias esten instaladas.
    echo.
    pause
)
