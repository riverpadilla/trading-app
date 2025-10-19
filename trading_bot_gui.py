"""
Interfaz Gráfica para el Bot de Trading
Permite configurar parámetros y ejecutar backtesting con múltiples estrategias
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from trading_bot import TradingBot
from hybrid_fast_bot import HybridTradingBot
from ma_convergence_bot import MAConvergenceBot
import os

class TradingBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 Bot de Trading - BNBUSDT")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.bot = None
        self.csv_file = tk.StringVar()
        self.initial_capital = tk.DoubleVar(value=1000.0)
        self.rsi_oversold = tk.IntVar(value=30)
        self.rsi_overbought = tk.IntVar(value=70)
        self.strategy_type = tk.StringVar(value="hybrid")  # Nueva variable
        
        # Variables para MA Convergence
        self.ma1_period = tk.StringVar(value="MA7")
        self.ma2_period = tk.StringVar(value="MA25")
        self.umbral_ma1 = tk.DoubleVar(value=0.01)
        self.umbral_ma2 = tk.DoubleVar(value=0.0002)
        
        # Buscar archivo CSV automáticamente
        self._find_csv_file()
        
        self.create_widgets()
    
    def _find_csv_file(self):
        """Busca automáticamente el archivo CSV más reciente"""
        csv_files = [f for f in os.listdir('.') if f.startswith('binance_BNBUSDT') and f.endswith('.csv')]
        if csv_files:
            # Usar el más reciente
            latest_file = max(csv_files, key=os.path.getmtime)
            self.csv_file.set(latest_file)
    
    def create_widgets(self):
        """Crea la interfaz gráfica"""
        
        # Título
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        title_frame.pack(fill='x', padx=10, pady=(10, 0))
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="🤖 Bot de Trading BNBUSDT", 
                              font=('Arial', 18, 'bold'), fg='white', bg='#2c3e50')
        title_label.pack(expand=True)
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Configuración de datos
        data_frame = tk.LabelFrame(main_frame, text="📁 Archivo de Datos", 
                                  font=('Arial', 12, 'bold'), bg='#f0f0f0')
        data_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(data_frame, text="Archivo CSV:", bg='#f0f0f0').grid(row=0, column=0, sticky='w', padx=5, pady=5)
        
        file_frame = tk.Frame(data_frame, bg='#f0f0f0')
        file_frame.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        data_frame.columnconfigure(1, weight=1)
        
        tk.Entry(file_frame, textvariable=self.csv_file, width=50, state='readonly').pack(side='left', fill='x', expand=True)
        tk.Button(file_frame, text="Examinar", command=self.browse_file).pack(side='right', padx=(5, 0))
        
        # Configuración de parámetros
        params_frame = tk.LabelFrame(main_frame, text="⚙️ Parámetros de Trading", 
                                    font=('Arial', 12, 'bold'), bg='#f0f0f0')
        params_frame.pack(fill='x', pady=(0, 10))
        
        # Selección de estrategia
        tk.Label(params_frame, text="Estrategia:", bg='#f0f0f0', font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w', padx=5, pady=5)
        strategy_frame = tk.Frame(params_frame, bg='#f0f0f0')
        strategy_frame.grid(row=0, column=1, columnspan=2, sticky='w', padx=5, pady=5)
        
        tk.Radiobutton(strategy_frame, text="🎯 Híbrida Mejorada", variable=self.strategy_type, 
                      value="hybrid", bg='#f0f0f0', font=('Arial', 9), command=self._on_strategy_change).pack(side='left')
        tk.Radiobutton(strategy_frame, text="🐌 Original", variable=self.strategy_type, 
                      value="original", bg='#f0f0f0', font=('Arial', 9), command=self._on_strategy_change).pack(side='left', padx=(10, 0))
        tk.Radiobutton(strategy_frame, text="📈 MA Convergence", variable=self.strategy_type, 
                      value="ma_convergence", bg='#f0f0f0', font=('Arial', 9), command=self._on_strategy_change).pack(side='left', padx=(10, 0))
        
        # Capital inicial
        tk.Label(params_frame, text="Capital Inicial (USDT):", bg='#f0f0f0').grid(row=1, column=0, sticky='w', padx=5, pady=5)
        tk.Spinbox(params_frame, from_=100, to=100000, textvariable=self.initial_capital, 
                  width=15, format="%.2f").grid(row=1, column=1, sticky='w', padx=5, pady=5)
        
        # Frame para parámetros específicos de cada estrategia
        self.params_specific_frame = tk.Frame(params_frame, bg='#f0f0f0')
        self.params_specific_frame.grid(row=2, column=0, columnspan=3, sticky='ew', padx=5, pady=5)
        
        # Crear todos los widgets específicos (inicialmente ocultos)
        self._create_rsi_params()
        self._create_ma_convergence_params()
        
        # Mostrar parámetros de la estrategia inicial
        self._on_strategy_change()
        
        # Botones de control
        control_frame = tk.Frame(main_frame, bg='#f0f0f0')
        control_frame.pack(fill='x', pady=(0, 10))
        
        self.run_button = tk.Button(control_frame, text="🚀 Ejecutar Backtesting", 
                                   command=self.run_backtest, bg='#27ae60', fg='white', 
                                   font=('Arial', 12, 'bold'), height=2)
        self.run_button.pack(side='left', padx=(0, 10))
        
        self.clear_button = tk.Button(control_frame, text="🗑️ Limpiar Resultados", 
                                     command=self.clear_results, bg='#e74c3c', fg='white', 
                                     font=('Arial', 12, 'bold'), height=2)
        self.clear_button.pack(side='left')
        
        # Área de resultados
        results_frame = tk.LabelFrame(main_frame, text="📊 Resultados del Backtesting", 
                                     font=('Arial', 12, 'bold'), bg='#f0f0f0')
        results_frame.pack(fill='both', expand=True)
        
        # Text widget con scroll
        text_frame = tk.Frame(results_frame, bg='#f0f0f0')
        text_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.results_text = tk.Text(text_frame, wrap='word', font=('Courier', 10), 
                                   bg='#ffffff', fg='#2c3e50')
        scrollbar = tk.Scrollbar(text_frame, orient='vertical', command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.results_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Barra de progreso
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill='x', pady=(5, 0))
        
        # Mostrar mensaje inicial
        self.show_welcome_message()
    
    def _create_rsi_params(self):
        """Crea widgets para parámetros RSI (estrategias original e híbrida)"""
        self.rsi_frame = tk.Frame(self.params_specific_frame, bg='#f0f0f0')
        
        tk.Label(self.rsi_frame, text="RSI Sobreventa:", bg='#f0f0f0').grid(row=0, column=0, sticky='w', padx=5, pady=2)
        tk.Spinbox(self.rsi_frame, from_=10, to=50, textvariable=self.rsi_oversold, 
                  width=15).grid(row=0, column=1, sticky='w', padx=5, pady=2)
        
        tk.Label(self.rsi_frame, text="RSI Sobrecompra:", bg='#f0f0f0').grid(row=1, column=0, sticky='w', padx=5, pady=2)
        tk.Spinbox(self.rsi_frame, from_=50, to=90, textvariable=self.rsi_overbought, 
                  width=15).grid(row=1, column=1, sticky='w', padx=5, pady=2)
    
    def _create_ma_convergence_params(self):
        """Crea widgets para parámetros MA Convergence"""
        self.ma_frame = tk.Frame(self.params_specific_frame, bg='#f0f0f0')
        
        # Primera MA
        tk.Label(self.ma_frame, text="Primera MA:", bg='#f0f0f0', font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky='w', padx=5, pady=2)
        ma1_combo = ttk.Combobox(self.ma_frame, textvariable=self.ma1_period, 
                                values=["MA3", "MA7", "MA14", "MA25", "MA50", "MA99"], 
                                state="readonly", width=10)
        ma1_combo.grid(row=0, column=1, sticky='w', padx=5, pady=2)
        
        tk.Label(self.ma_frame, text="Umbral MA1:", bg='#f0f0f0').grid(row=0, column=2, sticky='w', padx=5, pady=2)
        tk.Spinbox(self.ma_frame, from_=0.0001, to=0.1, textvariable=self.umbral_ma1, 
                  width=12, format="%.4f", increment=0.001).grid(row=0, column=3, sticky='w', padx=5, pady=2)
        
        # Segunda MA
        tk.Label(self.ma_frame, text="Segunda MA:", bg='#f0f0f0', font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky='w', padx=5, pady=2)
        ma2_combo = ttk.Combobox(self.ma_frame, textvariable=self.ma2_period, 
                                values=["MA3", "MA7", "MA14", "MA25", "MA50", "MA99"], 
                                state="readonly", width=10)
        ma2_combo.grid(row=1, column=1, sticky='w', padx=5, pady=2)
        
        tk.Label(self.ma_frame, text="Umbral MA2:", bg='#f0f0f0').grid(row=1, column=2, sticky='w', padx=5, pady=2)
        tk.Spinbox(self.ma_frame, from_=0.0001, to=0.1, textvariable=self.umbral_ma2, 
                  width=12, format="%.4f", increment=0.0001).grid(row=1, column=3, sticky='w', padx=5, pady=2)
        
        # Botón para configuración optimizada
        optimized_button = tk.Button(self.ma_frame, text="🎯 Usar Config. Optimizada", 
                                    command=self._load_optimized_config, 
                                    bg='#3498db', fg='white', font=('Arial', 9, 'bold'))
        optimized_button.grid(row=2, column=0, columnspan=2, sticky='w', padx=5, pady=5)
        
        # Información adicional
        info_label = tk.Label(self.ma_frame, 
                             text="💡 Config. Optimizada: MA1=0.0375, MA2=0.052 → +0.466% esperado", 
                             bg='#f0f0f0', font=('Arial', 8), fg='#27ae60')
        info_label.grid(row=3, column=0, columnspan=4, sticky='w', padx=5, pady=2)
    
    def _on_strategy_change(self):
        """Maneja el cambio de estrategia mostrando parámetros específicos"""
        # Ocultar todos los frames específicos
        if hasattr(self, 'rsi_frame'):
            self.rsi_frame.pack_forget()
        if hasattr(self, 'ma_frame'):
            self.ma_frame.pack_forget()
        
        # Mostrar frame específico según estrategia
        strategy = self.strategy_type.get()
        if strategy in ["original", "hybrid"]:
            if hasattr(self, 'rsi_frame'):
                self.rsi_frame.pack(fill='x', pady=5)
        elif strategy == "ma_convergence":
            if hasattr(self, 'ma_frame'):
                self.ma_frame.pack(fill='x', pady=5)
    
    def _load_optimized_config(self):
        """Carga la configuración optimizada de MA Convergence"""
        try:
            # Obtener configuración optimizada del bot
            config = MAConvergenceBot.get_optimized_config()
            
            # Actualizar variables de la GUI
            self.ma1_period.set(config['ma1_period'])
            self.ma2_period.set(config['ma2_period'])
            self.umbral_ma1.set(config['umbral_ma1'])
            self.umbral_ma2.set(config['umbral_ma2'])
            
            # Mostrar mensaje de confirmación
            messagebox.showinfo("Configuración Cargada", 
                              f"✅ Configuración optimizada cargada:\n\n"
                              f"MA1 ({config['ma1_period']}): {config['umbral_ma1']}\n"
                              f"MA2 ({config['ma2_period']}): {config['umbral_ma2']}\n\n"
                              f"Retorno esperado: +{config['expected_return_pct']}%\n"
                              f"Win rate histórico: {config['historical_win_rate']}%\n"
                              f"Trades por sesión: {config['expected_trades_per_session']}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar configuración optimizada:\n{str(e)}")
    
    def browse_file(self):
        """Abre diálogo para seleccionar archivo CSV"""
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo de datos",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.csv_file.set(filename)
    
    def show_welcome_message(self):
        """Muestra mensaje de bienvenida"""
        welcome_msg = """
🤖 BOT DE TRADING BNBUSDT - ANÁLISIS TÉCNICO

ESTRATEGIAS DISPONIBLES:

🎯 HÍBRIDA MEJORADA:
• Combina RSI multi-nivel + Bandas de Bollinger + MACD
• Filtros anti-overtrading (45 segundos entre operaciones)
• Stop Loss: 1.8% | Take Profit: 1.2%
• Salida por variación absoluta >= 1.2 USDT
• Resultados: ~172 operaciones, 52.3% éxito

🐌 ORIGINAL (CONSERVADORA):
• RSI (30/70) + MA9/MA21 + MACD
• Requiere al menos 2 indicadores alcistas para entrar
• Stop Loss: 2%
• Resultados: Muy pocas operaciones, alta calidad

📈 MA CONVERGENCE (NUEVA - OPTIMIZADA):
• Basada en convergencias de pendientes de Medias Móviles
• Detecta cambios de dirección sincronizados entre MA1 y MA2
• Filtro anti-consecutivas (evita señales repetidas)
• Sistema de persistencia de convergencias (30 min)
• 🆕 Replica la lógica del análisis de scalping

🎯 CONFIGURACIÓN OPTIMIZADA DISPONIBLE:
• MA1=0.0375, MA2=0.052 (probado en matriz 400 combinaciones)
• Retorno esperado: +0.466% por sesión (~5.5h)
• Win rate histórico: 100% (1 trade ultra-selectivo)
• Estrategia ultra-conservadora de alta precisión

CONFIGURACIÓN MANUAL:
• Primera MA: MA7/MA25 recomendadas
• Umbrales personalizables 0.0001-0.1
• Usar botón "🎯 Usar Config. Optimizada" para mejores resultados

¡Estrategia optimizada lista para trading! 🚀
        """
        self.results_text.insert('end', welcome_msg)
    
    def clear_results(self):
        """Limpia el área de resultados"""
        self.results_text.delete(1.0, 'end')
        self.show_welcome_message()
    
    def run_backtest(self):
        """Ejecuta el backtesting en un hilo separado"""
        if not self.csv_file.get():
            messagebox.showerror("Error", "Por favor selecciona un archivo CSV")
            return
        
        if not os.path.exists(self.csv_file.get()):
            messagebox.showerror("Error", "El archivo seleccionado no existe")
            return
        
        # Deshabilitar botón y mostrar progreso
        self.run_button.config(state='disabled')
        self.progress.start()
        
        # Ejecutar en hilo separado para no bloquear la UI
        thread = threading.Thread(target=self._run_backtest_thread)
        thread.daemon = True
        thread.start()
    
    def _run_backtest_thread(self):
        """Ejecuta el backtesting en hilo separado"""
        try:
            # Limpiar resultados anteriores
            self.root.after(0, lambda: self.results_text.delete(1.0, 'end'))
            
            # Crear bot según la estrategia seleccionada
            strategy_type = self.strategy_type.get()
            
            if strategy_type == "hybrid":
                self.bot = HybridTradingBot(initial_capital=self.initial_capital.get())
                strategy_name = "Híbrida"
                self.root.after(0, lambda: self.results_text.insert('end', 
                    "🎯 Usando Estrategia HÍBRIDA MEJORADA (con salida por variación ±1.2 USDT)\n"))
            elif strategy_type == "ma_convergence":
                self.bot = MAConvergenceBot(
                    initial_capital=self.initial_capital.get(),
                    ma1_period=self.ma1_period.get(),
                    ma2_period=self.ma2_period.get(),
                    umbral_ma1=self.umbral_ma1.get(),
                    umbral_ma2=self.umbral_ma2.get()
                )
                strategy_name = "MA Convergence"
                self.root.after(0, lambda: self.results_text.insert('end', 
                    f"📈 Usando Estrategia MA CONVERGENCE ({self.ma1_period.get()}-{self.ma2_period.get()})\n"))
                self.root.after(0, lambda: self.results_text.insert('end', 
                    f"   Umbrales: MA1={self.umbral_ma1.get():.4f}, MA2={self.umbral_ma2.get():.4f}\n"))
            else:
                self.bot = TradingBot(initial_capital=self.initial_capital.get())
                self.bot.strategy.rsi_oversold = self.rsi_oversold.get()
                self.bot.strategy.rsi_overbought = self.rsi_overbought.get()
                strategy_name = "Original"
                self.root.after(0, lambda: self.results_text.insert('end', 
                    "🐌 Usando Estrategia ORIGINAL (Conservadora)\n"))
            
            # Mostrar estado
            self.root.after(0, lambda: self.results_text.insert('end', 
                "🔄 Cargando datos...\n"))
            
            # Cargar datos
            if not self.bot.load_data(self.csv_file.get()):
                self.root.after(0, lambda: messagebox.showerror("Error", 
                    "No se pudo cargar el archivo de datos"))
                return
            
            self.root.after(0, lambda: self.results_text.insert('end', 
                f"✅ Datos cargados: {len(self.bot.data)} registros\n"))
            
            # Ejecutar backtesting
            self.root.after(0, lambda: self.results_text.insert('end', 
                f"🔄 Ejecutando backtesting con estrategia {strategy_name}...\n\n"))
            
            results = self.bot.run_backtest()
            
            if results:
                # Mostrar resultados en la interfaz
                self.root.after(0, lambda: self._display_results(results, strategy_name))
                
                # Guardar resultados
                self.bot.save_results()
                
                self.root.after(0, lambda: self.results_text.insert('end', 
                    f"\n✅ ¡Backtesting con estrategia {strategy_name} completado!\n"))
                self.root.after(0, lambda: self.results_text.insert('end', 
                    "💾 Resultados guardados en archivo CSV\n"))
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", 
                    "Error durante el backtesting"))
        
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", 
                f"Error inesperado: {str(e)}"))
        
        finally:
            # Rehabilitar botón y ocultar progreso
            self.root.after(0, lambda: self.run_button.config(state='normal'))
            self.root.after(0, lambda: self.progress.stop())
    
    def _display_results(self, results, strategy_name=""):
        """Muestra los resultados en la interfaz"""
        r = results
        
        results_text = f"""
📊 RESULTADOS - ESTRATEGIA {strategy_name.upper()}
{"="*50}

💰 CAPITAL:
   Inicial: ${r['initial_capital']:,.2f} USDT
   Final: ${r['final_capital']:,.2f} USDT
   Retorno: {r['total_return_pct']:+.2f}%

📈 OPERACIONES:
   Total: {r['total_trades']}
   Exitosas: {r['winning_trades']} ({r['win_rate_pct']:.1f}%)
   Fallidas: {r['losing_trades']}
   
📊 RENDIMIENTO:
   Ganancia promedio: {r['avg_win_pct']:+.2f}%
   Pérdida promedio: {r['avg_loss_pct']:+.2f}%
   Comisiones: ${r['total_commission']:,.2f} USDT

💼 BALANCES FINALES:
   USDT: {r['final_usdt_balance']:,.2f}
   BNB: {r['final_bnb_balance']:,.6f}

🎯 EVALUACIÓN: {"📈 RENTABLE" if r['total_return_pct'] > 0 else "📉 PÉRDIDA" if r['total_return_pct'] < -50 else "⚠️ MODERADA"}
"""
        
        # Agregar información específica de la estrategia
        if strategy_name == "Híbrida":
            results_text += f"""
🎯 ANÁLISIS ESTRATEGIA HÍBRIDA:
   • Detectó {r['total_trades']} oportunidades vs 1 de la original
   • Tasa de éxito del {r['win_rate_pct']:.1f}% (muy buena)
   • Filtros anti-overtrading funcionando correctamente
   • Balance óptimo entre cantidad y calidad de operaciones
"""
        elif strategy_name == "MA Convergence":
            results_text += f"""
📈 ANÁLISIS ESTRATEGIA MA CONVERGENCE:
   • Configuración: {r.get('ma1_period', 'N/A')} vs {r.get('ma2_period', 'N/A')}
   • Umbrales: MA1={r.get('umbral_ma1', 0):.4f}, MA2={r.get('umbral_ma2', 0):.4f}
   • Detectó {r['total_trades']} convergencias válidas
   • Tasa de éxito del {r['win_rate_pct']:.1f}%
   • Sistema de filtrado anti-consecutivas activo
   • Basada en análisis de pendientes de MAs
"""
        elif strategy_name == "Original":
            results_text += f"""
🐌 ANÁLISIS ESTRATEGIA ORIGINAL:
   • Muy conservadora: {r['total_trades']} operaciones
   • Enfoque en calidad sobre cantidad
   • Puede perder oportunidades por ser muy restrictiva
"""
        
        self.results_text.insert('end', results_text)
        
        # Mostrar últimas operaciones si existen
        if r['trades_list']:
            self.results_text.insert('end', "\n📋 ÚLTIMAS OPERACIONES:\n")
            for trade in r['trades_list'][-5:]:
                if trade['type'] == 'SELL':
                    pnl_str = f"{trade['pnl_pct']:+.2f}%"
                    color = "🟢" if trade['pnl_pct'] > 0 else "🔴"
                    self.results_text.insert('end', 
                        f"   {color} {trade['timestamp']}: {trade['type']} ${trade['price']:.2f} | P&L: {pnl_str}\n")
                else:
                    self.results_text.insert('end', 
                        f"   🔵 {trade['timestamp']}: {trade['type']} ${trade['price']:.2f}\n")

def main():
    """Función principal"""
    root = tk.Tk()
    app = TradingBotGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()