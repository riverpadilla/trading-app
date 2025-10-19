# 🤖 Bot de Trading BNBUSDT - Documentación

## 📋 Descripción General

Este bot de trading utiliza análisis técnico para realizar backtesting automatizado del par BNBUSDT. El sistema analiza datos históricos de velas de 1 segundo desde Binance y ejecuta una estrategia basada en tres indicadores técnicos principales.

## 🎯 Estrategia de Trading

### Indicadores Utilizados:
1. **RSI (Relative Strength Index)** - Mide la velocidad y magnitud de los cambios de precio
2. **Medias Móviles (MA9 y MA21)** - Identifica tendencias mediante cruces
3. **MACD** - Detecta cambios de momentum

### Lógica de Entrada (COMPRA):
- **Condición**: Al menos 2 de los 3 indicadores deben ser alcistas
- **RSI**: Salida de zona de sobreventa (< 30)
- **MA**: Cruce alcista de MA9 sobre MA21
- **MACD**: Cruce alcista de línea MACD sobre línea de señal

### Lógica de Salida (VENTA):
- **Condición**: Al menos 2 de los 3 indicadores bajistas O stop loss
- **RSI**: Entrada en zona de sobrecompra (> 70)
- **MA**: Cruce bajista de MA9 bajo MA21
- **MACD**: Cruce bajista de línea MACD bajo línea de señal
- **Stop Loss**: 2% de pérdida desde el precio de entrada

## 🏗️ Estructura del Sistema

### Archivos Principales:

1. **`binance_downloader.py`** - Descarga datos históricos desde Binance
2. **`trading_bot.py`** - Motor principal del bot (versión consola)
3. **`trading_bot_gui.py`** - Interfaz gráfica del bot
4. **`test_setup.py`** - Verificación de dependencias

### Clases Principales:

#### `TechnicalIndicators`
- Calcula RSI, medias móviles y MACD
- Métodos estáticos para fácil reutilización

#### `TradingStrategy`
- Implementa la lógica de entrada y salida
- Genera señales basadas en los indicadores
- Incluye gestión de riesgo con stop loss

#### `BacktestEngine`
- Ejecuta el backtesting con los datos históricos
- Simula operaciones de compra y venta
- Calcula comisiones y P&L
- Genera estadísticas de rendimiento

#### `TradingBot`
- Clase principal que coordina todo el sistema
- Carga datos, ejecuta estrategia y genera reportes

## 🚀 Cómo Usar el Sistema

### 1. Descargar Datos Históricos

```bash
python binance_downloader.py
```

Esto descargará 20,000 velas de 1 segundo de BNBUSDT y creará un archivo CSV.

### 2. Ejecutar Bot (Versión Consola)

```bash
python trading_bot.py
```

### 3. Ejecutar Bot (Interfaz Gráfica)

```bash
python trading_bot_gui.py
```

## ⚙️ Configuración de Parámetros

### Parámetros Modificables:

- **Capital Inicial**: Cantidad en USDT para invertir
- **RSI Sobreventa**: Umbral inferior del RSI (default: 30)
- **RSI Sobrecompra**: Umbral superior del RSI (default: 70)
- **Stop Loss**: Porcentaje de pérdida máxima (default: 2%)
- **Comisión**: Porcentaje de comisión por operación (default: 0.1%)

### En el código:
```python
# En TradingStrategy.__init__()
self.rsi_oversold = 30
self.rsi_overbought = 70

# En BacktestEngine.__init__()
self.commission = 0.001  # 0.1%

# En TradingStrategy._check_stop_loss()
stop_loss_pct = 0.02  # 2%
```

## 📊 Interpretación de Resultados

### Métricas Principales:

- **Capital Inicial/Final**: Dinero al inicio y final del período
- **Retorno Total**: Porcentaje de ganancia/pérdida
- **Total de Operaciones**: Número de trades ejecutados
- **Tasa de Éxito**: Porcentaje de operaciones rentables
- **Ganancia/Pérdida Promedio**: Rendimiento promedio por operación
- **Comisiones Totales**: Costos de transacción

### Ejemplo de Resultados:
```
💰 Capital inicial: $1,000.00 USDT
💰 Capital final: $996.26 USDT
📈 Retorno total: -0.37%
🔄 Total de operaciones: 1
🎯 Tasa de éxito: 0.0%
```

## 📁 Archivos Generados

1. **`binance_BNBUSDT_1s_[timestamp].csv`** - Datos históricos descargados
2. **`backtest_results_[timestamp].csv`** - Detalle de todas las operaciones

## 🔧 Personalización Avanzada

### Modificar Estrategia:

Para cambiar la estrategia, edita el método `generate_signals()` en la clase `TradingStrategy`:

```python
# Ejemplo: Cambiar a solo 1 indicador necesario
buy_signals = sum([rsi_buy, ma_bullish, macd_bullish])
if buy_signals >= 1:  # Cambiar de 2 a 1
    # Ejecutar compra
```

### Agregar Nuevos Indicadores:

1. Añadir método en `TechnicalIndicators`
2. Calcular en `generate_signals()`
3. Incluir en la lógica de decisión

### Ejemplo - Agregar Bandas de Bollinger:
```python
@staticmethod
def bollinger_bands(prices, period=20, std_dev=2):
    ma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = ma + (std * std_dev)
    lower = ma - (std * std_dev)
    return upper, ma, lower
```

## 🐛 Solución de Problemas

### Error: "No such file or directory"
- Verificar que el archivo CSV existe
- Ejecutar primero `binance_downloader.py`

### Error: "ModuleNotFoundError"
- Instalar dependencias: `pip install pandas python-binance matplotlib numpy`

### Bot no realiza operaciones:
- Verificar que los datos cubren suficiente volatilidad
- Revisar parámetros de los indicadores
- Comprobar que los indicadores generan señales

### Rendimiento bajo:
- Ajustar parámetros de RSI
- Modificar períodos de medias móviles
- Revisar configuración de stop loss

## 📈 Optimización de Parámetros

### Backtesting con Diferentes Configuraciones:

```python
# Probar diferentes configuraciones
configurations = [
    {'rsi_oversold': 25, 'rsi_overbought': 75},
    {'rsi_oversold': 35, 'rsi_overbought': 65},
    # ... más configuraciones
]

for config in configurations:
    bot = TradingBot()
    bot.strategy.rsi_oversold = config['rsi_oversold']
    bot.strategy.rsi_overbought = config['rsi_overbought']
    results = bot.run_backtest()
    # Comparar resultados
```

## ⚠️ Consideraciones Importantes

1. **Este es un sistema de backtesting**, no para trading en vivo
2. **Los resultados pasados no garantizan rendimientos futuros**
3. **Siempre considera comisiones y slippage en trading real**
4. **Usa este sistema solo para análisis y educación**
5. **Nunca inviertas más de lo que puedes permitirte perder**

## 🎯 Estrategia Híbrida Mejorada (NUEVA)

### 🆕 Actualización Octubre 2025

Se implementó una estrategia híbrida mejorada que combina las mejores características de todas las estrategias desarrolladas:

#### Características Principales:
- **RSI Multi-nivel**: Umbrales dinámicos (20, 25, 35) y (75, 80)
- **Bandas de Bollinger**: Detección de sobrecompra/sobreventa
- **MACD**: Confirmación de momentum
- **Filtro temporal**: 45 segundos entre operaciones
- **Scoring inteligente**: Sistema de puntuación para decisiones

#### 🚀 Nueva Mejora - Salida por Variación Absoluta:
- **Condición**: Cierra posición cuando `abs(precio_actual - precio_entrada) >= 1.2 USDT`
- **Funciona como**: Stop-loss y take-profit dinámico en términos absolutos
- **Beneficio**: Protege contra movimientos de precio significativos independientemente del porcentaje

#### Resultados del Backtest:
- **Operaciones**: 172 trades
- **Tasa de éxito**: 52.3%
- **Activaciones por precio**: 20 salidas por variación >= 1.2 USDT
- **Tiempo de ejecución**: ~5 segundos

#### Acceso:
- Disponible en la GUI como "🎯 Híbrida Mejorada (Recomendada)"
- Ejecutable desde `hybrid_fast_bot.py`

## 🔮 Próximas Mejoras

- [ ] Implementar más indicadores técnicos
- [ ] Agregar análisis de volatilidad
- [ ] Incluir gestión de posición variable
- [ ] Crear gráficos interactivos
- [ ] Implementar optimización automática de parámetros
- [ ] Añadir análisis de drawdown
- [ ] Crear alertas de condiciones de mercado

## 📞 Soporte

Para reportar bugs o sugerir mejoras, documenta:
1. Versión de Python utilizada
2. Archivo de datos usado
3. Configuración de parámetros
4. Error específico o comportamiento inesperado

---

**¡Feliz Trading! 🚀📈**