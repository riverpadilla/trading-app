# Guía de Uso - Trailing Stop Bot v2.0

## 🚀 Inicio Rápido

### 1. Instalación del Ambiente Virtual

```powershell
# Navegar al directorio del proyecto
cd "c:\Users\padillar\source\repos\riverpadilla\trading-app"

# Activar ambiente virtual (si aún no está activado)
.\.venv\Scripts\Activate.ps1

# Verificar que las dependencias estén instaladas
pip list
```

### 2. Ejecutar el Bot

**Opción A: Con archivo .bat (Recomendado)**
```powershell
cd "Traiding Stop Bot"
.\run_trailing_stop_bot.bat
```

**Opción B: Con Python directamente**
```powershell
# Desde la raíz del proyecto
.\.venv\Scripts\python.exe "Traiding Stop Bot\trailing_stop_bot_gui.py"
```

## 📋 Uso de la Interfaz

### Pestaña "⚙ Control"

#### 1. Saldos en Tiempo Real (💰)
- **BNB**: Muestra tu balance actual de BNB en Binance
- **USDT**: Muestra tu balance actual de USDT en Binance  
- **Precio BNB/USDT**: Precio actual del par
- **Botón 🔄 Actualizar Saldos**: Fuerza una actualización inmediata

💡 **Tip**: Los saldos se actualizan automáticamente cada 3 segundos cuando el bot está activo.

#### 2. Credenciales de API (🔑)
- **API Key**: Ingresa tu clave API de Binance
- **API Secret**: Ingresa tu clave secreta (se oculta con asteriscos)
- **☑ Usar Testnet**: Marca para usar Testnet (recomendado para pruebas)

🔒 **Seguridad**: 
- Las credenciales de Testnet ya vienen preconfiguradas
- Obtén credenciales de Testnet en: https://testnet.binance.vision/

#### 3. Configuración del Bot (⚙)
- **Cantidad BNB inicial**: Cuántos BNB vender al inicio (ej: 0.1, 1.0)
- **Trailing % Compra**: Porcentaje de seguimiento para compras (ej: 1.0 = 1%)
- **Trailing % Venta**: Porcentaje de seguimiento para ventas (ej: 1.0 = 1%)

📌 **Recomendaciones**:
- Trailing entre 0.5% y 2% para mercados normales
- Trailing más alto (2-3%) para mercados volátiles
- Cantidad inicial pequeña para pruebas (0.1 BNB)

#### 4. Control (🎮)
- **▶ Iniciar Bot**: Comienza la estrategia de trading
- **⬛ Detener Bot**: Detiene el bot y cancela órdenes pendientes
- **Estado**: Muestra el estado actual del bot

🚨 **Estados posibles**:
- `DETENIDO`: Bot no está ejecutándose
- `SELLING`: Ejecutando venta inicial
- `WAITING_BUY`: Esperando activación de orden de compra
- `BUYING`: Comprando BNB
- `WAITING_SELL`: Esperando activación de orden de venta

#### 5. Estadísticas y P&L (📊)
- **Total Trades**: Número total de operaciones
- **Exitosos**: Operaciones completadas exitosamente
- **P&L Realizado**: Ganancia/pérdida de operaciones cerradas
  - 🟢 Verde: Ganancia
  - 🔴 Rojo: Pérdida
- **P&L Total**: Incluye posición actual
- **Último precio compra/venta**: Precios de las últimas operaciones

#### 6. Log de Actividad (📝)
Muestra en tiempo real:
- Mensajes informativos (negro)
- Operaciones exitosas (verde)
- Advertencias (naranja)
- Errores (rojo)

### Pestaña "📊 Gráficos"

#### Gráfico 1: Precio BNB/USDT
- **Línea azul**: Movimiento del precio
- **Punto rojo**: Precio actual
- **Eje X**: Tiempo (últimos 60 minutos)
- **Eje Y**: Precio en USDT

📈 **Interpretación**:
- Tendencia alcista: Línea sube consistentemente
- Tendencia bajista: Línea baja consistentemente
- Lateral: Movimiento horizontal

#### Gráfico 2: RSI 7 periodos (Corto Plazo)
- **Línea morada**: Valor del RSI
- **Zona roja (>70)**: Sobrecompra - posible corrección a la baja
- **Zona verde (<30)**: Sobreventa - posible rebote al alza
- **Línea gris (50)**: Nivel neutral

🎯 **Cómo usarlo**:
- RSI > 70: El activo puede estar sobrevalorado, considera vender
- RSI < 30: El activo puede estar subvalorado, considera comprar
- RSI cruzando 50: Cambio de momentum

#### Gráfico 3: RSI 14 periodos (Estándar)
- **Línea naranja**: Valor del RSI
- Misma interpretación que RSI 7
- Más suave y menos reactivo que RSI 7

💡 **Estrategia combinada**:
- RSI 7 y RSI 14 ambos > 70: Fuerte señal de sobrecompra
- RSI 7 y RSI 14 ambos < 30: Fuerte señal de sobreventa
- Divergencias: RSI baja mientras precio sube (o viceversa) = posible reversión

#### Botón 🔄 Actualizar Gráficos
- Actualiza manualmente los gráficos
- También se actualizan automáticamente cada 60 segundos

## 🔄 Flujo de Operación Típico

1. **Inicio**:
   ```
   - Abre la GUI
   - Verifica saldos en Binance (pestaña Control)
   - Revisa precio actual
   ```

2. **Configuración**:
   ```
   - Establece cantidad BNB inicial (ej: 0.1)
   - Define trailing % (ej: 1.0% para ambos)
   - Verifica que Testnet esté marcado
   ```

3. **Análisis Previo** (Opcional):
   ```
   - Ve a pestaña Gráficos
   - Click en 🔄 Actualizar Gráficos
   - Revisa RSI 7 y RSI 14
   - Evalúa tendencia del precio
   ```

4. **Activación**:
   ```
   - Vuelve a pestaña Control
   - Click en ▶ Iniciar Bot
   - Observa el log de actividad
   ```

5. **Monitoreo**:
   ```
   - Revisa el estado en tiempo real
   - Observa P&L
   - Cambia a pestaña Gráficos periódicamente
   - Analiza RSI antes de decisiones manuales
   ```

6. **Detención**:
   ```
   - Click en ⬛ Detener Bot
   - Verifica que órdenes pendientes se cancelaron
   - Revisa P&L final
   ```

## 📊 Ejemplo de Uso con Análisis Técnico

### Escenario: Mercado en Tendencia Alcista

**Observación en Gráficos**:
- Precio subiendo constantemente
- RSI 7: 65 (acercándose a sobrecompra)
- RSI 14: 58 (neutral-alcista)

**Acción**:
- ✅ Buen momento para iniciar el bot
- El trailing stop de venta capturará ganancias si el precio sigue subiendo
- El trailing stop de compra esperará una corrección

### Escenario: RSI en Zona de Sobreventa

**Observación en Gráficos**:
- RSI 7: 25 (sobreventa)
- RSI 14: 28 (sobreventa)
- Precio bajó fuertemente

**Acción**:
- ✅ Excelente momento para iniciar
- Alta probabilidad de rebote
- El bot comprará en la recuperación

### Escenario: RSI en Zona de Sobrecompra

**Observación en Gráficos**:
- RSI 7: 75 (sobrecompra)
- RSI 14: 72 (sobrecompra)
- Precio en máximos

**Acción**:
- ⚠️ Espera una corrección
- Riesgo de comprar caro
- Considera trailing % más alto (2-3%)

## ⚙️ Ajustes Avanzados

### Trailing Stop Dinámico

**Para mercado volátil**:
```
Trailing % Compra: 2.0%
Trailing % Venta: 2.0%
```
- Más espacio para fluctuaciones
- Menos activaciones falsas
- Ganancias potencialmente mayores

**Para mercado estable**:
```
Trailing % Compra: 0.5%
Trailing % Venta: 0.5%
```
- Captura movimientos pequeños
- Más operaciones
- Mejor para scalping

### Cantidad de BNB

**Conservador** (Pruebas):
```
Cantidad BNB: 0.1
```

**Moderado**:
```
Cantidad BNB: 0.5
```

**Agresivo**:
```
Cantidad BNB: 1.0+
```

## 🆘 Solución de Problemas

### Los saldos muestran $0.00
1. Click en 🔄 Actualizar Saldos
2. Verifica que las API Keys sean correctas
3. Confirma que estés en el entorno correcto (Testnet/Producción)

### Los gráficos no se actualizan
1. Click manual en 🔄 Actualizar Gráficos
2. Verifica conexión a internet
3. Confirma que las API Keys tengan permisos de lectura

### El bot no ejecuta órdenes
1. Revisa el log de actividad (mensajes en rojo)
2. Verifica saldo suficiente de BNB
3. Confirma que las API Keys tengan permisos de trading
4. Asegúrate de estar en Testnet si usas credenciales de prueba

### RSI muestra valores extraños
- Normal durante alta volatilidad
- Espera 15+ minutos para valores estables
- Actualiza los gráficos manualmente

## 💡 Tips y Mejores Prácticas

1. **Siempre revisa los gráficos antes de iniciar** el bot
2. **Monitorea el RSI** periódicamente durante la operación
3. **Usa Testnet** hasta dominar la estrategia
4. **Empieza con cantidades pequeñas** (0.1 BNB)
5. **Ajusta trailing %** según volatilidad del mercado
6. **Revisa el log** constantemente para entender el comportamiento
7. **Actualiza los gráficos** antes de tomar decisiones manuales
8. **Combina RSI 7 y RSI 14** para confirmación de señales
9. **No operes con RSI extremos** (muy alto o muy bajo por tiempo prolongado)
10. **Ten paciencia**: El trailing stop necesita movimiento de precio para activarse

## 📱 Atajos de Teclado

La GUI no tiene atajos de teclado nativos, pero puedes:
- `Alt+Tab`: Cambiar entre pestañas (Control/Gráficos)
- `Ctrl+C` en terminal: Detener la aplicación completamente

## 📈 Análisis Post-Operación

Después de detener el bot, revisa:
1. **P&L Realizado**: ¿Fue rentable?
2. **Total Trades**: ¿Cuántas operaciones se ejecutaron?
3. **Gráficos**: ¿Cómo se movió el precio durante la sesión?
4. **RSI**: ¿Hubo zonas de sobrecompra/sobreventa que afectaron?
5. **Log**: ¿Hay mensajes de error o advertencia?

Usa esta información para ajustar:
- Cantidad de BNB inicial
- Porcentajes de trailing
- Momento de entrada (según RSI)

---

**¡Feliz Trading! 🚀** (Recuerda: Practica en Testnet primero)
