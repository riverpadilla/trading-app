"""
Estrategia Híbrida Rápida - Lo mejor de todas las estrategias combinadas
Versión optimizada para velocidad y efectividad
"""

import pandas as pd
import numpy as np
from datetime import datetime
from trading_bot import TechnicalIndicators, BacktestEngine

class HybridFastStrategy:
    """Estrategia híbrida rápida con lo mejor de cada enfoque"""
    
    def __init__(self):
        # Parámetros optimizados basados en análisis previo
        self.rsi_oversold = 25          # Más selectivo
        self.rsi_overbought = 75        # Más selectivo
        self.min_time_between_trades = 45  # Segundos
        self.last_trade_time = None
        
        # Thresholds simplificados
        self.buy_threshold = 2.0        # Score mínimo para comprar
        self.sell_threshold = 1.8       # Score mínimo para vender
        
    def generate_signals(self, df):
        """Genera señales rápidas y efectivas"""
        signals = pd.DataFrame(index=df.index)
        signals['price'] = df['close']
        signals['signal'] = 0
        signals['position'] = 0
        signals['signal_type'] = ''
        
        print("   Calculando RSI...")
        signals['rsi'] = TechnicalIndicators.rsi(df['close'], period=14)
        signals['rsi_fast'] = TechnicalIndicators.rsi(df['close'], period=7)
        
        print("   Calculando Medias Móviles...")
        signals['ma9'] = TechnicalIndicators.moving_average(df['close'], 9)
        signals['ma21'] = TechnicalIndicators.moving_average(df['close'], 21)
        
        print("   Calculando MACD...")
        macd_line, signal_line, _ = TechnicalIndicators.macd(df['close'])
        signals['macd'] = macd_line
        signals['macd_signal'] = signal_line
        
        print("   Calculando Bandas de Bollinger...")
        bb_upper, bb_middle, bb_lower = TechnicalIndicators.bollinger_bands(df['close'])
        signals['bb_upper'] = bb_upper
        signals['bb_middle'] = bb_middle
        signals['bb_lower'] = bb_lower
        
        print("   Generando señales...")
        
        # Generar señales con lógica simplificada pero efectiva
        for i in range(50, len(signals)):  # Empezar después de indicadores estables
            
            if self._time_filter(i):
                
                # Calcular scores simplificados
                buy_score = self._fast_buy_score(signals, i)
                sell_score = self._fast_sell_score(signals, i)
                
                current_position = signals['position'].iloc[i-1]
                
                if current_position == 0:  # Sin posición
                    if buy_score >= self.buy_threshold:
                        signals.loc[signals.index[i], 'signal'] = 1
                        signals.loc[signals.index[i], 'position'] = 1
                        signals.loc[signals.index[i], 'signal_type'] = f"BUY(Score:{buy_score:.1f})"
                        self.last_trade_time = i
                    else:
                        signals.loc[signals.index[i], 'position'] = 0
                        
                else:  # Con posición
                    # Verificar condiciones de salida
                    stop_loss = self._quick_stop_loss(signals, i)
                    take_profit = self._quick_take_profit(signals, i)
                    # Nueva condición: salir si la variación absoluta del precio >= 1.2 USDT
                    price_move = self._exit_by_abs_price(signals, i, abs_usdt=1.2)
                    
                    # Si cualquiera de las condiciones se cumple, salir
                    if sell_score >= self.sell_threshold or stop_loss or take_profit or price_move:
                        signals.loc[signals.index[i], 'signal'] = -1
                        signals.loc[signals.index[i], 'position'] = 0

                        # Construir lista de razones para mayor trazabilidad
                        reasons = []
                        if sell_score >= self.sell_threshold:
                            reasons.append("TECHNICAL")
                        if stop_loss:
                            reasons.append("STOP_LOSS")
                        if take_profit:
                            reasons.append("TAKE_PROFIT")
                        if price_move:
                            reasons.append("PRICE_MOVE>=1.2")

                        reason_str = "+".join(reasons) if reasons else "TECHNICAL"
                        signals.loc[signals.index[i], 'signal_type'] = f"SELL({reason_str})"
                        self.last_trade_time = i
                    else:
                        signals.loc[signals.index[i], 'position'] = 1
            else:
                # Mantener posición anterior
                signals.loc[signals.index[i], 'position'] = signals['position'].iloc[i-1]
        
        return signals
    
    def _time_filter(self, i):
        """Filtro de tiempo simple"""
        if self.last_trade_time is None:
            return True
        return (i - self.last_trade_time) >= self.min_time_between_trades
    
    def _fast_buy_score(self, signals, i):
        """Scoring rápido para compra (0-4)"""
        score = 0
        
        # RSI (peso alto)
        rsi = signals['rsi'].iloc[i]
        if rsi < 20:
            score += 2.0    # Muy fuerte
        elif rsi < self.rsi_oversold:
            score += 1.5    # Fuerte
        elif rsi < 35:
            score += 0.5    # Débil
        
        # Bandas de Bollinger
        price = signals['price'].iloc[i]
        bb_lower = signals['bb_lower'].iloc[i]
        bb_middle = signals['bb_middle'].iloc[i]
        
        if price <= bb_lower:
            score += 1.0    # En soporte
        elif price < bb_middle:
            score += 0.3    # Debajo de media
        
        # Medias Móviles
        ma9 = signals['ma9'].iloc[i]
        ma21 = signals['ma21'].iloc[i]
        
        if ma9 > ma21:
            score += 0.5    # Tendencia alcista
        
        # MACD
        macd = signals['macd'].iloc[i]
        macd_signal = signals['macd_signal'].iloc[i]
        
        if macd > macd_signal:
            score += 0.5    # MACD alcista
        
        # RSI rápido como confirmación
        rsi_fast = signals['rsi_fast'].iloc[i]
        if rsi_fast < 30:
            score += 0.3
        
        return score
    
    def _fast_sell_score(self, signals, i):
        """Scoring rápido para venta"""
        score = 0
        
        # RSI
        rsi = signals['rsi'].iloc[i]
        if rsi > 80:
            score += 2.0
        elif rsi > self.rsi_overbought:
            score += 1.5
        elif rsi > 65:
            score += 0.5
        
        # Bandas de Bollinger
        price = signals['price'].iloc[i]
        bb_upper = signals['bb_upper'].iloc[i]
        bb_middle = signals['bb_middle'].iloc[i]
        
        if price >= bb_upper:
            score += 1.0
        elif price > bb_middle:
            score += 0.3
        
        # Medias Móviles
        ma9 = signals['ma9'].iloc[i]
        ma21 = signals['ma21'].iloc[i]
        
        if ma9 < ma21:
            score += 0.5
        
        # MACD
        macd = signals['macd'].iloc[i]
        macd_signal = signals['macd_signal'].iloc[i]
        
        if macd < macd_signal:
            score += 0.5
        
        return score
    
    def _quick_stop_loss(self, signals, index, stop_pct=0.018):
        """Stop loss rápido (1.8%)"""
        if signals['position'].iloc[index-1] == 1:
            for j in range(index-1, max(0, index-100), -1):  # Buscar max 100 períodos atrás
                if signals['signal'].iloc[j] == 1:
                    entry_price = signals['price'].iloc[j]
                    current_price = signals['price'].iloc[index]
                    loss_pct = (entry_price - current_price) / entry_price
                    return loss_pct >= stop_pct
        return False
    
    def _quick_take_profit(self, signals, index, profit_pct=0.012):
        """Take profit rápido (1.2%)"""
        if signals['position'].iloc[index-1] == 1:
            for j in range(index-1, max(0, index-100), -1):
                if signals['signal'].iloc[j] == 1:
                    entry_price = signals['price'].iloc[j]
                    current_price = signals['price'].iloc[index]
                    profit = (current_price - entry_price) / entry_price
                    return profit >= profit_pct
        return False

    def _exit_by_abs_price(self, signals, index, abs_usdt=1.2):
        """Exit when absolute price variation from entry >= abs_usdt (USDT)."""
        # Solo aplicar si había posición previa
        if signals['position'].iloc[index-1] == 1:
            for j in range(index-1, max(0, index-200), -1):  # buscar hasta 200 pasos atrás
                if signals['signal'].iloc[j] == 1:
                    entry_price = signals['price'].iloc[j]
                    current_price = signals['price'].iloc[index]
                    price_diff = abs(current_price - entry_price)
                    # Variación absoluta en USDT (valor absoluto)
                    if price_diff >= abs_usdt:
                        # Debug: imprimir cuando se active esta condición
                        timestamp = signals.index[index]
                        print(f"🔴 SALIDA POR PRECIO ABSOLUTO: {timestamp} - Entrada: ${entry_price:.2f} -> Actual: ${current_price:.2f} (Δ: ${price_diff:.2f})")
                        return True
                    return False
        return False

class HybridTradingBot:
    """Bot híbrido rápido"""
    
    def __init__(self, initial_capital=1000):
        self.strategy = HybridFastStrategy()
        self.backtest_engine = BacktestEngine(initial_capital)
        self.data = None
        self.signals = None
        self.results = None
    
    def load_data(self, csv_file):
        try:
            print(f"📁 Cargando {csv_file}...")
            self.data = pd.read_csv(csv_file)
            self.data['datetime'] = pd.to_datetime(self.data['datetime'])
            self.data.set_index('datetime', inplace=True)
            print(f"✅ Datos cargados: {len(self.data):,} registros")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def run_backtest(self, initial_capital=None):
        if self.data is None:
            return None
        
        if initial_capital:
            self.backtest_engine.initial_usdt = initial_capital
        
        print("🚀 Ejecutando estrategia híbrida rápida...")
        self.signals = self.strategy.generate_signals(self.data)
        
        print("💹 Ejecutando backtesting...")
        self.results = self.backtest_engine.run_backtest(self.signals)
        
        if self.results:
            self.print_results()
            return self.results
        return None
    
    def print_results(self):
        if not self.results:
            return
        
        r = self.results
        print("\n" + "🎯"*20)
        print("🚀 ESTRATEGIA HÍBRIDA RÁPIDA - RESULTADOS")
        print("🎯"*20)
        print(f"💰 Capital: ${r['initial_capital']:,.2f} → ${r['final_capital']:,.2f}")
        print(f"📈 Retorno: {r['total_return_pct']:+.2f}%")
        print(f"🔄 Operaciones: {r['total_trades']}")
        print(f"✅ Exitosas: {r['winning_trades']} ({r['win_rate_pct']:.1f}%)")
        print(f"❌ Fallidas: {r['losing_trades']}")
        print(f"📊 Ganancia promedio: {r['avg_win_pct']:+.2f}%")
        print(f"📉 Pérdida promedio: {r['avg_loss_pct']:+.2f}%")
        print(f"💸 Comisiones: ${r['total_commission']:,.2f}")
        
        # Comparación con otras estrategias
        print(f"\n📊 COMPARACIÓN COMPLETA:")
        print(f"   🐌 Original: 1 trade (-0.37%)")
        print(f"   🔥 Agresiva: 2,420 trades (-99%)")
        print(f"   ⚖️  Balanceada: 169 trades (-28.43%)")
        print(f"   🎯 Híbrida: {r['total_trades']} trades ({r['total_return_pct']:+.2f}%)")
        
        if r['trades_list']:
            print(f"\n📋 ÚLTIMAS OPERACIONES:")
            for trade in r['trades_list'][-3:]:
                if trade['type'] == 'SELL':
                    pnl_str = f"{trade['pnl_pct']:+.2f}%"
                    emoji = "✅" if trade['pnl_pct'] > 0 else "❌"
                    print(f"   {emoji} {trade['timestamp']}: SELL ${trade['price']:.2f} | {pnl_str}")
                else:
                    print(f"   🔵 {trade['timestamp']}: BUY ${trade['price']:.2f}")
    
    def save_results(self, filename=None):
        if not self.results or not self.results['trades_list']:
            return
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hybrid_results_{timestamp}.csv"
        
        trades_df = pd.DataFrame(self.results['trades_list'])
        trades_df.to_csv(filename, index=False)
        print(f"💾 Guardado: {filename}")

def main():
    print("🚀 ESTRATEGIA HÍBRIDA RÁPIDA")
    print("🎯 Combina lo mejor de todas las estrategias")
    print("="*50)
    
    bot = HybridTradingBot(1000)
    
    if bot.load_data("binance_BNBUSDT_1s_20251018_234757.csv"):
        start_time = datetime.now()
        results = bot.run_backtest()
        end_time = datetime.now()
        
        if results:
            bot.save_results()
            duration = (end_time - start_time).total_seconds()
            print(f"\n⏱️  Tiempo de ejecución: {duration:.1f} segundos")
            print(f"🎉 ¡Estrategia híbrida completada!")

if __name__ == "__main__":
    main()