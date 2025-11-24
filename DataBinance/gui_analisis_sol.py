#!/usr/bin/env python3
"""
GUI Profesional para Análisis Técnico SOL/USDT
Interfaz gráfica con descarga de datos, análisis y visualización de gráficos
Genera reportes PDF con gráficos incluidos
Requisitos: pip install pandas numpy matplotlib python-binance reportlab pillow
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from datetime import datetime
from pathlib import Path
import threading
import os
import io

try:
    from binance.client import Client
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from PIL import Image as PILImage
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# API Keys hardcode (SOL Trading Anaysis Keys)
API_KEY = "ghf17lXepHDblRsp1Q2i9XPdPVCrzx7TO74SWDbhaNB6bKSGlQOXlHew5YTuer34"
API_SECRET = "x2b0OIBDxV4W34mvWXn4ndu3KYIU7vMHCA1RyK8VaYmlrUWjZzVqqTziQ4LJb1Kj"

class AnalisisSolUSDT:
    """Clase para análisis técnico SOL/USDT"""
    
    def __init__(self):
        self.dataframes = {}
        self.resultados = {}
        self.fuente_datos = "descargados"
        self.archivo_info = {}
        self.ultimo_timestamp = None
    
    def limpiar_archivos_antiguos(self, directorio='.', callback=None):
        """Elimina archivos antiguos, mantiene solo los más recientes por timeframe"""
        try:
            timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
            archivos_eliminados = 0
            
            for tf in timeframes:
                archivos = sorted(list(Path(directorio).glob(f"SOLUSDT_{tf}_*.csv")))
                
                if len(archivos) > 1:
                    # Mantener solo el más reciente, eliminar los demás
                    for archivo_antiguo in archivos[:-1]:
                        try:
                            os.remove(archivo_antiguo)
                            archivos_eliminados += 1
                            if callback:
                                callback(f"Eliminado: {archivo_antiguo.name}")
                        except Exception as e:
                            if callback:
                                callback(f"⚠️ Error eliminando {archivo_antiguo.name}: {str(e)}")
            
            if callback:
                callback(f"✓ {archivos_eliminados} archivos antiguos eliminados")
            
            return archivos_eliminados
        except Exception as e:
            raise Exception(f"Error limpiando archivos: {str(e)}")
        
    def descargar_datos(self, callback=None):
        """Descarga datos de Binance con 1000 para < 1D y 300 para 1D"""
        if not BINANCE_AVAILABLE:
            raise Exception("Binance API no disponible. Instala: pip install python-binance")
        
        try:
            client = Client(api_key=API_KEY, api_secret=API_SECRET)
            
            timeframes = {
                '1m': (Client.KLINE_INTERVAL_1MINUTE, 1000),
                '5m': (Client.KLINE_INTERVAL_5MINUTE, 1000),
                '15m': (Client.KLINE_INTERVAL_15MINUTE, 1000),
                '1h': (Client.KLINE_INTERVAL_1HOUR, 1000),
                '4h': (Client.KLINE_INTERVAL_4HOUR, 1000),
                '1d': (Client.KLINE_INTERVAL_1DAY, 300),
            }
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.ultimo_timestamp = timestamp
            
            for tf, (interval, limit) in timeframes.items():
                if callback:
                    callback(f"Descargando {tf} ({limit} candles)...")
                
                klines = client.get_klines(symbol='SOLUSDT', interval=interval, limit=limit)
                
                df = pd.DataFrame(klines, columns=[
                    'Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume',
                    'Close_Time', 'Quote_Asset_Volume', 'Number_of_Trades',
                    'Taker_Buy_Base', 'Taker_Buy_Quote', 'Ignore'
                ])
                
                df['Open_Time'] = pd.to_datetime(df['Open_Time'], unit='ms')
                df['Close_Time'] = pd.to_datetime(df['Close_Time'], unit='ms')
                df['Open'] = df['Open'].astype(float)
                df['High'] = df['High'].astype(float)
                df['Low'] = df['Low'].astype(float)
                df['Close'] = df['Close'].astype(float)
                df['Volume'] = df['Volume'].astype(float)
                
                self._calcular_indicadores(df)
                self.dataframes[tf] = df
                
                filename = f'SOLUSDT_{tf}_{timestamp}.csv'
                df.to_csv(filename, index=False)
                
                self.archivo_info[tf] = {
                    'archivo': filename,
                    'timestamp': timestamp,
                    'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'registros': len(df)
                }
            
            # Eliminar archivos antiguos después de descargar
            if callback:
                callback(f"Limpiando archivos antiguos...")
            
            def callback_limpieza(msg):
                if callback:
                    callback(msg)
            
            self.limpiar_archivos_antiguos(callback=callback_limpieza)
            
            if callback:
                callback(f"✓ Datos descargados exitosamente")
            
            self.fuente_datos = "online"
            return True
        except Exception as e:
            raise Exception(f"Error descargando datos: {str(e)}")
    
    def cargar_datos_locales(self, directorio='.', callback=None):
        """Carga datos desde CSVs locales más recientes"""
        try:
            timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
            archivos_encontrados = {}
            archivos_cargados = 0
            
            for tf in timeframes:
                # Buscar archivos con patrón flexible
                archivos = sorted(list(Path(directorio).glob(f"SOLUSDT_{tf}_*.csv")))
                
                if archivos:
                    # Tomar el más reciente
                    archivo = archivos[-1]
                    
                    if callback:
                        callback(f"Cargando {tf}...")
                    
                    try:
                        df = pd.read_csv(archivo)
                        self.dataframes[tf] = df
                        
                        # Extraer timestamp del nombre del archivo
                        nombre = archivo.name
                        # Buscar el timestamp en el nombre (formato: YYYYMMDD_HHMMSS)
                        import re
                        match = re.search(r'(\d{8}_\d{6})', nombre)
                        if match:
                            timestamp = match.group(1)
                            fecha_obj = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                        else:
                            timestamp = "desconocido"
                            fecha_obj = datetime.fromtimestamp(archivo.stat().st_mtime)
                        
                        self.archivo_info[tf] = {
                            'archivo': nombre,
                            'timestamp': timestamp,
                            'fecha': fecha_obj.strftime("%Y-%m-%d %H:%M:%S"),
                            'registros': len(df),
                            'ruta': str(archivo)
                        }
                        
                        self.ultimo_timestamp = timestamp
                        archivos_encontrados[tf] = nombre
                        archivos_cargados += 1
                    except Exception as e:
                        if callback:
                            callback(f"⚠️ Error cargando {tf}: {str(e)}")
                else:
                    if callback:
                        callback(f"⚠️ No encontrado: SOLUSDT_{tf}_*.csv")
            
            if archivos_cargados == 0:
                raise Exception("No se encontraron archivos CSV válidos para cargar")
            
            if callback:
                callback(f"✓ {archivos_cargados} timeframes cargados")
            
            self.fuente_datos = "descargados"
            return True, archivos_encontrados
        except Exception as e:
            raise Exception(f"Error cargando datos locales: {str(e)}")
    
    def _calcular_indicadores(self, df):
        """Calcula indicadores técnicos"""
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        ema12 = df['Close'].ewm(span=12).mean()
        ema26 = df['Close'].ewm(span=26).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        df['MA7'] = df['Close'].rolling(window=7).mean()
        df['MA25'] = df['Close'].rolling(window=25).mean()
        df['MA99'] = df['Close'].rolling(window=99).mean()
        
        df['TR'] = np.maximum(
            df['High'] - df['Low'],
            np.maximum(
                abs(df['High'] - df['Close'].shift()),
                abs(df['Low'] - df['Close'].shift())
            )
        )
        df['ATR'] = df['TR'].rolling(window=14).mean()
    
    def generar_analisis(self, callback=None):
        """Genera análisis técnico"""
        if not self.dataframes:
            raise Exception("No hay datos cargados")
        
        analisis = {
            'timestamp': datetime.now().isoformat(),
            'fuente': self.fuente_datos,
            'archivo_info': self.archivo_info,
            'precio_actual': float(self.dataframes['1h'].iloc[-1]['Close']),
            'macd': {},
            'rsi': {},
            'medias_moviles': {},
            'recomendaciones_long': {},
            'recomendaciones_short': {}
        }
        
        for tf, df in self.dataframes.items():
            if len(df) < 2:
                continue
            
            last = df.iloc[-1]
            analisis['macd'][tf] = {
                'valor': float(last['MACD']),
                'signal': float(last['MACD_Signal']),
                'histogram': float(last['MACD_Histogram'])
            }
            
            analisis['rsi'][tf] = {
                'valor': float(last['RSI']),
                'estado': self._interpretar_rsi(last['RSI'])
            }
            
            analisis['medias_moviles'][tf] = {
                'close': float(last['Close']),
                'ma7': float(last['MA7']) if not pd.isna(last['MA7']) else None,
                'ma25': float(last['MA25']) if not pd.isna(last['MA25']) else None,
                'ma99': float(last['MA99']) if not pd.isna(last['MA99']) else None,
            }
        
        if '1h' in self.dataframes:
            df_1h = self.dataframes['1h']
            current = df_1h.iloc[-1]['Close']
            ma99 = df_1h.iloc[-1]['MA99']
            ma25 = df_1h.iloc[-1]['MA25']
            max_recent = df_1h.iloc[-5:]['High'].max()
            support = df_1h.iloc[-100:]['Low'].min()
            
            analisis['recomendaciones_long'] = {
                'estado': 'LONG',
                'entrada_1': float(current),
                'entrada_2': float(ma99),
                'target_1': float(max_recent),
                'target_2': 134.50,
                'stop_loss': float(support),
                'riesgo': float((current - support) / current * 100) if current > 0 else 0,
                'ganancia': float((max_recent - current) / current * 100) if current > 0 else 0,
                'confianza': self._calcular_confianza_long(df_1h, current)
            }
            
            resistance = df_1h.iloc[-100:]['High'].max()
            min_recent = df_1h.iloc[-5:]['Low'].min()
            
            analisis['recomendaciones_short'] = {
                'estado': 'SHORT',
                'entrada_1': 133.50,
                'entrada_2': float(max_recent),
                'target_1': float(min_recent),
                'target_2': 125.00,
                'stop_loss': float(resistance),
                'riesgo': float((resistance - 133.50) / 133.50 * 100),
                'ganancia': float((133.50 - min_recent) / 133.50 * 100),
                'confianza': self._calcular_confianza_short(df_1h, current)
            }
        
        self.resultados = analisis
        return analisis
    
    def _calcular_confianza_long(self, df_1h, current_price):
        """Calcula confianza de estrategia LONG"""
        last = df_1h.iloc[-1]
        score = 0
        
        if last['RSI'] > 50 and last['RSI'] < 70:
            score += 25
        elif last['RSI'] > 70:
            score += 10
        
        if last['MACD'] > last['MACD_Signal']:
            score += 25
        
        if current_price > last['MA25']:
            score += 25
        if current_price > last['MA99']:
            score += 25
        
        return min(100, score)
    
    def _calcular_confianza_short(self, df_1h, current_price):
        """Calcula confianza de estrategia SHORT"""
        last = df_1h.iloc[-1]
        score = 0
        
        if last['RSI'] > 70:
            score += 30
        elif last['RSI'] > 60:
            score += 15
        
        if last['MACD'] < last['MACD_Signal']:
            score += 25
        
        resistance = df_1h.iloc[-100:]['High'].max()
        if abs(current_price - resistance) / resistance < 0.02:
            score += 30
        
        return min(100, score)
    
    def _interpretar_rsi(self, rsi):
        """Interpreta valor de RSI"""
        if pd.isna(rsi):
            return "N/A"
        if rsi > 70:
            return "SOBRECOMPRA"
        elif rsi > 60:
            return "ALCISTA FUERTE"
        elif rsi > 40:
            return "NEUTRAL"
        elif rsi > 30:
            return "BAJISTA"
        else:
            return "SOBREVENTA"


class GUIAnalisisSol:
    """Interfaz gráfica para análisis SOL/USDT"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Análisis SOL/USDT - Sistema Profesional")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2b2b2b')
        
        self.analizador = AnalisisSolUSDT()
        self.crear_interfaz()
    
    def crear_interfaz(self):
        """Crea la interfaz gráfica"""
        # Panel superior - Controles
        self.panel_controles = ttk.Frame(self.root)
        self.panel_controles.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            self.panel_controles,
            text="☁️ Descargar Online",
            command=self.descargar_datos
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            self.panel_controles,
            text="💾 Cargar Local",
            command=self.cargar_locales
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            self.panel_controles,
            text="📊 Generar Análisis",
            command=self.generar_analisis
        ).pack(side=tk.LEFT, padx=5)
        
        # Labels de estado
        self.label_estado = ttk.Label(self.panel_controles, text="✓ Listo", foreground="green")
        self.label_estado.pack(side=tk.RIGHT, padx=5)
        
        self.label_fuente = ttk.Label(self.panel_controles, text="Fuente: N/A", foreground="gray")
        self.label_fuente.pack(side=tk.RIGHT, padx=5)
        
        self.label_timestamp = ttk.Label(self.panel_controles, text="Datos: N/A", foreground="cyan")
        self.label_timestamp.pack(side=tk.RIGHT, padx=5)
        
        # Notebook - Pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pestaña 1: Resumen
        self.tab_resumen = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_resumen, text="📊 Resumen")
        
        self.text_resumen = scrolledtext.ScrolledText(
            self.tab_resumen,
            height=30,
            width=100,
            bg='#1e1e1e',
            fg='#00ff00',
            font=('Courier', 10)
        )
        self.text_resumen.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Pestaña 2: Indicadores
        self.tab_indicadores = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_indicadores, text="📈 Indicadores")
        
        self.text_indicadores = scrolledtext.ScrolledText(
            self.tab_indicadores,
            height=30,
            width=100,
            bg='#1e1e1e',
            fg='#00ff00',
            font=('Courier', 10)
        )
        self.text_indicadores.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Pestaña 3: Estrategias
        self.tab_estrategias = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_estrategias, text="🎯 Estrategias")
        
        self.text_estrategias = scrolledtext.ScrolledText(
            self.tab_estrategias,
            height=30,
            width=100,
            bg='#1e1e1e',
            fg='#00ff00',
            font=('Courier', 10)
        )
        self.text_estrategias.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Pestaña 4: Gráficos
        self.tab_graficos = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_graficos, text="📊 Gráficos")
        
        # Pestaña 5: Info Archivos
        self.tab_archivos = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_archivos, text="📁 Info Archivos")
        
        self.text_archivos = scrolledtext.ScrolledText(
            self.tab_archivos,
            height=30,
            width=100,
            bg='#1e1e1e',
            fg='#00ff00',
            font=('Courier', 10)
        )
        self.text_archivos.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def actualizar_estado(self, mensaje):
        """Actualiza label de estado"""
        self.label_estado.config(text=mensaje, foreground="blue")
        self.root.update()
    
    def actualizar_fuente(self, fuente):
        """Actualiza label de fuente de datos"""
        self.label_fuente.config(text=f"Fuente: {fuente}", foreground="orange")
    
    def actualizar_timestamp(self, timestamp):
        """Actualiza label de timestamp"""
        if timestamp and timestamp != "desconocido":
            try:
                fecha_obj = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                fecha_formateada = fecha_obj.strftime("%Y-%m-%d %H:%M:%S")
                self.label_timestamp.config(text=f"Datos: {fecha_formateada}", foreground="cyan")
            except:
                self.label_timestamp.config(text=f"Datos: {timestamp}", foreground="cyan")
    
    def descargar_datos(self):
        """Descarga datos de Binance"""
        if not BINANCE_AVAILABLE:
            messagebox.showerror("Error", "Binance API no disponible\nInstala: pip install python-binance")
            return
        
        try:
            self.actualizar_estado("⏳ Descargando datos...")
            
            def callback(msg):
                self.actualizar_estado(f"⏳ {msg}")
            
            def run_download():
                try:
                    self.analizador.descargar_datos(callback)
                    self.actualizar_estado("✓ Datos descargados")
                    self.actualizar_fuente("Online ☁️")
                    self.actualizar_timestamp(self.analizador.ultimo_timestamp)
                    self.mostrar_info_archivos()
                    messagebox.showinfo("Éxito", "Datos descargados exitosamente\n(Archivos antiguos eliminados)")
                except Exception as e:
                    self.actualizar_estado("✗ Error")
                    messagebox.showerror("Error", str(e))
            
            thread = threading.Thread(target=run_download, daemon=True)
            thread.start()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def cargar_locales(self):
        """Carga datos locales"""
        try:
            self.actualizar_estado("⏳ Cargando datos locales...")
            
            def callback(msg):
                self.actualizar_estado(f"⏳ {msg}")
            
            self.analizador.cargar_datos_locales(callback=callback)
            self.actualizar_estado("✓ Datos cargados")
            self.actualizar_fuente("Local 💾")
            self.actualizar_timestamp(self.analizador.ultimo_timestamp)
            self.mostrar_info_archivos()
            messagebox.showinfo("Éxito", "Datos cargados (más recientes)")
        except Exception as e:
            self.actualizar_estado("✗ Error")
            messagebox.showerror("Error", str(e))
    
    def mostrar_info_archivos(self):
        """Muestra información de archivos cargados en pestaña"""
        self.text_archivos.delete(1.0, tk.END)
        
        if not self.analizador.archivo_info:
            self.text_archivos.insert(tk.END, "No hay información de archivos disponible")
            return
        
        texto = """
╔════════════════════════════════════════════════════════════════════╗
║            INFORMACIÓN DE ARCHIVOS UTILIZADOS EN ANÁLISIS          ║
╚════════════════════════════════════════════════════════════════════╝

"""
        
        for tf in sorted(self.analizador.archivo_info.keys()):
            info = self.analizador.archivo_info[tf]
            texto += f"\n{tf.upper()}:\n"
            texto += f"  Archivo: {info['archivo']}\n"
            texto += f"  Timestamp: {info['timestamp']}\n"
            texto += f"  Fecha/Hora: {info['fecha']}\n"
            texto += f"  Registros: {info['registros']:,}\n"
            texto += "─" * 70 + "\n"
        
        self.text_archivos.insert(tk.END, texto)
        self.notebook.select(4)  # Cambiar a pestaña de archivos
    
    def guardar_reporte_pdf(self):
        """Genera y guarda un reporte en PDF con gráficos"""
        try:
            if not REPORTLAB_AVAILABLE:
                raise Exception("Requiere: pip install reportlab pillow")
            
            # Crear PDF
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"reporte_SOLUSDT_{timestamp}.pdf"
            doc = SimpleDocTemplate(pdf_filename, pagesize=A4)
            story = []
            
            # Estilos
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor("#001AFF"),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#001AFF'),
                spaceAfter=12,
                spaceBefore=12
            )
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6
            )
            
            # Título
            story.append(Paragraph("ANÁLISIS TÉCNICO SOL/USDT", title_style))
            story.append(Spacer(1, 0.3 * inch))
            
            # Resumen
            story.append(Paragraph("📊 RESUMEN EJECUTIVO", heading_style))
            resultado = self.analizador.resultados
            
            resumen_data = [
                ["Precio Actual:", f"${resultado['precio_actual']:.2f}"],
                ["Timestamp:", resultado['timestamp']],
                ["Fuente de Datos:", resultado['fuente'].upper()],
                ["Confianza LONG:", f"{resultado['recomendaciones_long'].get('confianza', 0):.0f}%"],
                ["Confianza SHORT:", f"{resultado['recomendaciones_short'].get('confianza', 0):.0f}%"],
            ]
            
            resumen_table = Table(resumen_data, colWidths=[2*inch, 4*inch])
            resumen_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#000000")),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            story.append(resumen_table)
            story.append(Spacer(1, 0.3 * inch))
            
            # Archivos utilizados
            story.append(Paragraph("📁 ARCHIVOS UTILIZADOS", heading_style))
            archivos_data = [["Timeframe", "Archivo", "Registros"]]
            for tf in sorted(resultado['archivo_info'].keys()):
                info = resultado['archivo_info'][tf]
                archivos_data.append([tf.upper(), info['archivo'], f"{info['registros']:,}"])
            
            archivos_table = Table(archivos_data, colWidths=[1*inch, 3*inch, 1.5*inch])
            archivos_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00FFFF')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            story.append(archivos_table)
            story.append(PageBreak())
            
            # Indicadores
            story.append(Paragraph("📈 INDICADORES TÉCNICOS", heading_style))
            indicadores_data = [["Timeframe", "RSI", "Estado", "MACD", "Signal"]]
            for tf in ['1m', '5m', '15m', '1h', '4h', '1d']:
                if tf in resultado['rsi']:
                    rsi = resultado['rsi'][tf]
                    macd = resultado['macd'].get(tf, {})
                    indicadores_data.append([
                        tf.upper(),
                        f"{rsi['valor']:.2f}",
                        rsi['estado'],
                        f"{macd.get('valor', 0):.6f}",
                        f"{macd.get('signal', 0):.6f}"
                    ])
            
            indicadores_table = Table(indicadores_data, colWidths=[1*inch, 1*inch, 1.2*inch, 1.4*inch, 1.4*inch])
            indicadores_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00FFFF')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            story.append(indicadores_table)
            story.append(Spacer(1, 0.3 * inch))
            
            # Estrategias
            story.append(Paragraph("🎯 ESTRATEGIAS OPERATIVAS", heading_style))
            
            long = resultado.get('recomendaciones_long', {})
            short = resultado.get('recomendaciones_short', {})
            
            estrategias_data = [
                ["CONCEPTO", "LONG", "SHORT"],
                ["Confianza", f"{long.get('confianza', 0):.0f}%", f"{short.get('confianza', 0):.0f}%"],
                ["Entrada 1", f"${long.get('entrada_1', 0):.2f}", f"${short.get('entrada_1', 0):.2f}"],
                ["Entrada 2", f"${long.get('entrada_2', 0):.2f}", f"${short.get('entrada_2', 0):.2f}"],
                ["Target 1", f"${long.get('target_1', 0):.2f}", f"${short.get('target_1', 0):.2f}"],
                ["Target 2", f"${long.get('target_2', 0):.2f}", f"${short.get('target_2', 0):.2f}"],
                ["Stop Loss", f"${long.get('stop_loss', 0):.2f}", f"${short.get('stop_loss', 0):.2f}"],
                ["Riesgo", f"-{long.get('riesgo', 0):.2f}%", f"+{short.get('riesgo', 0):.2f}%"],
                ["Ganancia", f"+{long.get('ganancia', 0):.2f}%", f"+{short.get('ganancia', 0):.2f}%"],
            ]
            
            estrategias_table = Table(estrategias_data, colWidths=[2*inch, 2*inch, 2*inch])
            estrategias_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00FFFF')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('BACKGROUND', (1, 1), (1, -1), colors.HexColor('#90EE90')),
                ('BACKGROUND', (2, 1), (2, -1), colors.HexColor('#FFB6C6')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            story.append(estrategias_table)
            story.append(PageBreak())
            
            # Gráficos
            story.append(Paragraph("📊 GRÁFICOS TÉCNICOS", heading_style))
            
            if '1h' in self.analizador.dataframes:
                df_1h = self.analizador.dataframes['1h']
                
                # Generar gráfico
                fig = plt.Figure(figsize=(7, 5), dpi=100, facecolor='white')
                
                ax1 = fig.add_subplot(2, 2, 1)
                ax1.plot(range(len(df_1h)-50, len(df_1h)), df_1h['Close'].iloc[-50:], label='Close', color='cyan', linewidth=2)
                ax1.plot(range(len(df_1h)-50, len(df_1h)), df_1h['MA7'].iloc[-50:], label='MA7', color='yellow', alpha=0.7)
                ax1.plot(range(len(df_1h)-50, len(df_1h)), df_1h['MA25'].iloc[-50:], label='MA25', color='orange', alpha=0.7)
                ax1.plot(range(len(df_1h)-50, len(df_1h)), df_1h['MA99'].iloc[-50:], label='MA99', color='red', alpha=0.7)
                ax1.set_title('Precio y Medias Móviles', fontsize=10, fontweight='bold')
                ax1.legend(loc='best', fontsize=8)
                ax1.grid(alpha=0.2)
                ax1.set_facecolor('#f5f5f5')
                
                ax2 = fig.add_subplot(2, 2, 2)
                ax2.plot(range(len(df_1h)-50, len(df_1h)), df_1h['RSI'].iloc[-50:], color='cyan', linewidth=2)
                ax2.axhline(y=70, color='red', linestyle='--', alpha=0.5, label='Sobrecompra')
                ax2.axhline(y=30, color='green', linestyle='--', alpha=0.5, label='Sobreventa')
                ax2.fill_between(range(len(df_1h)-50, len(df_1h)), 30, 70, alpha=0.1, color='gray')
                ax2.set_title('RSI(14)', fontsize=10, fontweight='bold')
                ax2.legend(loc='best', fontsize=8)
                ax2.set_ylim(0, 100)
                ax2.grid(alpha=0.2)
                ax2.set_facecolor('#f5f5f5')
                
                ax3 = fig.add_subplot(2, 2, 3)
                ax3.plot(range(len(df_1h)-50, len(df_1h)), df_1h['MACD'].iloc[-50:], label='MACD', color='cyan', linewidth=2)
                ax3.plot(range(len(df_1h)-50, len(df_1h)), df_1h['MACD_Signal'].iloc[-50:], label='Signal', color='red', linewidth=2)
                ax3.bar(range(len(df_1h)-50, len(df_1h)), df_1h['MACD_Histogram'].iloc[-50:], label='Histogram', color='gray', alpha=0.3)
                ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
                ax3.set_title('MACD', fontsize=10, fontweight='bold')
                ax3.legend(loc='best', fontsize=8)
                ax3.grid(alpha=0.2)
                ax3.set_facecolor('#f5f5f5')
                
                ax4 = fig.add_subplot(2, 2, 4)
                colors_vol = ['green' if df_1h['Close'].iloc[i] >= df_1h['Open'].iloc[i] else 'red' 
                              for i in range(len(df_1h)-50, len(df_1h))]
                ax4.bar(range(len(df_1h)-50, len(df_1h)), df_1h['Volume'].iloc[-50:], color=colors_vol, alpha=0.7)
                ax4.set_title('Volumen', fontsize=10, fontweight='bold')
                ax4.grid(alpha=0.2, axis='y')
                ax4.set_facecolor('#f5f5f5')
                
                fig.tight_layout()
                
                # Convertir figura a imagen
                img_buffer = io.BytesIO()
                fig.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
                img_buffer.seek(0)
                
                # Agregar imagen al PDF
                temp_img_path = f"temp_graph_{timestamp}.png"
                with open(temp_img_path, 'wb') as f:
                    f.write(img_buffer.getvalue())
                
                story.append(Image(temp_img_path, width=7*inch, height=5*inch))
                story.append(Spacer(1, 0.2 * inch))
                
                plt.close(fig)
            
            # Footer
            story.append(Spacer(1, 0.3 * inch))
            footer_text = f"Reporte generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Sistema de Análisis SOL/USDT"
            story.append(Paragraph(footer_text, normal_style))
            
            # Generar PDF
            doc.build(story)
            
            # Eliminar archivo temporal después de generar el PDF
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)
 
            return pdf_filename
        except Exception as e:
            raise Exception(f"Error generando PDF: {str(e)}")
    
    def generar_analisis(self):
        """Genera análisis y gráficos"""
        try:
            self.actualizar_estado("⏳ Generando análisis...")
            self.analizador.generar_analisis()
            
            self.mostrar_resumen()
            self.mostrar_indicadores()
            self.mostrar_estrategias()
            
            self.actualizar_estado("⏳ Generando gráficos...")
            self.generar_graficos()
            
            # Generar PDF
            self.actualizar_estado("⏳ Generando reporte PDF...")
            pdf_file = self.guardar_reporte_pdf()
            
            self.notebook.select(0)
            
            self.actualizar_estado("✓ Análisis completado")
            messagebox.showinfo("Éxito", f"Análisis generado exitosamente\n\nReporte PDF: {pdf_file}")
        except Exception as e:
            self.actualizar_estado("✗ Error")
            messagebox.showerror("Error", str(e))
    
    def mostrar_resumen(self):
        """Muestra resumen de análisis"""
        self.text_resumen.delete(1.0, tk.END)
        
        if not self.analizador.resultados:
            self.text_resumen.insert(tk.END, "No hay datos disponibles")
            return
        
        resultado = self.analizador.resultados
        
        texto = f"""
╔════════════════════════════════════════════════════════════════════╗
║         ANÁLISIS TÉCNICO SOL/USDT - RESUMEN EJECUTIVO             ║
╚════════════════════════════════════════════════════════════════════╝

📊 PRECIO ACTUAL: ${resultado['precio_actual']:.2f} USD

⏰ Timestamp Análisis: {resultado['timestamp']}

📍 Fuente de datos: {resultado['fuente'].upper()}
   • Timeframes < 1D: 1000 candles
   • Timeframe 1D: 300 candles

📁 ARCHIVOS UTILIZADOS:
"""
        
        for tf in sorted(resultado['archivo_info'].keys()):
            info = resultado['archivo_info'][tf]
            texto += f"   {tf.upper()}: {info['archivo']} ({info['registros']:,} registros)\n"
        
        texto += f"""
═══════════════════════════════════════════════════════════════════════

✓ Análisis completado exitosamente
  - Indicadores técnicos: RSI, MACD, Medias Móviles
  - Estrategias: LONG y SHORT con confianza %
  - Gráficos generados
  - PDF de reporte generado automáticamente
"""
        
        self.text_resumen.insert(tk.END, texto)
    
    def mostrar_indicadores(self):
        """Muestra indicadores"""
        self.text_indicadores.delete(1.0, tk.END)
        
        if not self.analizador.resultados:
            self.text_indicadores.insert(tk.END, "No hay datos disponibles")
            return
        
        resultado = self.analizador.resultados
        
        texto = "ANÁLISIS DE INDICADORES POR TIMEFRAME\n"
        texto += "=" * 70 + "\n\n"
        
        for tf in ['1m', '5m', '15m', '1h', '4h', '1d']:
            if tf in resultado['rsi']:
                rsi = resultado['rsi'][tf]
                macd = resultado['macd'].get(tf, {})
                
                texto += f"\n{tf.upper()}:\n"
                texto += f"  RSI: {rsi['valor']:.2f} ({rsi['estado']})\n"
                texto += f"  MACD: {macd.get('valor', 0):.6f}\n"
                texto += f"  Signal: {macd.get('signal', 0):.6f}\n"
                texto += "-" * 70 + "\n"
        
        self.text_indicadores.insert(tk.END, texto)
    
    def mostrar_estrategias(self):
        """Muestra recomendaciones LONG y SHORT"""
        self.text_estrategias.delete(1.0, tk.END)
        
        if not self.analizador.resultados:
            self.text_estrategias.insert(tk.END, "No hay datos disponibles")
            return
        
        long = self.analizador.resultados.get('recomendaciones_long', {})
        short = self.analizador.resultados.get('recomendaciones_short', {})
        
        texto = f"""
╔════════════════════════════════════════════════════════════════════╗
║                    ESTRATEGIAS OPERATIVAS                          ║
╚════════════════════════════════════════════════════════════════════╝

{'='*70}
🟢 ESTRATEGIA LONG - COMPRA
{'='*70}

Confianza: {long.get('confianza', 0):.0f}%

ENTRADA FASE 1 (50% capital):
  Precio: ${long.get('entrada_1', 0):.2f}
  Target 1: ${long.get('target_1', 0):.2f} (+{long.get('ganancia', 0):.2f}%)
  Target 2: ${long.get('target_2', 0):.2f}

ENTRADA FASE 2 (50% capital, si baja):
  Precio: ${long.get('entrada_2', 0):.2f}

STOP LOSS (CIERRA TODO):
  Precio: ${long.get('stop_loss', 0):.2f}
  Riesgo: -{long.get('riesgo', 0):.2f}%

Risk/Reward: 1:{(long.get('ganancia', 0) / max(long.get('riesgo', 1), 0.01)):.2f}
Timeframe: 2-4 horas

{'='*70}
🔴 ESTRATEGIA SHORT - VENTA
{'='*70}

Confianza: {short.get('confianza', 0):.0f}%

ENTRADA FASE 1 (50% capital):
  Precio: ${short.get('entrada_1', 0):.2f}
  Target 1: ${short.get('target_1', 0):.2f} ({((short.get('target_1', 0) - short.get('entrada_1', 0)) / short.get('entrada_1', 1) * 100):.2f}%)
  Target 2: ${short.get('target_2', 0):.2f}

ENTRADA FASE 2 (50% capital, si sube):
  Precio: ${short.get('entrada_2', 0):.2f}

STOP LOSS (CIERRA TODO):
  Precio: ${short.get('stop_loss', 0):.2f}
  Riesgo: +{short.get('riesgo', 0):.2f}%

Risk/Reward: 1:{(short.get('ganancia', 0) / max(short.get('riesgo', 1), 0.01)):.2f}
Timeframe: 4-6 horas

{'='*70}
📋 RECOMENDACIÓN FINAL
{'='*70}

Basado en confianza calculada:
  • LONG: {long.get('confianza', 0):.0f}%
  • SHORT: {short.get('confianza', 0):.0f}%

Elige la estrategia con MAYOR confianza.
"""
        
        self.text_estrategias.insert(tk.END, texto)
    
    def generar_graficos(self):
        """Genera gráficos en la pestaña Gráficos"""
        if not self.analizador.dataframes:
            messagebox.showwarning("Advertencia", "No hay datos para graficar")
            return
        
        for widget in self.tab_graficos.winfo_children():
            widget.destroy()
        
        try:
            fig = Figure(figsize=(14, 8), dpi=100, facecolor='#2b2b2b')
            
            ax1 = fig.add_subplot(2, 2, 1)
            df_1h = self.analizador.dataframes['1h']
            ax1.plot(range(len(df_1h)-50, len(df_1h)), df_1h['Close'].iloc[-50:], label='Close', color='cyan', linewidth=2)
            ax1.plot(range(len(df_1h)-50, len(df_1h)), df_1h['MA7'].iloc[-50:], label='MA7', color='yellow', alpha=0.7)
            ax1.plot(range(len(df_1h)-50, len(df_1h)), df_1h['MA25'].iloc[-50:], label='MA25', color='orange', alpha=0.7)
            ax1.plot(range(len(df_1h)-50, len(df_1h)), df_1h['MA99'].iloc[-50:], label='MA99', color='red', alpha=0.7)
            ax1.set_title('SOL/USDT 1H - Precio y Medias Móviles', color='cyan', fontsize=12, fontweight='bold')
            ax1.legend(loc='best', facecolor='#1e1e1e', edgecolor='white', labelcolor='cyan')
            ax1.grid(alpha=0.2)
            ax1.set_facecolor('#1e1e1e')
            ax1.tick_params(colors='white')
            
            ax2 = fig.add_subplot(2, 2, 2)
            ax2.plot(range(len(df_1h)-50, len(df_1h)), df_1h['RSI'].iloc[-50:], color='cyan', linewidth=2)
            ax2.axhline(y=70, color='red', linestyle='--', alpha=0.5, label='Sobrecompra')
            ax2.axhline(y=30, color='green', linestyle='--', alpha=0.5, label='Sobreventa')
            ax2.fill_between(range(len(df_1h)-50, len(df_1h)), 30, 70, alpha=0.1, color='gray')
            ax2.set_title('RSI(14) 1H', color='cyan', fontsize=12, fontweight='bold')
            ax2.legend(loc='best', facecolor='#1e1e1e', edgecolor='white', labelcolor='cyan')
            ax2.set_ylim(0, 100)
            ax2.grid(alpha=0.2)
            ax2.set_facecolor('#1e1e1e')
            ax2.tick_params(colors='white')
            
            ax3 = fig.add_subplot(2, 2, 3)
            ax3.plot(range(len(df_1h)-50, len(df_1h)), df_1h['MACD'].iloc[-50:], label='MACD', color='cyan', linewidth=2)
            ax3.plot(range(len(df_1h)-50, len(df_1h)), df_1h['MACD_Signal'].iloc[-50:], label='Signal', color='red', linewidth=2)
            ax3.bar(range(len(df_1h)-50, len(df_1h)), df_1h['MACD_Histogram'].iloc[-50:], label='Histogram', color='gray', alpha=0.3)
            ax3.axhline(y=0, color='white', linestyle='-', alpha=0.3)
            ax3.set_title('MACD 1H', color='cyan', fontsize=12, fontweight='bold')
            ax3.legend(loc='best', facecolor='#1e1e1e', edgecolor='white', labelcolor='cyan')
            ax3.grid(alpha=0.2)
            ax3.set_facecolor('#1e1e1e')
            ax3.tick_params(colors='white')
            
            ax4 = fig.add_subplot(2, 2, 4)
            colors = ['green' if df_1h['Close'].iloc[i] >= df_1h['Open'].iloc[i] else 'red' 
                      for i in range(len(df_1h)-50, len(df_1h))]
            ax4.bar(range(len(df_1h)-50, len(df_1h)), df_1h['Volume'].iloc[-50:], color=colors, alpha=0.7)
            ax4.set_title('Volumen 1H', color='cyan', fontsize=12, fontweight='bold')
            ax4.grid(alpha=0.2, axis='y')
            ax4.set_facecolor('#1e1e1e')
            ax4.tick_params(colors='white')
            
            fig.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, master=self.tab_graficos)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            messagebox.showerror("Error", f"Error mostrando gráficos: {str(e)}")


def main():
    """Función principal"""
    root = tk.Tk()
    gui = GUIAnalisisSol(root)
    root.mainloop()


if __name__ == '__main__':
    main()
