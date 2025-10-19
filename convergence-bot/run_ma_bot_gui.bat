@echo off
echo Iniciando MA Convergence Bot GUI...
echo ================================================

REM Cambiar a directorio del bot
cd /d "G:\Repos\Trading App\convergence-bot"

REM Activar entorno virtual
call "..\\.venv\Scripts\Activate.bat"

REM Ejecutar bot
python "ma_convergence_gui.py"
echo ================================================
echo Bot finalizado. Presiona cualquier tecla para cerrar.
pause 