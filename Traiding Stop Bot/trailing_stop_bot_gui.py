"""
GUI Mejorada para Bot de Trading con Trailing Stop Market
Incluye gráficos de velas, RSI y saldos en tiempo real
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from datetime import datetime, timedelta
from trailing_stop_bot import TrailingStopBot
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
from collections import deque

class TrailingStopBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Trailing Stop Bot - BNB/USDT [Advanced]")
        self.root.geometry("1400x900")
        self.root.resizable(True, True)
        
        # Configurar tema
        style = ttk.Style()
        style.theme_use('clam')
        
        # Inicializar bot
        self.bot = None
        self.update_thread = None
        self.is_updating = False
        
        # Datos para gráficos
        self.price_history = deque(maxlen=60)  # 60 minutos
        self.time_history = deque(maxlen=60)
        self.rsi_7_history = deque(maxlen=60)
        self.rsi_14_history = deque(maxlen=60)
        # Series de ticks (precio en tiempo real)
        self.tick_prices = deque(maxlen=300)  # ~5 minutos a 1s
        self.tick_times = deque(maxlen=300)
        
        # Crear interfaz
        self.create_widgets()
        
        # Iniciar actualización de GUI
        self.start_gui_update()
    
    def calculate_rsi(self, prices, period=14):
        """Calcula el RSI (Relative Strength Index)."""
        if len(prices) < period + 1:
            return None
        
        deltas = np.diff(prices)
        seed = deltas[:period]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        
        if down == 0:
            return 100
        
        rs = up / down
        rsi = 100 - (100 / (1 + rs))
        
        # RSI for remaining data
        for delta in deltas[period:]:
            if delta > 0:
                upval = delta
                downval = 0
            else:
                upval = 0
                downval = -delta
            
            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            
            if down == 0:
                rsi = 100
            else:
                rs = up / down
                rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def create_widgets(self):
        """Crea todos los widgets de la interfaz."""
        
        # Crear notebook para pestañas
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Pestaña 1: Control y Configuración
        control_tab = ttk.Frame(notebook)
        notebook.add(control_tab, text="⚙ Control")
        
        # Pestaña 2: Gráficos
        charts_tab = ttk.Frame(notebook)
        notebook.add(charts_tab, text="📊 Gráficos")
        
        # Crear contenido de cada pestaña
        self.create_control_tab(control_tab)
        self.create_charts_tab(charts_tab)
    
    def create_control_tab(self, parent):
        """Crea la pestaña de control y configuración."""
        
        # Frame principal con padding
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # === SECCIÓN 1: SALDOS EN TIEMPO REAL ===
        balance_frame = ttk.LabelFrame(main_frame, text="💰 Saldos en Binance (Tiempo Real)", padding="10")
        balance_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        balance_frame.columnconfigure(1, weight=1)
        balance_frame.columnconfigure(3, weight=1)
        
        # BNB Balance
        ttk.Label(balance_frame, text="BNB:", font=("Arial", 11, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=5
        )
        self.binance_bnb_var = tk.StringVar(value="0.00000000")
        ttk.Label(balance_frame, textvariable=self.binance_bnb_var, 
                 font=("Arial", 12, "bold"), foreground="blue").grid(
            row=0, column=1, sticky=tk.W, pady=5, padx=5
        )
        
        # USDT Balance
        ttk.Label(balance_frame, text="USDT:", font=("Arial", 11, "bold")).grid(
            row=0, column=2, sticky=tk.W, pady=5, padx=5
        )
        self.binance_usdt_var = tk.StringVar(value="$0.00")
        ttk.Label(balance_frame, textvariable=self.binance_usdt_var, 
                 font=("Arial", 12, "bold"), foreground="green").grid(
            row=0, column=3, sticky=tk.W, pady=5, padx=5
        )
        
        # Precio actual
        ttk.Label(balance_frame, text="Precio BNB/USDT:", font=("Arial", 11, "bold")).grid(
            row=1, column=0, sticky=tk.W, pady=5, padx=5
        )
        self.current_price_var = tk.StringVar(value="$0.00")
        ttk.Label(balance_frame, textvariable=self.current_price_var, 
                 font=("Arial", 12, "bold"), foreground="orange").grid(
            row=1, column=1, sticky=tk.W, pady=5, padx=5
        )
        
        # Botón actualizar saldos
        ttk.Button(balance_frame, text="🔄 Actualizar Saldos", 
                  command=self.force_update_balances).grid(
            row=1, column=2, columnspan=2, sticky=tk.W, padx=5
        )
        
        # === SECCIÓN DE ÓRDENES ACTIVAS (OCULTA HASTA QUE SE ACTIVE EL BOT) ===
        self.orders_frame = ttk.LabelFrame(main_frame, text="🎯 Órdenes Activas", padding="10")
        self.orders_frame.grid(row=0, column=2, rowspan=2, sticky=(tk.N, tk.E, tk.W), pady=5, padx=10)
        self.orders_frame.columnconfigure(1, weight=1)
        self.orders_frame.grid_remove()  # Ocultar inicialmente
        
        # Stop Loss Fijo
        ttk.Label(self.orders_frame, text="🛡️ Stop Loss (Fijo):", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=5
        )
        self.stop_loss_price_var = tk.StringVar(value="--")
        ttk.Label(self.orders_frame, textvariable=self.stop_loss_price_var, 
                 font=("Arial", 11, "bold"), foreground="red").grid(
            row=0, column=1, sticky=tk.W, pady=5, padx=5
        )
        
        # Trailing Stop Dinámico
        ttk.Label(self.orders_frame, text="📊 Trailing Stop (Dinámico):", font=("Arial", 10, "bold")).grid(
            row=1, column=0, sticky=tk.W, pady=5, padx=5
        )
        self.trailing_stop_price_var = tk.StringVar(value="--")
        ttk.Label(self.orders_frame, textvariable=self.trailing_stop_price_var, 
                 font=("Arial", 11, "bold"), foreground="blue").grid(
            row=1, column=1, sticky=tk.W, pady=5, padx=5
        )
        
        # Estado actual
        ttk.Label(self.orders_frame, text="Estado:", font=("Arial", 9)).grid(
            row=2, column=0, sticky=tk.W, pady=2, padx=5
        )
        self.order_state_var = tk.StringVar(value="--")
        ttk.Label(self.orders_frame, textvariable=self.order_state_var, 
                 font=("Arial", 9, "italic")).grid(
            row=2, column=1, sticky=tk.W, pady=2, padx=5
        )
        
        # Precio extremo actual
        ttk.Label(self.orders_frame, text="Precio Extremo:", font=("Arial", 9)).grid(
            row=3, column=0, sticky=tk.W, pady=2, padx=5
        )
        self.extreme_price_var = tk.StringVar(value="--")
        ttk.Label(self.orders_frame, textvariable=self.extreme_price_var, 
                 font=("Arial", 9, "italic")).grid(
            row=3, column=1, sticky=tk.W, pady=2, padx=5
        )
        
        # === SECCIÓN 2: CREDENCIALES ===
        cred_frame = ttk.LabelFrame(main_frame, text="🔑 Credenciales de API", padding="10")
        cred_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        cred_frame.columnconfigure(1, weight=1)
        
        ttk.Label(cred_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.api_key_var = tk.StringVar(value="7ZPT9vq9NRD8rDcV87ykvrPWBPQzPuZ9QkLKLLxGguQaDvT5mACl4nQSP8uwGxBH")
        ttk.Entry(cred_frame, textvariable=self.api_key_var, width=50).grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2
        )
        
        ttk.Label(cred_frame, text="API Secret:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.api_secret_var = tk.StringVar(value="SpCz5aKF9c16gpJec6EQ3r0BC4GAqjmTO1Bevh2193mvVEEdClpIhP2jx7Wf1QFO")
        ttk.Entry(cred_frame, textvariable=self.api_secret_var, width=50, show="*").grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2
        )
        
        self.testnet_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(cred_frame, text="Usar Testnet", variable=self.testnet_var).grid(
            row=2, column=0, columnspan=2, pady=5
        )
        
        # === SECCIÓN 3: CONFIGURACIÓN DEL BOT ===
        config_frame = ttk.LabelFrame(main_frame, text="⚙ Configuración del Bot", padding="10")
        config_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        config_frame.columnconfigure(1, weight=1)
        config_frame.columnconfigure(3, weight=1)
        
        # Cantidad inicial de BNB
        ttk.Label(config_frame, text="Cantidad BNB inicial:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.initial_bnb_var = tk.StringVar(value="0.1")
        ttk.Entry(config_frame, textvariable=self.initial_bnb_var, width=15).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=2
        )
        
        ttk.Label(config_frame, text="BNB").grid(row=0, column=2, sticky=tk.W)
        
        # Separador
        ttk.Separator(config_frame, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Stop Loss Fijo
        ttk.Label(config_frame, text="🛡️ Stop Loss % (Fijo):", font=("Arial", 9, "bold")).grid(row=2, column=0, sticky=tk.W, pady=2)
        self.stop_loss_var = tk.StringVar(value="2.0")
        ttk.Entry(config_frame, textvariable=self.stop_loss_var, width=15).grid(
            row=2, column=1, sticky=tk.W, padx=5, pady=2
        )
        ttk.Label(config_frame, text="% (limita pérdidas)").grid(row=2, column=2, sticky=tk.W)
        
        # Trailing distance para compra
        ttk.Label(config_frame, text="📈 Trailing % Compra:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.trailing_buy_var = tk.StringVar(value="1.0")
        ttk.Entry(config_frame, textvariable=self.trailing_buy_var, width=15).grid(
            row=3, column=1, sticky=tk.W, padx=5, pady=2
        )
        ttk.Label(config_frame, text="% (dinámico, sigue precio)").grid(row=3, column=2, sticky=tk.W)
        
        # Trailing distance para venta
        ttk.Label(config_frame, text="📉 Trailing % Venta:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.trailing_sell_var = tk.StringVar(value="1.0")
        ttk.Entry(config_frame, textvariable=self.trailing_sell_var, width=15).grid(
            row=4, column=1, sticky=tk.W, padx=5, pady=2
        )
        ttk.Label(config_frame, text="% (dinámico, sigue precio)").grid(row=4, column=2, sticky=tk.W)
        
        # === SECCIÓN 4: CONTROL DEL BOT ===
        control_frame = ttk.LabelFrame(main_frame, text="🎮 Control", padding="10")
        control_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)
        
        self.start_button = ttk.Button(
            button_frame, 
            text="▶ Iniciar Bot", 
            command=self.start_bot,
            style="Success.TButton"
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(
            button_frame, 
            text="⬛ Detener Bot", 
            command=self.stop_bot,
            state=tk.DISABLED,
            style="Danger.TButton"
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Estado del bot
        self.status_var = tk.StringVar(value="Estado: DETENIDO")
        status_label = ttk.Label(
            button_frame, 
            textvariable=self.status_var, 
            font=("Arial", 10, "bold")
        )
        status_label.pack(side=tk.LEFT, padx=20)
        
        # === SECCIÓN 5: ESTADÍSTICAS Y P&L ===
        stats_frame = ttk.LabelFrame(main_frame, text="📊 Estadísticas y P&L", padding="10")
        stats_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        stats_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(3, weight=1)
        
        # Trades
        ttk.Label(stats_frame, text="Total Trades:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.total_trades_var = tk.StringVar(value="0")
        ttk.Label(stats_frame, textvariable=self.total_trades_var, font=("Arial", 10, "bold")).grid(
            row=0, column=1, sticky=tk.W, padx=5
        )
        
        ttk.Label(stats_frame, text="Exitosos:").grid(row=0, column=2, sticky=tk.W, pady=2)
        self.successful_trades_var = tk.StringVar(value="0")
        ttk.Label(stats_frame, textvariable=self.successful_trades_var, 
                 font=("Arial", 10, "bold"), foreground="green").grid(
            row=0, column=3, sticky=tk.W, padx=5
        )
        
        # Balances
        ttk.Label(stats_frame, text="Balance USDT:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.usdt_balance_var = tk.StringVar(value="$0.00")
        ttk.Label(stats_frame, textvariable=self.usdt_balance_var, font=("Arial", 10, "bold")).grid(
            row=1, column=1, sticky=tk.W, padx=5
        )
        
        ttk.Label(stats_frame, text="Balance BNB:").grid(row=1, column=2, sticky=tk.W, pady=2)
        self.bnb_balance_var = tk.StringVar(value="0.000")
        ttk.Label(stats_frame, textvariable=self.bnb_balance_var, font=("Arial", 10, "bold")).grid(
            row=1, column=3, sticky=tk.W, padx=5
        )
        
        # P&L
        ttk.Label(stats_frame, text="P&L Realizado:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.realized_pnl_var = tk.StringVar(value="$0.00")
        self.realized_pnl_label = ttk.Label(
            stats_frame, 
            textvariable=self.realized_pnl_var, 
            font=("Arial", 11, "bold")
        )
        self.realized_pnl_label.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(stats_frame, text="P&L Total:").grid(row=2, column=2, sticky=tk.W, pady=2)
        self.total_pnl_var = tk.StringVar(value="$0.00")
        self.total_pnl_label = ttk.Label(
            stats_frame, 
            textvariable=self.total_pnl_var, 
            font=("Arial", 11, "bold")
        )
        self.total_pnl_label.grid(row=2, column=3, sticky=tk.W, padx=5)
        
        # Precios
        ttk.Label(stats_frame, text="Último precio compra:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.last_buy_var = tk.StringVar(value="$0.00")
        ttk.Label(stats_frame, textvariable=self.last_buy_var, font=("Arial", 9)).grid(
            row=3, column=1, sticky=tk.W, padx=5
        )
        
        ttk.Label(stats_frame, text="Último precio venta:").grid(row=3, column=2, sticky=tk.W, pady=2)
        self.last_sell_var = tk.StringVar(value="$0.00")
        ttk.Label(stats_frame, textvariable=self.last_sell_var, font=("Arial", 9)).grid(
            row=2, column=3, sticky=tk.W, padx=5
        )
        
        # === SECCIÓN 6: LOG DE ACTIVIDAD ===
        # Log a la derecha ocupando varias filas
        log_frame = ttk.LabelFrame(main_frame, text="📝 Log de Actividad", padding="10")
        log_frame.grid(row=1, column=2, rowspan=4, sticky=(tk.N, tk.S, tk.E, tk.W), pady=5, padx=10)
        main_frame.columnconfigure(2, weight=1)
        for r in range(1, 5):
            main_frame.rowconfigure(r, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=12, 
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configurar colores para el log
        self.log_text.tag_config("INFO", foreground="black")
        self.log_text.tag_config("SUCCESS", foreground="green")
        self.log_text.tag_config("ERROR", foreground="red")
        self.log_text.tag_config("WARNING", foreground="orange")
        
        # Estilos
        style = ttk.Style()
        style.configure("Success.TButton", foreground="green")
        style.configure("Danger.TButton", foreground="red")
    
    def create_charts_tab(self, parent):
        """Crea la pestaña de gráficos."""
        
        # Frame principal
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crear figura de matplotlib
        self.fig = Figure(figsize=(12, 8), dpi=100)
        
        # Subplot 1: Precio (velas)
        self.ax1 = self.fig.add_subplot(311)
        self.ax1.set_title('BNB/USDT - Precio (1 min)', fontsize=12, fontweight='bold')
        self.ax1.set_ylabel('Precio (USDT)', fontsize=10)
        self.ax1.grid(True, alpha=0.3)
        
        # Subplot 2: RSI 7
        self.ax2 = self.fig.add_subplot(312)
        self.ax2.set_title('RSI 7 periodos', fontsize=11, fontweight='bold')
        self.ax2.set_ylabel('RSI', fontsize=10)
        self.ax2.axhline(y=70, color='r', linestyle='--', alpha=0.5, label='Sobrecompra')
        self.ax2.axhline(y=30, color='g', linestyle='--', alpha=0.5, label='Sobreventa')
        self.ax2.set_ylim(0, 100)
        self.ax2.grid(True, alpha=0.3)
        self.ax2.legend(loc='upper right', fontsize=8)
        
        # Subplot 3: RSI 14
        self.ax3 = self.fig.add_subplot(313)
        self.ax3.set_title('RSI 14 periodos', fontsize=11, fontweight='bold')
        self.ax3.set_ylabel('RSI', fontsize=10)
        self.ax3.set_xlabel('Tiempo', fontsize=10)
        self.ax3.axhline(y=70, color='r', linestyle='--', alpha=0.5, label='Sobrecompra')
        self.ax3.axhline(y=30, color='g', linestyle='--', alpha=0.5, label='Sobreventa')
        self.ax3.set_ylim(0, 100)
        self.ax3.grid(True, alpha=0.3)
        self.ax3.legend(loc='upper right', fontsize=8)
        
        self.fig.tight_layout()
        
        # Canvas para la figura
        self.canvas = FigureCanvasTkAgg(self.fig, master=main_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Botón para actualizar gráficos
        ttk.Button(main_frame, text="🔄 Actualizar Gráficos", 
                  command=self.update_charts_async).pack(pady=5)
    
    def update_charts_async(self):
        """Obtiene datos de klines en un hilo y luego actualiza los gráficos en el hilo de UI."""
        def run():
            try:
                if not self.bot:
                    temp_bot = TrailingStopBot(
                        self.api_key_var.get(),
                        self.api_secret_var.get(),
                        self.testnet_var.get()
                    )
                    client = temp_bot.client
                else:
                    client = self.bot.client
                klines = client.get_klines(symbol='BNBUSDT', interval='1m', limit=60)
                times = []
                prices = []
                for k in klines:
                    timestamp = datetime.fromtimestamp(k[0] / 1000)
                    close_price = float(k[4])
                    times.append(timestamp)
                    prices.append(close_price)
                # Calcular RSI
                rsi_7 = rsi_14 = None
                if len(prices) >= 15:
                    prices_array = np.array(prices)
                    rsi_7 = self.calculate_rsi(prices_array[-15:], period=7)
                    rsi_14 = self.calculate_rsi(prices_array, period=14)
                self.root.after(0, self._apply_charts, times, prices, rsi_7, rsi_14)
            except Exception as e:
                self.root.after(0, self.log_message, f"✗ Error actualizando gráficos: {e}", "ERROR")
        threading.Thread(target=run, daemon=True).start()

    def _apply_charts(self, times, prices, rsi_7, rsi_14):
        """Aplica los datos recibidos a los gráficos (UI thread)."""
        if not times or not prices:
            return
        # Actualizar historial
        self.time_history = deque(times, maxlen=60)
        self.price_history = deque(prices, maxlen=60)
        if rsi_7 is not None:
            self.rsi_7_history.append(rsi_7)
        if rsi_14 is not None:
            self.rsi_14_history.append(rsi_14)
        # Limpiar y dibujar
        self.ax1.clear(); self.ax2.clear(); self.ax3.clear()
        self.ax1.plot(times, prices, color='blue', linewidth=2, label='Precio')
        self.ax1.scatter(times[-1:], prices[-1:], color='red', s=100, zorder=5, label='Actual')
        self.ax1.set_title(f'BNB/USDT - Precio: ${prices[-1]:.2f}', fontsize=12, fontweight='bold')
        self.ax1.set_ylabel('Precio (USDT)', fontsize=10)
        self.ax1.grid(True, alpha=0.3)
        self.ax1.legend(loc='upper left', fontsize=8)
        self.ax1.tick_params(axis='x', rotation=45, labelsize=8)
        # RSI 7
        if len(self.rsi_7_history) > 0:
            rsi_7_list = list(self.rsi_7_history)
            times_rsi = list(self.time_history)[-len(rsi_7_list):]
            self.ax2.plot(times_rsi, rsi_7_list, color='purple', linewidth=2, label='RSI 7')
            self.ax2.axhline(y=70, color='r', linestyle='--', alpha=0.5, label='Sobrecompra')
            self.ax2.axhline(y=30, color='g', linestyle='--', alpha=0.5, label='Sobreventa')
            self.ax2.axhline(y=50, color='gray', linestyle=':', alpha=0.3)
            self.ax2.fill_between(times_rsi, 70, 100, alpha=0.1, color='red')
            self.ax2.fill_between(times_rsi, 0, 30, alpha=0.1, color='green')
            self.ax2.set_title(f'RSI 7 periodos: {rsi_7_list[-1]:.2f}', fontsize=11, fontweight='bold')
            self.ax2.set_ylabel('RSI', fontsize=10)
            self.ax2.set_ylim(0, 100)
            self.ax2.grid(True, alpha=0.3)
            self.ax2.legend(loc='upper right', fontsize=8)
            self.ax2.tick_params(axis='x', rotation=45, labelsize=8)
        # RSI 14
        if len(self.rsi_14_history) > 0:
            rsi_14_list = list(self.rsi_14_history)
            times_rsi = list(self.time_history)[-len(rsi_14_list):]
            self.ax3.plot(times_rsi, rsi_14_list, color='orange', linewidth=2, label='RSI 14')
            self.ax3.axhline(y=70, color='r', linestyle='--', alpha=0.5, label='Sobrecompra')
            self.ax3.axhline(y=30, color='g', linestyle='--', alpha=0.5, label='Sobreventa')
            self.ax3.axhline(y=50, color='gray', linestyle=':', alpha=0.3)
            self.ax3.fill_between(times_rsi, 70, 100, alpha=0.1, color='red')
            self.ax3.fill_between(times_rsi, 0, 30, alpha=0.1, color='green')
            self.ax3.set_title(f'RSI 14 periodos: {rsi_14_list[-1]:.2f}', fontsize=11, fontweight='bold')
            self.ax3.set_ylabel('RSI', fontsize=10)
            self.ax3.set_xlabel('Tiempo', fontsize=10)
            self.ax3.set_ylim(0, 100)
            self.ax3.grid(True, alpha=0.3)
            self.ax3.legend(loc='upper right', fontsize=8)
            self.ax3.tick_params(axis='x', rotation=45, labelsize=8)
        self.fig.tight_layout()
        self.canvas.draw()

    def _apply_tick(self, price):
        """Aplica un tick de precio a la UI (sin IO)."""
        now = datetime.now()
        self.tick_prices.append(price)
        self.tick_times.append(now)
        self.current_price_var.set(f"${price:.2f}")
        # Redibujar eje de precio
        self.ax1.clear()
        times = list(self.tick_times)
        prices = list(self.tick_prices)
        self.ax1.plot(times, prices, color='blue', linewidth=1.8, label='Tick')
        self.ax1.scatter(times[-1:], prices[-1:], color='red', s=60, zorder=5, label='Actual')
        self.ax1.set_title(f'BNB/USDT - Precio (ticks): ${prices[-1]:.2f}', fontsize=12, fontweight='bold')
        self.ax1.set_ylabel('Precio (USDT)', fontsize=10)
        self.ax1.grid(True, alpha=0.3)
        self.ax1.legend(loc='upper left', fontsize=8)
        self.ax1.tick_params(axis='x', rotation=45, labelsize=8)
        self.fig.tight_layout()
        self.canvas.draw()
    
    def force_update_balances(self):
        """Fuerza la actualización de saldos."""
        threading.Thread(target=self._update_balances_thread, daemon=True).start()
    
    def _update_balances_thread(self):
        """Actualiza saldos en thread separado."""
        try:
            if not self.bot:
                temp_bot = TrailingStopBot(
                    self.api_key_var.get(),
                    self.api_secret_var.get(),
                    self.testnet_var.get()
                )
                balances = temp_bot.get_balances()
                current_price = temp_bot.get_current_price()
            else:
                balances = self.bot.get_balances()
                current_price = self.bot.get_current_price()
            
            if balances:
                bnb_balance = balances.get('BNB', {}).get('free', 0)
                usdt_balance = balances.get('USDT', {}).get('free', 0)
                
                self.root.after(0, lambda: self.binance_bnb_var.set(f"{bnb_balance:.8f}"))
                self.root.after(0, lambda: self.binance_usdt_var.set(f"${usdt_balance:.2f}"))
            
            if current_price:
                self.root.after(0, lambda: self.current_price_var.set(f"${current_price:.2f}"))
                self.root.after(0, lambda: self.log_message("✓ Saldos actualizados", "SUCCESS"))
            
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"✗ Error: {e}", "ERROR"))
    
    def log_message(self, message, level="INFO"):
        """Añade un mensaje al log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, formatted_msg, level)
        self.log_text.see(tk.END)
        self.log_text.update()
    
    def validate_inputs(self):
        """Valida los inputs antes de iniciar el bot."""
        try:
            # Validar API keys
            if not self.api_key_var.get() or not self.api_secret_var.get():
                raise ValueError("Las credenciales API son obligatorias")
            
            # Validar cantidad de BNB
            initial_bnb = float(self.initial_bnb_var.get())
            if initial_bnb <= 0:
                raise ValueError("La cantidad de BNB debe ser mayor a 0")
            
            # Validar stop loss
            stop_loss = float(self.stop_loss_var.get())
            if stop_loss <= 0 or stop_loss > 10:
                raise ValueError("El stop loss % debe estar entre 0 y 10")
            
            # Validar trailing percentages
            trailing_buy = float(self.trailing_buy_var.get())
            trailing_sell = float(self.trailing_sell_var.get())
            
            if trailing_buy <= 0 or trailing_buy > 5:
                raise ValueError("El trailing % de compra debe estar entre 0 y 5")
            
            if trailing_sell <= 0 or trailing_sell > 5:
                raise ValueError("El trailing % de venta debe estar entre 0 y 5")
            
            return True, initial_bnb, stop_loss, trailing_buy, trailing_sell
            
        except ValueError as e:
            messagebox.showerror("Error de Validación", str(e))
            return False, None, None, None, None
    
    def start_bot(self):
        """Inicia el bot de trading."""
        # Validar inputs
        valid, initial_bnb, stop_loss, trailing_buy, trailing_sell = self.validate_inputs()
        if not valid:
            return
        
        try:
            # Crear instancia del bot
            self.log_message("Inicializando bot...", "INFO")
            self.bot = TrailingStopBot(
                self.api_key_var.get(),
                self.api_secret_var.get(),
                self.testnet_var.get()
            )
            
            # Redirigir logging del bot a la GUI
            self.setup_bot_logging()
            
            # Iniciar bot en thread separado
            def start_thread():
                success = self.bot.start(initial_bnb, stop_loss, trailing_buy, trailing_sell)
                if success:
                    self.log_message("✓ Bot iniciado correctamente", "SUCCESS")
                    self.root.after(0, self.update_ui_state, True)
                else:
                    self.log_message("✗ Error al iniciar el bot", "ERROR")
                    self.root.after(0, self.update_ui_state, False)
            
            thread = threading.Thread(target=start_thread, daemon=True)
            thread.start()
            
        except Exception as e:
            self.log_message(f"✗ Error: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Error al iniciar el bot:\n{str(e)}")
    
    def stop_bot(self):
        """Detiene el bot de trading."""
        if self.bot and self.bot.is_running:
            self.log_message("Deteniendo bot...", "WARNING")
            
            def stop_thread():
                self.bot.stop()
                self.log_message("✓ Bot detenido", "INFO")
                self.root.after(0, self.update_ui_state, False)
            
            thread = threading.Thread(target=stop_thread, daemon=True)
            thread.start()
    
    def update_ui_state(self, running):
        """Actualiza el estado de los controles de la UI."""
        if running:
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_var.set("Estado: EJECUTANDO ✓")
            self.orders_frame.grid()  # Mostrar frame de órdenes activas
        else:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_var.set("Estado: DETENIDO")
            self.orders_frame.grid_remove()  # Ocultar frame de órdenes activas
    
    def setup_bot_logging(self):
        """Redirige el logging del bot a la GUI."""
        import logging
        
        class GUILogHandler(logging.Handler):
            def __init__(self, gui):
                super().__init__()
                self.gui = gui
            
            def emit(self, record):
                msg = self.format(record)
                level = "INFO"
                if record.levelno >= logging.ERROR:
                    level = "ERROR"
                elif record.levelno >= logging.WARNING:
                    level = "WARNING"
                elif "✓" in msg or "completada" in msg.lower():
                    level = "SUCCESS"
                
                self.gui.root.after(0, self.gui.log_message, msg, level)
        
        # Añadir handler
        handler = GUILogHandler(self)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logging.getLogger().addHandler(handler)
    
    def update_statistics(self):
        """Actualiza las estadísticas en la GUI."""
        if self.bot:
            status = self.bot.get_status()
            
            self.total_trades_var.set(str(status['total_trades']))
            self.successful_trades_var.set(str(status['successful_trades']))
            
            realized = status['realized_pnl']
            total = status['total_pnl']
            
            self.realized_pnl_var.set(f"${realized:.2f}")
            self.total_pnl_var.set(f"${total:.2f}")
            
            # Actualizar órdenes activas si el bot está corriendo
            if status['is_running']:
                self.update_active_orders()
            
            realized_color = "green" if realized >= 0 else "red"
            total_color = "green" if total >= 0 else "red"
            
            self.realized_pnl_label.config(foreground=realized_color)
            self.total_pnl_label.config(foreground=total_color)
            
            self.last_buy_var.set(f"${status['last_buy_price']:.2f}")
            self.last_sell_var.set(f"${status['last_sell_price']:.2f}")
            
            if status['is_running']:
                self.status_var.set(f"Estado: {status['state']} ✓")
        
        # Actualizar saldos de Binance
        self._update_balances_thread()
    
    def update_active_orders(self):
        """Actualiza la información de órdenes activas en la GUI."""
        try:
            if not self.bot or not self.bot.is_running:
                self.orders_frame.grid_remove()
                return
            
            # Mostrar el frame de órdenes
            self.orders_frame.grid()
            
            # Determinar estado (comprando o vendiendo)
            state = self.bot.current_state
            
            if state in ("WAITING_BUY", "BUYING"):
                self.order_state_var.set("Esperando compra (posición en USDT)")
                
                # Stop Loss Fijo - se activa si precio SUBE
                if hasattr(self.bot, 'sell_entry_price') and self.bot.sell_entry_price:
                    stop_loss_price = self.bot.sell_entry_price * (1 + self.bot.stop_loss_percent / 100)
                    self.stop_loss_price_var.set(f"${stop_loss_price:.2f} ↑")
                else:
                    self.stop_loss_price_var.set("--")
                
                # Trailing Stop Dinámico - sigue el precio a la baja
                if hasattr(self.bot, 'lowest_price_since_sell') and self.bot.lowest_price_since_sell:
                    trailing_price = self.bot.lowest_price_since_sell * (1 + self.bot.trailing_percent_buy / 100)
                    self.trailing_stop_price_var.set(f"${trailing_price:.2f} (base: ${self.bot.lowest_price_since_sell:.2f})")
                    self.extreme_price_var.set(f"Mínimo: ${self.bot.lowest_price_since_sell:.2f}")
                else:
                    self.trailing_stop_price_var.set("--")
                    self.extreme_price_var.set("--")
                
            elif state in ("WAITING_SELL", "SELLING"):
                self.order_state_var.set("Esperando venta (posición en BNB)")
                
                # Stop Loss Fijo - se activa si precio BAJA
                if hasattr(self.bot, 'buy_entry_price') and self.bot.buy_entry_price:
                    stop_loss_price = self.bot.buy_entry_price * (1 - self.bot.stop_loss_percent / 100)
                    self.stop_loss_price_var.set(f"${stop_loss_price:.2f} ↓")
                else:
                    self.stop_loss_price_var.set("--")
                
                # Trailing Stop Dinámico - sigue el precio al alza
                if hasattr(self.bot, 'highest_price_since_buy') and self.bot.highest_price_since_buy:
                    trailing_price = self.bot.highest_price_since_buy * (1 - self.bot.trailing_percent_sell / 100)
                    self.trailing_stop_price_var.set(f"${trailing_price:.2f} (base: ${self.bot.highest_price_since_buy:.2f})")
                    self.extreme_price_var.set(f"Máximo: ${self.bot.highest_price_since_buy:.2f}")
                else:
                    self.trailing_stop_price_var.set("--")
                    self.extreme_price_var.set("--")
            else:
                self.order_state_var.set(state)
                self.stop_loss_price_var.set("--")
                self.trailing_stop_price_var.set("--")
                self.extreme_price_var.set("--")
                
        except Exception as e:
            self.log_message(f"Error actualizando órdenes activas: {e}", "ERROR")
    
    def start_gui_update(self):
        """Inicia el loop de actualización de la GUI."""
        def update_loop():
            while True:
                if self.bot:
                    self.root.after(0, self.update_statistics)
                time.sleep(3)
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
        
        # Loop rápido cada 1s para ticks; refresco completo cada 60s
        def chart_update_loop():
            counter = 0
            while True:
                time.sleep(1)
                counter += 1
                # Obtener precio en este hilo y aplicar en UI
                try:
                    price = None
                    if self.bot:
                        price = self.bot.get_current_price()
                    else:
                        temp_bot = TrailingStopBot(
                            self.api_key_var.get(),
                            self.api_secret_var.get(),
                            self.testnet_var.get()
                        )
                        price = temp_bot.get_current_price()
                    if price:
                        self.root.after(0, self._apply_tick, price)
                except Exception:
                    pass
                # Cada 60s refrescar klines + RSI
                if counter % 60 == 0:
                    self.root.after(0, self.update_charts_async)
        
        threading.Thread(target=chart_update_loop, daemon=True).start()
        
        # Primera actualización inmediata de gráficos
        self.root.after(1000, self.update_charts_async)
    
    def _update_current_price(self):
        """Actualiza solo el precio actual sin afectar los balances."""
        try:
            if self.bot:
                current_price = self.bot.get_current_price()
                if current_price:
                    self.current_price_var.set(f"${current_price:.2f}")
        except Exception as e:
            pass  # Ignorar errores silenciosamente para no saturar el log
    
    def on_closing(self):
        """Maneja el cierre de la aplicación."""
        if self.bot and self.bot.is_running:
            if messagebox.askokcancel("Salir", "El bot está ejecutándose. ¿Desea detenerlo y salir?"):
                self.bot.stop()
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    root = tk.Tk()
    app = TrailingStopBotGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
