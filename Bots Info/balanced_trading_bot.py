"""
Estrategia de Trading Balanceada - Equilibrio entre Oportunidades y Calidad
Detecta más entradas que la conservadora pero evita el overtrading
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
from trading_bot import TechnicalIndicators, BacktestEngine

class BalancedTradingStrategy:
    """Estrategia balanceada que detecta más oportunidades sin ser demasiado agresiva"""
    
    def __init__(self, 
                 rsi_oversold=30, rsi_overbought=70,
                 rsi_strong_oversold=25, rsi_strong_overbought=75):
        
        # Parámetros RSI
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.rsi_strong_oversold = rsi_strong_oversold
        self.rsi_strong_overbought = rsi_strong_overbought
        
        # Estado de posición
        self.position = None
        self.entry_price = 0
        self.entry_time = None
        self.last_trade_time = None
        
        # Control de frecuencia de trading
        self.min_time_between_trades = 30  # segundos mínimos entre trades
        
    def generate_signals(self, df):
        """Genera señales balanceadas"""
        signals = pd.DataFrame(index=df.index)
        signals['price'] = df['close']
        signals['high'] = df['high']
        signals['low'] = df['low']
        signals['signal'] = 0
        signals['position'] = 0
        signals['signal_strength'] = 0.0
        signals['signal_type'] = ''
        
        # Calcular indicadores principales
        signals['rsi'] = TechnicalIndicators.rsi(df['close'], period=14)
        signals['rsi_fast'] = TechnicalIndicators.rsi(df['close'], period=7)
        
        # Múltiples medias móviles
        signals['ma9'] = TechnicalIndicators.moving_average(df['close'], 9)
        signals['ma21'] = TechnicalIndicators.moving_average(df['close'], 21)
        signals['ma50'] = TechnicalIndicators.moving_average(df['close'], 50)
        
        # MACD
        macd_line, signal_line, histogram = TechnicalIndicators.macd(df['close'])
        signals['macd'] = macd_line
        signals['macd_signal'] = signal_line
        signals['macd_histogram'] = histogram
        
        # Bandas de Bollinger
        bb_upper, bb_middle, bb_lower = TechnicalIndicators.bollinger_bands(df['close'], period=20)
        signals['bb_upper'] = bb_upper
        signals['bb_middle'] = bb_middle
        signals['bb_lower'] = bb_lower
        
        # Calcular volatilidad
        signals['volatility'] = df['close'].rolling(window=20).std()
        signals['price_position'] = (df['close'] - bb_lower) / (bb_upper - bb_lower)
        
        # Generar señales con control de calidad
        for i in range(50, len(signals)):  # Empezar después de calcular todos los indicadores
            
            # Verificar tiempo mínimo entre trades
            if self._time_filter_check(signals, i):
                
                # Calcular señales de entrada y salida
                buy_score = self._calculate_buy_score(signals, i)
                sell_score = self._calculate_sell_score(signals, i)
                
                current_position = signals['position'].iloc[i-1]
                
                if current_position == 0:  # Sin posición
                    # Condiciones más selectivas para entrada
                    if buy_score >= 2.5:  # Umbral más alto
                        signals.loc[signals.index[i], 'signal'] = 1
                        signals.loc[signals.index[i], 'position'] = 1
                        signals.loc[signals.index[i], 'signal_strength'] = buy_score
                        signals.loc[signals.index[i], 'signal_type'] = self._get_buy_reason(signals, i)
                        self.last_trade_time = i
                    else:
                        signals.loc[signals.index[i], 'position'] = 0
                        
                else:  # Con posición
                    # Verificar stop loss y take profit
                    stop_loss = self._check_stop_loss(signals, i, stop_loss_pct=0.02)  # 2%
                    take_profit = self._check_take_profit(signals, i, take_profit_pct=0.015)  # 1.5%
                    
                    # Salir por señales técnicas o gestión de riesgo
                    if sell_score >= 2.0 or stop_loss or take_profit:
                        signals.loc[signals.index[i], 'signal'] = -1
                        signals.loc[signals.index[i], 'position'] = 0
                        signals.loc[signals.index[i], 'signal_strength'] = sell_score
                        
                        exit_reason = []
                        if stop_loss: exit_reason.append("STOP_LOSS")
                        if take_profit: exit_reason.append("TAKE_PROFIT")
                        if sell_score >= 2.0: exit_reason.append("TECHNICAL")
                        
                        signals.loc[signals.index[i], 'signal_type'] = f"SELL: {', '.join(exit_reason)}"
                        self.last_trade_time = i
                    else:
                        signals.loc[signals.index[i], 'position'] = 1
            else:
                # Mantener posición anterior si no pasa el filtro de tiempo
                signals.loc[signals.index[i], 'position'] = signals['position'].iloc[i-1]
        
        return signals
    
    def _time_filter_check(self, signals, i):
        """Verifica si ha pasado suficiente tiempo desde el último trade"""
        if self.last_trade_time is None:
            return True
        return (i - self.last_trade_time) >= self.min_time_between_trades
    
    def _calculate_buy_score(self, signals, i):
        """Calcula puntuación de compra (0-5)"""
        score = 0
        
        # RSI Conditions
        rsi = signals['rsi'].iloc[i]
        rsi_prev = signals['rsi'].iloc[i-1]
        rsi_fast = signals['rsi_fast'].iloc[i]
        
        if rsi < self.rsi_strong_oversold:
            score += 1.5  # Muy sobrevvendido
        elif rsi < self.rsi_oversold and rsi_prev >= self.rsi_oversold:
            score += 1.0  # Saliendo de sobreventa
        elif rsi < self.rsi_oversold:
            score += 0.5  # En sobreventa
        
        if rsi_fast < 25:
            score += 0.5  # RSI rápido bajo
        
        # Moving Average Conditions
        ma9 = signals['ma9'].iloc[i]
        ma21 = signals['ma21'].iloc[i]
        ma50 = signals['ma50'].iloc[i]
        ma9_prev = signals['ma9'].iloc[i-1]
        ma21_prev = signals['ma21'].iloc[i-1]
        
        if ma9 > ma21 and ma9_prev <= ma21_prev:
            score += 1.0  # Golden cross
        elif ma9 > ma21 > ma50:
            score += 0.8  # Tendencia alcista fuerte
        elif ma9 > ma21:
            score += 0.3  # Tendencia alcista básica
        
        # MACD Conditions
        macd = signals['macd'].iloc[i]
        macd_signal = signals['macd_signal'].iloc[i]
        macd_prev = signals['macd'].iloc[i-1]
        macd_signal_prev = signals['macd_signal'].iloc[i-1]
        
        if macd > macd_signal and macd_prev <= macd_signal_prev:
            score += 0.8  # MACD cross up
        elif macd > macd_signal:
            score += 0.3  # MACD above signal
        
        # Bollinger Bands
        price = signals['price'].iloc[i]
        bb_lower = signals['bb_lower'].iloc[i]
        bb_middle = signals['bb_middle'].iloc[i]
        price_position = signals['price_position'].iloc[i]
        
        if price <= bb_lower:
            score += 0.8  # Precio en banda inferior
        elif price_position < 0.3:
            score += 0.4  # Precio en tercio inferior
        
        # Momentum y volatilidad
        if i >= 5:
            recent_low = signals['price'].iloc[i-5:i].min()
            if price > recent_low * 1.001:  # Rebote del mínimo reciente
                score += 0.3
        
        # Penalizar si ya hay mucha volatilidad
        volatility = signals['volatility'].iloc[i]
        avg_volatility = signals['volatility'].iloc[max(0, i-20):i].mean()
        if volatility > avg_volatility * 1.5:
            score -= 0.5  # Reducir score en alta volatilidad
        
        return score
    
    def _calculate_sell_score(self, signals, i):
        """Calcula puntuación de venta (0-5)"""
        score = 0
        
        # RSI Conditions
        rsi = signals['rsi'].iloc[i]
        rsi_prev = signals['rsi'].iloc[i-1]
        rsi_fast = signals['rsi_fast'].iloc[i]
        
        if rsi > self.rsi_strong_overbought:
            score += 1.5  # Muy sobrecomprado
        elif rsi > self.rsi_overbought and rsi_prev <= self.rsi_overbought:
            score += 1.0  # Entrando en sobrecompra
        elif rsi > self.rsi_overbought:
            score += 0.5  # En sobrecompra
        
        if rsi_fast > 75:
            score += 0.5  # RSI rápido alto
        
        # Moving Average Conditions
        ma9 = signals['ma9'].iloc[i]
        ma21 = signals['ma21'].iloc[i]
        ma50 = signals['ma50'].iloc[i]
        ma9_prev = signals['ma9'].iloc[i-1]
        ma21_prev = signals['ma21'].iloc[i-1]
        
        if ma9 < ma21 and ma9_prev >= ma21_prev:
            score += 1.0  # Death cross
        elif ma9 < ma21 < ma50:
            score += 0.8  # Tendencia bajista fuerte
        elif ma9 < ma21:
            score += 0.3  # Tendencia bajista básica
        
        # MACD Conditions
        macd = signals['macd'].iloc[i]
        macd_signal = signals['macd_signal'].iloc[i]
        macd_prev = signals['macd'].iloc[i-1]
        macd_signal_prev = signals['macd_signal'].iloc[i-1]
        
        if macd < macd_signal and macd_prev >= macd_signal_prev:
            score += 0.8  # MACD cross down
        elif macd < macd_signal:
            score += 0.3  # MACD below signal
        
        # Bollinger Bands
        price = signals['price'].iloc[i]
        bb_upper = signals['bb_upper'].iloc[i]
        bb_middle = signals['bb_middle'].iloc[i]
        price_position = signals['price_position'].iloc[i]
        
        if price >= bb_upper:
            score += 0.8  # Precio en banda superior
        elif price_position > 0.7:
            score += 0.4  # Precio en tercio superior
        
        # Momentum bajista
        if i >= 5:
            recent_high = signals['price'].iloc[i-5:i].max()
            if price < recent_high * 0.999:  # Caída del máximo reciente
                score += 0.3
        
        return score
    
    def _get_buy_reason(self, signals, i):
        """Identifica la razón principal de compra"""
        reasons = []
        
        rsi = signals['rsi'].iloc[i]
        ma9 = signals['ma9'].iloc[i]
        ma21 = signals['ma21'].iloc[i]
        ma9_prev = signals['ma9'].iloc[i-1]
        ma21_prev = signals['ma21'].iloc[i-1]
        price = signals['price'].iloc[i]
        bb_lower = signals['bb_lower'].iloc[i]
        
        if rsi < self.rsi_strong_oversold:
            reasons.append("RSI_EXTREME")
        elif rsi < self.rsi_oversold:
            reasons.append("RSI_OVERSOLD")
        
        if ma9 > ma21 and ma9_prev <= ma21_prev:
            reasons.append("GOLDEN_CROSS")
        elif ma9 > ma21:
            reasons.append("MA_BULLISH")
        
        if price <= bb_lower:
            reasons.append("BB_SUPPORT")
        
        return f"BUY: {', '.join(reasons)}" if reasons else "BUY: MULTIPLE"
    
    def _check_stop_loss(self, signals, index, stop_loss_pct=0.02):
        """Verifica stop loss"""
        if signals['position'].iloc[index-1] == 1:
            for j in range(index-1, -1, -1):
                if signals['signal'].iloc[j] == 1:
                    entry_price = signals['price'].iloc[j]
                    current_price = signals['price'].iloc[index]
                    loss_pct = (entry_price - current_price) / entry_price
                    return loss_pct >= stop_loss_pct
        return False
    
    def _check_take_profit(self, signals, index, take_profit_pct=0.015):
        """Verifica take profit"""
        if signals['position'].iloc[index-1] == 1:
            for j in range(index-1, -1, -1):
                if signals['signal'].iloc[j] == 1:
                    entry_price = signals['price'].iloc[j]
                    current_price = signals['price'].iloc[index]
                    profit_pct = (current_price - entry_price) / entry_price
                    return profit_pct >= take_profit_pct
        return False

class BalancedTradingBot:
    """Bot de Trading Balanceado"""
    
    def __init__(self, initial_capital=1000):
        self.strategy = BalancedTradingStrategy()
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
        
        print("🔄 Calculando indicadores técnicos balanceados...")
        self.signals = self.strategy.generate_signals(self.data)
        
        print("🔄 Ejecutando backtesting con estrategia balanceada...")
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
        print("📊 RESULTADOS DEL BACKTESTING BALANCEADO")
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
        
        # Mostrar últimas operaciones
        if r['trades_list']:
            print(f"\n📋 ÚLTIMAS 5 OPERACIONES:")
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
            filename = f"balanced_backtest_results_{timestamp}.csv"
        
        trades_df = pd.DataFrame(self.results['trades_list'])
        trades_df.to_csv(filename, index=False)
        
        print(f"💾 Resultados guardados en: {filename}")

def main():
    """Función principal"""
    
    print("⚖️ BOT DE TRADING BALANCEADO - ESTRATEGIA EQUILIBRADA")
    print("="*60)
    
    CSV_FILE = "binance_BNBUSDT_1s_20251018_234757.csv"
    INITIAL_CAPITAL = 1000
    
    bot = BalancedTradingBot(initial_capital=INITIAL_CAPITAL)
    
    if not bot.load_data(CSV_FILE):
        print("❌ No se pudo cargar el archivo de datos")
        return
    
    results = bot.run_backtest()
    
    if results:
        bot.save_results()
        print(f"\n🎉 ¡Backtesting balanceado completado!")
        print(f"📊 Comparación:")
        print(f"   • Estrategia original: 1 operación")
        print(f"   • Estrategia agresiva: 2,420 operaciones (-99%)")
        print(f"   • Estrategia balanceada: {results['total_trades']} operaciones ({results['total_return_pct']:+.2f}%)")
    else:
        print("❌ Error en el backtesting")

if __name__ == "__main__":
    main()