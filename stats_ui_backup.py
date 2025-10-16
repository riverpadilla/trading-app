"""Interfaz gráfica para mostrar estadísticas de variación usando tkinter."""
import tkinter as tk
from tkinter import ttk
import pandas as pd
import requests
import estrategia2

# --- Configuración de Binance US ---
SYMBOLS = ["BNBUSDT", "BTCUSDT", "ETHUSDT", "ADAUSDT", "DOGEUSDT"]
INTERVALS = ["1s", "1m", "5m", "15m", "30m", "1h", "4h", "1d"]
BINANCE_URL = "https://api.binance.us/api/v3/klines"

def obtener_datos_binance(symbol, interval, limit=10000):
    """Obtiene datos históricos de velas desde Binance US con paginación hacia atrás (endTime) hasta 10000.

    Estrategia: pedir el último lote disponible y continuar pidiendo lotes más antiguos
    usando endTime = (primer Open time del lote) - 1, hasta completar 'limit' o no
    haya más datos. Al final, se ordena por tiempo y se recortan las velas más recientes.
    """
    try:
        total = 0
        end_time_ms = None  # paginación hacia atrás
        frames = []
        remaining = max(0, int(limit))
        lote = 0

        while remaining > 0:
            batch_limit = 1000 if remaining > 1000 else remaining
            params = {
                "symbol": symbol.upper(),
                "interval": interval,
                "limit": batch_limit,
            }
            if end_time_ms is not None:
                params["endTime"] = end_time_ms

            response = requests.get(BINANCE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data:
                print(f"Paginación: No más datos disponibles. Total: {total}")
                break

            df_batch = pd.DataFrame(
                data,
                columns=[
                    "Open time", "Open", "High", "Low", "Close", "Volume",
                    "Close time", "Quote asset volume", "Number of trades",
                    "Taker buy base asset volume", "Taker buy quote asset volume", "Ignore"
                ]
            )

            batch_count = len(df_batch)
            first_open_time_ms = int(df_batch.iloc[0]["Open time"])  # más antiguo dentro del lote
            last_close_time_ms = int(df_batch.iloc[-1]["Close time"])  # más reciente dentro del lote
            lote += 1

            print(
                f"Lote {lote}: {batch_count} registros, Open time: {first_open_time_ms}, Close time: {last_close_time_ms}"
            )

            frames.append(df_batch)
            total += batch_count
            remaining -= batch_count

            # Preparar siguiente página: pedir velas ANTERIORES al primer Open time del lote actual
            end_time_ms = first_open_time_ms - 1

            if batch_count < batch_limit:
                print(f"Lote incompleto. Total final: {total}")
                break

        if not frames:
            return pd.DataFrame()

        # Unir y ordenar cronológicamente; eliminar posibles duplicados por Open time
        df = pd.concat(frames, ignore_index=True)
        df.drop_duplicates(subset=["Open time"], keep="last", inplace=True)
        df.sort_values(by="Open time", inplace=True)
        df.reset_index(drop=True, inplace=True)

        # Mantener las N más recientes si por algún motivo hubiese más
        if len(df) > limit:
            df = df.iloc[-limit:].copy()

        # Conversiones de tipo
        df["Open time"] = pd.to_datetime(df["Open time"], unit="ms")
        df["Close time"] = pd.to_datetime(df["Close time"], unit="ms")
        df["Open"] = df["Open"].astype(float)
        df["High"] = df["High"].astype(float)
        df["Low"] = df["Low"].astype(float)
        df["Close"] = df["Close"].astype(float)
        df["Volume"] = df["Volume"].astype(float)

        print(f"Datos finales: {len(df)} registros")
        return df
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener datos de Binance: {e}")
        return pd.DataFrame()

def mostrar_tabla_estadisticas(df, symbol="", interval=""):
    stats_df = estrategia2.calcular_estadisticas(df)
    fecha_inicio = df['Close time'].min().strftime('%Y-%m-%d %H:%M:%S') if 'Close time' in df.columns else "N/A"
    fecha_fin = df['Close time'].max().strftime('%Y-%m-%d %H:%M:%S') if 'Close time' in df.columns else "N/A"

    root = tk.Tk()
    titulo = f"Estadísticas de Variación - {symbol} ({interval})"
    if fecha_inicio != "N/A":
        titulo += f" | {fecha_inicio} → {fecha_fin}"
    root.title(titulo)

    frame = ttk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    columns = ("Estadística", "Valor", "Fecha/Hora", "Open/High", "Close/Low")
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=len(stats_df))

    tree.heading("Estadística", text="Estadística")
    tree.heading("Valor", text="Valor")
    tree.heading("Fecha/Hora", text="Fecha/Hora")
    tree.heading("Open/High", text="Open/High")
    tree.heading("Close/Low", text="Close/Low")

    tree.column("Estadística", anchor=tk.W, width=350)
    tree.column("Valor", anchor=tk.CENTER, width=120)
    tree.column("Fecha/Hora", anchor=tk.CENTER, width=180)
    tree.column("Open/High", anchor=tk.CENTER, width=120)
    tree.column("Close/Low", anchor=tk.CENTER, width=120)

    for _, row in stats_df.iterrows():
        tree.insert(
            "", tk.END,
            values=(
                row.get("Estadística", ""),
                f"{row.get('Valor', 0):.6f}",
                row.get("Fecha/Hora", ""),
                f"{row.get('Open/High', '')}" if row.get('Open/High', '') != '' else '',
                f"{row.get('Close/Low', '')}" if row.get('Close/Low', '') != '' else ''
            )
        )

    tree.pack(fill=tk.BOTH, expand=True)
    ttk.Button(root, text="Cerrar", command=root.destroy).pack(pady=10)
    root.mainloop()

def interfaz_principal():
    root = tk.Tk()
    root.title("Estadísticas de Trading - Binance US")
    root.geometry("600x350")
    
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(main_frame, text="Estadísticas de Variación de Precios", 
              font=("Arial", 14, "bold")).pack(pady=(0, 15))
    
    config_frame = ttk.Frame(main_frame)
    config_frame.pack(pady=(0, 10))
    
    ttk.Label(config_frame, text="Símbolo:", font=("Arial", 10)).grid(row=0, column=0, padx=10, pady=5, sticky="e")
    symbol_var = tk.StringVar(value=SYMBOLS[0])
    symbol_combo = ttk.Combobox(config_frame, textvariable=symbol_var, values=SYMBOLS, 
                                state="readonly", width=15, font=("Arial", 10))
    symbol_combo.grid(row=0, column=1, padx=10, pady=5)
    
    ttk.Label(config_frame, text="Intervalo:", font=("Arial", 10)).grid(row=1, column=0, padx=10, pady=5, sticky="e")
    interval_var = tk.StringVar(value=INTERVALS[1])
    interval_combo = ttk.Combobox(config_frame, textvariable=interval_var, values=INTERVALS, 
                                  state="readonly", width=15, font=("Arial", 10))
    interval_combo.grid(row=1, column=1, padx=10, pady=5)
    
    ttk.Label(config_frame, text="Cantidad de datos:", font=("Arial", 10)).grid(row=2, column=0, padx=10, pady=5, sticky="e")
    limit_var = tk.IntVar(value=100)

    # Crear primero la variable de entrada para evitar NameError en el callback del slider
    limit_entry_var = tk.StringVar(value=str(limit_var.get()))

    def on_slider_change(value):
        # Se invoca cuando se mueve el slider
        limit_var.set(int(float(value)))
        try:
            limit_entry_var.set(str(limit_var.get()))
        except Exception:
            pass

    def on_entry_change(*args):
        # Se invoca cuando cambia el texto del entry (se activará tras crear el slider)
        try:
            v = int(limit_entry_var.get())
            # Ajustar a múltiplos de 100 y límites [100, 10000]
            if v < 100:
                v = 100
            if v > 10000:
                v = 10000
            # Redondear al múltiplo de 100 más cercano
            v = int(round(v / 100.0)) * 100
            limit_var.set(v)
            # limit_slider ya existe cuando el trace está activo
            limit_slider.set(v)
        except ValueError:
            pass

    # Crear slider (pasos de 100) después de definir variables y callbacks
    limit_slider = tk.Scale(
        config_frame,
        from_=100,
        to=10000,
        orient=tk.HORIZONTAL,
        length=200,
        resolution=100,
        command=on_slider_change,
    )
    limit_slider.set(limit_var.get())
    limit_slider.grid(row=2, column=1, padx=10, pady=5, sticky="we")

    # Crear entry y luego activar el trace para evitar disparos antes de que exista el slider
    limit_entry = ttk.Entry(config_frame, textvariable=limit_entry_var, width=8, font=("Arial", 10))
    limit_entry.grid(row=2, column=2, padx=10, pady=5)
    limit_entry_var.trace_add('write', on_entry_change)
    
    status_label = ttk.Label(main_frame, text="", font=("Arial", 9), foreground="blue")
    status_label.pack(pady=(5, 10))
    
    def cargar_estadisticas():
        symbol = symbol_var.get()
        interval = interval_var.get()
        try:
            limit = int(limit_var.get())
            if limit < 100 or limit > 10000:
                status_label.config(text="Error: Límite debe estar entre 100 y 10000 (en pasos de 100)", foreground="red")
                return
        except ValueError:
            status_label.config(text="Error: Límite debe ser un número", foreground="red")
            return
        
        status_label.config(text=f"Cargando datos de {symbol} ({interval})...", foreground="blue")
        root.update()
        
        df = obtener_datos_binance(symbol, interval, limit)
        
        if df.empty:
            status_label.config(text="Error: No se pudieron obtener datos de Binance", foreground="red")
            return
        
        status_label.config(text=f"✓ Datos cargados: {len(df)} registros", foreground="green")
        mostrar_tabla_estadisticas(df, symbol, interval)
    
    buttons_frame = ttk.Frame(main_frame)
    buttons_frame.pack(pady=(5, 0))
    
    ttk.Button(buttons_frame, text="Mostrar Estadísticas", command=cargar_estadisticas,
              width=25).pack(pady=5)
    
    ttk.Button(buttons_frame, text="Salir", command=root.destroy, width=25).pack(pady=5)
    
    root.mainloop()

if __name__ == "__main__":
    interfaz_principal()
