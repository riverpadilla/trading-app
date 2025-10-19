"""
Estrategia de Trading Mejorada - Múltiples Señales de Entrada y Salida
Bot de Trading con mayor sensibilidad para detectar más oportunidades
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os

class TechnicalIndicators:
    """Clase para calcular indicadores técnicos ampliados"""
    
    @staticmethod
    def rsi(prices, period=14):
        """Calcula el RSI (Relative Strength Index)"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def moving_average(prices, period):
        """Calcula Media Móvil Simple"""
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def ema(prices, period):
        """Calcula Media Móvil Exponencial"""
        return prices.ewm(span=period).mean()
    
    @staticmethod
    def macd(prices, fast=12, slow=26, signal=9):
        """Calcula MACD (Moving Average Convergence Divergence)"""
        exp1 = prices.ewm(span=fast).mean()
        exp2 = prices.ewm(span=slow).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def bollinger_bands(prices, period=20, std_dev=2):
        """Calcula Bandas de Bollinger"""
        ma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = ma + (std * std_dev)
        lower = ma - (std * std_dev)
        return upper, ma, lower
    
    @staticmethod
    def stochastic(high, low, close, k_period=14, d_period=3):
        """Calcula el oscilador estocástico"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        return k_percent, d_percent
    
    @staticmethod
    def momentum(prices, period=10):
        """Calcula el momentum"""
        return prices.diff(period)
    
    @staticmethod
    def price_change_rate(prices, period=1):
        """Calcula tasa de cambio de precio"""
        return (prices.pct_change(period) * 100)

class EnhancedTradingStrategy:
    """Estrategia de trading mejorada con múltiples señales"""
    
    def __init__(self, 
                 rsi_oversold=35, rsi_overbought=65,  # Menos extremos
                 rsi_extreme_oversold=20, rsi_extreme_overbought=80):  # Niveles extremos
        
        # Parámetros RSI
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.rsi_extreme_oversold = rsi_extreme_oversold
        self.rsi_extreme_overbought = rsi_extreme_overbought
        
        # Estado de posición
        self.position = None
        self.entry_price = 0
        self.entry_time = None
        
        # Configuración de sensibilidad
        self.min_signals_for_entry = 1  # Reducido de 2 a 1
        self.min_signals_for_exit = 1   # Reducido de 2 a 1
        
    def generate_signals(self, df):
        """Genera señales de compra y venta mejoradas"""
        signals = pd.DataFrame(index=df.index)
        signals['price'] = df['close']
        signals['high'] = df['high']
        signals['low'] = df['low']
        signals['signal'] = 0
        signals['position'] = 0
        signals['signal_strength'] = 0  # Nueva columna para fuerza de señal
        signals['signal_type'] = ''     # Tipo de señal que activó la operación
        
        # Calcular todos los indicadores
        signals['rsi'] = TechnicalIndicators.rsi(df['close'])
        signals['rsi_fast'] = TechnicalIndicators.rsi(df['close'], period=7)  # RSI más rápido
        
        signals['ma9'] = TechnicalIndicators.moving_average(df['close'], 9)
        signals['ma21'] = TechnicalIndicators.moving_average(df['close'], 21)
        signals['ema12'] = TechnicalIndicators.ema(df['close'], 12)
        signals['ema26'] = TechnicalIndicators.ema(df['close'], 26)
        
        macd_line, signal_line, histogram = TechnicalIndicators.macd(df['close'])
        signals['macd'] = macd_line
        signals['macd_signal'] = signal_line
        signals['macd_histogram'] = histogram
        
        # Bandas de Bollinger
        bb_upper, bb_middle, bb_lower = TechnicalIndicators.bollinger_bands(df['close'])
        signals['bb_upper'] = bb_upper
        signals['bb_middle'] = bb_middle
        signals['bb_lower'] = bb_lower
        
        # Estocástico
        stoch_k, stoch_d = TechnicalIndicators.stochastic(df['high'], df['low'], df['close'])
        signals['stoch_k'] = stoch_k
        signals['stoch_d'] = stoch_d
        
        # Momentum
        signals['momentum'] = TechnicalIndicators.momentum(df['close'])
        signals['price_change'] = TechnicalIndicators.price_change_rate(df['close'])
        
        # Generar señales con lógica mejorada
        for i in range(2, len(signals)):  # Comenzar desde 2 para tener datos previos
            
            # Obtener valores actuales y previos
            current_price = signals['price'].iloc[i]
            prev_price = signals['price'].iloc[i-1]
            
            # Calcular señales de entrada múltiples
            buy_signals = self._calculate_buy_signals(signals, i)
            sell_signals = self._calculate_sell_signals(signals, i)
            
            # Verificar condiciones especiales
            stop_loss_triggered = self._check_stop_loss(signals, i)
            take_profit_triggered = self._check_take_profit(signals, i)
            
            # Lógica de decisión mejorada
            current_position = signals['position'].iloc[i-1]
            
            if current_position == 0:  # Sin posición
                # Buscar señales de compra
                total_buy_strength = sum(buy_signals.values())
                strong_signals = [k for k, v in buy_signals.items() if v >= 0.7]
                
                # Entrar si hay al menos 1 señal fuerte O 2 señales medianas
                if (total_buy_strength >= 0.7 or len(strong_signals) >= 1 or 
                    sum(1 for v in buy_signals.values() if v >= 0.4) >= 2):
                    
                    signals.loc[signals.index[i], 'signal'] = 1
                    signals.loc[signals.index[i], 'position'] = 1
                    signals.loc[signals.index[i], 'signal_strength'] = total_buy_strength
                    signals.loc[signals.index[i], 'signal_type'] = f"BUY: {', '.join(strong_signals)}"
                else:
                    signals.loc[signals.index[i], 'position'] = 0
                    
            else:  # Con posición larga
                # Buscar señales de venta
                total_sell_strength = sum(sell_signals.values())
                strong_sell_signals = [k for k, v in sell_signals.items() if v >= 0.7]
                
                # Salir por señales técnicas, stop loss o take profit
                if (stop_loss_triggered or take_profit_triggered or 
                    total_sell_strength >= 0.6 or len(strong_sell_signals) >= 1):
                    
                    signals.loc[signals.index[i], 'signal'] = -1
                    signals.loc[signals.index[i], 'position'] = 0
                    
                    exit_reason = []
                    if stop_loss_triggered: exit_reason.append("STOP_LOSS")
                    if take_profit_triggered: exit_reason.append("TAKE_PROFIT")
                    if strong_sell_signals: exit_reason.extend(strong_sell_signals)
                    
                    signals.loc[signals.index[i], 'signal_strength'] = total_sell_strength
                    signals.loc[signals.index[i], 'signal_type'] = f"SELL: {', '.join(exit_reason)}"
                else:
                    signals.loc[signals.index[i], 'position'] = 1
        
        return signals
    
    def _calculate_buy_signals(self, signals, i):
        """Calcula múltiples señales de compra con ponderaciones"""
        buy_signals = {}
        
        # Valores actuales y previos
        current_rsi = signals['rsi'].iloc[i]
        prev_rsi = signals['rsi'].iloc[i-1]
        current_rsi_fast = signals['rsi_fast'].iloc[i]
        
        current_ma9 = signals['ma9'].iloc[i]
        current_ma21 = signals['ma21'].iloc[i]
        prev_ma9 = signals['ma9'].iloc[i-1]
        prev_ma21 = signals['ma21'].iloc[i-1]
        
        current_price = signals['price'].iloc[i]
        bb_lower = signals['bb_lower'].iloc[i]
        bb_middle = signals['bb_middle'].iloc[i]
        
        current_macd = signals['macd'].iloc[i]
        current_macd_signal = signals['macd_signal'].iloc[i]
        prev_macd = signals['macd'].iloc[i-1]
        prev_macd_signal = signals['macd_signal'].iloc[i-1]
        
        stoch_k = signals['stoch_k'].iloc[i]
        momentum = signals['momentum'].iloc[i]
        price_change = signals['price_change'].iloc[i]
        
        # 1. RSI Signals (múltiples niveles)
        if current_rsi < self.rsi_extreme_oversold:
            buy_signals['RSI_EXTREME'] = 1.0  # Señal muy fuerte
        elif current_rsi < self.rsi_oversold and prev_rsi >= self.rsi_oversold:
            buy_signals['RSI_OVERSOLD'] = 0.8  # Señal fuerte
        elif current_rsi < self.rsi_oversold:
            buy_signals['RSI_LOW'] = 0.5  # Señal media
        
        # 2. RSI rápido
        if current_rsi_fast < 25:
            buy_signals['RSI_FAST'] = 0.6
        
        # 3. Media Móvil Signals
        if current_ma9 > current_ma21 and prev_ma9 <= prev_ma21:
            buy_signals['MA_GOLDEN_CROSS'] = 0.9  # Cruce dorado
        elif current_ma9 > current_ma21:
            buy_signals['MA_BULLISH'] = 0.4  # Tendencia alcista
        
        # 4. MACD Signals
        if current_macd > current_macd_signal and prev_macd <= prev_macd_signal:
            buy_signals['MACD_CROSS'] = 0.8  # Cruce alcista
        elif current_macd > current_macd_signal:
            buy_signals['MACD_BULLISH'] = 0.4
        
        # 5. Bollinger Bands
        if current_price <= bb_lower:
            buy_signals['BB_OVERSOLD'] = 0.7  # Precio en banda inferior
        elif current_price < bb_middle:
            buy_signals['BB_BELOW_MIDDLE'] = 0.3
        
        # 6. Estocástico
        if stoch_k < 20:
            buy_signals['STOCH_OVERSOLD'] = 0.6
        
        # 7. Momentum
        if momentum > 0 and price_change > 0.1:
            buy_signals['MOMENTUM_POSITIVE'] = 0.5
        
        # 8. Rebote rápido (precio cae y sube rápidamente)
        if i >= 3:
            price_3_ago = signals['price'].iloc[i-3]
            if current_price > price_3_ago and signals['price'].iloc[i-1] < price_3_ago:
                buy_signals['QUICK_BOUNCE'] = 0.6
        
        return buy_signals
    
    def _calculate_sell_signals(self, signals, i):
        """Calcula múltiples señales de venta con ponderaciones"""
        sell_signals = {}
        
        # Valores actuales y previos
        current_rsi = signals['rsi'].iloc[i]
        prev_rsi = signals['rsi'].iloc[i-1]
        current_rsi_fast = signals['rsi_fast'].iloc[i]
        
        current_ma9 = signals['ma9'].iloc[i]
        current_ma21 = signals['ma21'].iloc[i]
        prev_ma9 = signals['ma9'].iloc[i-1]
        prev_ma21 = signals['ma21'].iloc[i-1]
        
        current_price = signals['price'].iloc[i]
        bb_upper = signals['bb_upper'].iloc[i]
        bb_middle = signals['bb_middle'].iloc[i]
        
        current_macd = signals['macd'].iloc[i]
        current_macd_signal = signals['macd_signal'].iloc[i]
        prev_macd = signals['macd'].iloc[i-1]
        prev_macd_signal = signals['macd_signal'].iloc[i-1]
        
        stoch_k = signals['stoch_k'].iloc[i]
        momentum = signals['momentum'].iloc[i]
        price_change = signals['price_change'].iloc[i]
        
        # 1. RSI Signals
        if current_rsi > self.rsi_extreme_overbought:
            sell_signals['RSI_EXTREME'] = 1.0
        elif current_rsi > self.rsi_overbought and prev_rsi <= self.rsi_overbought:
            sell_signals['RSI_OVERBOUGHT'] = 0.8
        elif current_rsi > self.rsi_overbought:
            sell_signals['RSI_HIGH'] = 0.5
        
        # 2. RSI rápido
        if current_rsi_fast > 75:
            sell_signals['RSI_FAST'] = 0.6
        
        # 3. Media Móvil Signals
        if current_ma9 < current_ma21 and prev_ma9 >= prev_ma21:
            sell_signals['MA_DEATH_CROSS'] = 0.9
        elif current_ma9 < current_ma21:
            sell_signals['MA_BEARISH'] = 0.4
        
        # 4. MACD Signals
        if current_macd < current_macd_signal and prev_macd >= prev_macd_signal:
            sell_signals['MACD_CROSS'] = 0.8
        elif current_macd < current_macd_signal:
            sell_signals['MACD_BEARISH'] = 0.4
        
        # 5. Bollinger Bands
        if current_price >= bb_upper:
            sell_signals['BB_OVERBOUGHT'] = 0.7
        elif current_price > bb_middle:
            sell_signals['BB_ABOVE_MIDDLE'] = 0.3
        
        # 6. Estocástico
        if stoch_k > 80:
            sell_signals['STOCH_OVERBOUGHT'] = 0.6
        
        # 7. Momentum negativo
        if momentum < 0 and price_change < -0.1:
            sell_signals['MOMENTUM_NEGATIVE'] = 0.5
        
        # 8. Caída rápida
        if i >= 3:
            price_3_ago = signals['price'].iloc[i-3]
            if current_price < price_3_ago and signals['price'].iloc[i-1] > price_3_ago:
                sell_signals['QUICK_DROP'] = 0.6
        
        return sell_signals
    
    def _check_stop_loss(self, signals, index, stop_loss_pct=0.015):  # Reducido a 1.5%
        """Verifica stop loss más ajustado"""
        if signals['position'].iloc[index-1] == 1:
            for j in range(index-1, -1, -1):
                if signals['signal'].iloc[j] == 1:
                    entry_price = signals['price'].iloc[j]
                    current_price = signals['price'].iloc[index]
                    loss_pct = (entry_price - current_price) / entry_price
                    return loss_pct >= stop_loss_pct
        return False
    
    def _check_take_profit(self, signals, index, take_profit_pct=0.01):  # Take profit al 1%
        """Verifica take profit para asegurar ganancias"""
        if signals['position'].iloc[index-1] == 1:
            for j in range(index-1, -1, -1):
                if signals['signal'].iloc[j] == 1:
                    entry_price = signals['price'].iloc[j]
                    current_price = signals['price'].iloc[index]
                    profit_pct = (current_price - entry_price) / entry_price
                    return profit_pct >= take_profit_pct
        return False

# Resto del código del BacktestEngine y TradingBot se mantiene igual...
# Solo necesitamos cambiar la estrategia

class BacktestEngine:
    """Motor de backtesting (sin cambios)"""
    
    def __init__(self, initial_usdt=1000, commission=0.001):
        self.initial_usdt = initial_usdt
        self.commission = commission
        self.reset()
    
    def reset(self):
        """Resetea el estado del backtest"""
        self.usdt_balance = self.initial_usdt
        self.bnb_balance = 0
        self.trades = []
        self.current_position = None
        self.entry_price = 0
        self.entry_time = None
        
    def run_backtest(self, signals_df):
        """Ejecuta el backtesting"""
        self.reset()
        
        for i, row in signals_df.iterrows():
            if row['signal'] == 1 and self.current_position is None:
                self._execute_buy(row['price'], i, row.get('signal_type', ''))
            elif row['signal'] == -1 and self.current_position == 'long':
                self._execute_sell(row['price'], i, row.get('signal_type', ''))
        
        if self.current_position == 'long':
            last_price = signals_df['price'].iloc[-1]
            last_time = signals_df.index[-1]
            self._execute_sell(last_price, last_time, 'FORCE_CLOSE', force_close=True)
        
        return self._calculate_results()
    
    def _execute_buy(self, price, timestamp, signal_type=''):
        """Ejecuta una operación de compra"""
        if self.usdt_balance > 10:
            usdt_to_spend = self.usdt_balance * 0.95
            commission_cost = usdt_to_spend * self.commission
            net_usdt = usdt_to_spend - commission_cost
            bnb_bought = net_usdt / price
            
            self.bnb_balance += bnb_bought
            self.usdt_balance -= usdt_to_spend
            
            self.current_position = 'long'
            self.entry_price = price
            self.entry_time = timestamp
            
            trade = {
                'type': 'BUY',
                'timestamp': timestamp,
                'price': price,
                'bnb_amount': bnb_bought,
                'usdt_amount': usdt_to_spend,
                'commission': commission_cost,
                'usdt_balance': self.usdt_balance,
                'bnb_balance': self.bnb_balance,
                'signal_type': signal_type
            }
            self.trades.append(trade)
    
    def _execute_sell(self, price, timestamp, signal_type='', force_close=False):
        """Ejecuta una operación de venta"""
        if self.bnb_balance > 0:
            usdt_received = self.bnb_balance * price
            commission_cost = usdt_received * self.commission
            net_usdt = usdt_received - commission_cost
            
            if self.entry_price > 0:
                pnl_pct = ((price - self.entry_price) / self.entry_price) * 100
            else:
                pnl_pct = 0
            
            self.usdt_balance += net_usdt
            bnb_sold = self.bnb_balance
            self.bnb_balance = 0
            
            trade = {
                'type': 'SELL',
                'timestamp': timestamp,
                'price': price,
                'bnb_amount': bnb_sold,
                'usdt_amount': usdt_received,
                'commission': commission_cost,
                'pnl_pct': pnl_pct,
                'entry_price': self.entry_price,
                'entry_time': self.entry_time,
                'usdt_balance': self.usdt_balance,
                'bnb_balance': self.bnb_balance,
                'force_close': force_close,
                'signal_type': signal_type
            }
            self.trades.append(trade)
            
            self.current_position = None
            self.entry_price = 0
            self.entry_time = None
    
    def _calculate_results(self):
        """Calcula los resultados del backtesting"""
        if not self.trades:
            return None
        
        buy_trades = [t for t in self.trades if t['type'] == 'BUY']
        sell_trades = [t for t in self.trades if t['type'] == 'SELL']
        
        total_trades = len(sell_trades)
        winning_trades = len([t for t in sell_trades if t['pnl_pct'] > 0])
        losing_trades = len([t for t in sell_trades if t['pnl_pct'] <= 0])
        
        if total_trades > 0:
            win_rate = (winning_trades / total_trades) * 100
            avg_win = np.mean([t['pnl_pct'] for t in sell_trades if t['pnl_pct'] > 0]) if winning_trades > 0 else 0
            avg_loss = np.mean([t['pnl_pct'] for t in sell_trades if t['pnl_pct'] <= 0]) if losing_trades > 0 else 0
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
        
        final_value = self.usdt_balance
        if self.bnb_balance > 0:
            last_price = sell_trades[-1]['price'] if sell_trades else buy_trades[-1]['price']
            final_value += self.bnb_balance * last_price
        
        total_return = ((final_value - self.initial_usdt) / self.initial_usdt) * 100
        total_commission = sum([t['commission'] for t in self.trades])
        
        # Análisis de tipos de señales
        buy_signal_types = [t.get('signal_type', '') for t in buy_trades]
        sell_signal_types = [t.get('signal_type', '') for t in sell_trades]
        
        results = {
            'initial_capital': self.initial_usdt,
            'final_capital': final_value,
            'total_return_pct': total_return,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate_pct': win_rate,
            'avg_win_pct': avg_win,
            'avg_loss_pct': avg_loss,
            'final_usdt_balance': self.usdt_balance,
            'final_bnb_balance': self.bnb_balance,
            'total_commission': total_commission,
            'trades_list': self.trades,
            'buy_signal_analysis': buy_signal_types,
            'sell_signal_analysis': sell_signal_types
        }
        
        return results

class EnhancedTradingBot:
    """Bot de Trading Mejorado"""
    
    def __init__(self, initial_capital=1000):
        self.strategy = EnhancedTradingStrategy()  # Nueva estrategia
        self.backtest_engine = BacktestEngine(initial_capital)
        self.data = None
        self.signals = None
        self.results = None
    
    def load_data(self, csv_file):
        """Carga datos desde archivo CSV"""
        try:
            self.data = pd.read_csv(csv_file)
            self.data['datetime'] = pd.to_datetime(self.data['datetime'])
            self.data.set_index('datetime', inplace=True)
            print(f"✅ Datos cargados: {len(self.data)} registros")
            print(f"📅 Período: {self.data.index[0]} a {self.data.index[-1]}")
            return True
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            return False
    
    def run_backtest(self, initial_capital=None):
        """Ejecuta el backtesting completo"""
        if self.data is None:
            print("❌ No hay datos cargados")
            return None
        
        if initial_capital:
            self.backtest_engine.initial_usdt = initial_capital
        
        print("🔄 Calculando indicadores técnicos mejorados...")
        self.signals = self.strategy.generate_signals(self.data)
        
        print("🔄 Ejecutando backtesting con estrategia mejorada...")
        self.results = self.backtest_engine.run_backtest(self.signals)
        
        if self.results:
            self.print_results()
            return self.results
        else:
            print("❌ Error en el backtesting")
            return None
    
    def print_results(self):
        """Imprime los resultados del backtesting"""
        if not self.results:
            print("❌ No hay resultados disponibles")
            return
        
        r = self.results
        
        print("\n" + "="*60)
        print("📊 RESULTADOS DEL BACKTESTING MEJORADO")
        print("="*60)
        
        print(f"💰 Capital inicial: ${r['initial_capital']:,.2f} USDT")
        print(f"💰 Capital final: ${r['final_capital']:,.2f} USDT")
        print(f"📈 Retorno total: {r['total_return_pct']:+.2f}%")
        print(f"💸 Comisiones totales: ${r['total_commission']:,.2f} USDT")
        
        print(f"\n📊 ESTADÍSTICAS DE TRADING:")
        print(f"🔄 Total de operaciones: {r['total_trades']}")
        print(f"✅ Operaciones exitosas: {r['winning_trades']}")
        print(f"❌ Operaciones fallidas: {r['losing_trades']}")
        print(f"🎯 Tasa de éxito: {r['win_rate_pct']:.1f}%")
        print(f"📈 Ganancia promedio: {r['avg_win_pct']:+.2f}%")
        print(f"📉 Pérdida promedio: {r['avg_loss_pct']:+.2f}%")
        
        print(f"\n💼 BALANCES FINALES:")
        print(f"💵 USDT: {r['final_usdt_balance']:,.2f}")
        print(f"🪙 BNB: {r['final_bnb_balance']:,.6f}")
        
        # Análisis de señales
        if r['trades_list']:
            print(f"\n📋 ANÁLISIS DE SEÑALES:")
            buy_signals = [t.get('signal_type', '') for t in r['trades_list'] if t['type'] == 'BUY']
            sell_signals = [t.get('signal_type', '') for t in r['trades_list'] if t['type'] == 'SELL']
            
            print(f"🟢 Señales de compra más frecuentes:")
            for signal in set(buy_signals):
                count = buy_signals.count(signal)
                if count > 0:
                    print(f"   • {signal}: {count} veces")
            
            print(f"🔴 Señales de venta más frecuentes:")
            for signal in set(sell_signals):
                count = sell_signals.count(signal)
                if count > 0:
                    print(f"   • {signal}: {count} veces")
        
        # Mostrar últimas operaciones
        if r['trades_list']:
            print(f"\n📋 ÚLTIMAS 5 OPERACIONES:")
            for trade in r['trades_list'][-5:]:
                signal_info = trade.get('signal_type', '')
                if trade['type'] == 'SELL':
                    pnl_str = f"{trade['pnl_pct']:+.2f}%"
                    print(f"   {trade['timestamp']}: {trade['type']} ${trade['price']:.2f} | P&L: {pnl_str} | {signal_info}")
                else:
                    print(f"   {trade['timestamp']}: {trade['type']} ${trade['price']:.2f} | {signal_info}")
    
    def save_results(self, filename=None):
        """Guarda los resultados en CSV"""
        if not self.results or not self.results['trades_list']:
            print("❌ No hay resultados para guardar")
            return
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"enhanced_backtest_results_{timestamp}.csv"
        
        trades_df = pd.DataFrame(self.results['trades_list'])
        trades_df.to_csv(filename, index=False)
        
        print(f"💾 Resultados guardados en: {filename}")

def main():
    """Función principal para probar la estrategia mejorada"""
    
    print("🚀 BOT DE TRADING MEJORADO - MÚLTIPLES SEÑALES")
    print("="*60)
    
    CSV_FILE = "binance_BNBUSDT_1s_20251018_234757.csv"
    INITIAL_CAPITAL = 1000
    
    bot = EnhancedTradingBot(initial_capital=INITIAL_CAPITAL)
    
    if not bot.load_data(CSV_FILE):
        print("❌ No se pudo cargar el archivo de datos")
        return
    
    results = bot.run_backtest()
    
    if results:
        bot.save_results()
        print(f"\n🎉 ¡Backtesting mejorado completado!")
        print(f"📈 Estrategia con {results['total_trades']} operaciones vs 1 de la estrategia anterior")
    else:
        print("❌ Error en el backtesting")

if __name__ == "__main__":
    main()