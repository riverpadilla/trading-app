"""Modulo generador de gráficos, usando datos de Binance y TA-Lib para indicadores técnicos."""
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import mplfinance as mpf
import requests
import pandas as pd
import talib  # pylint: disable=no-member
import estrategia

# --- Parámetros de la interfaz ---
SYMBOLS = ["BNBUSDT", "USDTARS"]
INTERVALS = ["1s", "1m", "5m", "15m", "30m", "1h", "4h", "1d"]
BINANCE_URL = "https://api.binance.us/api/v3/klines"

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
def obtener_historico_binance(symbol, interval, limit=1000):
    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
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
    df["Open"] = df["Open"].astype(float)
    df["High"] = df["High"].astype(float)
    df["Low"] = df["Low"].astype(float)
    df["Close"] = df["Close"].astype(float)
    df["Volume"] = df["Volume"].astype(float)
    df.set_index("Close time", inplace=True)
    return df

""" --- Procesar indicadores y señales ---"""
def procesar_indicadores(df):
    df["MA7"] = sma(df["Close"], 7)
    df["MA25"] = sma(df["Close"], 25)
    df["MA50"] = sma(df["Close"], 50)
    df["MA99"] = sma(df["Close"], 99)
    df["RSI"] = rsi(df["Close"], 14)
    df["MACD"], df["Signal"] = macd(df["Close"])
    return df

""" --- Incluye los valores actuales en la gráfica ---"""
def mostrar_valores_actuales(df):
    ultimo = df.iloc[-1]
    color_vela = 'green' if ultimo['Close'] >= ultimo['Open'] else 'red'

    # Margen superior y entre etiquetas (en coordenadas relativas)
    top_margins = [0.97, 0.94, 0.94]  # Panel 0, 1, 2 (ajusta según lo que veas en pantalla)
    vertical_margin = 0.06  # ~10px entre cada valor
    boxstyle = 'round,pad=0.3,rounding_size=0.2'  # Estilo uniforme para todos

    # Panel 0: Velas
    axes[0].text(
        0.01, top_margins[0], f"Precio: {ultimo['Close']:.2f}".ljust(15),
        transform=axes[0].transAxes,
        fontsize=11, color=color_vela, ha='left', va='top',
        bbox=dict(facecolor='none', edgecolor=color_vela, boxstyle=boxstyle, linewidth=1)
    )
    axes[0].text(
        0.01, top_margins[0] - vertical_margin, f"MA7: {ultimo['MA7']:.2f}".ljust(15),
        transform=axes[0].transAxes,
        fontsize=11, color='purple', ha='left', va='top',
        bbox=dict(facecolor='none', edgecolor='purple', boxstyle=boxstyle, linewidth=1)
    )
    axes[0].text(
        0.01, top_margins[0] - 2*vertical_margin, f"MA25: {ultimo['MA25']:.2f}".ljust(15),
        transform=axes[0].transAxes,
        fontsize=11, color='pink', ha='left', va='top',
        bbox=dict(facecolor='none', edgecolor='pink', boxstyle=boxstyle, linewidth=1)
    )
    axes[0].text(
        0.01, top_margins[0] - 3*vertical_margin, f"MA50: {ultimo['MA50']:.2f}".ljust(15),
        transform=axes[0].transAxes,
        fontsize=11, color='orange', ha='left', va='top',
        bbox=dict(facecolor='none', edgecolor='orange', boxstyle=boxstyle, linewidth=1)
    )
    axes[0].text(
        0.01, top_margins[0] - 4*vertical_margin, f"MA99: {ultimo['MA99']:.2f}".ljust(15),
        transform=axes[0].transAxes,
        fontsize=11, color='cyan', ha='left', va='top',
        bbox=dict(facecolor='none', edgecolor='cyan', boxstyle=boxstyle, linewidth=1)
    )
    # Panel 1: RSI
    axes[1].text(
        0.01, top_margins[1], f"RSI: {ultimo['RSI']:.2f}".ljust(15),
        transform=axes[1].transAxes,
        fontsize=11, color='blue', ha='left', va='top',
        bbox=dict(facecolor='none', edgecolor='blue', boxstyle=boxstyle, linewidth=1)
    )
    # Panel 2: MACD
    axes[2].text(
        0.01, top_margins[2], f"MACD: {ultimo['MACD']:.2f}".ljust(15),
        transform=axes[2].transAxes,
        fontsize=11, color='white', ha='left', va='top',
        bbox=dict(facecolor='none', edgecolor='white', boxstyle=boxstyle, linewidth=1)
    )
    axes[2].text(
        0.01, top_margins[2] - 2*vertical_margin, f"Signal: {ultimo['Signal']:.2f}".ljust(15),
        transform=axes[2].transAxes,
        fontsize=11, color='orange', ha='left', va='top',
        bbox=dict(facecolor='none', edgecolor='orange', boxstyle=boxstyle, linewidth=1)
    )
    axes[2].text(
        0.01, top_margins[2] - 4*vertical_margin, f"Delta: {(ultimo['MACD'] - ultimo['Signal']):.2f}".ljust(15),
        transform=axes[2].transAxes,
        fontsize=11, color='green' if (ultimo['MACD'] - ultimo['Signal']) >= 0 else 'red', ha='left', va='top',
        bbox=dict(facecolor='none', edgecolor='gray', boxstyle=boxstyle, linewidth=1)
    )
    
""" --- Graficar ---"""
def plot_charts(df):
    df_plot = df.copy()
    df_plot.index.name = 'Date'
    df_plot = df_plot[['Open', 'High', 'Low', 'Close', 'Volume', 'MA7', 'MA25', 'MA50', 'MA99', 'RSI', 'MACD', 'Signal']]

    apds = [
        mpf.make_addplot(df_plot['MA7'], color='purple', panel=0, width=1.0, secondary_y=False, label='MA 7'),
        mpf.make_addplot(df_plot['MA25'], color='pink', panel=0, width=1.0, secondary_y=False, label='MA 25'),
        mpf.make_addplot(df_plot['MA50'], color='orange', panel=0, width=1.0, secondary_y=False, label='MA 50'),
        mpf.make_addplot(df_plot['MA99'], color='cyan', panel=0, width=1.0, secondary_y=False, label='MA 99'),
        mpf.make_addplot(df_plot['RSI'], color='blue', panel=1, ylabel='RSI', label='RSI'),
        mpf.make_addplot(df_plot['MACD'], color='black', panel=2, ylabel='MACD', label='MACD'),
        mpf.make_addplot(df_plot['Signal'], color='orange', panel=2, label='Signal')
    ]

    fig, axes = mpf.plot(
        df_plot,
        type='candle',
        style='yahoo',
        addplot=apds,
        volume=True,
        panel_ratios=(2,1,1),
        ylabel='Precio',
        ylabel_lower='Volumen',
        title=f'{symbol_var.get()} - {interval_var.get()}',
        datetime_format='%Y-%m-%d %H:%M',
        xrotation=15,
        warn_too_much_data=10000,
        returnfig=True
    )

    # Títulos personalizados para cada panel
    axes[0].set_title('Velas + MA7 + MA25 + MA50 + MA99', fontsize=12)
    axes[1].set_title('RSI', fontsize=12)
    axes[2].set_title('MACD', fontsize=12)
    return fig

# --- Actualización automática ---
actualizando = True
canvas = None
fig = None

""" --- Funciones de la interfaz gráfica ---"""
def cargar_datos():
    symbol = symbol_var.get()
    interval = interval_var.get()
    try:
        df = obtener_historico_binance(symbol, interval)
        df = procesar_indicadores(df)
        mostrar_valores_actuales(df)
        for widget in frame_chart.winfo_children():
            widget.destroy()
        fig, axes = mpf.plot(
            df[['Open', 'High', 'Low', 'Close', 'Volume', 'MA7', 'MA25', 'MA99', 'RSI', 'MACD', 'Signal']],
            type='candle',
            style='yahoo',
            addplot=[
                mpf.make_addplot(df['MA7'], color='purple', panel=0, width=1.0, secondary_y=False, label='MA 7'),
                mpf.make_addplot(df['MA25'], color='pink', panel=0, width=1.0, secondary_y=False, label='MA 25'),
                mpf.make_addplot(df['MA99'], color='cyan', panel=0, width=1.0, secondary_y=False, label='MA 99'),
                mpf.make_addplot(df['RSI'], color='blue', panel=1, ylabel='RSI', label='RSI'),
                mpf.make_addplot(df['MACD'], color='black', panel=2, ylabel='MACD', label='MACD'),
                mpf.make_addplot(df['Signal'], color='orange', panel=2, label='Signal')
            ],
            volume=True,
            panel_ratios=(2,1,1),
            ylabel='Precio',
            ylabel_lower='Volumen',
            title=f'{symbol_var.get()} - {interval_var.get()}',
            datetime_format='%Y-%m-%d %H:%M',
            xrotation=15,
            warn_too_much_data=10000,
            returnfig=True
        )
        axes[0].set_title('Velas + MA7 + MA25 + MA50 + MA99', fontsize=12)
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
    plt.style.use('dark_background')  # <-- Fondo oscuro
    fig, axes = plt.subplots(3, 1, figsize=(18, 10), sharex=True, gridspec_kw={'height_ratios': [2, 1, 1]})
    canvas = FigureCanvasTkAgg(fig, master=frame_chart)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

""" --- Actualización periódica del gráfico ---"""
def actualizar_grafico():
    global actualizando, axes
    if actualizando:
        symbol = symbol_var.get()
        interval = interval_var.get()
        try:
            plt.style.use('dark_background')  # <-- Fondo oscuro también al actualizar
            df = obtener_historico_binance(symbol, interval)
            df = procesar_indicadores(df)
            df = estrategia.detectar_entradas(df)
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
            axes[0].plot(df_plot['Date'], df_plot['MA7'], color='purple', label='MA7')
            axes[0].plot(df_plot['Date'], df_plot['MA25'], color='pink', label='MA25')
            axes[0].plot(df_plot['Date'], df_plot['MA50'], color='orange', label='MA50')  # <-- AGREGADO
            axes[0].plot(df_plot['Date'], df_plot['MA99'], color='cyan', label='MA99')
            axes[0].set_title('Velas + MA7 + MA25 + MA50 + MA99')
            axes[0].legend()
            axes[0].set_ylabel('Precio')
            axes[0].xaxis_date()
            # Sombrea regiones de compra/venta
            estrategia.sombrear_regiones(axes, df)
            # Panel 1: RSI
            axes[1].plot(df_plot['Date'], df_plot['RSI'], color='blue', label='RSI')
            axes[1].axhline(70, color='red', linestyle='--')
            axes[1].axhline(30, color='green', linestyle='--')
            axes[1].set_title('RSI')
            axes[1].set_ylabel('RSI')
            axes[1].legend()
            # Panel 2: MACD
            axes[2].plot(df_plot['Date'], df_plot['MACD'], color='white', label='MACD')  # <-- Línea MACD blanca
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
            fig.suptitle(f'{symbol} - {interval}')
            fig.tight_layout()
            # Mostrar valores actuales en cada panel
            mostrar_valores_actuales(df)
            # Mostrar número de señales encontradas
            n_buy = df['Buy'].sum()
            n_sell = df['Sell'].sum()
            n_exit = df['Exit'].sum()
            label_signals.config(
                text=f"Entradas (Compra): {n_buy} | Entradas (Venta): {n_sell} | Salidas: {n_exit}"
            )
            canvas.draw()
        except Exception as e:
            for widget in frame_chart.winfo_children():
                widget.destroy()
            error_label = tk.Label(frame_chart, text=f"Error al obtener datos: {e}", fg="red")
            error_label.pack()
        root.after(1000, actualizar_grafico)

def detener_app():
    global actualizando
    actualizando = False
    root.destroy()
    import sys
    sys.exit(0)  # <-- fuerza la salida del proceso

if __name__ == "__main__":
    # --- Interfaz gráfica ---
    root = tk.Tk()
    root.title("Binance Chart Viewer")
    root.state('zoomed')  # Pantalla completa en Windows

    frame_controls = ttk.Frame(root)
    frame_controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

    ttk.Label(frame_controls, text="Símbolo:").pack(side=tk.LEFT)
    symbol_var = tk.StringVar(value=SYMBOLS[0])
    symbol_menu = ttk.OptionMenu(frame_controls, symbol_var, SYMBOLS[0], *SYMBOLS)
    symbol_menu.pack(side=tk.LEFT, padx=5)

    ttk.Label(frame_controls, text="Intervalo:").pack(side=tk.LEFT)
    interval_var = tk.StringVar(value=INTERVALS[5])
    interval_menu = ttk.OptionMenu(frame_controls, interval_var, INTERVALS[5], *INTERVALS)
    interval_menu.pack(side=tk.LEFT, padx=5)

    ttk.Button(frame_controls, text="Cargar y Graficar", command=cargar_datos).pack(side=tk.LEFT, padx=10)
    ttk.Button(frame_controls, text="Detener y Salir", command=detener_app).pack(side=tk.LEFT, padx=10)

    label_valores = tk.Label(root, text="", font=("Arial", 12), fg="blue")
    label_valores.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

    label_signals = tk.Label(root, text="", font=("Arial", 12), fg="darkgreen")
    label_signals.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

    frame_chart = ttk.Frame(root)
    frame_chart.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    inicializar_grafico()

    actualizar_grafico()
    root.mainloop()
    main()


