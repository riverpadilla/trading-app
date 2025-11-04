@echo off
echo 🤖 Iniciando Bot de Trading - Interfaz Grafica
echo =============================================

:: Activar entorno virtual si existe
if exist ".venv\Scripts\activate.bat" (
    echo Activando entorno virtual...
    call .venv\Scripts\activate.bat
) else (
    echo Usando Python del sistema...
)

:: Ejecutar la interfaz grafica
echo Ejecutando interfaz grafica...
python trading_bot_gui.py

if errorlevel 1 (
    echo.
    echo ❌ Error al ejecutar la interfaz grafica
    echo.
    echo Intentando metodo alternativo...
    ".venv\Scripts\python.exe" trading_bot_gui.py
)

echo.
echo Presiona cualquier tecla para continuar...
pause >nul