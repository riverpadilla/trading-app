"""Modulo generador de gráficos para scalping, usando datos de Binance y TA-Lib para indicadores técnicos.
Configurado para intervalo de 1s y sombreado de zonas RSI extremas."""
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import mplfinance as mpf
import requests
import pandas as pd
import talib  # pylint: disable=no-member

# --- Parámetros de la interfaz ---
SYMBOLS = ["BNBUSDT", "USDTARS"]
INTERVAL = "1s"  # Fijado a 1s para scalping
TIEMPO_OPTIONS = {
    "10 min": 600,   # 600 velas de 1s = 10 minutos
    "20 min": 1200,  # 1200 velas de 1s = 20 minutos  
    "30 min": 1800,  # 1800 velas de 1s = 30 minutos
    "1 hora": 3600   # 3600 velas de 1s = 1 hora
}
BINANCE_URL = "https://api.binance.com/api/v3/klines"

"""Funciones para calcular indicadores técnicos usando TA-Lib."""
def sma(values, window):
    # TA-Lib SMA
    return pd.Series(talib.SMA(values.values, timeperiod=window), index=values.index) # pylint: disable=no-member

""" --- Indicadores técnicos con TA-Lib ---"""
def rsi(values, window=14):
    # TA-Lib espera un array numpy
    return pd.Series(talib.RSI(values.values, timeperiod=window), index=values.index) # pylint: disable=no-member

""" --- Indicadores técnicos con TA-Lib ---"""
def macd(values, fast=12, slow=26, signal=9):
    # TA-Lib MACD
    macd_line, signal_line, _ = talib.MACD(values.values, fastperiod=fast, slowperiod=slow, signalperiod=signal) # pylint: disable=no-member
    # Devuelve como pd.Series para mantener compatibilidad
    return pd.Series(macd_line, index=values.index), pd.Series(signal_line, index=values.index)

""" --- Obtener datos históricos de Binance ---"""
def obtener_historico_binance(symbol, interval, limit=600):
    all_data = []
    
    # Para 1s, Binance limita a 1000 velas por llamada
    if interval == "1s" and limit > 1000:
        # Hacer múltiples llamadas para obtener más datos
        calls_needed = min(4, (limit + 999) // 1000)  # Máximo 4 llamadas para evitar rate limit
        current_end_time = None
        
        for i in range(calls_needed):
            params = {"symbol": symbol.upper(), "interval": interval, "limit": 1000}
            if current_end_time:
                params["endTime"] = current_end_time
            
            try:
                response = requests.get(BINANCE_URL, params=params, timeout=10)
                data = response.json()
                if data and len(data) > 0:
                    all_data.extend(data)
                    # Usar el timestamp del primer elemento para la próxima llamada
                    current_end_time = int(data[0][0]) - 1
                else:
                    break
            except Exception as e:
                print(f"Error en llamada {i+1}: {e}")
                break
        
        # Remover duplicados y ordenar
        seen = set()
        unique_data = []
        for item in all_data:
            if item[0] not in seen:
                seen.add(item[0])
                unique_data.append(item)
        
        # Ordenar por timestamp y tomar los últimos 'limit' elementos
        unique_data.sort(key=lambda x: x[0])
        data = unique_data[-limit:] if len(unique_data) > limit else unique_data
    else:
        # Llamada única para otros intervalos o límites pequeños
        params = {"symbol": symbol.upper(), "interval": interval, "limit": min(limit, 1000)}
        response = requests.get(BINANCE_URL, params=params, timeout=10)
        data = response.json()
    
    df = pd.DataFrame(
        data,
        columns=[
            "Open time", "Open", "High", "Low", "Close", "Volume",
            "Close time", "Quote asset volume", "Number of trades",
            "Taker buy base asset volume", "Taker buy quote asset volume", "Ignore"
        ]
    )
    df["Open time"] = pd.to_datetime(df["Open time"], unit="ms")
    df["Close time"] = pd.to_datetime(df["Close time"], unit="ms")
    
    # Ajustar zona horaria a UTC-5 (Colombia) - Restar 5 horas directamente
    df["Open time"] = df["Open time"] - pd.Timedelta(hours=5)
    df["Close time"] = df["Close time"] - pd.Timedelta(hours=5)
    
    df["Open"] = df["Open"].astype(float)
    df["High"] = df["High"].astype(float)
    df["Low"] = df["Low"].astype(float)
    df["Close"] = df["Close"].astype(float)
    df["Volume"] = df["Volume"].astype(float)
    df.set_index("Close time", inplace=True)
    
    print(f"Obtenidos {len(df)} registros de datos")  # Debug info
    return df

""" --- Procesar indicadores y señales ---"""
def procesar_indicadores(df):
    df["MA3"] = sma(df["Close"], 3)
    df["MA7"] = sma(df["Close"], 7)
    df["MA14"] = sma(df["Close"], 14)
    df["MA25"] = sma(df["Close"], 25)
    df["MA50"] = sma(df["Close"], 50)
    df["MA99"] = sma(df["Close"], 99)
    df["RSI"] = rsi(df["Close"], 14)
    df["MACD"], df["Signal"] = macd(df["Close"])
    return df



""" --- Función para calcular líneas de tendencia de MA para addplot ---"""
def calcular_lineas_tendencia_ma_individual_addplot(df, periodo_ma, umbral_pendiente, es_segunda_ma=False):
    """Calcula líneas de tendencia de una MA específica y retorna datos para addplot"""
    import numpy as np
    
    # Verificar si se deben mostrar las líneas de tendencia (con verificación de None)
    if es_segunda_ma and mostrar_lineas_tendencia_ma2 and not mostrar_lineas_tendencia_ma2.get():
        return []
    elif not es_segunda_ma and mostrar_lineas_tendencia_ma1 and not mostrar_lineas_tendencia_ma1.get():
        return []
    
    ma_values = df[periodo_ma].dropna()
    
    if len(ma_values) < 10:  # Necesitamos suficientes datos
        return []
    
    # Calcular pendientes móviles para detectar cambios
    ventana = 3  # Ventana más pequeña para mayor sensibilidad
    pendientes_locales = []
    indices_validos = []
    
    for i in range(ventana, len(ma_values) - ventana):
        # Calcular pendiente en una ventana pequeña alrededor del punto
        inicio_idx = i - ventana // 2
        fin_idx = i + ventana // 2
        
        x_vals = np.arange(inicio_idx, fin_idx + 1)
        y_vals = ma_values.iloc[inicio_idx:fin_idx + 1].values
        
        if len(y_vals) > 1:
            pendiente_local = np.polyfit(x_vals, y_vals, 1)[0]
            pendientes_locales.append(pendiente_local)
            indices_validos.append(i)
    
    if not pendientes_locales:
        return []
    
    # Detectar cambios significativos de pendiente
    segmentos_tendencia = []
    inicio_segmento = 0
    pendiente_anterior = pendientes_locales[0]
    
    threshold_cambio = 0.00005  # Umbral para detectar cambios de pendiente
    min_longitud = 5  # Longitud mínima del segmento
    
    for i in range(1, len(pendientes_locales)):
        pendiente_actual = pendientes_locales[i]
        cambio_pendiente = abs(pendiente_actual - pendiente_anterior)
        
        # Si hay un cambio significativo o llegamos al final
        if cambio_pendiente > threshold_cambio or i == len(pendientes_locales) - 1:
            fin_segmento = i - 1 if i < len(pendientes_locales) - 1 else i
            
            # Verificar longitud mínima del segmento
            if fin_segmento - inicio_segmento >= min_longitud:
                inicio_idx = indices_validos[inicio_segmento]
                fin_idx = indices_validos[fin_segmento]
                
                inicio_timestamp = ma_values.index[inicio_idx]
                fin_timestamp = ma_values.index[fin_idx]
                inicio_valor = ma_values.iloc[inicio_idx]
                fin_valor = ma_values.iloc[fin_idx]
                
                # Calcular pendiente promedio del segmento
                pendiente_segmento = np.mean(pendientes_locales[inicio_segmento:fin_segmento + 1])
                
                segmentos_tendencia.append({
                    'inicio_timestamp': inicio_timestamp,
                    'fin_timestamp': fin_timestamp,
                    'inicio_valor': inicio_valor,
                    'fin_valor': fin_valor,
                    'pendiente': pendiente_segmento,
                    'longitud': fin_idx - inicio_idx + 1
                })
            
            inicio_segmento = i
            pendiente_anterior = pendiente_actual
    
    # Preparar datos para addplot basados en el umbral
    lineas_addplot = []
    
    for segmento in segmentos_tendencia:
        # Determinar color según la pendiente usando umbral dinámico
        if segmento['pendiente'] > umbral_pendiente:  # Pendiente alcista significativa
            color_tendencia = 'lime'
        elif segmento['pendiente'] < -umbral_pendiente:  # Pendiente bajista significativa
            color_tendencia = 'red'
        else:  # Pendiente lateral/neutral
            color_tendencia = 'yellow'
        
        # Crear serie para la línea de tendencia
        line_data = pd.Series(index=df.index, dtype=float)
        
        # Encontrar índices en el DataFrame original
        mask = (df.index >= segmento['inicio_timestamp']) & (df.index <= segmento['fin_timestamp'])
        indices_segmento = df.index[mask]
        
        if len(indices_segmento) >= 2:
            # Crear línea recta entre puntos
            inicio_val = segmento['inicio_valor']
            fin_val = segmento['fin_valor']
            
            # Interpolar valores para toda la línea
            for i, timestamp in enumerate(indices_segmento):
                ratio = i / (len(indices_segmento) - 1) if len(indices_segmento) > 1 else 0
                line_data[timestamp] = inicio_val + (fin_val - inicio_val) * ratio
        
        # Usar diferente estilo para la segunda MA
        line_width = 1.0 if es_segunda_ma else 1.5
        alpha = 0.7 if es_segunda_ma else 0.9
        
        lineas_addplot.append({
            'data': line_data,
            'color': color_tendencia,
            'width': line_width,
            'alpha': alpha
        })
    
    return lineas_addplot

""" --- Función original mantenida para compatibilidad ---"""
def calcular_lineas_tendencia_ma_individual(axes, df, periodo_ma, es_segunda_ma=False):
    """Calcula y muestra líneas de tendencia de una MA específica basadas en cambios significativos de pendiente"""
    import matplotlib.dates as mdates
    import numpy as np
    
    # Verificar si se deben mostrar las líneas de tendencia
    if es_segunda_ma and not mostrar_lineas_tendencia_ma2.get():
        return []
    elif not es_segunda_ma and not mostrar_lineas_tendencia_ma1.get():
        return []
    
    ma_values = df[periodo_ma].dropna()
    
    if len(ma_values) < 10:  # Necesitamos suficientes datos
        return []
    
    # Calcular pendientes móviles para detectar cambios
    ventana = 3  # Ventana más pequeña para mayor sensibilidad
    pendientes_locales = []
    indices_validos = []
    
    for i in range(ventana, len(ma_values) - ventana):
        # Calcular pendiente en una ventana pequeña alrededor del punto
        inicio_idx = i - ventana // 2
        fin_idx = i + ventana // 2
        
        x_window = np.arange(fin_idx - inicio_idx + 1)
        y_window = ma_values.iloc[inicio_idx:fin_idx+1].values
        
        # Calcular pendiente usando regresión lineal
        if len(x_window) > 1 and not np.any(np.isnan(y_window)):
            pendiente = np.polyfit(x_window, y_window, 1)[0]
            pendientes_locales.append(pendiente)
            indices_validos.append(i)
    
    if len(pendientes_locales) < 3:
        return []
    
    # Enfoque alternativo: dividir en segmentos de tamaño fijo y luego analizar cada uno
    longitud_segmento = max(20, len(ma_values) // 10)  # Segmentos adaptativos
    cambios_tendencia = [0]
    
    # Crear puntos de división cada cierto número de datos
    for i in range(longitud_segmento, len(ma_values), longitud_segmento):
        cambios_tendencia.append(i)
    
    # También agregar detección de cambios significativos
    umbral_cambio = max(np.std(pendientes_locales) * 0.8, 0.00005)
    
    for i in range(1, len(pendientes_locales)):
        cambio_pendiente = abs(pendientes_locales[i] - pendientes_locales[i-1])
        cambio_direccion = (pendientes_locales[i-1] > 0 and pendientes_locales[i] < 0) or \
                          (pendientes_locales[i-1] < 0 and pendientes_locales[i] > 0)
        
        if (cambio_pendiente > umbral_cambio or cambio_direccion) and indices_validos[i] not in cambios_tendencia:
            cambios_tendencia.append(indices_validos[i])
    
    # Ordenar y eliminar duplicados
    cambios_tendencia = sorted(list(set(cambios_tendencia)))
    
    cambios_tendencia.append(len(ma_values) - 1)  # Terminar al final
    
    # Crear segmentos de líneas de tendencia
    segmentos_tendencia = []
    for i in range(len(cambios_tendencia) - 1):
        inicio_idx = cambios_tendencia[i]
        fin_idx = cambios_tendencia[i + 1]
        
        if fin_idx > inicio_idx:
            # Calcular pendiente del segmento completo
            x_segment = np.arange(fin_idx - inicio_idx + 1)
            y_segment = ma_values.iloc[inicio_idx:fin_idx+1].values
            
            if len(x_segment) > 1 and not np.any(np.isnan(y_segment)):
                pendiente_segmento = np.polyfit(x_segment, y_segment, 1)[0]
                
                inicio_timestamp = ma_values.index[inicio_idx]
                fin_timestamp = ma_values.index[fin_idx]
                inicio_valor = ma_values.iloc[inicio_idx]
                fin_valor = ma_values.iloc[fin_idx]
                
                segmentos_tendencia.append({
                    'inicio_timestamp': inicio_timestamp,
                    'fin_timestamp': fin_timestamp,
                    'inicio_valor': inicio_valor,
                    'fin_valor': fin_valor,
                    'pendiente': pendiente_segmento,
                    'longitud': fin_idx - inicio_idx + 1
                })
    
    # Dibujar las líneas de tendencia
    for i, segmento in enumerate(segmentos_tendencia):
        # Determinar color según la pendiente usando umbral fijo
        umbral_actual = 0.0002  # Umbral fijo
        if segmento['pendiente'] > umbral_actual:  # Pendiente alcista significativa
            color_tendencia = 'lime'
        elif segmento['pendiente'] < -umbral_actual:  # Pendiente bajista significativa
            color_tendencia = 'red'
        else:  # Pendiente lateral/neutral
            color_tendencia = 'yellow'
        
        # Convertir timestamps a números para matplotlib
        inicio_date = mdates.date2num(segmento['inicio_timestamp'])
        fin_date = mdates.date2num(segmento['fin_timestamp'])
        
        # Usar diferente estilo para la segunda MA
        if es_segunda_ma:
            linestyle = ':'  # Líneas punteadas más densas para MA2
            linewidth = 2.5
        else:
            linestyle = '--'  # Líneas punteadas normales para MA1
            linewidth = 3
        
        # Dibujar línea de tendencia recta basada en la regresión del segmento
        axes[0].plot([inicio_date, fin_date], 
                    [segmento['inicio_valor'], segmento['fin_valor']], 
                    color=color_tendencia, linewidth=linewidth, alpha=0.8, linestyle=linestyle)
    
    # Etiquetas de MA eliminadas por solicitud del usuario
    
    return segmentos_tendencia

def calcular_lineas_tendencia_ma(axes, df):
    """Calcula y muestra líneas de tendencia de MA(s) habilitadas"""
    segmentos_ma1 = []
    segmentos_ma2 = []
    
    # Procesar primera MA si está habilitada
    if mostrar_ma.get():
        periodo_seleccionado = ma_periodo.get()
        segmentos_ma1 = calcular_lineas_tendencia_ma_individual(axes, df, periodo_seleccionado, False)
    
    # Procesar segunda MA si está habilitada
    if mostrar_ma2.get():
        periodo_seleccionado2 = ma2_periodo.get()
        segmentos_ma2 = calcular_lineas_tendencia_ma_individual(axes, df, periodo_seleccionado2, True)
    
    return segmentos_ma1, segmentos_ma2

""" --- Función helper para obtener umbral dinámico ---"""
def obtener_umbral_dinamico():
    """Retorna el umbral dinámico o un valor por defecto"""
    try:
        return umbral_pendiente.get() if umbral_pendiente else 0.0002
    except:
        return 0.0002

""" --- Función para detectar convergencias entre MAs (sin RSI) ---"""
def marcar_convergencias_doble_ma_rsi(axes, df, segmentos_ma1, segmentos_ma2):
    """Detecta y marca convergencias específicas entre tendencias de las dos MAs"""
    import matplotlib.dates as mdates
    import numpy as np
    
    # Verificar que al menos tenemos una MA y RSI, y que ambas MAs estén habilitadas
    if not (mostrar_ma.get() and mostrar_ma2.get()) or not segmentos_ma1 or not segmentos_ma2:
        return []
    
    convergencias_detectadas = []
    
    # Función para obtener la tendencia en un timestamp específico
    def obtener_tendencia_en_timestamp(segmentos, timestamp):
        for segmento in segmentos:
            if segmento['inicio_timestamp'] <= timestamp <= segmento['fin_timestamp']:
                umbral_actual = obtener_umbral_dinamico()  # Umbral dinámico
                if segmento['pendiente'] > umbral_actual:
                    return 'alcista'
                elif segmento['pendiente'] < -umbral_actual:
                    return 'bajista'
                else:
                    return 'lateral'
        return None
    
    # Función para detectar cambios de dirección en MA2
    def detectar_cambios_direccion_ma2():
        cambios = []
        umbral_actual = obtener_umbral_dinamico()  # Umbral dinámico
        for i in range(1, len(segmentos_ma2)):
            segmento_anterior = segmentos_ma2[i-1]
            segmento_actual = segmentos_ma2[i]
            
            # Clasificar tendencias usando umbral fijo
            tend_anterior = 'alcista' if segmento_anterior['pendiente'] > umbral_actual else ('bajista' if segmento_anterior['pendiente'] < -umbral_actual else 'lateral')
            tend_actual = 'alcista' if segmento_actual['pendiente'] > umbral_actual else ('bajista' if segmento_actual['pendiente'] < -umbral_actual else 'lateral')
            
            # Detectar cambios significativos
            if (tend_anterior != 'bajista' and tend_actual == 'bajista') or \
               (tend_anterior != 'alcista' and tend_actual == 'alcista'):
                cambios.append({
                    'timestamp': segmento_actual['inicio_timestamp'],
                    'direccion_nueva': tend_actual,
                    'direccion_anterior': tend_anterior
                })
        return cambios
    
    # Obtener cambios de dirección en MA2
    cambios_ma2 = detectar_cambios_direccion_ma2()
    
    # Para cada cambio de dirección en MA2, verificar condiciones
    for cambio in cambios_ma2:
        timestamp = cambio['timestamp']
        
        # Verificar RSI en ese momento
        try:
            rsi_valor = df.loc[timestamp, 'RSI']
        except KeyError:
            # Si no hay dato exacto, buscar el más cercano
            idx_cercano = df.index.get_indexer([timestamp], method='nearest')[0]
            timestamp_cercano = df.index[idx_cercano]
            rsi_valor = df.loc[timestamp_cercano, 'RSI']
            timestamp = timestamp_cercano
        
        # Obtener tendencia de MA1 en ese momento
        tendencia_ma1 = obtener_tendencia_en_timestamp(segmentos_ma1, timestamp)
        
        # CONDICIÓN 1: MA1 bajista + MA2 cambia a bajista (sin RSI)
        if (tendencia_ma1 == 'bajista' and 
            cambio['direccion_nueva'] == 'bajista'):
            
            convergencias_detectadas.append({
                'timestamp': timestamp,
                'tipo': 'VENTA_CONVERGENCIA',
                'rsi': rsi_valor,
                'ma1_tendencia': tendencia_ma1,
                'ma2_cambio': cambio['direccion_nueva'],
                'descripcion': f'MA1↘ + MA2→↘'
            })
        
        # CONDICIÓN 2: MA1 alcista + MA2 cambia a alcista (sin RSI)
        elif (tendencia_ma1 == 'alcista' and 
              cambio['direccion_nueva'] == 'alcista'):
            
            convergencias_detectadas.append({
                'timestamp': timestamp,
                'tipo': 'COMPRA_CONVERGENCIA',
                'rsi': rsi_valor,
                'ma1_tendencia': tendencia_ma1,
                'ma2_cambio': cambio['direccion_nueva'],
                'descripcion': f'MA1↗ + MA2→↗'
            })
    
    # Análisis de pendientes para debugging
    if segmentos_ma1 or segmentos_ma2:
        print("\n[ANALISIS] PENDIENTES DE MA:")
        
        # Obtener todas las pendientes de ambas MAs
        todas_pendientes = []
        if segmentos_ma1:
            pendientes_ma1 = [s['pendiente'] for s in segmentos_ma1]
            todas_pendientes.extend(pendientes_ma1)
            print(f"MA1 - Min: {min(pendientes_ma1):.6f}, Max: {max(pendientes_ma1):.6f}")
        
        if segmentos_ma2:
            pendientes_ma2 = [s['pendiente'] for s in segmentos_ma2]
            todas_pendientes.extend(pendientes_ma2)
            print(f"MA2 - Min: {min(pendientes_ma2):.6f}, Max: {max(pendientes_ma2):.6f}")
        
        if todas_pendientes:
            print(f"GLOBAL - Min: {min(todas_pendientes):.6f}, Max: {max(todas_pendientes):.6f}")
            
            # Contar clasificaciones con umbral dinámico
            umbral_actual = obtener_umbral_dinamico()  # Umbral dinámico
            alcistas = sum(1 for p in todas_pendientes if p > umbral_actual)
            bajistas = sum(1 for p in todas_pendientes if p < -umbral_actual)
            laterales = sum(1 for p in todas_pendientes if -umbral_actual <= p <= umbral_actual)
            
            print(f"Clasificación actual (umbral ±{umbral_actual:.6f}):")
            print(f"  [+] Alcistas: {alcistas} ({alcistas/len(todas_pendientes)*100:.1f}%)")
            print(f"  [-] Bajistas: {bajistas} ({bajistas/len(todas_pendientes)*100:.1f}%)")
            print(f"  ⚪ Laterales: {laterales} ({laterales/len(todas_pendientes)*100:.1f}%)")
    
    # Filtrar señales consecutivas del mismo tipo
    convergencias_filtradas = []
    ultima_senal_tipo = None
    
    for conv in convergencias_detectadas:
        # Solo agregar si es diferente al tipo anterior
        if conv['tipo'] != ultima_senal_tipo:
            convergencias_filtradas.append(conv)
            ultima_senal_tipo = conv['tipo']
        # Si es del mismo tipo que la anterior, se omite
    
    # Dibujar las convergencias filtradas
    for conv in convergencias_filtradas:
        date = mdates.date2num(conv['timestamp'])
        
        if conv['tipo'] == 'VENTA_CONVERGENCIA':
            color = 'darkred'
            simbolo = 'SELL'
            flecha = 'v'
        else:  # COMPRA_CONVERGENCIA
            color = 'darkgreen'
            simbolo = 'BUY'
            flecha = '^'
        
        # Líneas verticales prominentes en los 3 paneles
        for ax in axes:
            ax.axvline(x=date, color=color, linestyle='-', linewidth=4, alpha=0.9)
        
        # Obtener precio actual para posicionar etiqueta
        try:
            precio_actual = df.loc[conv['timestamp'], 'Close']
        except KeyError:
            idx_cercano = df.index.get_indexer([conv['timestamp']], method='nearest')[0]
            precio_actual = df.iloc[idx_cercano]['Close']
        
        # Mostrar etiquetas solo si está habilitado
        if mostrar_etiquetas_convergencia.get():
            # Panel 0 (Velas): Etiqueta principal con precio
            axes[0].annotate(f'{simbolo} CONVERGENCIA MA {flecha}\n${precio_actual:.4f}\n{conv["descripcion"]}', 
                            xy=(date, precio_actual),
                            xytext=(20, 40 if conv['tipo'] == 'COMPRA_CONVERGENCIA' else -60), 
                            textcoords='offset points',
                            bbox=dict(boxstyle='round,pad=0.6', facecolor=color, alpha=0.95, 
                                    edgecolor='white', linewidth=2),
                            fontsize=10, color='white', weight='bold', ha='center',
                            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.2', 
                                          color=color, lw=2))
            
            # Panel 2 (MACD): Información de las MAs
            axes[2].annotate(f'MA1: {conv["ma1_tendencia"]}\nMA2: {conv["ma2_cambio"]}', 
                            xy=(date, 0),
                            xytext=(15, 30 if conv['tipo'] == 'COMPRA_CONVERGENCIA' else -40), 
                            textcoords='offset points',
                            bbox=dict(boxstyle='round,pad=0.4', facecolor=color, alpha=0.9),
                            fontsize=9, color='white', weight='bold', ha='center')
    
    return convergencias_filtradas



""" --- Función para marcar extremos RSI con líneas verticales ---"""
def marcar_extremos_rsi(axes, df):
    """Marca el máximo/mínimo valor de BNB durante cada período continuo que RSI permanece en zona extrema"""
    import matplotlib.dates as mdates
    
    if not mostrar_extremos_rsi.get():
        return
    
    # Función para encontrar períodos continuos
    def encontrar_periodos_continuos(mask):
        """Encuentra períodos continuos donde la máscara es True"""
        periodos = []
        inicio = None
        
        for i, valor in enumerate(mask):
            if valor and inicio is None:
                # Comenzar un nuevo período
                inicio = i
            elif not valor and inicio is not None:
                # Terminar el período actual
                periodos.append((inicio, i-1))
                inicio = None
        
        # Si el período continúa hasta el final
        if inicio is not None:
            periodos.append((inicio, len(mask)-1))
        
        return periodos
    
    # Encontrar períodos continuos de sobrecompra (RSI > 70)
    sobrecompra_mask = df['RSI'] > 70
    periodos_sobrecompra = encontrar_periodos_continuos(sobrecompra_mask.values)
    
    # Marcar el MÁXIMO valor durante cada período de sobrecompra
    for inicio_idx, fin_idx in periodos_sobrecompra:
        periodo_data = df.iloc[inicio_idx:fin_idx+1]
        if len(periodo_data) > 0:
            max_precio = periodo_data['Close'].max()
            max_idx = periodo_data['Close'].idxmax()
            max_date = mdates.date2num(max_idx)
            
            # Línea vertical roja para el máximo del período
            axes[0].axvline(x=max_date, color='red', linestyle='-', linewidth=2, alpha=0.8)
            
            # Etiqueta con el valor máximo
            axes[0].annotate(f'MAX: {max_precio:.4f}', 
                            xy=(max_date, max_precio),
                            xytext=(8, 15), textcoords='offset points',
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.8),
                            fontsize=8, color='white', weight='bold',
                            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.1'))
    
    # Encontrar períodos continuos de sobreventa (RSI < 30)
    sobreventa_mask = df['RSI'] < 30
    periodos_sobreventa = encontrar_periodos_continuos(sobreventa_mask.values)
    
    # Marcar el MÍNIMO valor durante cada período de sobreventa
    for inicio_idx, fin_idx in periodos_sobreventa:
        periodo_data = df.iloc[inicio_idx:fin_idx+1]
        if len(periodo_data) > 0:
            min_precio = periodo_data['Close'].min()
            min_idx = periodo_data['Close'].idxmin()
            min_date = mdates.date2num(min_idx)
            
            # Línea vertical verde para el mínimo del período
            axes[0].axvline(x=min_date, color='green', linestyle='-', linewidth=2, alpha=0.8)
            
            # Etiqueta con el valor mínimo
            axes[0].annotate(f'MIN: {min_precio:.4f}', 
                            xy=(min_date, min_precio),
                            xytext=(8, -25), textcoords='offset points',
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='green', alpha=0.8),
                            fontsize=8, color='white', weight='bold',
                            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.1'))

""" --- Función para marcar convergencias RSI extremo + MACD cruces ---"""
def marcar_convergencias_rsi_macd(axes, df):
    """Marca líneas verticales cuando RSI está en zona extrema Y MACD cruza sobre/bajo la línea de señal"""
    import matplotlib.dates as mdates
    
    if not mostrar_convergencias_rsi_macd.get():
        return
    
    convergencias = []
    
    # Detectar cruces entre MACD y línea de señal
    macd_prev = df['MACD'].shift(1)
    signal_prev = df['Signal'].shift(1)
    
    # Cruce alcista: MACD cruza SOBRE la línea de señal (de abajo hacia arriba)
    # MACD anterior < Signal anterior Y MACD actual >= Signal actual
    cruces_alcistas = (macd_prev < signal_prev) & (df['MACD'] >= df['Signal'])
    
    # Cruce bajista: MACD cruza DEBAJO de la línea de señal (de arriba hacia abajo)
    # MACD anterior > Signal anterior Y MACD actual <= Signal actual
    cruces_bajistas = (macd_prev > signal_prev) & (df['MACD'] <= df['Signal'])
    
    # Combinar todos los cruces
    cruces_macd = cruces_alcistas | cruces_bajistas
    
    # Para cada cruce, verificar si RSI está en zona extrema
    for idx in df[cruces_macd].index:
        rsi_valor = df.loc[idx, 'RSI']
        macd_valor = df.loc[idx, 'MACD']
        signal_valor = df.loc[idx, 'Signal']
        close_valor = df.loc[idx, 'Close']
        
        # Verificar si RSI está en zona extrema
        if rsi_valor > 70 or rsi_valor < 30:
            # Determinar tipo de cruce
            es_cruce_alcista = cruces_alcistas[idx] if idx in cruces_alcistas.index else False
            
            convergencias.append({
                'timestamp': idx,
                'rsi': rsi_valor,
                'macd': macd_valor,
                'signal': signal_valor,
                'close': close_valor,
                'zona_rsi': 'sobrecompra' if rsi_valor > 70 else 'sobreventa',
                'cruce_macd': 'alcista' if es_cruce_alcista else 'bajista'
            })
    
    # Marcar las convergencias en todos los paneles
    for conv in convergencias:
        date = mdates.date2num(conv['timestamp'])
        
        # Determinar color según el tipo de zona RSI
        color = 'red' if conv['zona_rsi'] == 'sobrecompra' else 'green'
        # Determinar estilo según tipo de cruce MACD
        linestyle = '--' if conv['cruce_macd'] == 'alcista' else ':'
        
        # Líneas verticales en los 3 paneles
        for i, ax in enumerate(axes):
            ax.axvline(x=date, color=color, linestyle=linestyle, linewidth=1.5, alpha=0.8)
        
        # Etiquetas específicas en cada panel
        # Panel 0 (Velas): Precio + tipo de señal
        cruce_simbolo = '↗' if conv['cruce_macd'] == 'alcista' else '↘'
        axes[0].annotate(f'${conv["close"]:.4f} {cruce_simbolo}', 
                        xy=(date, conv['close']),
                        xytext=(10, 20), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor=color, alpha=0.8),
                        fontsize=8, color='white', weight='bold')
        
        # Panel 1 (RSI): Valor RSI + zona
        zona_simbolo = 'SC' if conv['zona_rsi'] == 'sobrecompra' else 'SV'
        axes[1].annotate(f'RSI:{conv["rsi"]:.1f} {zona_simbolo}', 
                        xy=(date, conv['rsi']),
                        xytext=(10, 10), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor=color, alpha=0.8),
                        fontsize=8, color='white', weight='bold')
        
        # Panel 2 (MACD): Diferencia MACD-Signal + dirección del cruce
        diferencia = conv['macd'] - conv['signal']
        axes[2].annotate(f'Δ:{diferencia:.4f} {cruce_simbolo}', 
                        xy=(date, conv['macd']),
                        xytext=(10, 15 if conv['macd'] > 0 else -25), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor=color, alpha=0.8),
                        fontsize=8, color='white', weight='bold')
    
    return len(convergencias)

""" --- Función para señales de trading combinadas RSI + MACD + MA ---"""
def marcar_senales_trading_combinadas(axes, df):
    """Detecta señales de compra/venta combinando RSI extremo + MACD cruce + condición de MA"""
    import matplotlib.dates as mdates
    
    if not mostrar_senales_combinadas.get() or not mostrar_ma.get():
        return 0
    
    # Obtener la MA seleccionada
    periodo_seleccionado = ma_periodo.get()
    
    senales = []
    
    # Detectar cruces entre MACD y línea de señal
    macd_prev = df['MACD'].shift(1)
    signal_prev = df['Signal'].shift(1)
    
    # Cruce alcista: MACD cruza SOBRE la línea de señal
    cruces_alcistas = (macd_prev < signal_prev) & (df['MACD'] >= df['Signal'])
    
    # Cruce bajista: MACD cruza DEBAJO de la línea de señal
    cruces_bajistas = (macd_prev > signal_prev) & (df['MACD'] <= df['Signal'])
    
    # Combinar todos los cruces
    cruces_macd = cruces_alcistas | cruces_bajistas
    
    # Para cada cruce, verificar condiciones combinadas
    for idx in df[cruces_macd].index:
        rsi_valor = df.loc[idx, 'RSI']
        macd_valor = df.loc[idx, 'MACD']
        signal_valor = df.loc[idx, 'Signal']
        close_valor = df.loc[idx, 'Close']
        ma_valor = df.loc[idx, periodo_seleccionado]
        
        # Determinar tipo de cruce
        es_cruce_alcista = cruces_alcistas[idx] if idx in cruces_alcistas.index else False
        
        # SEÑAL DE COMPRA: RSI < 30 (sobreventa) + MACD cruce alcista + Precio > MA
        if (rsi_valor < 30 and es_cruce_alcista and close_valor > ma_valor):
            senales.append({
                'timestamp': idx,
                'tipo': 'COMPRA',
                'rsi': rsi_valor,
                'macd': macd_valor,
                'signal': signal_valor,
                'close': close_valor,
                'ma': ma_valor,
                'ma_periodo': periodo_seleccionado,
                'condiciones': f'RSI:{rsi_valor:.1f}<30, MACD↗, Precio>${close_valor:.4f}>${ma_valor:.4f}'
            })
        
        # SEÑAL DE VENTA: RSI > 70 (sobrecompra) + MACD cruce bajista + Precio < MA
        elif (rsi_valor > 70 and not es_cruce_alcista and close_valor < ma_valor):
            senales.append({
                'timestamp': idx,
                'tipo': 'VENTA',
                'rsi': rsi_valor,
                'macd': macd_valor,
                'signal': signal_valor,
                'close': close_valor,
                'ma': ma_valor,
                'ma_periodo': periodo_seleccionado,
                'condiciones': f'RSI:{rsi_valor:.1f}>70, MACD↘, Precio${close_valor:.4f}<${ma_valor:.4f}'
            })
    
    # Marcar las señales en el gráfico
    for senal in senales:
        date = mdates.date2num(senal['timestamp'])
        
        # Colores y símbolos según tipo de señal
        if senal['tipo'] == 'COMPRA':
            color = 'lime'
            simbolo = 'BUY'
            flecha = '^'
            offset_y = 30
        else:  # VENTA
            color = 'red'
            simbolo = 'SELL'
            flecha = 'v'
            offset_y = -40
        
        # Líneas verticales en los 3 paneles con mayor grosor para señales importantes
        for ax in axes:
            ax.axvline(x=date, color=color, linestyle='-', linewidth=2.5, alpha=0.9)
        
        # Panel 0 (Velas): Señal principal con precio y tipo
        axes[0].annotate(f'{simbolo} {senal["tipo"]} {flecha}\n${senal["close"]:.4f}', 
                        xy=(date, senal['close']),
                        xytext=(15, offset_y), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.5', facecolor=color, alpha=0.9, edgecolor='white', linewidth=2),
                        fontsize=10, color='white', weight='bold', ha='center')
        
        # Panel 1 (RSI): Condición RSI
        axes[1].annotate(f'{senal["tipo"]}\nRSI:{senal["rsi"]:.1f}', 
                        xy=(date, senal['rsi']),
                        xytext=(15, 20 if senal['tipo'] == 'COMPRA' else -30), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.8),
                        fontsize=9, color='white', weight='bold', ha='center')
        
        # Panel 2 (MACD): Condición MACD
        diferencia = senal['macd'] - senal['signal']
        axes[2].annotate(f'{senal["tipo"]}\nMACD{flecha}', 
                        xy=(date, senal['macd']),
                        xytext=(15, 25 if senal['macd'] > 0 else -35), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.8),
                        fontsize=9, color='white', weight='bold', ha='center')
    
    return len(senales)

# Variables globales para tracking de convergencias
convergencias_ma_rsi_global = []

def obtener_titulo_panel():
    """Genera el título dinámico del panel basado en las opciones seleccionadas"""
    titulo_base = "Velas"
    
    adicionales = []
    if mostrar_extremos_rsi.get():
        adicionales.append("Extremos RSI")
    if mostrar_ma.get():
        adicionales.append("Tendencias MA")
    if mostrar_convergencias_rsi_macd.get():
        adicionales.append("RSI+MACD Cruces")
    if mostrar_senales_combinadas.get():
        adicionales.append("Señales Trading")
    
    # Agregar información sobre convergencias MA
    if mostrar_convergencias_ma_rsi.get() and convergencias_ma_rsi_global:
        adicionales.append(f"CONV: {len(convergencias_ma_rsi_global)} MA")
    
    if adicionales:
        titulo_base += f" ({' + '.join(adicionales)})"
    
    return titulo_base

""" --- Incluye los valores actuales en la gráfica ---"""
def mostrar_valores_actuales(df):
    global mostrar_ma, ma_periodo
    ultimo = df.iloc[-1]
    color_vela = 'green' if ultimo['Close'] >= ultimo['Open'] else 'red'
    
    # Determinar color del RSI según zona
    if ultimo['RSI'] > 70:
        color_rsi = 'red'
        zona_rsi = 'Sobrecompra'
    elif ultimo['RSI'] < 30:
        color_rsi = 'green'
        zona_rsi = 'Sobreventa'
    else:
        color_rsi = 'blue'
        zona_rsi = 'Normal'

    # Margen superior y entre etiquetas (sin necesidad de espacio para etiquetas de tendencia)
    top_margins = [0.97, 0.94, 0.94]  # Panel 0, 1, 2
    vertical_margin = 0.06  # Entre cada valor
    boxstyle = 'round,pad=0.3,rounding_size=0.2'  # Estilo uniforme

    # Panel 0: Velas y precio
    axes[0].text(
        0.01, top_margins[0], f"Precio: {ultimo['Close']:.4f}".ljust(18),
        transform=axes[0].transAxes,
        fontsize=11, color=color_vela, ha='left', va='top',
        bbox=dict(facecolor='none', edgecolor=color_vela, boxstyle=boxstyle, linewidth=1)
    )
    # Mostrar valor de MA solo si está activada
    if mostrar_ma.get():
        periodo_seleccionado = ma_periodo.get()
        colores_ma = {"MA3": "magenta", "MA7": "red", "MA14": "cyan", "MA25": "orange", "MA50": "purple", "MA99": "blue"}
        color_ma = colores_ma.get(periodo_seleccionado, "purple")
        axes[0].text(
            0.01, top_margins[0] - vertical_margin, f"{periodo_seleccionado}: {ultimo[periodo_seleccionado]:.4f}".ljust(18),
            transform=axes[0].transAxes,
            fontsize=11, color=color_ma, ha='left', va='top',
            bbox=dict(facecolor='none', edgecolor=color_ma, boxstyle=boxstyle, linewidth=1)
        )
    
    # Mostrar valor de segunda MA solo si está activada
    if mostrar_ma2.get():
        periodo_seleccionado2 = ma2_periodo.get()
        colores_ma2 = {"MA3": "lightcoral", "MA7": "lightblue", "MA14": "lightyellow", "MA25": "lightgreen", "MA50": "lightpink", "MA99": "lightgray"}
        color_ma2 = colores_ma2.get(periodo_seleccionado2, "lightgray")
        offset_adicional = vertical_margin if mostrar_ma.get() else 0  # Ajustar posición según primera MA
        axes[0].text(
            0.01, top_margins[0] - vertical_margin - offset_adicional, f"{periodo_seleccionado2}: {ultimo[periodo_seleccionado2]:.4f}".ljust(18),
            transform=axes[0].transAxes,
            fontsize=11, color=color_ma2, ha='left', va='top',
            bbox=dict(facecolor='none', edgecolor=color_ma2, boxstyle=boxstyle, linewidth=1)
        )
    
    # Panel 1: RSI
    axes[1].text(
        0.01, top_margins[1], f"RSI: {ultimo['RSI']:.2f} ({zona_rsi})".ljust(20),
        transform=axes[1].transAxes,
        fontsize=11, color=color_rsi, ha='left', va='top',
        bbox=dict(facecolor='none', edgecolor=color_rsi, boxstyle=boxstyle, linewidth=1)
    )
    
    # Panel 2: MACD
    macd_delta = ultimo['MACD'] - ultimo['Signal']
    axes[2].text(
        0.01, top_margins[2], f"MACD: {ultimo['MACD']:.4f}".ljust(18),
        transform=axes[2].transAxes,
        fontsize=11, color='white', ha='left', va='top',
        bbox=dict(facecolor='none', edgecolor='white', boxstyle=boxstyle, linewidth=1)
    )
    axes[2].text(
        0.01, top_margins[2] - vertical_margin, f"Signal: {ultimo['Signal']:.4f}".ljust(18),
        transform=axes[2].transAxes,
        fontsize=11, color='orange', ha='left', va='top',
        bbox=dict(facecolor='none', edgecolor='orange', boxstyle=boxstyle, linewidth=1)
    )
    axes[2].text(
        0.01, top_margins[2] - 2*vertical_margin, f"Delta: {macd_delta:.4f}".ljust(18),
        transform=axes[2].transAxes,
        fontsize=11, color='green' if macd_delta >= 0 else 'red', ha='left', va='top',
        bbox=dict(facecolor='none', edgecolor='gray', boxstyle=boxstyle, linewidth=1)
    )

""" --- Funciones de la interfaz gráfica ---"""
def cargar_datos():
    global mostrar_ma, ma_periodo, mostrar_senales_combinadas
    symbol = symbol_var.get()
    try:
        df = obtener_historico_binance(symbol, INTERVAL)
        df = procesar_indicadores(df)
        
        for widget in frame_chart.winfo_children():
            widget.destroy()
            
        # Preparar addplots según configuración
        addplots = []
        
        # Agregar MA seleccionada si está activada
        if mostrar_ma.get():
            periodo_seleccionado = ma_periodo.get()
            colores_ma = {"MA3": "magenta", "MA7": "red", "MA14": "cyan", "MA25": "orange", "MA50": "purple", "MA99": "blue"}
            color_ma = colores_ma.get(periodo_seleccionado, "purple")
            addplots.append(mpf.make_addplot(df[periodo_seleccionado], color=color_ma, panel=0, width=1.5, secondary_y=False, label=periodo_seleccionado, alpha=0.8))
        
        # Agregar segunda MA si está activada
        if mostrar_ma2.get():
            periodo_seleccionado2 = ma2_periodo.get()
            colores_ma2 = {"MA3": "lightcoral", "MA7": "lightblue", "MA14": "lightyellow", "MA25": "lightgreen", "MA50": "lightpink", "MA99": "lightgray"}
            color_ma2 = colores_ma2.get(periodo_seleccionado2, "lightgray")
            addplots.append(mpf.make_addplot(df[periodo_seleccionado2], color=color_ma2, panel=0, width=1.5, secondary_y=False, label=periodo_seleccionado2, alpha=0.7))
        
        # Agregar líneas de tendencia dinámicas
        umbral_actual = umbral_pendiente.get() if umbral_pendiente else 0.0002
        
        # Líneas de tendencia MA1
        if mostrar_ma.get():
            lineas_ma1 = calcular_lineas_tendencia_ma_individual_addplot(df, ma_periodo.get(), umbral_actual, False)
            for linea in lineas_ma1:
                addplots.append(mpf.make_addplot(linea['data'], color=linea['color'], panel=0, 
                                               width=linea['width'], alpha=linea['alpha'], secondary_y=False))
        
        # Líneas de tendencia MA2  
        if mostrar_ma2.get():
            lineas_ma2 = calcular_lineas_tendencia_ma_individual_addplot(df, ma2_periodo.get(), umbral_actual, True)
            for linea in lineas_ma2:
                addplots.append(mpf.make_addplot(linea['data'], color=linea['color'], panel=0, 
                                               width=linea['width'], alpha=linea['alpha'], secondary_y=False))
        
        # Agregar indicadores RSI y MACD
        addplots.extend([
            mpf.make_addplot(df['RSI'], color='blue', panel=1, ylabel='RSI', label='RSI'),
            mpf.make_addplot(df['MACD'], color='black', panel=2, ylabel='MACD', label='MACD'),
            mpf.make_addplot(df['Signal'], color='orange', panel=2, label='Signal'),
            mpf.make_addplot(df['Histogram'], type='bar', color='gray', panel=2, alpha=0.7, label='Histogram')
        ])

        fig, axes = mpf.plot(
            df[['Open', 'High', 'Low', 'Close', 'Volume']],
            type='candle',
            style='yahoo',
            addplot=addplots,
            volume=True,
            panel_ratios=(2,1,1),
            ylabel='Precio',
            ylabel_lower='Volumen',
            title=f'{symbol} - Scalping Analysis (1s) UTC-5',
            datetime_format='%m/%d %H:%M:%S',
            xrotation=15,
            warn_too_much_data=10000,
            returnfig=True
        )
        
        # Configurar locators para evitar demasiados ticks
        import matplotlib.dates as mdates
        import matplotlib.ticker as ticker
        for ax in axes:
            # Usar MaxNLocator para control estricto de ticks
            ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=6))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            # Desactivar ticks menores para evitar overflow
            ax.xaxis.set_minor_locator(ticker.NullLocator())
        
        axes[0].set_title(obtener_titulo_panel(), fontsize=12)
        axes[1].set_title('RSI', fontsize=12)
        axes[2].set_title('MACD', fontsize=12)
        
        canvas = FigureCanvasTkAgg(fig, master=frame_chart)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    except Exception as e:
        for widget in frame_chart.winfo_children():
            widget.destroy()
        error_label = tk.Label(frame_chart, text=f"Error al obtener datos: {e}", fg="red")
        error_label.pack()

""" --- Configuración de la interfaz gráfica ---"""
def inicializar_grafico():
    global fig, axes, canvas
    plt.style.use('dark_background')  # Fondo oscuro
    fig, axes = plt.subplots(3, 1, figsize=(18, 10), sharex=True, gridspec_kw={'height_ratios': [2, 1, 1]})
    canvas = FigureCanvasTkAgg(fig, master=frame_chart)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

""" --- Actualización periódica del gráfico ---"""
def actualizar_grafico():
    global actualizando, axes, mostrar_ma, ma_periodo, mostrar_senales_combinadas
    if actualizando:
        symbol = symbol_var.get()
        tiempo_seleccionado = tiempo_var.get()
        limit = TIEMPO_OPTIONS[tiempo_seleccionado]
        try:
            plt.style.use('dark_background')  # Fondo oscuro también al actualizar
            df = obtener_historico_binance(symbol, INTERVAL, limit)
            df = procesar_indicadores(df)
            
            for ax in axes:
                ax.clear()
                
            # Panel 0: Velas + MA
            import matplotlib.dates as mdates
            df_plot = df.reset_index()
            df_plot['Date'] = mdates.date2num(df_plot['Close time'])
            ohlc = df_plot[['Date', 'Open', 'High', 'Low', 'Close']].values

            # Calcular ancho de barra (80% del intervalo)
            if len(df_plot['Date']) > 1:
                interval_width = (df_plot['Date'][1] - df_plot['Date'][0]) * 0.8
            else:
                interval_width = 0.0008  # valor por defecto

            from mplfinance.original_flavor import candlestick_ohlc
            candlestick_ohlc(axes[0], ohlc, width=interval_width, colorup='g', colordown='r')
            
            # Agregar MA seleccionada si está activada
            if mostrar_ma.get():
                periodo_seleccionado = ma_periodo.get()
                colores_ma = {"MA3": "magenta", "MA7": "red", "MA14": "cyan", "MA25": "orange", "MA50": "purple", "MA99": "blue"}
                color_ma = colores_ma.get(periodo_seleccionado, "purple")
                axes[0].plot(df_plot['Date'], df_plot[periodo_seleccionado], color=color_ma, linewidth=1.5, label=periodo_seleccionado, alpha=0.8)
            
            # Agregar segunda MA si está activada
            if mostrar_ma2.get():
                periodo_seleccionado2 = ma2_periodo.get()
                colores_ma2 = {"MA3": "lightcoral", "MA7": "lightblue", "MA14": "lightyellow", "MA25": "lightgreen", "MA50": "lightpink", "MA99": "lightgray"}
                color_ma2 = colores_ma2.get(periodo_seleccionado2, "lightgray")
                axes[0].plot(df_plot['Date'], df_plot[periodo_seleccionado2], color=color_ma2, linewidth=1.5, label=periodo_seleccionado2, alpha=0.7)
            
            # Mostrar leyenda si hay alguna MA activa
            if mostrar_ma.get() or mostrar_ma2.get():
                axes[0].legend(loc='upper left')
            
            axes[0].set_title(obtener_titulo_panel())
            axes[0].set_ylabel('Precio')
            axes[0].xaxis_date()
            
            # Mejorar formato de fechas en el eje X
            import matplotlib.dates as mdates
            axes[0].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            axes[0].xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
            plt.setp(axes[0].xaxis.get_majorticklabels(), rotation=45)
            

            
            # Marcar extremos RSI con líneas verticales
            marcar_extremos_rsi(axes, df)
            
            # Calcular y mostrar líneas de tendencia de MA basadas en cambios de pendiente
            segmentos_ma1, segmentos_ma2 = calcular_lineas_tendencia_ma(axes, df)
            
            # CONV: NUEVA FUNCIONALIDAD: Marcar convergencias entre MAs (sin RSI)
            global convergencias_ma_rsi_global
            if mostrar_convergencias_ma_rsi.get():
                convergencias_ma_rsi_global = marcar_convergencias_doble_ma_rsi(axes, df, segmentos_ma1, segmentos_ma2)
                
                # Imprimir convergencias detectadas para feedback
                if convergencias_ma_rsi_global:
                    print(f"\n>>> CONVERGENCIAS MA FILTRADAS: {len(convergencias_ma_rsi_global)}")
                    print("   (Se omiten señales consecutivas del mismo tipo)")
                    for i, conv in enumerate(convergencias_ma_rsi_global, 1):
                        tipo_emoji = "SELL" if conv['tipo'] == 'VENTA_CONVERGENCIA' else "BUY"
                        print(f"{i}. {tipo_emoji} {conv['timestamp'].strftime('%H:%M:%S')} - {conv['descripcion']}")
            else:
                convergencias_ma_rsi_global = []
            
            # Marcar convergencias RSI extremo + MACD Signal cruce por 0
            num_convergencias = marcar_convergencias_rsi_macd(axes, df)
            
            # Marcar señales de trading combinadas RSI + MACD + MA
            num_senales = marcar_senales_trading_combinadas(axes, df)
            
            # Panel 1: RSI
            axes[1].plot(df_plot['Date'], df_plot['RSI'], color='blue', label='RSI')
            axes[1].axhline(70, color='red', linestyle='--', alpha=0.7, label='Sobrecompra (70)')
            axes[1].axhline(30, color='green', linestyle='--', alpha=0.7, label='Sobreventa (30)')
            axes[1].fill_between(df_plot['Date'], 70, 100, alpha=0.1, color='red')
            axes[1].fill_between(df_plot['Date'], 0, 30, alpha=0.1, color='green')
            axes[1].set_title('RSI (Zonas extremas resaltadas)')
            axes[1].set_ylabel('RSI')
            axes[1].legend()
            axes[1].set_ylim(0, 100)
            
            # Panel 2: MACD
            axes[2].plot(df_plot['Date'], df_plot['MACD'], color='white', label='MACD')
            axes[2].plot(df_plot['Date'], df_plot['Signal'], color='orange', label='Signal')
            axes[2].axhline(0, color='grey', linestyle='--')
            macd_delta = df_plot['MACD'] - df_plot['Signal']
            axes[2].bar(
                df_plot['Date'],
                macd_delta,
                width=interval_width,
                color=['green' if v >= 0 else 'red' for v in macd_delta],
                alpha=0.5,
                label='MACD Delta'
            )
            axes[2].set_title('MACD')
            axes[2].set_ylabel('MACD')
            axes[2].legend()
            
            # Aplicar el mismo formato de fecha a todos los paneles
            for ax in axes:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                if ax != axes[0]:  # Solo rotar en el panel principal
                    plt.setp(ax.xaxis.get_majorticklabels(), rotation=0)
            
            fig.suptitle(f'{symbol} - Scalping Analysis (1s) UTC-5')
            fig.tight_layout()
            

            
            # Mostrar valores actuales en cada panel
            mostrar_valores_actuales(df)
            
            # Mostrar estadísticas RSI y transiciones
            rsi_extremos = len(df[(df['RSI'] > 70) | (df['RSI'] < 30)])
            rsi_sobrecompra = len(df[df['RSI'] > 70])
            rsi_sobreventa = len(df[df['RSI'] < 30])
            

            
            # Información adicional sobre extremos RSI
            estadisticas_base = f"RSI Extremos: {rsi_extremos} | Sobrecompra: {rsi_sobrecompra} | Sobreventa: {rsi_sobreventa}"
            
            if mostrar_extremos_rsi.get() and rsi_extremos > 0:
                # Contar períodos continuos para las estadísticas
                def contar_periodos_continuos(mask):
                    periodos = 0
                    en_periodo = False
                    for valor in mask:
                        if valor and not en_periodo:
                            periodos += 1
                            en_periodo = True
                        elif not valor:
                            en_periodo = False
                    return periodos
                
                sobrecompra_periodos = contar_periodos_continuos(df['RSI'] > 70)
                sobreventa_periodos = contar_periodos_continuos(df['RSI'] < 30)
                total_periodos = sobrecompra_periodos + sobreventa_periodos
                
                estadisticas_extremos = f" | Períodos extremos: {total_periodos} (SC:{sobrecompra_periodos}, SV:{sobreventa_periodos})"
            else:
                estadisticas_extremos = ""
            
            # Agregar información de convergencias si están activadas
            if mostrar_convergencias_rsi_macd.get():
                try:
                    estadisticas_extremos += f" | RSI+MACD Cruces: {num_convergencias}"
                except Exception:
                    estadisticas_extremos += " | RSI+MACD Cruces: 0"
            
            # Agregar información de señales combinadas si están activadas
            if mostrar_senales_combinadas.get():
                try:
                    estadisticas_extremos += f" | Señales Trading: {num_senales}"
                except Exception:
                    estadisticas_extremos += " | Señales Trading: 0"
            
            # Agregar información de segmentos de tendencia MA si están activados
            if mostrar_ma.get() or mostrar_ma2.get():
                try:
                    # Combinar segmentos de ambas MAs para estadísticas
                    todos_segmentos = []
                    info_mas = []
                    
                    if mostrar_ma.get() and segmentos_ma1:
                        todos_segmentos.extend(segmentos_ma1)
                        info_mas.append(f"MA1({len(segmentos_ma1)})")
                    
                    if mostrar_ma2.get() and segmentos_ma2:
                        todos_segmentos.extend(segmentos_ma2)
                        info_mas.append(f"MA2({len(segmentos_ma2)})")
                    
                    if todos_segmentos:
                        # Contar tipos de tendencias total
                        alcistas = sum(1 for s in todos_segmentos if s['pendiente'] > 0.0002)
                        bajistas = sum(1 for s in todos_segmentos if s['pendiente'] < -0.0002)
                        laterales = len(todos_segmentos) - alcistas - bajistas
                        mas_info = " + ".join(info_mas)
                        estadisticas_extremos += f" | Tendencias {mas_info}: ↗{alcistas}, ↘{bajistas}, →{laterales}"
                    else:
                        estadisticas_extremos += " | Tendencias MA: 0"
                except Exception:
                    estadisticas_extremos += " | Tendencias MA: 0"
            
            # Mostrar estadísticas simplificadas
            label_signals.config(
                text=f"{estadisticas_base}{estadisticas_extremos}"
            )
            
            canvas.draw()
            
        except Exception as e:
            for widget in frame_chart.winfo_children():
                widget.destroy()
            error_label = tk.Label(frame_chart, text=f"Error al obtener datos: {e}", fg="red")
            error_label.pack()
            
        root.after(1000, actualizar_grafico)  # Actualizar cada segundo

def detener_app():
    global actualizando, root
    try:
        print("Cerrando aplicación...")
        actualizando = False
        
        # Cancelar cualquier tarea pendiente de after()
        if root:
            for after_id in root.tk.call('after', 'info'):
                root.after_cancel(after_id)
        
        # Limpiar matplotlib
        import matplotlib.pyplot as plt
        plt.close('all')
        
        # Destruir ventana principal
        if root:
            root.quit()
            root.destroy()
            
    except Exception as e:
        print(f"Error al cerrar: {e}")
    finally:
        import sys
        sys.exit(0)

# Asignar el callback del umbral después de definir actualizar_grafico
# def setup_umbral_callback():
#     global umbral_callback
#     umbral_callback = actualizar_grafico_manual

# --- Variables globales ---
actualizando = True
canvas = None
fig = None
axes = None

# Variables para controlar el sombreado
mostrar_extremos_rsi = None
mostrar_convergencias_rsi_macd = None
mostrar_convergencias_ma_rsi = None  # Nueva variable para convergencias MA
mostrar_etiquetas_convergencia = None  # Control para etiquetas de convergencia
mostrar_lineas_tendencia_ma1 = None  # Control para líneas de tendencia MA1
mostrar_lineas_tendencia_ma2 = None  # Control para líneas de tendencia MA2
umbral_pendiente = None  # Variable para el umbral dinámico de pendiente
# umbral_pendiente = None  # Variable eliminada - ahora es fijo
# umbral_callback = None  # Callback eliminado
# actualizando_umbral = False  # Flag eliminado
mostrar_senales_combinadas = None
mostrar_ma = None
ma_periodo = None
mostrar_ma2 = None
ma2_periodo = None
tiempo_var = None

if __name__ == "__main__":
    # --- Interfaz gráfica ---
    root = tk.Tk()
    root.title("Binance Scalping Chart Analyzer - 1s RSI Extreme Zones")
    root.state('zoomed')  # Pantalla completa en Windows

    frame_controls = ttk.Frame(root)
    frame_controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

    ttk.Label(frame_controls, text="Símbolo:").pack(side=tk.LEFT)
    symbol_var = tk.StringVar(value=SYMBOLS[0])
    symbol_menu = ttk.OptionMenu(frame_controls, symbol_var, SYMBOLS[0], *SYMBOLS)
    symbol_menu.pack(side=tk.LEFT, padx=5)

    ttk.Label(frame_controls, text="Tiempo:").pack(side=tk.LEFT)
    tiempo_var = tk.StringVar(value="10 min")
    tiempo_menu = ttk.OptionMenu(frame_controls, tiempo_var, "10 min", *TIEMPO_OPTIONS.keys())
    tiempo_menu.pack(side=tk.LEFT, padx=5)

    # Mostrar el intervalo fijo
    ttk.Label(frame_controls, text=f"Intervalo: {INTERVAL} | Hora Colombia (UTC-5)").pack(side=tk.LEFT, padx=20)

    ttk.Button(frame_controls, text="Detener y Salir", command=detener_app).pack(side=tk.LEFT, padx=10)

    # Frame para los checkboxes de sombreado
    frame_checkboxes = ttk.Frame(root)
    frame_checkboxes.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
    
    ttk.Label(frame_checkboxes, text="Opciones de Análisis:").pack(side=tk.LEFT)
    
    mostrar_extremos_rsi = tk.BooleanVar(value=False)
    checkbox_extremos = ttk.Checkbutton(frame_checkboxes, text="Extremos RSI (Líneas)", 
                                       variable=mostrar_extremos_rsi)
    checkbox_extremos.pack(side=tk.LEFT, padx=10)
    
    mostrar_convergencias_rsi_macd = tk.BooleanVar(value=False)
    checkbox_convergencias = ttk.Checkbutton(frame_checkboxes, text="RSI Extremo + MACD Cruces", 
                                            variable=mostrar_convergencias_rsi_macd)
    checkbox_convergencias.pack(side=tk.LEFT, padx=10)
    
    # Nueva funcionalidad: Convergencias MA (sin RSI)
    mostrar_convergencias_ma_rsi = tk.BooleanVar(value=False)
    
    # Función para activar dependencias automáticamente
    def on_convergencias_ma_change():
        if mostrar_convergencias_ma_rsi.get():
            # Si se activa convergencias MA, activar automáticamente:
            if not mostrar_ma.get():
                mostrar_ma.set(True)
                print("✅ Auto-activando MA1")
            if not mostrar_ma2.get():
                mostrar_ma2.set(True) 
                print("✅ Auto-activando MA2")
            if not mostrar_lineas_tendencia_ma1.get():
                mostrar_lineas_tendencia_ma1.set(True)
                print("✅ Auto-activando líneas de tendencia MA1")
            if not mostrar_lineas_tendencia_ma2.get():
                mostrar_lineas_tendencia_ma2.set(True)
                print("✅ Auto-activando líneas de tendencia MA2")
        # Si se desactiva, no desactivar nada más (como solicitaste)
    
    checkbox_conv_ma_rsi = ttk.Checkbutton(frame_checkboxes, text=">>> Convergencias MA", 
                                          variable=mostrar_convergencias_ma_rsi,
                                          command=on_convergencias_ma_change)
    checkbox_conv_ma_rsi.pack(side=tk.LEFT, padx=10)

    # --- Frame para controles de Media Móvil ---
    frame_ma = ttk.Frame(root)
    frame_ma.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
    
    # Checkbox para activar/desactivar MA
    mostrar_ma = tk.BooleanVar(value=False)
    checkbox_ma = ttk.Checkbutton(frame_ma, text="Mostrar MA1:", variable=mostrar_ma)
    checkbox_ma.pack(side=tk.LEFT, padx=(0, 10))
    
    # Lista desplegable para seleccionar periodo de MA
    ttk.Label(frame_ma, text="Periodo:").pack(side=tk.LEFT)
    ma_periodo = tk.StringVar(value="MA7")
    combobox_ma = ttk.Combobox(frame_ma, textvariable=ma_periodo, 
                              values=["MA3", "MA7", "MA14", "MA25", "MA50", "MA99"], 
                              state="readonly", width=10)
    combobox_ma.pack(side=tk.LEFT, padx=(5, 20))
    
    # --- Frame para segunda Media Móvil ---
    frame_ma2 = ttk.Frame(root)
    frame_ma2.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
    
    # Checkbox para activar/desactivar segunda MA
    mostrar_ma2 = tk.BooleanVar(value=False)
    checkbox_ma2 = ttk.Checkbutton(frame_ma2, text="Mostrar MA2:", variable=mostrar_ma2)
    checkbox_ma2.pack(side=tk.LEFT, padx=(0, 10))
    
    # Lista desplegable para seleccionar periodo de segunda MA
    ttk.Label(frame_ma2, text="Periodo:").pack(side=tk.LEFT)
    ma2_periodo = tk.StringVar(value="MA25")
    combobox_ma2 = ttk.Combobox(frame_ma2, textvariable=ma2_periodo, 
                               values=["MA3", "MA7", "MA14", "MA25", "MA50", "MA99"], 
                               state="readonly", width=10)
    combobox_ma2.pack(side=tk.LEFT, padx=(5, 10))

    # --- Frame para controles adicionales de MA ---
    frame_ma_controles = ttk.Frame(root)
    frame_ma_controles.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
    
    ttk.Label(frame_ma_controles, text="Controles MA:").pack(side=tk.LEFT)
    
    # Checkbox para mostrar/ocultar líneas de tendencia MA1
    mostrar_lineas_tendencia_ma1 = tk.BooleanVar(value=True)
    checkbox_tendencia_ma1 = ttk.Checkbutton(frame_ma_controles, text="Líneas Tend. MA1", 
                                            variable=mostrar_lineas_tendencia_ma1)
    checkbox_tendencia_ma1.pack(side=tk.LEFT, padx=10)
    
    # Checkbox para mostrar/ocultar líneas de tendencia MA2
    mostrar_lineas_tendencia_ma2 = tk.BooleanVar(value=True)
    checkbox_tendencia_ma2 = ttk.Checkbutton(frame_ma_controles, text="Líneas Tend. MA2", 
                                            variable=mostrar_lineas_tendencia_ma2)
    checkbox_tendencia_ma2.pack(side=tk.LEFT, padx=10)
    
    # Checkbox para mostrar/ocultar etiquetas de convergencia
    mostrar_etiquetas_convergencia = tk.BooleanVar(value=True)
    checkbox_etiquetas_conv = ttk.Checkbutton(frame_ma_controles, text="Etiquetas Convergencia", 
                                             variable=mostrar_etiquetas_convergencia)
    checkbox_etiquetas_conv.pack(side=tk.LEFT, padx=10)

    # --- Frame para control dinámico del umbral ---
    frame_umbral = ttk.Frame(root)
    frame_umbral.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
    
    ttk.Label(frame_umbral, text="Umbral Pendiente:").pack(side=tk.LEFT)
    
    # Variable para el umbral dinámico
    umbral_pendiente = tk.DoubleVar(value=0.0002)
    
    # Función para actualizar la etiqueta del umbral
    def actualizar_etiqueta_umbral(value):
        valor_actual = float(value)
        label_umbral_valor.config(text=f"±{valor_actual:.6f}")
        return True
    
    # Slider para el umbral (rango de 0.0001 a 0.005)
    scale_umbral = tk.Scale(frame_umbral, from_=0.0001, to=0.005, resolution=0.0001,
                           orient=tk.HORIZONTAL, variable=umbral_pendiente,
                           command=actualizar_etiqueta_umbral, length=200)
    scale_umbral.pack(side=tk.LEFT, padx=5)
    
    # Etiqueta que muestra el valor actual
    label_umbral_valor = ttk.Label(frame_umbral, text="±0.000200")
    label_umbral_valor.pack(side=tk.LEFT, padx=5)
    
    # Botones predefinidos para valores comunes
    frame_presets = ttk.Frame(frame_umbral)
    frame_presets.pack(side=tk.LEFT, padx=10)
    
    def set_umbral(valor):
        umbral_pendiente.set(valor)
        actualizar_etiqueta_umbral(valor)
    
    ttk.Button(frame_presets, text="Ultra", command=lambda: set_umbral(0.0001), width=6).pack(side=tk.LEFT, padx=2)
    ttk.Button(frame_presets, text="Sensible", command=lambda: set_umbral(0.0002), width=8).pack(side=tk.LEFT, padx=2)
    ttk.Button(frame_presets, text="Moderado", command=lambda: set_umbral(0.001), width=8).pack(side=tk.LEFT, padx=2)
    ttk.Button(frame_presets, text="Conservador", command=lambda: set_umbral(0.002), width=10).pack(side=tk.LEFT, padx=2)

    # --- Frame para señales combinadas ---
    frame_senales = ttk.Frame(root)
    frame_senales.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
    
    # Checkbox para señales combinadas RSI + MACD + MA
    mostrar_senales_combinadas = tk.BooleanVar(value=False)
    checkbox_senales_combinadas = ttk.Checkbutton(frame_senales, text="Señales de Trading: RSI + MACD + MA (Compra/Venta)", 
                                                 variable=mostrar_senales_combinadas)
    checkbox_senales_combinadas.pack(side=tk.LEFT, padx=10)

    label_valores = tk.Label(root, text="Análisis de Scalping: RSI Extremos, MACD Convergencias y Señales de Trading (UTC-5)", font=("Arial", 12), fg="blue")
    label_valores.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

    label_signals = tk.Label(root, text="", font=("Arial", 12), fg="darkgreen")
    label_signals.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

    frame_chart = ttk.Frame(root)
    frame_chart.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # Configurar el callback del umbral - ELIMINADO
    # setup_umbral_callback()
    
    inicializar_grafico()
    actualizar_grafico()
    root.mainloop()