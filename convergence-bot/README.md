# 🤖 MA Convergence Trading Bot

Bot de trading automatizado basado en convergencias de medias móviles con configuración optimizada.

## 📁 Contenido de la Carpeta

### 📊 **Archivos Principales del Bot:**
- `ma_convergence_bot.py` - Clase principal del bot con lógica de convergencias MA
- `ma_convergence_gui.py` - Interfaz gráfica completa para monitoreo
- `ma_convergence_console.py` - Versión de consola para ejecución 24/7
- `ma_convergence_live_bot.py` - Bot original de línea de comandos

### 🚀 **Archivos de Ejecución (.bat):**
- `run_ma_bot_gui.bat` - Ejecutar GUI independiente de VS Code
- `run_ma_console_bot.bat` - Ejecutar versión consola independiente

### 📈 **Archivos de Resultados:**
- `ma_convergence_results_*.csv` - Resultados de backtests y pruebas

## ⚙️ **Configuración Optimizada**

El bot usa parámetros científicamente optimizados basados en test de matriz de 400 combinaciones:

- **MA1 (MA7)**: Umbral = 0.0375
- **MA2 (MA25)**: Umbral = 0.052 
- **Retorno Esperado**: +0.466% por sesión
- **Win Rate**: 100% (estrategia ultra-selectiva)
- **Frecuencia**: ~1 operación por sesión de 5.5 horas

## 🎯 **Cómo Usar**

### **Opción 1: GUI (Recomendada para monitoreo)**
1. Doble-click en `run_ma_bot_gui.bat`
2. Click en "🔗 Test Conexión" para verificar Binance
3. Click en "🎯 Config Óptima" para cargar parámetros optimizados
4. Click en "🚀 INICIAR BOT" para comenzar trading

### **Opción 2: Consola (Para ejecución 24/7)**
1. Doble-click en `run_ma_console_bot.bat`
2. El bot iniciará automáticamente con configuración optimizada
3. Presiona Ctrl+C para detener

### **Opción 3: Desde VS Code**
```bash
cd "G:/Repos/Trading App/convergence-bot"
python ma_convergence_gui.py
# o
python ma_convergence_console.py
```

## 💰 **Configuración de Binance**

### **Testnet (Por defecto - Seguro para pruebas):**
- ✅ Dinero virtual ($10,000 USDT)
- ✅ Sin riesgo real
- ✅ API keys incluidas en el código

### **Cuenta Real (Opcional):**
1. Cambiar `testnet=True` a `testnet=False`
2. Reemplazar API keys con las de tu cuenta real
3. ⚠️ **IMPORTANTE**: Empezar con cantidades pequeñas

## 📊 **Características**

### **Análisis Técnico:**
- Medias móviles MA7 y MA25 con análisis de pendientes
- Detección automática de convergencias
- RSI y MACD como indicadores auxiliares
- Take profit automático (0.2%) y stop loss (-0.1%)

### **Interfaz GUI:**
- Gráfico de precios en tiempo real
- Monitor de balances USDT/BNB
- Log detallado de operaciones
- Controles para iniciar/detener bot
- Actualización de parámetros en vivo

### **Seguridad:**
- Ejecuta en Binance Testnet por defecto
- Validación de parámetros antes de iniciar
- Manejo de errores sin crashes
- Cierre limpio con Ctrl+C

## 🔧 **Requisitos**

- Python 3.8+
- Librerías: pandas, numpy, talib, python-binance, matplotlib, tkinter
- Conexión a internet para datos de Binance

## 📈 **Resultados Históricos**

Basado en backtests con datos reales de BNBUSDT:
- **Mejor configuración**: MA1=0.0375, MA2=0.052
- **Retorno promedio**: +0.466% por sesión
- **Estrategia**: Ultra-selectiva, alta precisión
- **Drawdown máximo**: Mínimo debido a stop loss

## ⚠️ **Disclaimer**

Este bot es para fines educativos y de prueba. El trading de criptomonedas implica riesgos significativos. Siempre:
- Prueba primero en testnet
- Usa solo capital que puedas permitirte perder
- Monitorea las operaciones regularmente
- Los resultados pasados no garantizan resultados futuros

---
**Desarrollado**: Octubre 2025  
**Versión**: 1.0 Optimizada  
**Testnet**: Binance Spot Test Network  