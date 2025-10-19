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
    df["MA7"] = sma(df["Close"], 7)
    df["MA14"] = sma(df["Close"], 14)
    df["MA25"] = sma(df["Close"], 25)
    df["MA50"] = sma(df["Close"], 50)
    df["MA99"] = sma(df["Close"], 99)
    df["RSI"] = rsi(df["Close"], 14)
    df["MACD"], df["Signal"] = macd(df["Close"])
    return df



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
            simbolo = '🟢'
            flecha = '⬆'
            offset_y = 30
        else:  # VENTA
            color = 'red'
            simbolo = '🔴'
            flecha = '⬇'
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

def obtener_titulo_panel():
    """Genera el título dinámico del panel basado en las opciones seleccionadas"""
    titulo_base = "Velas"
    
    adicionales = []
    if mostrar_extremos_rsi.get():
        adicionales.append("Extremos RSI")
    if mostrar_convergencias_rsi_macd.get():
        adicionales.append("RSI+MACD Cruces")
    if mostrar_senales_combinadas.get():
        adicionales.append("Señales Trading")
    
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

    # Margen superior y entre etiquetas (en coordenadas relativas)
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
        colores_ma = {"MA7": "red", "MA14": "cyan", "MA25": "orange", "MA50": "purple", "MA99": "blue"}
        color_ma = colores_ma.get(periodo_seleccionado, "purple")
        axes[0].text(
            0.01, top_margins[0] - vertical_margin, f"{periodo_seleccionado}: {ultimo[periodo_seleccionado]:.4f}".ljust(18),
            transform=axes[0].transAxes,
            fontsize=11, color=color_ma, ha='left', va='top',
            bbox=dict(facecolor='none', edgecolor=color_ma, boxstyle=boxstyle, linewidth=1)
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
            colores_ma = {"MA7": "red", "MA14": "cyan", "MA25": "orange", "MA50": "purple", "MA99": "blue"}
            color_ma = colores_ma.get(periodo_seleccionado, "purple")
            addplots.append(mpf.make_addplot(df[periodo_seleccionado], color=color_ma, panel=0, width=1.5, secondary_y=False, label=periodo_seleccionado, alpha=0.8))
        
        # Agregar indicadores RSI y MACD
        addplots.extend([
            mpf.make_addplot(df['RSI'], color='blue', panel=1, ylabel='RSI', label='RSI'),
            mpf.make_addplot(df['MACD'], color='black', panel=2, ylabel='MACD', label='MACD'),
            mpf.make_addplot(df['Signal'], color='orange', panel=2, label='Signal')
        ])

        fig, axes = mpf.plot(
            df[['Open', 'High', 'Low', 'Close', 'Volume', 'RSI', 'MACD', 'Signal']],
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
                colores_ma = {"MA7": "red", "MA14": "cyan", "MA25": "orange", "MA50": "purple", "MA99": "blue"}
                color_ma = colores_ma.get(periodo_seleccionado, "purple")
                axes[0].plot(df_plot['Date'], df_plot[periodo_seleccionado], color=color_ma, linewidth=1.5, label=periodo_seleccionado, alpha=0.8)
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
                    estadisticas_extremos += f" | RSI+MACD Cruces: 0"
            
            # Agregar información de señales combinadas si están activadas
            if mostrar_senales_combinadas.get():
                try:
                    estadisticas_extremos += f" | Señales Trading: {num_senales}"
                except Exception:
                    estadisticas_extremos += f" | Señales Trading: 0"
            
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
    global actualizando
    actualizando = False
    root.destroy()
    import sys
    sys.exit(0)

# --- Variables globales ---
actualizando = True
canvas = None
fig = None
axes = None

# Variables para controlar el sombreado
mostrar_extremos_rsi = None
mostrar_convergencias_rsi_macd = None
mostrar_senales_combinadas = None
mostrar_ma = None
ma_periodo = None
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

    # --- Frame para controles de Media Móvil ---
    frame_ma = ttk.Frame(root)
    frame_ma.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
    
    # Checkbox para activar/desactivar MA
    mostrar_ma = tk.BooleanVar(value=False)
    checkbox_ma = ttk.Checkbutton(frame_ma, text="Mostrar MA:", variable=mostrar_ma)
    checkbox_ma.pack(side=tk.LEFT, padx=(0, 10))
    
    # Lista desplegable para seleccionar periodo de MA
    ttk.Label(frame_ma, text="Periodo:").pack(side=tk.LEFT)
    ma_periodo = tk.StringVar(value="MA50")
    combobox_ma = ttk.Combobox(frame_ma, textvariable=ma_periodo, 
                              values=["MA7", "MA14", "MA25", "MA50", "MA99"], 
                              state="readonly", width=10)
    combobox_ma.pack(side=tk.LEFT, padx=(5, 10))

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

    inicializar_grafico()
    actualizar_grafico()
    root.mainloop()