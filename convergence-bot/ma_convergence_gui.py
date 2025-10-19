#!/usr/bin/env python3
"""
GUI para Bot MA Convergence - Trading en Tiempo Real
Interfaz gráfica completa para monitorear y controlar el bot
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import queue
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FormatStrFormatter
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from ma_convergence_bot import MAConvergenceBot
import talib

class MAConvergenceGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 MA Convergence Trading Bot - Monitor")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1e1e1e')
        
        # Variables del bot
        self.bot_thread = None
        self.is_running = False
        self.client = None
        self.position = None
        self.entry_price = 0.0
        self.balance_usdt = 0.0
        self.balance_bnb = 0.0
        self.current_price = 0.0
        
        # Datos para gráfico
        self.price_data = []
        self.time_data = []
        self.max_data_points = 100
        
        # Cola para comunicación entre threads
        self.message_queue = queue.Queue()
        
        # Configurar estilo
        self.setup_style()
        
        # Crear interfaz
        self.create_widgets()
        
        # Inicializar valores por defecto
        self.load_default_config()
        
        # Iniciar actualizaciones
        self.root.after(100, self.process_queue)
    
    def setup_style(self):
        """Configurar estilo dark theme"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colores del tema oscuro
        style.configure('Dark.TFrame', background='#2b2b2b')
        style.configure('Dark.TLabel', background='#2b2b2b', foreground='white')
        style.configure('Dark.TButton', background='#404040', foreground='white')
        style.map('Dark.TButton', 
                 background=[('active', '#505050'), ('pressed', '#606060')])
        
        style.configure('Success.TButton', background='#28a745', foreground='white')
        style.map('Success.TButton',
                 background=[('active', '#34ce57'), ('pressed', '#1e7e34')])
        
        style.configure('Danger.TButton', background='#dc3545', foreground='white')
        style.map('Danger.TButton',
                 background=[('active', '#e4606d'), ('pressed', '#bd2130')])
    
    def create_widgets(self):
        """Crear todos los widgets de la interfaz"""
        # Frame principal
        main_frame = ttk.Frame(self.root, style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título
        title_label = tk.Label(main_frame, 
                              text="🤖 MA Convergence Trading Bot", 
                              font=('Arial', 16, 'bold'),
                              bg='#1e1e1e', fg='#00ff88')
        title_label.pack(pady=(0, 10))
        
        # Frame superior - Controles
        control_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.create_control_panel(control_frame)
        
        # Frame medio - Información y configuración
        info_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.create_info_panel(info_frame)
        
        # Frame inferior - Gráfico y log
        bottom_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        bottom_frame.pack(fill=tk.BOTH, expand=True)
        
        self.create_chart_and_log(bottom_frame)
    
    def create_control_panel(self, parent):
        """Panel de controles principales"""
        # Frame izquierdo - Botones principales
        left_frame = ttk.Frame(parent, style='Dark.TFrame')
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        
        # Botón Start/Stop
        self.start_stop_btn = ttk.Button(left_frame, 
                                        text="🚀 INICIAR BOT",
                                        command=self.toggle_bot,
                                        style='Success.TButton',
                                        width=15)
        self.start_stop_btn.pack(pady=5)
        
        # Botón configuración optimizada
        opt_config_btn = ttk.Button(left_frame,
                                   text="🎯 Config Óptima",
                                   command=self.load_optimized_config,
                                   style='Dark.TButton',
                                   width=15)
        opt_config_btn.pack(pady=5)
        
        # Botón test conexión
        test_btn = ttk.Button(left_frame,
                             text="🔗 Test Conexión",
                             command=self.test_connection,
                             style='Dark.TButton',
                             width=15)
        test_btn.pack(pady=5)
        
        # Frame derecho - Configuración básica
        right_frame = ttk.Frame(parent, style='Dark.TFrame')
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Monto inicial
        ttk.Label(right_frame, text="💰 Monto Inicial (USDT):", style='Dark.TLabel').grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.amount_var = tk.StringVar(value="100")
        amount_entry = ttk.Entry(right_frame, textvariable=self.amount_var, width=10)
        amount_entry.grid(row=0, column=1, padx=5, pady=2)
        
        # Umbral MA1
        ttk.Label(right_frame, text="📊 Umbral MA1:", style='Dark.TLabel').grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.ma1_var = tk.StringVar(value="0.0375")
        ma1_entry = ttk.Entry(right_frame, textvariable=self.ma1_var, width=10)
        ma1_entry.grid(row=1, column=1, padx=5, pady=2)
        
        # Umbral MA2
        ttk.Label(right_frame, text="📈 Umbral MA2:", style='Dark.TLabel').grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.ma2_var = tk.StringVar(value="0.052")
        ma2_entry = ttk.Entry(right_frame, textvariable=self.ma2_var, width=10)
        ma2_entry.grid(row=2, column=1, padx=5, pady=2)
        
        # Symbol
        ttk.Label(right_frame, text="🎯 Par:", style='Dark.TLabel').grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.symbol_var = tk.StringVar(value="BNBUSDT")
        symbol_entry = ttk.Entry(right_frame, textvariable=self.symbol_var, width=10)
        symbol_entry.grid(row=0, column=3, padx=5, pady=2)
        
        # Testnet checkbox
        self.testnet_var = tk.BooleanVar(value=True)
        testnet_check = ttk.Checkbutton(right_frame, 
                                       text="🧪 Testnet",
                                       variable=self.testnet_var)
        testnet_check.grid(row=1, column=2, columnspan=2, sticky=tk.W, padx=5, pady=2)
    
    def create_info_panel(self, parent):
        """Panel de información del bot"""
        # Frame izquierdo - Estado
        status_frame = tk.LabelFrame(parent, text="📊 Estado del Bot", 
                                   bg='#2b2b2b', fg='white', font=('Arial', 10, 'bold'))
        status_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Estado
        self.status_label = tk.Label(status_frame, text="⭕ Detenido", 
                                   bg='#2b2b2b', fg='#ff6b6b', font=('Arial', 12, 'bold'))
        self.status_label.pack(pady=5)
        
        # Precio actual
        self.price_label = tk.Label(status_frame, text="Precio: $0.00", 
                                  bg='#2b2b2b', fg='white')
        self.price_label.pack(pady=2)
        
        # Posición
        self.position_label = tk.Label(status_frame, text="Posición: None", 
                                     bg='#2b2b2b', fg='white')
        self.position_label.pack(pady=2)
        
        # Frame derecho - Balances
        balance_frame = tk.LabelFrame(parent, text="💰 Balances", 
                                    bg='#2b2b2b', fg='white', font=('Arial', 10, 'bold'))
        balance_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Balance USDT
        self.usdt_label = tk.Label(balance_frame, text="USDT: $0.00", 
                                 bg='#2b2b2b', fg='#4ecdc4')
        self.usdt_label.pack(pady=2)
        
        # Balance BNB
        self.bnb_label = tk.Label(balance_frame, text="BNB: 0.00", 
                                bg='#2b2b2b', fg='#ffeaa7')
        self.bnb_label.pack(pady=2)
        
        # P&L
        self.pnl_label = tk.Label(balance_frame, text="P&L: $0.00", 
                                bg='#2b2b2b', fg='white')
        self.pnl_label.pack(pady=2)
    
    def create_chart_and_log(self, parent):
        """Panel de gráfico y log"""
        # Frame izquierdo - Gráfico
        chart_frame = tk.LabelFrame(parent, text="📈 Gráfico de Precios", 
                                  bg='#2b2b2b', fg='white', font=('Arial', 10, 'bold'))
        chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Crear gráfico
        self.fig = Figure(figsize=(6, 4), dpi=100, facecolor='#2b2b2b')
        self.ax = self.fig.add_subplot(111, facecolor='#1e1e1e')
        self.ax.tick_params(colors='white')
        self.ax.set_xlabel('Tiempo', color='white')
        self.ax.set_ylabel('Precio (USDT)', color='white')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Frame derecho - Log
        log_frame = tk.LabelFrame(parent, text="📝 Log de Actividad", 
                                bg='#2b2b2b', fg='white', font=('Arial', 10, 'bold'))
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Área de log
        self.log_text = scrolledtext.ScrolledText(log_frame, 
                                                 width=40, height=20,
                                                 bg='#1e1e1e', fg='white',
                                                 font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def load_default_config(self):
        """Cargar configuración por defecto"""
        self.log_message("🔧 Configuración por defecto cargada")
    
    def load_optimized_config(self):
        """Cargar configuración optimizada"""
        try:
            bot = MAConvergenceBot()
            config = bot.get_optimized_config()
            
            self.ma1_var.set(str(config['umbral_ma1']))
            self.ma2_var.set(str(config['umbral_ma2']))
            
            self.log_message(f"🎯 Config optimizada cargada: MA1={config['umbral_ma1']}, MA2={config['umbral_ma2']}")
            self.log_message(f"📈 Retorno esperado: +{config['expected_return_pct']}%")
            
        except Exception as e:
            self.log_message(f"❌ Error cargando config: {e}")
    
    def test_connection(self):
        """Probar conexión con Binance"""
        try:
            # API keys (testnet)
            api_key = '7ZPT9vq9NRD8rDcV87ykvrPWBPQzPuZ9QkLKLLxGguQaDvT5mACl4nQSP8uwGxBH'
            api_secret = 'SpCz5aKF9c16gpJec6EQ3r0BC4GAqjmTO1Bevh2193mvVEEdClpIhP2jx7Wf1QFO'
            
            client = Client(api_key, api_secret, testnet=self.testnet_var.get())
            
            # Test ping
            ping = client.ping()
            
            # Get account info
            account = client.get_account()
            
            # Get price
            price = client.get_symbol_ticker(symbol=self.symbol_var.get())
            
            self.log_message("✅ Conexión exitosa con Binance")
            self.log_message(f"📊 Precio {self.symbol_var.get()}: ${float(price['price']):.4f}")
            
            # Actualizar balances
            self.update_balances(account['balances'])
            
            # Log de balances principales
            usdt_bal = next((float(b['free']) for b in account['balances'] if b['asset'] == 'USDT'), 0)
            bnb_bal = next((float(b['free']) for b in account['balances'] if b['asset'] == 'BNB'), 0)
            self.log_message(f"💰 Balance inicial - USDT: ${usdt_bal:.2f}, BNB: {bnb_bal:.6f}")
            
        except Exception as e:
            self.log_message(f"❌ Error de conexión: {e}")
            messagebox.showerror("Error", f"No se pudo conectar a Binance:\n{e}")
    
    def toggle_bot(self):
        """Iniciar o detener el bot"""
        if not self.is_running:
            self.start_bot()
        else:
            self.stop_bot()
    
    def start_bot(self):
        """Iniciar el bot"""
        try:
            # Validar configuración
            if not self.validate_config():
                return
            
            # Cambiar estado
            self.is_running = True
            self.start_stop_btn.configure(text="⏹️ DETENER BOT", style='Danger.TButton')
            self.status_label.configure(text="🟢 Ejecutándose", fg='#51cf66')
            
            # Iniciar thread del bot
            self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
            self.bot_thread.start()
            
            self.log_message("🚀 Bot iniciado")
            
        except Exception as e:
            self.log_message(f"❌ Error iniciando bot: {e}")
            messagebox.showerror("Error", f"No se pudo iniciar el bot:\n{e}")
    
    def stop_bot(self):
        """Detener el bot"""
        self.is_running = False
        self.start_stop_btn.configure(text="🚀 INICIAR BOT", style='Success.TButton')
        self.status_label.configure(text="⭕ Detenido", fg='#ff6b6b')
        self.log_message("⏹️ Bot detenido")
    
    def validate_config(self):
        """Validar configuración antes de iniciar"""
        try:
            float(self.amount_var.get())
            float(self.ma1_var.get())
            float(self.ma2_var.get())
            
            if not self.symbol_var.get():
                raise ValueError("Symbol no puede estar vacío")
            
            return True
        except ValueError as e:
            messagebox.showerror("Error", f"Configuración inválida:\n{e}")
            return False
    
    def run_bot(self):
        """Ejecutar el bot en thread separado"""
        try:
            # API keys
            api_key = '7ZPT9vq9NRD8rDcV87ykvrPWBPQzPuZ9QkLKLLxGguQaDvT5mACl4nQSP8uwGxBH'
            api_secret = 'SpCz5aKF9c16gpJec6EQ3r0BC4GAqjmTO1Bevh2193mvVEEdClpIhP2jx7Wf1QFO'
            
            # Crear cliente
            self.client = Client(api_key, api_secret, testnet=self.testnet_var.get())
            
            # Configurar bot MA
            ma_bot = MAConvergenceBot(
                umbral_ma1=float(self.ma1_var.get()),
                umbral_ma2=float(self.ma2_var.get()),
                verbose=True
            )
            
            iteration = 0
            
            while self.is_running:
                try:
                    iteration += 1
                    
                    # Obtener precio actual
                    ticker = self.client.get_symbol_ticker(symbol=self.symbol_var.get())
                    current_price = float(ticker['price'])
                    
                    # Actualizar datos del gráfico
                    self.message_queue.put(('price_update', current_price))
                    
                    # Obtener datos históricos para análisis
                    klines = self.client.get_klines(
                        symbol=self.symbol_var.get(),
                        interval=Client.KLINE_INTERVAL_1MINUTE,
                        limit=100
                    )
                    
                    # Preparar datos para análisis
                    df = pd.DataFrame(klines, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_asset_volume', 'number_of_trades',
                        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
                    ])
                    
                    df['close'] = df['close'].astype(float)
                    
                    # Análisis simplificado con MA Convergence
                    if len(df) >= 100:  # Suficientes datos para MA99
                        try:
                            # Preparar datos para el bot con índice numérico
                            analysis_df = df.copy().reset_index(drop=True)
                            analysis_df['Date'] = pd.to_datetime(analysis_df['timestamp'], unit='ms')
                            analysis_df['Open'] = analysis_df['open'].astype(float)
                            analysis_df['High'] = analysis_df['high'].astype(float) 
                            analysis_df['Low'] = analysis_df['low'].astype(float)
                            analysis_df['Close'] = analysis_df['close'].astype(float)
                            analysis_df['Volume'] = analysis_df['volume'].astype(float)
                            
                            # Asignar datos al bot con índice correcto
                            analysis_df.index = analysis_df['Date']
                            ma_bot.data = analysis_df
                            
                            # Calcular solo indicadores básicos para evitar errores complejos
                            ma_bot._calculate_indicators()
                            
                            # Análisis simplificado: verificar tendencias de MAs recientes
                            ma7_values = ma_bot.data[f'MA{ma_bot.ma1_value}'].dropna()
                            ma25_values = ma_bot.data[f'MA{ma_bot.ma2_value}'].dropna()
                            
                            if len(ma7_values) >= 5 and len(ma25_values) >= 5:
                                # Calcular pendientes recientes (últimos 3 períodos)
                                ma7_slope = (ma7_values.iloc[-1] - ma7_values.iloc[-3]) / ma7_values.iloc[-3]
                                ma25_slope = (ma25_values.iloc[-1] - ma25_values.iloc[-3]) / ma25_values.iloc[-3]
                                
                                # Señal de compra: ambas MAs con pendiente positiva y por encima de umbrales
                                if (ma7_slope > ma_bot.umbral_ma1 and 
                                    ma25_slope > ma_bot.umbral_ma2 and 
                                    self.position is None):
                                    self.message_queue.put(('signal', 'BUY', current_price))
                                    self.message_queue.put(('log', f"📈 Señal COMPRA: MA7={ma7_slope:.4f}, MA25={ma25_slope:.4f}"))
                                
                                # Señal de venta: take profit o stop loss
                                elif self.position == 'LONG':
                                    profit_pct = (current_price - self.entry_price) / self.entry_price
                                    if profit_pct > 0.002:  # 0.2% profit
                                        self.message_queue.put(('signal', 'SELL', current_price))
                                        self.message_queue.put(('log', f"💰 Take Profit: {profit_pct*100:.2f}%"))
                                    elif profit_pct < -0.001:  # -0.1% loss
                                        self.message_queue.put(('signal', 'SELL', current_price))
                                        self.message_queue.put(('log', f"🛑 Stop Loss: {profit_pct*100:.2f}%"))
                                
                        except Exception as analysis_error:
                            if iteration % 60 == 1:  # Log error cada minuto
                                self.message_queue.put(('log', f"⚠️ Error en análisis: {str(analysis_error)[:50]}..."))
                    
                    # Actualizar balances cada 30 segundos
                    if iteration % 6 == 1:  # Cada 30 segundos aprox
                        try:
                            account = self.client.get_account()
                            self.message_queue.put(('balance_update', account['balances']))
                        except:
                            pass  # No es crítico si falla
                    
                    # Log periódico
                    if iteration % 12 == 1:  # Cada minuto aprox
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        pos_text = self.position if self.position else "None"
                        self.message_queue.put(('log', f"[{iteration:4d}] {timestamp} | Precio: ${current_price:.4f} | Posición: {pos_text}"))
                    
                    time.sleep(5)  # 5 segundos entre checks
                    
                except Exception as e:
                    self.message_queue.put(('error', f"Error en iteración {iteration}: {e}"))
                    time.sleep(10)
                    
        except Exception as e:
            self.message_queue.put(('error', f"Error crítico en bot: {e}"))
    
    def update_balances(self, balances):
        """Actualizar balances en la GUI"""
        usdt_balance = 0.0
        bnb_balance = 0.0
        
        for balance in balances:
            if balance['asset'] == 'USDT':
                usdt_balance = float(balance['free'])
            elif balance['asset'] == 'BNB':
                bnb_balance = float(balance['free'])
        
        self.balance_usdt = usdt_balance
        self.balance_bnb = bnb_balance
        
        self.usdt_label.configure(text=f"USDT: ${usdt_balance:.2f}")
        self.bnb_label.configure(text=f"BNB: {bnb_balance:.6f}")
    
    def update_chart(self, price):
        """Actualizar gráfico de precios"""
        current_time = datetime.now()
        
        self.time_data.append(current_time)
        self.price_data.append(price)
        
        # Mantener solo los últimos puntos
        if len(self.time_data) > self.max_data_points:
            self.time_data = self.time_data[-self.max_data_points:]
            self.price_data = self.price_data[-self.max_data_points:]
        
        # Actualizar gráfico
        self.ax.clear()
        self.ax.plot(self.time_data, self.price_data, color='#00ff88', linewidth=2)
        self.ax.set_facecolor('#1e1e1e')
        self.ax.tick_params(colors='white')
        self.ax.set_xlabel('Tiempo', color='white')
        self.ax.set_ylabel('Precio (USDT)', color='white')
        self.ax.grid(True, alpha=0.3)
        
        # Configurar formato del eje Y para evitar notación científica
        if len(self.price_data) > 0:
            min_price = min(self.price_data)
            max_price = max(self.price_data)
            price_range = max_price - min_price
            
            # Establecer límites del eje Y con un pequeño margen
            margin = price_range * 0.02 if price_range > 0 else 1
            self.ax.set_ylim(min_price - margin, max_price + margin)
            
            # Formato de números sin notación científica
            from matplotlib.ticker import FormatStrFormatter
            self.ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
        
        # Formato de fecha en eje X
        if len(self.time_data) > 1:
            self.fig.autofmt_xdate()
        
        self.canvas.draw()
        
        # Actualizar precio en GUI
        self.current_price = price
        self.price_label.configure(text=f"Precio: ${price:.4f}")
    
    def process_signal(self, signal_type, price):
        """Procesar señal de trading"""
        if signal_type == 'BUY':
            self.position = 'LONG'
            self.entry_price = price
            self.position_label.configure(text=f"Posición: LONG @ ${price:.4f}", fg='#51cf66')
            self.log_message(f"🟢 COMPRA ejecutada a ${price:.4f}")
            
        elif signal_type == 'SELL':
            if self.position == 'LONG':
                pnl = ((price - self.entry_price) / self.entry_price) * 100
                self.position = None
                self.entry_price = 0.0
                self.position_label.configure(text="Posición: None", fg='white')
                self.pnl_label.configure(text=f"P&L: {pnl:+.2f}%", 
                                       fg='#51cf66' if pnl > 0 else '#ff6b6b')
                self.log_message(f"🔴 VENTA ejecutada a ${price:.4f} | P&L: {pnl:+.2f}%")
    
    def process_queue(self):
        """Procesar mensajes de la cola"""
        try:
            while True:
                message = self.message_queue.get_nowait()
                msg_type = message[0]
                
                if msg_type == 'price_update':
                    self.update_chart(message[1])
                    
                elif msg_type == 'signal':
                    self.process_signal(message[1], message[2])
                    
                elif msg_type == 'log':
                    self.log_message(message[1])
                    
                elif msg_type == 'error':
                    self.log_message(f"❌ {message[1]}")
                    
                elif msg_type == 'balance_update':
                    self.update_balances(message[1])
                    
        except queue.Empty:
            pass
        
        # Programar siguiente check
        self.root.after(100, self.process_queue)
    
    def log_message(self, message):
        """Agregar mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, full_message)
        self.log_text.see(tk.END)

def main():
    """Función principal"""
    root = tk.Tk()
    app = MAConvergenceGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()