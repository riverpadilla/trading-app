"""
Bot de Trading con Análisis Técnico para Backtesting
Indicadores: RSI, MA9/MA21, MACD
Par: BNBUSDT
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os

class TechnicalIndicators:
    """Clase para calcular indicadores técnicos"""
    
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

class TradingStrategy:
    """Estrategia de trading basada en RSI, MA y MACD"""
    
    def __init__(self, rsi_oversold=30, rsi_overbought=70):
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.position = None  # 'long', 'short', None
        self.entry_price = 0
        self.entry_time = None
    
    def generate_signals(self, df):
        """Genera señales de compra y venta"""
        signals = pd.DataFrame(index=df.index)
        signals['price'] = df['close']
        signals['signal'] = 0  # 0: hold, 1: buy, -1: sell
        signals['position'] = 0  # 0: no position, 1: long position
        
        # Calcular indicadores
        signals['rsi'] = TechnicalIndicators.rsi(df['close'])
        signals['ma9'] = TechnicalIndicators.moving_average(df['close'], 9)
        signals['ma21'] = TechnicalIndicators.moving_average(df['close'], 21)
        
        macd_line, signal_line, histogram = TechnicalIndicators.macd(df['close'])
        signals['macd'] = macd_line
        signals['macd_signal'] = signal_line
        signals['macd_histogram'] = histogram
        
        # Generar señales de entrada y salida
        for i in range(1, len(signals)):
            current_rsi = signals['rsi'].iloc[i]
            prev_rsi = signals['rsi'].iloc[i-1]
            
            current_ma9 = signals['ma9'].iloc[i]
            current_ma21 = signals['ma21'].iloc[i]
            prev_ma9 = signals['ma9'].iloc[i-1]
            prev_ma21 = signals['ma21'].iloc[i-1]
            
            current_macd = signals['macd'].iloc[i]
            current_macd_signal = signals['macd_signal'].iloc[i]
            prev_macd = signals['macd'].iloc[i-1]
            prev_macd_signal = signals['macd_signal'].iloc[i-1]
            
            # Condiciones de entrada (COMPRA)
            rsi_buy = current_rsi < self.rsi_oversold and prev_rsi >= self.rsi_oversold
            ma_bullish = current_ma9 > current_ma21 and prev_ma9 <= prev_ma21  # Cruce alcista
            macd_bullish = current_macd > current_macd_signal and prev_macd <= prev_macd_signal
            
            # Condiciones de salida (VENTA)
            rsi_sell = current_rsi > self.rsi_overbought and prev_rsi <= self.rsi_overbought
            ma_bearish = current_ma9 < current_ma21 and prev_ma9 >= prev_ma21  # Cruce bajista
            macd_bearish = current_macd < current_macd_signal and prev_macd >= prev_macd_signal
            
            # Lógica de señales
            if not pd.isna(current_rsi) and not pd.isna(current_ma9) and not pd.isna(current_macd):
                # Señal de compra: al menos 2 indicadores alcistas
                buy_signals = sum([rsi_buy, ma_bullish, macd_bullish])
                if buy_signals >= 2 and signals['position'].iloc[i-1] == 0:
                    signals.loc[signals.index[i], 'signal'] = 1
                    signals.loc[signals.index[i], 'position'] = 1
                
                # Señal de venta: al menos 2 indicadores bajistas O stop loss
                sell_signals = sum([rsi_sell, ma_bearish, macd_bearish])
                if (sell_signals >= 2 or self._check_stop_loss(signals, i)) and signals['position'].iloc[i-1] == 1:
                    signals.loc[signals.index[i], 'signal'] = -1
                    signals.loc[signals.index[i], 'position'] = 0
                else:
                    # Mantener posición anterior
                    signals.loc[signals.index[i], 'position'] = signals['position'].iloc[i-1]
        
        return signals
    
    def _check_stop_loss(self, signals, index, stop_loss_pct=0.02):
        """Verifica si se debe ejecutar stop loss (2% de pérdida)"""
        if signals['position'].iloc[index-1] == 1:  # Si tenemos posición larga
            # Buscar el precio de entrada (última señal de compra)
            for j in range(index-1, -1, -1):
                if signals['signal'].iloc[j] == 1:
                    entry_price = signals['price'].iloc[j]
                    current_price = signals['price'].iloc[index]
                    loss_pct = (entry_price - current_price) / entry_price
                    return loss_pct >= stop_loss_pct
        return False

class BacktestEngine:
    """Motor de backtesting"""
    
    def __init__(self, initial_usdt=1000, commission=0.001):
        self.initial_usdt = initial_usdt
        self.commission = commission  # 0.1% comisión por operación
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
                # Señal de compra
                self._execute_buy(row['price'], i)
            elif row['signal'] == -1 and self.current_position == 'long':
                # Señal de venta
                self._execute_sell(row['price'], i)
        
        # Si termina con posición abierta, cerrarla al último precio
        if self.current_position == 'long':
            last_price = signals_df['price'].iloc[-1]
            last_time = signals_df.index[-1]
            self._execute_sell(last_price, last_time, force_close=True)
        
        return self._calculate_results()
    
    def _execute_buy(self, price, timestamp):
        """Ejecuta una operación de compra"""
        if self.usdt_balance > 10:  # Mínimo para operar
            # Calcular cantidad a comprar (usar todo el saldo USDT disponible)
            usdt_to_spend = self.usdt_balance * 0.95  # Dejar 5% de margen
            commission_cost = usdt_to_spend * self.commission
            net_usdt = usdt_to_spend - commission_cost
            bnb_bought = net_usdt / price
            
            # Actualizar balances
            self.bnb_balance += bnb_bought
            self.usdt_balance -= usdt_to_spend
            
            # Registrar trade
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
                'bnb_balance': self.bnb_balance
            }
            self.trades.append(trade)
    
    def _execute_sell(self, price, timestamp, force_close=False):
        """Ejecuta una operación de venta"""
        if self.bnb_balance > 0:
            # Vender todo el BNB
            usdt_received = self.bnb_balance * price
            commission_cost = usdt_received * self.commission
            net_usdt = usdt_received - commission_cost
            
            # Calcular P&L
            if self.entry_price > 0:
                pnl_pct = ((price - self.entry_price) / self.entry_price) * 100
            else:
                pnl_pct = 0
            
            # Actualizar balances
            self.usdt_balance += net_usdt
            bnb_sold = self.bnb_balance
            self.bnb_balance = 0
            
            # Registrar trade
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
                'force_close': force_close
            }
            self.trades.append(trade)
            
            # Resetear posición
            self.current_position = None
            self.entry_price = 0
            self.entry_time = None
    
    def _calculate_results(self):
        """Calcula los resultados del backtesting"""
        if not self.trades:
            return None
        
        # Separar trades de compra y venta
        buy_trades = [t for t in self.trades if t['type'] == 'BUY']
        sell_trades = [t for t in self.trades if t['type'] == 'SELL']
        
        # Calcular estadísticas
        total_trades = len(sell_trades)  # Solo contar trades completos
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
        
        # Calcular valor total actual
        final_value = self.usdt_balance
        if self.bnb_balance > 0:  # Si queda BNB, usar último precio
            last_price = sell_trades[-1]['price'] if sell_trades else buy_trades[-1]['price']
            final_value += self.bnb_balance * last_price
        
        total_return = ((final_value - self.initial_usdt) / self.initial_usdt) * 100
        total_commission = sum([t['commission'] for t in self.trades])
        
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
            'trades_list': self.trades
        }
        
        return results

class TradingBot:
    """Bot de Trading Principal"""
    
    def __init__(self, initial_capital=1000):
        self.strategy = TradingStrategy()
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
        
        print("🔄 Calculando indicadores técnicos...")
        self.signals = self.strategy.generate_signals(self.data)
        
        print("🔄 Ejecutando backtesting...")
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
        print("📊 RESULTADOS DEL BACKTESTING")
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
        
        # Mostrar últimas 5 operaciones
        if r['trades_list']:
            print(f"\n📋 ÚLTIMAS OPERACIONES:")
            for trade in r['trades_list'][-5:]:
                if trade['type'] == 'SELL':
                    pnl_str = f"{trade['pnl_pct']:+.2f}%"
                    print(f"   {trade['timestamp']}: {trade['type']} ${trade['price']:.2f} | P&L: {pnl_str}")
                else:
                    print(f"   {trade['timestamp']}: {trade['type']} ${trade['price']:.2f}")
    
    def save_results(self, filename=None):
        """Guarda los resultados en CSV"""
        if not self.results or not self.results['trades_list']:
            print("❌ No hay resultados para guardar")
            return
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backtest_results_{timestamp}.csv"
        
        # Convertir trades a DataFrame
        trades_df = pd.DataFrame(self.results['trades_list'])
        trades_df.to_csv(filename, index=False)
        
        print(f"💾 Resultados guardados en: {filename}")

def main():
    """Función principal para ejecutar el bot"""
    
    print("🤖 BOT DE TRADING - ANÁLISIS TÉCNICO")
    print("="*50)
    
    # Configuración
    CSV_FILE = "binance_BNBUSDT_1s_20251018_234757.csv"  # Archivo generado anteriormente
    INITIAL_CAPITAL = 1000  # USDT
    
    # Crear bot
    bot = TradingBot(initial_capital=INITIAL_CAPITAL)
    
    # Cargar datos
    if not bot.load_data(CSV_FILE):
        print("❌ No se pudo cargar el archivo de datos")
        return
    
    # Ejecutar backtesting
    results = bot.run_backtest()
    
    if results:
        # Guardar resultados
        bot.save_results()
        
        print(f"\n🎉 ¡Backtesting completado!")
        print(f"📁 Revisa los archivos generados para más detalles")
    else:
        print("❌ Error en el backtesting")

if __name__ == "__main__":
    main()