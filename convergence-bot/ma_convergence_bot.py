"""
Bot de Trading basado en Convergencias de Medias Móviles
Estrategia basada en el análisis de scalping de chart_Scalping_analisys_umbral_fijo.py
"""

import pandas as pd
import numpy as np
import talib
from datetime import datetime, timedelta
import os

class MAConvergenceBot:
    def __init__(self, initial_capital=1000.0, ma1_period="MA7", ma2_period="MA25", 
                 umbral_ma1=0.0375, umbral_ma2=0.052, commission_rate=0.001, 
                 take_profit=0.002, stop_loss=0.001, verbose=True):
        """
        Inicializa el bot de convergencias MA con configuración optimizada
        
        Args:
            initial_capital: Capital inicial en USDT
            ma1_period: Período de la primera MA (MA3, MA7, MA14, MA25, MA50, MA99)
            ma2_period: Período de la segunda MA
            umbral_ma1: Umbral de pendiente para MA1 (0.0375 optimizado)
            umbral_ma2: Umbral de pendiente para MA2 (0.052 optimizado)
            commission_rate: Tasa de comisión (0.1% por defecto)
            take_profit: Objetivo de ganancia (0.2% por defecto)
            stop_loss: Stop loss (0.1% por defecto)
            verbose: Si mostrar output detallado (True por defecto)
            
        Configuración optimizada basada en test de matriz 400 combinaciones:
        - MA1=0.0375, MA2=0.052 → +0.466% retorno esperado
        - Estrategia ultra-selectiva: 1 trade por sesión, 100% win rate
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        
        # Configuración de MAs
        self.ma1_period = ma1_period
        self.ma2_period = ma2_period
        self.umbral_ma1 = umbral_ma1
        self.umbral_ma2 = umbral_ma2
        
        # Configuración de trading
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.verbose = verbose
        
        # Extraer números de los períodos
        self.ma1_value = int(ma1_period.replace('MA', ''))
        self.ma2_value = int(ma2_period.replace('MA', ''))
        
        # Estado del bot
        self.capital = initial_capital
        self.usdt_balance = initial_capital
        self.bnb_balance = 0.0
        
        # Tracking de operaciones
        self.trades = []
        self.position = None  # 'LONG' o None
        self.entry_price = 0.0
        self.entry_time = None
        
        # Sistema de convergencias persistentes
        self.convergencias_persistentes = []
        
        # Filtro anti-overtrading (45 segundos entre operaciones)
        self.last_trade_time = None
        self.min_time_between_trades = 45  # segundos
        
        self.data = None
    
    @classmethod
    def get_optimized_config(cls):
        """
        Retorna la configuración optimizada basada en test de matriz completa
        
        Returns:
            dict: Configuración optimizada con parámetros y estadísticas
        """
        return {
            'ma1_period': 'MA7',
            'ma2_period': 'MA25', 
            'umbral_ma1': 0.0375,
            'umbral_ma2': 0.052,
            'expected_return_pct': 0.466,
            'expected_trades_per_session': 1,
            'historical_win_rate': 100.0,
            'strategy_type': 'Ultra-selectiva',
            'test_basis': '400 combinaciones matriz completa',
            'session_duration': '5.5 horas',
            'description': 'Configuración óptima: 1 trade selectivo por sesión con alta precisión'
        }
    
    def _get_empty_result(self):
        """Retorna un resultado vacío válido"""
        return {
            'initial_capital': self.initial_capital,
            'final_capital': self.capital,
            'retorno_pct': 0.0,
            'total_return_pct': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'win_rate_pct': 0.0,
            'avg_win_pct': 0.0,
            'avg_loss_pct': 0.0,
            'total_commission': 0.0,
            'final_usdt_balance': self.usdt_balance,
            'final_bnb_balance': self.bnb_balance,
            'capital_final': self.capital,
            'convergencias_detectadas': 0,
            'convergencias_filtradas': 0,
            'trades_list': []
        }
    
    def load_data(self, csv_file):
        """Carga datos desde archivo CSV"""
        try:
            if not os.path.exists(csv_file):
                if self.verbose:
                    print(f"Error: Archivo {csv_file} no encontrado")
                return False
                
            self.data = pd.read_csv(csv_file)
            
            # Mapear columnas según el formato del CSV
            column_mapping = {
                'datetime': 'Open time',
                'open': 'Open',
                'high': 'High', 
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            }
            
            # Verificar si tenemos las columnas en minúsculas (formato del archivo actual)
            if 'datetime' in self.data.columns:
                # Renombrar columnas para consistencia
                self.data = self.data.rename(columns=column_mapping)
            
            # Verificar columnas requeridas
            required_columns = ['Open time', 'Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_columns:
                if col not in self.data.columns:
                    if self.verbose:
                        print(f"Error: Columna {col} no encontrada")
                        print(f"Columnas disponibles: {self.data.columns.tolist()}")
                    return False
            
            # Convertir tipos de datos
            self.data['Open time'] = pd.to_datetime(self.data['Open time'])
            self.data['Open'] = self.data['Open'].astype(float)
            self.data['High'] = self.data['High'].astype(float)
            self.data['Low'] = self.data['Low'].astype(float)
            self.data['Close'] = self.data['Close'].astype(float)
            self.data['Volume'] = self.data['Volume'].astype(float)
            
            # Crear índice temporal
            self.data.set_index('Open time', inplace=True)
            
            # Procesar indicadores
            self._calculate_indicators()
            
            if self.verbose:
                print(f"Datos cargados: {len(self.data)} registros")
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"Error cargando datos: {e}")
            return False
    
    def _calculate_indicators(self):
        """Calcula indicadores técnicos necesarios"""
        # Calcular todas las MAs disponibles
        for period in [3, 7, 14, 25, 50, 99]:
            self.data[f'MA{period}'] = talib.SMA(self.data['Close'].values, timeperiod=period)
        
        # Calcular RSI y MACD para referencia
        self.data['RSI'] = talib.RSI(self.data['Close'].values, timeperiod=14)
        macd_line, signal_line, _ = talib.MACD(self.data['Close'].values, 
                                              fastperiod=12, slowperiod=26, signalperiod=9)
        self.data['MACD'] = macd_line
        self.data['Signal'] = signal_line
    
    def _calculate_ma_segments(self, ma_column, umbral):
        """
        Calcula segmentos de tendencia para una MA específica
        Replica la lógica de calcular_lineas_tendencia_ma_individual
        """
        ma_values = self.data[ma_column].dropna()
        
        if len(ma_values) < 10:
            return []
        
        # Calcular pendientes móviles
        ventana = 3
        pendientes_locales = []
        indices_validos = []
        
        for i in range(ventana, len(ma_values) - ventana):
            inicio_idx = i - ventana // 2
            fin_idx = i + ventana // 2
            
            x_window = np.arange(fin_idx - inicio_idx + 1)
            y_window = ma_values.iloc[inicio_idx:fin_idx+1].values
            
            if len(x_window) > 1 and not np.any(np.isnan(y_window)):
                try:
                    pendiente = np.polyfit(x_window, y_window, 1)[0]
                    pendientes_locales.append(pendiente)
                    indices_validos.append(i)
                except:
                    continue
        
        if len(pendientes_locales) < 3:
            return []
        
        # Crear segmentos adaptativos
        longitud_segmento = max(20, len(ma_values) // 10)
        cambios_tendencia = [0]
        
        # Puntos de división fijos
        for i in range(longitud_segmento, len(ma_values), longitud_segmento):
            cambios_tendencia.append(i)
        
        # Detectar cambios significativos de pendiente
        umbral_cambio = max(np.std(pendientes_locales) * 0.8, 0.00005)
        
        for i in range(1, len(pendientes_locales)):
            cambio_pendiente = abs(pendientes_locales[i] - pendientes_locales[i-1])
            cambio_direccion = (pendientes_locales[i-1] > 0 and pendientes_locales[i] < 0) or \
                              (pendientes_locales[i-1] < 0 and pendientes_locales[i] > 0)
            
            if (cambio_pendiente > umbral_cambio or cambio_direccion) and \
               indices_validos[i] not in cambios_tendencia:
                cambios_tendencia.append(indices_validos[i])
        
        # Ordenar y agregar final
        cambios_tendencia = sorted(list(set(cambios_tendencia)))
        cambios_tendencia.append(len(ma_values) - 1)
        
        # Crear segmentos de tendencia
        segmentos_tendencia = []
        for i in range(len(cambios_tendencia) - 1):
            inicio_idx = cambios_tendencia[i]
            fin_idx = cambios_tendencia[i + 1]
            
            if fin_idx > inicio_idx:
                inicio_timestamp = ma_values.index[inicio_idx]
                fin_timestamp = ma_values.index[fin_idx]
                inicio_valor = ma_values.iloc[inicio_idx]
                fin_valor = ma_values.iloc[fin_idx]
                
                # Calcular pendiente del segmento
                x_vals = np.arange(fin_idx - inicio_idx + 1)
                y_vals = ma_values.iloc[inicio_idx:fin_idx+1].values
                
                if len(x_vals) > 1 and not np.any(np.isnan(y_vals)):
                    try:
                        pendiente = np.polyfit(x_vals, y_vals, 1)[0]
                        
                        # Determinar dirección según umbral
                        if pendiente > umbral:
                            direccion = 'alcista'
                        elif pendiente < -umbral:
                            direccion = 'bajista'
                        else:
                            direccion = 'lateral'
                        
                        segmentos_tendencia.append({
                            'inicio_idx': inicio_idx,
                            'fin_idx': fin_idx,
                            'inicio_timestamp': inicio_timestamp,
                            'fin_timestamp': fin_timestamp,
                            'inicio_valor': inicio_valor,
                            'fin_valor': fin_valor,
                            'pendiente': pendiente,
                            'direccion': direccion
                        })
                    except:
                        continue
        
        return segmentos_tendencia
    
    def _get_trend_at_timestamp(self, segmentos, timestamp):
        """Obtiene la tendencia de una MA en un timestamp específico"""
        for segmento in segmentos:
            if segmento['inicio_timestamp'] <= timestamp <= segmento['fin_timestamp']:
                return segmento['direccion']
        return None
    
    def _detect_ma2_direction_changes(self, segmentos_ma2):
        """Detecta cambios de dirección en MA2"""
        cambios = []
        
        for i in range(1, len(segmentos_ma2)):
            segmento_anterior = segmentos_ma2[i-1]
            segmento_actual = segmentos_ma2[i]
            
            # Verificar si hay cambio de dirección significativo
            if (segmento_anterior['direccion'] != segmento_actual['direccion'] and
                segmento_actual['direccion'] in ['alcista', 'bajista']):
                
                cambios.append({
                    'timestamp': segmento_actual['inicio_timestamp'],
                    'direccion_anterior': segmento_anterior['direccion'],
                    'direccion_nueva': segmento_actual['direccion'],
                    'pendiente_anterior': segmento_anterior['pendiente'],
                    'pendiente_nueva': segmento_actual['pendiente']
                })
        
        return cambios
    
    def _detect_convergences(self, segmentos_ma1, segmentos_ma2):
        """
        Detecta convergencias entre MA1 y MA2
        Replica la lógica de marcar_convergencias_doble_ma_rsi
        """
        convergencias_detectadas = []
        
        # Detectar cambios de dirección en MA2
        cambios_ma2 = self._detect_ma2_direction_changes(segmentos_ma2)
        
        # Para cada cambio de dirección en MA2, verificar condiciones
        for cambio in cambios_ma2:
            timestamp = cambio['timestamp']
            
            # Obtener RSI en ese momento para referencia
            try:
                idx = self.data.index[self.data.index >= timestamp][0]
                rsi_valor = self.data.loc[idx, 'RSI']
                close_valor = self.data.loc[idx, 'Close']
            except:
                continue
            
            # Obtener tendencia de MA1 en ese momento
            tendencia_ma1 = self._get_trend_at_timestamp(segmentos_ma1, timestamp)
            
            # CONDICIÓN 1: MA1 bajista + MA2 cambia a bajista (VENTA)
            if (tendencia_ma1 == 'bajista' and 
                cambio['direccion_nueva'] == 'bajista'):
                
                convergencias_detectadas.append({
                    'timestamp': timestamp,
                    'tipo': 'VENTA_CONVERGENCIA',
                    'rsi': rsi_valor,
                    'close': close_valor,
                    'ma1_tendencia': tendencia_ma1,
                    'ma2_cambio': cambio['direccion_nueva'],
                    'descripcion': 'MA1↘ + MA2→↘'
                })
            
            # CONDICIÓN 2: MA1 alcista + MA2 cambia a alcista (COMPRA)
            elif (tendencia_ma1 == 'alcista' and 
                  cambio['direccion_nueva'] == 'alcista'):
                
                convergencias_detectadas.append({
                    'timestamp': timestamp,
                    'tipo': 'COMPRA_CONVERGENCIA',
                    'rsi': rsi_valor,
                    'close': close_valor,
                    'ma1_tendencia': tendencia_ma1,
                    'ma2_cambio': cambio['direccion_nueva'],
                    'descripcion': 'MA1↗ + MA2→↗'
                })
        
        return convergencias_detectadas
    
    def _filter_consecutive_signals(self, convergencias):
        """
        Filtra señales consecutivas del mismo tipo
        Replica el sistema de filtrado del archivo original
        """
        # Agregar nuevas convergencias a la lista persistente (evitar duplicados)
        for conv in convergencias:
            es_nueva = True
            for conv_existente in self.convergencias_persistentes:
                # Convertir timestamps a valores comparables
                try:
                    tiempo_diff = abs((pd.Timestamp(conv['timestamp']) - pd.Timestamp(conv_existente['timestamp'])).total_seconds())
                    if tiempo_diff < 5:
                        es_nueva = False
                        break
                except:
                    # Si hay error en la conversión, considerar como nueva
                    continue
            
            if es_nueva:
                self.convergencias_persistentes.append(conv)
        
        # Limpiar convergencias muy antiguas (más de 30 minutos)
        if self.convergencias_persistentes:
            try:
                tiempo_actual = max([pd.Timestamp(c['timestamp']) for c in self.convergencias_persistentes])
                self.convergencias_persistentes = [
                    conv for conv in self.convergencias_persistentes 
                    if (tiempo_actual - pd.Timestamp(conv['timestamp'])).total_seconds() < 1800
                ]
            except:
                # Si hay error, mantener todas las convergencias
                pass
        
        # Filtrar señales consecutivas del mismo tipo
        convergencias_ordenadas = sorted(self.convergencias_persistentes, 
                                       key=lambda x: pd.Timestamp(x['timestamp']))
        
        convergencias_filtradas = []
        ultimo_tipo = None
        
        for conv in convergencias_ordenadas:
            if conv['tipo'] != ultimo_tipo:
                convergencias_filtradas.append(conv)
                ultimo_tipo = conv['tipo']
        
        return convergencias_filtradas
    
    def _can_trade(self, current_time):
        """Verifica si se puede hacer trading (filtro anti-overtrading)"""
        if self.last_trade_time is None:
            return True
        
        try:
            time_diff = (pd.Timestamp(current_time) - pd.Timestamp(self.last_trade_time)).total_seconds()
            return time_diff >= self.min_time_between_trades
        except:
            # Si hay error en la conversión, permitir trade
            return True
    
    def _execute_buy(self, price, timestamp):
        """Ejecuta una orden de compra"""
        if self.position is not None:
            return False  # Ya tenemos posición
        
        # Calcular cantidad a comprar (usar todo el USDT disponible)
        commission = self.usdt_balance * self.commission_rate
        usdt_to_spend = self.usdt_balance - commission
        
        if usdt_to_spend <= 0:
            return False
        
        bnb_quantity = usdt_to_spend / price
        
        # Actualizar balances
        self.usdt_balance = 0.0
        self.bnb_balance = bnb_quantity
        self.position = 'LONG'
        self.entry_price = price
        self.entry_time = timestamp
        self.last_trade_time = timestamp
        
        # Registrar operación
        self.trades.append({
            'timestamp': timestamp,
            'type': 'BUY',
            'price': price,
            'quantity': bnb_quantity,
            'commission': commission,
            'usdt_balance': self.usdt_balance,
            'bnb_balance': self.bnb_balance
        })
        
        return True
    
    def _execute_sell(self, price, timestamp, reason="SIGNAL"):
        """Ejecuta una orden de venta"""
        if self.position != 'LONG':
            return False  # No tenemos posición
        
        # Calcular valor de venta
        usdt_received = self.bnb_balance * price
        commission = usdt_received * self.commission_rate
        usdt_final = usdt_received - commission
        
        # Calcular P&L
        pnl_usdt = usdt_final - self.initial_capital
        pnl_pct = (pnl_usdt / self.initial_capital) * 100
        
        # Actualizar balances
        self.usdt_balance = usdt_final
        self.capital = usdt_final
        old_bnb_balance = self.bnb_balance
        self.bnb_balance = 0.0
        self.position = None
        self.last_trade_time = timestamp
        
        # Registrar operación
        self.trades.append({
            'timestamp': timestamp,
            'type': 'SELL',
            'price': price,
            'quantity': old_bnb_balance,
            'commission': commission,
            'usdt_balance': self.usdt_balance,
            'bnb_balance': self.bnb_balance,
            'pnl_usdt': pnl_usdt,
            'pnl_pct': pnl_pct,
            'reason': reason
        })
        
        return True
    
    def run_backtest(self, csv_file=None):
        """Ejecuta el backtesting de la estrategia"""
        if csv_file:
            if not self.load_data(csv_file):
                # Retornar resultado válido en lugar de None
                return self._get_empty_result()
        
        if self.data is None:
            if self.verbose:
                print("Error: No hay datos cargados")
            # Retornar resultado válido en lugar de None
            return self._get_empty_result()
        
        if self.verbose:
            print(f"Iniciando backtesting con {len(self.data)} registros...")
            print(f"MA1: {self.ma1_period} (umbral: {self.umbral_ma1})")
            print(f"MA2: {self.ma2_period} (umbral: {self.umbral_ma2})")
        
        # Calcular segmentos de tendencia UNA SOLA VEZ para todo el dataset
        if self.verbose:
            print("Calculando segmentos de tendencia...")
        segmentos_ma1 = self._calculate_ma_segments(self.ma1_period, self.umbral_ma1)
        segmentos_ma2 = self._calculate_ma_segments(self.ma2_period, self.umbral_ma2)
        
        if not segmentos_ma1 or not segmentos_ma2:
            if self.verbose:
                print("Error: No se pudieron calcular segmentos de tendencia")
            # Retornar resultado válido con 0 trades en lugar de None
            self.convergencias_detectadas = 0
            self.convergencias_filtradas_count = 0
            return self._get_empty_result()
        
        if self.verbose:
            print(f"Segmentos MA1: {len(segmentos_ma1)}, Segmentos MA2: {len(segmentos_ma2)}")
        
        # Detectar TODAS las convergencias de una vez
        if self.verbose:
            print("Detectando convergencias...")
        convergencias = self._detect_convergences(segmentos_ma1, segmentos_ma2)
        convergencias_filtradas = self._filter_consecutive_signals(convergencias)
        
        if self.verbose:
            print(f"Convergencias detectadas: {len(convergencias)}")
            print(f"Convergencias filtradas: {len(convergencias_filtradas)}")
        
        # Guardar convergencias para el resultado
        self.convergencias_detectadas = len(convergencias)
        self.convergencias_filtradas_count = len(convergencias_filtradas)
        
        # Procesar solo las convergencias filtradas en orden cronológico
        convergencias_ordenadas = sorted(convergencias_filtradas, 
                                       key=lambda x: pd.Timestamp(x['timestamp']))
        
        # Procesar datos row by row para simular trading en tiempo real
        convergencia_idx = 0
        processed_count = 0
        
        if self.verbose:
            print("Iniciando simulación de trading...")
        
        for i in range(50, len(self.data)):  # Empezar después de que las MAs estén estables
            current_row = self.data.iloc[i]
            current_time = self.data.index[i]
            current_price = current_row['Close']
            
            # Mostrar progreso cada 1000 registros
            processed_count += 1
            if self.verbose and processed_count % 1000 == 0:
                print(f"Procesados: {processed_count}/{len(self.data)-50} registros...")
            
            # Verificar si hay una convergencia en este timestamp
            signal_type = None
            
            while (convergencia_idx < len(convergencias_ordenadas)):
                conv = convergencias_ordenadas[convergencia_idx]
                conv_time = pd.Timestamp(conv['timestamp'])
                
                # Si la convergencia es anterior o igual al tiempo actual
                if conv_time <= current_time:
                    # Verificar si es muy reciente (dentro de los últimos 10 segundos)
                    time_diff = abs((current_time - conv_time).total_seconds())
                    if time_diff <= 10:
                        signal_type = conv['tipo']
                    convergencia_idx += 1
                else:
                    break
            # Verificar si tenemos una señal
            if signal_type and self._can_trade(current_time):
                if signal_type == 'COMPRA_CONVERGENCIA':
                    if self.position is None:
                        success = self._execute_buy(current_price, current_time)
                        if success and self.verbose:
                            print(f"COMPRA ejecutada: ${current_price:.4f} en {current_time}")
                
                elif signal_type == 'VENTA_CONVERGENCIA':
                    if self.position == 'LONG':
                        success = self._execute_sell(current_price, current_time, "CONVERGENCE_SIGNAL")
                        if success and self.verbose:
                            trade = self.trades[-1]
                            print(f"VENTA ejecutada: ${current_price:.4f} en {current_time} "
                                 f"| P&L: {trade['pnl_pct']:+.2f}%")
        
        # Cerrar posición final si está abierta
        if self.position == 'LONG':
            final_price = self.data.iloc[-1]['Close']
            final_time = self.data.index[-1]  # Usar el índice temporal
            self._execute_sell(final_price, final_time, "FINAL_CLOSE")
            if self.verbose:
                print(f"Posición final cerrada a ${final_price:.4f}")
        
        return self._calculate_results()
    
    def _calculate_results(self):
        """Calcula los resultados del backtesting"""
        if not self.trades:
            return {
                'initial_capital': self.initial_capital,
                'final_capital': self.capital,
                'retorno_pct': 0.0,
                'total_return_pct': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'win_rate_pct': 0.0,
                'avg_win_pct': 0.0,
                'avg_loss_pct': 0.0,
                'total_commission': 0.0,
                'final_usdt_balance': self.usdt_balance,
                'final_bnb_balance': self.bnb_balance,
                'capital_final': self.capital,
                'convergencias_detectadas': getattr(self, 'convergencias_detectadas', 0),
                'convergencias_filtradas': getattr(self, 'convergencias_filtradas_count', 0),
                'trades_list': []
            }
        
        # Calcular estadísticas de trades
        buy_trades = [t for t in self.trades if t['type'] == 'BUY']
        sell_trades = [t for t in self.trades if t['type'] == 'SELL']
        
        total_trades = len(sell_trades)  # Solo contar sells como trades completos
        winning_trades = len([t for t in sell_trades if t.get('pnl_pct', 0) > 0])
        losing_trades = total_trades - winning_trades
        
        win_rate_pct = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Promedio de ganancias y pérdidas
        wins = [t['pnl_pct'] for t in sell_trades if t.get('pnl_pct', 0) > 0]
        losses = [t['pnl_pct'] for t in sell_trades if t.get('pnl_pct', 0) <= 0]
        
        avg_win_pct = sum(wins) / len(wins) if wins else 0
        avg_loss_pct = sum(losses) / len(losses) if losses else 0
        
        # Comisiones totales
        total_commission = sum(t.get('commission', 0) for t in self.trades)
        
        # Retorno total
        total_return_pct = ((self.capital - self.initial_capital) / self.initial_capital) * 100
        
        return {
            'initial_capital': self.initial_capital,
            'final_capital': self.capital,
            'retorno_pct': total_return_pct,
            'total_return_pct': total_return_pct,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate_pct,
            'win_rate_pct': win_rate_pct,
            'avg_win_pct': avg_win_pct,
            'avg_loss_pct': avg_loss_pct,
            'total_commission': total_commission,
            'final_usdt_balance': self.usdt_balance,
            'final_bnb_balance': self.bnb_balance,
            'capital_final': self.capital,
            'convergencias_detectadas': getattr(self, 'convergencias_detectadas', 0),
            'convergencias_filtradas': getattr(self, 'convergencias_filtradas_count', 0),
            'trades_list': self.trades,
            'ma1_period': self.ma1_period,
            'ma2_period': self.ma2_period,
            'umbral_ma1': self.umbral_ma1,
            'umbral_ma2': self.umbral_ma2
        }
    
    def save_results(self):
        """Guarda los resultados en un archivo CSV"""
        if not self.trades:
            print("No hay trades para guardar")
            return
        
        # Crear DataFrame con los trades
        df_trades = pd.DataFrame(self.trades)
        
        # Generar nombre de archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ma_convergence_results_{self.ma1_period}_{self.ma2_period}_{timestamp}.csv"
        
        # Guardar archivo
        df_trades.to_csv(filename, index=False)
        print(f"Resultados guardados en: {filename}")
        
        return filename