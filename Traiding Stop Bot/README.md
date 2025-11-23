# Trailing Stop Bot - BNB/USDT

Bot de trading automatizado que ejecuta una estrategia de compra/venta alternada usando órdenes **Trailing Stop Market** en Binance.

## 🎯 Características

### Estrategia de Trading
1. **Venta Inicial**: El bot inicia vendiendo una cantidad especificada de BNB (ej. 1 BNB)
2. **Trailing Stop Buy**: Crea una orden de compra con trailing stop que se activa cuando el precio baja
3. **Trailing Stop Sell**: Tras completar la compra, crea una orden de venta con trailing stop que se activa cuando el precio sube
4. **Ciclo Continuo**: Alterna automáticamente entre compra y venta

### Interfaz Gráfica (GUI) - MEJORADA ✨
- ✅ **Saldos en Tiempo Real**: Visualiza BNB y USDT directamente desde tu cuenta Binance
- ✅ **Precio Actual BNB/USDT**: Actualización constante del precio de mercado
- ✅ **Gráfico de Velas 1 min**: Visualiza el movimiento del precio en tiempo real (últimos 60 minutos)
- ✅ **RSI 7 periodos**: Indicador técnico para detectar sobrecompra/sobreventa
- ✅ **RSI 14 periodos**: Indicador técnico estándar para análisis
- ✅ Configuración de parámetros de trading
- ✅ Control de inicio/detención del bot
- ✅ Seguimiento en tiempo real de P&L (Profit & Loss)
- ✅ Log detallado de actividad
- ✅ Visualización de estadísticas de trading
- ✅ Soporte para Testnet y producción
- ✅ **Interfaz con pestañas**: Control y Gráficos separados para mejor organización

## 📋 Requisitos

- Python 3.8+
- Cuenta de Binance (o Testnet para pruebas)
- API Keys de Binance

### Dependencias
```bash
pip install python-binance matplotlib pandas numpy mplfinance
```

O instalar desde el archivo requirements.txt:
```bash
pip install -r requirements.txt
```

## 🚀 Instalación

1. Clona o descarga este repositorio
2. Instala las dependencias:
```bash
pip install python-binance
```

3. Configura tus API Keys en la interfaz gráfica

## 💻 Uso

### Opción 1: Ejecutar con archivo .bat (Windows)
```bash
run_trailing_stop_bot.bat
```

### Opción 2: Ejecutar directamente con Python
```bash
python trailing_stop_bot_gui.py
```

## ⚙️ Configuración

### Parámetros del Bot

1. **Cantidad BNB Inicial**: Cantidad de BNB a vender inicialmente (ej. 0.1, 1.0)
2. **Trailing % Compra**: Porcentaje de trailing para órdenes de compra (ej. 1.0 = 1%)
3. **Trailing % Venta**: Porcentaje de trailing para órdenes de venta (ej. 1.0 = 1%)

### Credenciales API

- **API Key**: Tu clave API de Binance
- **API Secret**: Tu clave secreta de Binance
- **Testnet**: Marca esta opción para usar Binance Testnet (recomendado para pruebas)

## 📊 Seguimiento P&L y Análisis Técnico

### Pestaña Control
La GUI muestra en tiempo real:
- **💰 Saldos en Binance**: BNB y USDT actuales en tu cuenta
- **Precio Actual BNB/USDT**: Valor de mercado en tiempo real
- **Total Trades**: Número total de operaciones ejecutadas
- **Trades Exitosos**: Operaciones completadas con éxito
- **P&L Realizado**: Ganancia/pérdida de operaciones cerradas
- **P&L Total**: Ganancia/pérdida incluyendo posición actual
- **Precios**: Último precio de compra y venta

### Pestaña Gráficos 📈
Análisis técnico visual en tiempo real:
- **Gráfico de Precio**: Movimiento del precio BNB/USDT (últimos 60 minutos, 1 min cada vela)
- **RSI 7**: Indicador de impulso a corto plazo
  - > 70: Zona de sobrecompra (rojo)
  - < 30: Zona de sobreventa (verde)
- **RSI 14**: Indicador de impulso estándar
  - > 70: Zona de sobrecompra (rojo)
  - < 30: Zona de sobreventa (verde)

Los gráficos se actualizan automáticamente cada 60 segundos y también puedes actualizarlos manualmente.

## 🔧 Funcionamiento Técnico

### Stop Loss Limit (Simulación de Trailing Stop)

**Para Compra (BUY)**:
- Se establece un precio de stop **por debajo** del precio actual (según el % configurado)
- Se activa cuando el precio **baja** hasta ese nivel
- Se ejecuta la compra automáticamente
- Ejemplo: Precio actual $100, trailing 1% → stop en $99

**Para Venta (SELL)**:
- Se establece un precio de stop **por encima** del precio actual (según el % configurado)
- Se activa cuando el precio **sube** hasta ese nivel
- Se ejecuta la venta automáticamente
- Ejemplo: Precio actual $100, trailing 1% → stop en $101

**Nota**: En Binance Testnet se usa STOP_LOSS_LIMIT en lugar de TRAILING_STOP_MARKET por compatibilidad. El comportamiento es similar pero el stop es fijo, no dinámico.

### Ciclo de Operación

```
[INICIO] 
   ↓
Vender BNB (Market Order)
   ↓
Crear Trailing Stop BUY
   ↓
Esperar ejecución → COMPRA ejecutada
   ↓
Crear Trailing Stop SELL
   ↓
Esperar ejecución → VENTA ejecutada
   ↓
[REPETIR desde Trailing Stop BUY]
```

## 🛡️ Seguridad

### Recomendaciones
1. **Usa Testnet primero**: Prueba el bot en Testnet antes de usar fondos reales
2. **API Keys con permisos limitados**: Solo habilita trading spot, NO habilites retiros
3. **Restricción por IP**: Configura whitelist de IPs en Binance
4. **Cantidades pequeñas**: Empieza con cantidades pequeñas para validar

### Obtener Credenciales Testnet
1. Visita: https://testnet.binance.vision/
2. Inicia sesión con GitHub
3. Genera API Keys

## 📁 Estructura de Archivos

```
Traiding Stop Bot/
│
├── trailing_stop_bot.py          # Lógica principal del bot
├── trailing_stop_bot_gui.py      # Interfaz gráfica
├── run_trailing_stop_bot.bat     # Script para ejecutar (Windows)
└── README.md                      # Este archivo
```

## ⚠️ Disclaimer

Este bot es una herramienta educativa y experimental. El trading de criptomonedas conlleva riesgos significativos. 

**NO ME HAGO RESPONSABLE POR:**
- Pérdidas financieras
- Errores en la ejecución de órdenes
- Problemas con la API de Binance
- Cambios en las condiciones del mercado

**Siempre:**
- Realiza pruebas exhaustivas en Testnet
- Entiende completamente cómo funciona antes de usar fondos reales
- Nunca inviertas más de lo que puedes permitirte perder
- Monitorea activamente las operaciones del bot

## 🐛 Solución de Problemas

### Error: "Import binance.client could not be resolved"
```bash
pip install python-binance
```

### Error: "API key format invalid"
- Verifica que hayas copiado correctamente las API Keys
- Asegúrate de no tener espacios al inicio o final
- Confirma que las keys correspondan al entorno correcto (Testnet vs Producción)

### El bot no ejecuta órdenes
- Verifica tu conexión a internet
- Confirma que tengas saldo suficiente
- Revisa los logs en la GUI para mensajes de error
- Verifica que las API Keys tengan permisos de trading

### P&L no se actualiza
- El bot actualiza cada 5 segundos
- Verifica que el bot esté en estado "EJECUTANDO"
- Revisa el log por posibles errores

## 📞 Soporte

Para problemas o preguntas:
1. Revisa el log de actividad en la GUI
2. Verifica la documentación de Binance API
3. Asegúrate de estar usando la última versión del bot

## 📝 Changelog

### v2.0.0 (Noviembre 2025) - VERSIÓN MEJORADA
- ✅ **NUEVO**: Visualización de saldos BNB y USDT en tiempo real desde Binance
- ✅ **NUEVO**: Precio actual BNB/USDT en pantalla principal
- ✅ **NUEVO**: Gráfico de precio (velas 1 minuto) - últimos 60 minutos
- ✅ **NUEVO**: Indicador RSI 7 periodos con zonas de sobrecompra/sobreventa
- ✅ **NUEVO**: Indicador RSI 14 periodos con zonas de sobrecompra/sobreventa
- ✅ **NUEVO**: Interfaz con pestañas (Control y Gráficos)
- ✅ **NUEVO**: Botón para actualizar saldos manualmente
- ✅ **NUEVO**: Actualización automática de gráficos cada 60 segundos
- ✅ Mejoras visuales con emojis y colores

### v1.0.0 (Noviembre 2025)
- ✅ Implementación inicial
- ✅ Soporte para Trailing Stop Market
- ✅ GUI completa con tkinter
- ✅ Tracking de P&L en tiempo real
- ✅ Soporte para Testnet y producción
- ✅ Sistema de logging detallado

## 📄 Licencia

Este proyecto es de código abierto y está disponible para uso educativo y de investigación.

---

**⚡ Happy Trading! (Responsablemente)** 🚀
