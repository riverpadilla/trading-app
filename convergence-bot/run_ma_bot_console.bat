@echo off
echo Iniciando MA Convergence Bot (Consola)...
echo ================================================
echo Este bot puede ejecutarse independientemente de VS Code
echo Presiona Ctrl+C para detener
echo ================================================

REM Cambiar a directorio del bot
cd /d "G:\Repos\Trading App\convergence-bot"

REM Activar entorno virtual
call "..\\.venv\Scripts\Activate.bat"

REM Ejecutar bot de consola
python "ma_convergence_console.py"

echo ================================================
echo Bot finalizado. Presiona cualquier tecla para cerrar.
pause