@echo off
echo Activando entorno virtual...
call .venv\Scripts\activate.bat

echo Ejecutando descargador de Binance...
python binance_downloader.py

echo.
echo Presiona cualquier tecla para continuar...
pause >nul