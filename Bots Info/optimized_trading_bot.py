"""
Estrategia de Trading Optimizada - Selectiva y Rentable
Basada en análisis de los resultados anteriores para maximizar rentabilidad
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
from trading_bot import TechnicalIndicators, BacktestEngine

class OptimizedTradingStrategy:
    """Estrategia optimizada basada en confluencia de señales de alta calidad"""
    
    def __init__(self):
        # Parámetros optimizados basados en análisis
        self.rsi_oversold = 25      # Más extremo para mayor calidad
        self.rsi_overbought = 75    # Más extremo para mayor calidad
        self.rsi_strong_oversold = 20
        self.rsi_strong_overbought = 80
        
        # Control estricto de trading
        self.min_time_between_trades = 60  # 1 minuto mínimo entre trades
        self.last_trade_time = None
        
        # Thresholds de calidad
        self.min_buy_score = 3.0    # Score mínimo para comprar
        self.min_sell_score = 2.5   # Score mínimo para vender
        
    def generate_signals(self, df):
        """Genera señales optimizadas con alta selectividad"""
        signals = pd.DataFrame(index=df.index)
        signals['price'] = df['close']
        signals['high'] = df['high']
        signals['low'] = df['low']
        signals['signal'] = 0
        signals['position'] = 0
        signals['buy_score'] = 0.0
        signals['sell_score'] = 0.0
        signals['signal_type'] = ''
        
        # Calcular indicadores con períodos optimizados
        signals['rsi'] = TechnicalIndicators.rsi(df['close'], period=14)
        signals['rsi_short'] = TechnicalIndicators.rsi(df['close'], period=7)
        signals['rsi_long'] = TechnicalIndicators.rsi(df['close'], period=21)
        
        # Múltiples timeframes de MA
        signals['ma5'] = TechnicalIndicators.moving_average(df['close'], 5)
        signals['ma10'] = TechnicalIndicators.moving_average(df['close'], 10)
        signals['ma20'] = TechnicalIndicators.moving_average(df['close'], 20)
        signals['ma50'] = TechnicalIndicators.moving_average(df['close'], 50)
        
        # MACD optimizado
        macd_line, signal_line, histogram = TechnicalIndicators.macd(df['close'], fast=8, slow=21, signal=5)
        signals['macd'] = macd_line
        signals['macd_signal'] = signal_line
        signals['macd_histogram'] = histogram
        
        # Bandas de Bollinger más estrechas
        bb_upper, bb_middle, bb_lower = TechnicalIndicators.bollinger_bands(df['close'], period=20, std_dev=1.5)
        signals['bb_upper'] = bb_upper
        signals['bb_middle'] = bb_middle
        signals['bb_lower'] = bb_lower
        signals['bb_width'] = (bb_upper - bb_lower) / bb_middle
        
        # Indicadores de momentum
        signals['price_change_5'] = df['close'].pct_change(5) * 100
        signals['price_change_10'] = df['close'].pct_change(10) * 100
        signals['volatility'] = df['close'].rolling(window=20).std()
        
        # Volume analysis (si está disponible)
        if 'volume' in df.columns:
            signals['volume_ma'] = df['volume'].rolling(window=20).mean()
            signals['volume_ratio'] = df['volume'] / signals['volume_ma']
        
        # Generar señales con lógica optimizada
        for i in range(100, len(signals)):  # Comenzar después de tener suficientes datos
            
            if self._time_and_market_filter(signals, i):
                
                # Calcular scores de calidad
                buy_score = self._calculate_optimized_buy_score(signals, i)
                sell_score = self._calculate_optimized_sell_score(signals, i)
                
                signals.loc[signals.index[i], 'buy_score'] = buy_score
                signals.loc[signals.index[i], 'sell_score'] = sell_score
                
                current_position = signals['position'].iloc[i-1]
                
                if current_position == 0:  # Sin posición
                    # Entrada solo con score muy alto Y confluencia de señales
                    if buy_score >= self.min_buy_score and self._confirm_buy_confluence(signals, i):
                        signals.loc[signals.index[i], 'signal'] = 1
                        signals.loc[signals.index[i], 'position'] = 1
                        signals.loc[signals.index[i], 'signal_type'] = self._get_detailed_buy_reason(signals, i)
                        self.last_trade_time = i
                    else:
                        signals.loc[signals.index[i], 'position'] = 0
                        
                else:  # Con posición
                    # Verificar condiciones de salida
                    stop_loss = self._check_dynamic_stop_loss(signals, i)
                    take_profit = self._check_dynamic_take_profit(signals, i)
                    technical_exit = sell_score >= self.min_sell_score
                    
                    if stop_loss or take_profit or technical_exit:
                        signals.loc[signals.index[i], 'signal'] = -1
                        signals.loc[signals.index[i], 'position'] = 0
                        
                        exit_reasons = []
                        if stop_loss: exit_reasons.append("STOP_LOSS")
                        if take_profit: exit_reasons.append("TAKE_PROFIT")
                        if technical_exit: exit_reasons.append("TECHNICAL")
                        
                        signals.loc[signals.index[i], 'signal_type'] = f"SELL: {', '.join(exit_reasons)}"
                        self.last_trade_time = i
                    else:
                        signals.loc[signals.index[i], 'position'] = 1
            else:
                # Mantener posición anterior
                signals.loc[signals.index[i], 'position'] = signals['position'].iloc[i-1]
        
        return signals
    
    def _time_and_market_filter(self, signals, i):
        """Filtro combinado de tiempo y condiciones de mercado"""
        # Filtro de tiempo
        if self.last_trade_time is not None:
            if (i - self.last_trade_time) < self.min_time_between_trades:
                return False
        
        # Filtro de volatilidad excesiva
        if i >= 20:
            current_vol = signals['volatility'].iloc[i]
            avg_vol = signals['volatility'].iloc[i-20:i].mean()
            if current_vol > avg_vol * 2:  # Evitar volatilidad extrema
                return False
        
        # Filtro de Bollinger Band width (evitar mercados muy planos)
        bb_width = signals['bb_width'].iloc[i]
        if bb_width < 0.01:  # Mercado muy lateral
            return False
        
        return True
    
    def _calculate_optimized_buy_score(self, signals, i):
        """Score optimizado para compras (0-5)"""
        score = 0
        
        # RSI multi-timeframe con pesos optimizados
        rsi = signals['rsi'].iloc[i]
        rsi_short = signals['rsi_short'].iloc[i]
        rsi_long = signals['rsi_long'].iloc[i]
        
        # Score RSI con múltiples confirmaciones
        if rsi < self.rsi_strong_oversold and rsi_short < 25:
            score += 2.0  # Muy fuerte: ambos RSI muy bajos
        elif rsi < self.rsi_oversold:
            if rsi_short < rsi:  # RSI corto más bajo = momentum bajista terminando
                score += 1.5
            else:
                score += 1.0
        
        # Divergencia RSI (precio baja pero RSI sube)
        if i >= 10:
            price_trend = signals['price'].iloc[i] - signals['price'].iloc[i-10]
            rsi_trend = rsi - signals['rsi'].iloc[i-10]
            if price_trend < 0 and rsi_trend > 0:  # Divergencia bullish
                score += 0.8
        
        # Moving Averages con jerarquía clara
        ma5 = signals['ma5'].iloc[i]
        ma10 = signals['ma10'].iloc[i]
        ma20 = signals['ma20'].iloc[i]
        ma50 = signals['ma50'].iloc[i]
        price = signals['price'].iloc[i]
        
        # Estructura de MA alcista
        if ma5 > ma10 > ma20 > ma50:
            score += 1.0  # Alineación perfect alcista
        elif ma5 > ma10 > ma20:
            score += 0.6  # Tendencia alcista corto plazo
        elif ma5 > ma10:
            score += 0.3  # Momentum alcista básico
        
        # Precio cerca del soporte de MA
        if price < ma20 and price > ma20 * 0.999:  # Precio tocando MA20
            score += 0.5
        
        # MACD optimizado
        macd = signals['macd'].iloc[i]
        macd_signal = signals['macd_signal'].iloc[i]
        macd_hist = signals['macd_histogram'].iloc[i]
        macd_hist_prev = signals['macd_histogram'].iloc[i-1]
        
        if macd > macd_signal and macd_hist > macd_hist_prev:
            score += 0.8  # MACD alcista con momentum creciente
        elif macd > macd_signal:
            score += 0.4
        
        # Bollinger Bands táctical
        bb_lower = signals['bb_lower'].iloc[i]
        bb_middle = signals['bb_middle'].iloc[i]
        bb_position = (price - bb_lower) / (bb_middle - bb_lower)
        
        if price <= bb_lower * 1.001:  # Muy cerca del soporte BB
            score += 1.0
        elif bb_position < 0.2:  # En quintil inferior
            score += 0.5
        
        # Momentum reversal
        price_change_5 = signals['price_change_5'].iloc[i]
        price_change_10 = signals['price_change_10'].iloc[i]
        
        if price_change_10 < -0.2 and price_change_5 > -0.1:  # Ralentización de caída
            score += 0.4
        
        # Volume confirmation (si disponible)
        if 'volume_ratio' in signals.columns:
            vol_ratio = signals['volume_ratio'].iloc[i]
            if vol_ratio > 1.2:  # Volumen por encima del promedio
                score += 0.3
        
        return min(score, 5.0)  # Cap en 5.0
    
    def _calculate_optimized_sell_score(self, signals, i):
        """Score optimizado para ventas"""
        score = 0
        
        # RSI con multiple confirmations
        rsi = signals['rsi'].iloc[i]
        rsi_short = signals['rsi_short'].iloc[i]
        
        if rsi > self.rsi_strong_overbought and rsi_short > 75:
            score += 2.0
        elif rsi > self.rsi_overbought:
            if rsi_short > rsi:
                score += 1.5
            else:
                score += 1.0
        
        # MA structure bearish
        ma5 = signals['ma5'].iloc[i]
        ma10 = signals['ma10'].iloc[i]
        ma20 = signals['ma20'].iloc[i]
        price = signals['price'].iloc[i]
        
        if ma5 < ma10 < ma20:
            score += 1.0
        elif ma5 < ma10:
            score += 0.5
        
        # Resistencia en MA
        if price > ma20 and price < ma20 * 1.001:
            score += 0.5
        
        # MACD bearish
        macd = signals['macd'].iloc[i]
        macd_signal = signals['macd_signal'].iloc[i]
        macd_hist = signals['macd_histogram'].iloc[i]
        macd_hist_prev = signals['macd_histogram'].iloc[i-1]
        
        if macd < macd_signal and macd_hist < macd_hist_prev:
            score += 0.8
        
        # BB resistance
        bb_upper = signals['bb_upper'].iloc[i]
        if price >= bb_upper * 0.999:
            score += 1.0
        
        return min(score, 5.0)
    
    def _confirm_buy_confluence(self, signals, i):
        """Confirma confluencia de al menos 3 indicadores para compra"""
        confirmations = 0
        
        # 1. RSI confirmation
        if signals['rsi'].iloc[i] < self.rsi_oversold:
            confirmations += 1
        
        # 2. Price vs BB
        if signals['price'].iloc[i] <= signals['bb_lower'].iloc[i] * 1.002:
            confirmations += 1
        
        # 3. MACD positive
        if signals['macd'].iloc[i] > signals['macd_signal'].iloc[i]:
            confirmations += 1
        
        # 4. MA structure
        if signals['ma5'].iloc[i] > signals['ma10'].iloc[i]:
            confirmations += 1
        
        # 5. Recent momentum change
        if i >= 5:
            recent_change = signals['price_change_5'].iloc[i]
            if recent_change > -0.5:  # No está cayendo fuertemente
                confirmations += 1
        
        return confirmations >= 3
    
    def _get_detailed_buy_reason(self, signals, i):
        """Genera razón detallada de compra"""
        reasons = []
        
        if signals['rsi'].iloc[i] < self.rsi_strong_oversold:
            reasons.append("RSI_EXTREME")
        elif signals['rsi'].iloc[i] < self.rsi_oversold:
            reasons.append("RSI_OVERSOLD")
        
        if signals['price'].iloc[i] <= signals['bb_lower'].iloc[i]:
            reasons.append("BB_SUPPORT")
        
        if signals['macd'].iloc[i] > signals['macd_signal'].iloc[i]:
            reasons.append("MACD_BULLISH")
        
        if signals['ma5'].iloc[i] > signals['ma10'].iloc[i]:
            reasons.append("MA_SHORT_BULLISH")
        
        score = signals['buy_score'].iloc[i]
        return f"BUY({score:.1f}): {', '.join(reasons)}"
    
    def _check_dynamic_stop_loss(self, signals, index):
        """Stop loss dinámico basado en volatilidad"""
        if signals['position'].iloc[index-1] == 1:
            for j in range(index-1, -1, -1):
                if signals['signal'].iloc[j] == 1:
                    entry_price = signals['price'].iloc[j]
                    current_price = signals['price'].iloc[index]
                    
                    # Stop loss adaptativo basado en volatilidad
                    volatility = signals['volatility'].iloc[index]
                    avg_volatility = signals['volatility'].iloc[max(0, index-20):index].mean()
                    
                    base_stop = 0.015  # 1.5% base
                    vol_multiplier = min(volatility / avg_volatility, 2.0)  # Max 2x
                    dynamic_stop = base_stop * vol_multiplier
                    
                    loss_pct = (entry_price - current_price) / entry_price
                    return loss_pct >= dynamic_stop
        return False
    
    def _check_dynamic_take_profit(self, signals, index):
        """Take profit dinámico basado en momentum"""
        if signals['position'].iloc[index-1] == 1:
            for j in range(index-1, -1, -1):
                if signals['signal'].iloc[j] == 1:
                    entry_price = signals['price'].iloc[j]
                    current_price = signals['price'].iloc[index]
                    
                    profit_pct = (current_price - entry_price) / entry_price
                    
                    # Take profit escalonado
                    if profit_pct >= 0.02:  # 2% ganancia
                        return True
                    elif profit_pct >= 0.01:  # 1% ganancia
                        # Solo tomar si momentum se está debilitando
                        rsi = signals['rsi'].iloc[index]
                        if rsi > 60:  # RSI alto sugiere ralentización
                            return True
        return False

# Usar las mismas clases BacktestEngine y Bot estructura
class OptimizedTradingBot:
    """Bot optimizado"""
    
    def __init__(self, initial_capital=1000):
        self.strategy = OptimizedTradingStrategy()
        self.backtest_engine = BacktestEngine(initial_capital)
        self.data = None
        self.signals = None
        self.results = None
    
    def load_data(self, csv_file):
        try:
            self.data = pd.read_csv(csv_file)
            self.data['datetime'] = pd.to_datetime(self.data['datetime'])
            self.data.set_index('datetime', inplace=True)
            print(f"✅ Datos cargados: {len(self.data)} registros")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def run_backtest(self, initial_capital=None):
        if self.data is None:
            return None
        
        if initial_capital:
            self.backtest_engine.initial_usdt = initial_capital
        
        print("🔄 Estrategia optimizada ejecutándose...")
        self.signals = self.strategy.generate_signals(self.data)
        self.results = self.backtest_engine.run_backtest(self.signals)
        
        if self.results:
            self.print_results()
            return self.results
        return None
    
    def print_results(self):
        if not self.results:
            return
        
        r = self.results
        print("\n" + "="*60)
        print("🎯 RESULTADOS ESTRATEGIA OPTIMIZADA")
        print("="*60)
        print(f"💰 Capital: ${r['initial_capital']:,.2f} → ${r['final_capital']:,.2f}")
        print(f"📈 Retorno: {r['total_return_pct']:+.2f}%")
        print(f"🔄 Operaciones: {r['total_trades']}")
        print(f"🎯 Éxito: {r['win_rate_pct']:.1f}%")
        print(f"📊 Promedio: +{r['avg_win_pct']:.2f}% / {r['avg_loss_pct']:.2f}%")
    
    def save_results(self, filename=None):
        if not self.results or not self.results['trades_list']:
            return
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"optimized_results_{timestamp}.csv"
        
        trades_df = pd.DataFrame(self.results['trades_list'])
        trades_df.to_csv(filename, index=False)
        print(f"💾 Guardado: {filename}")

def main():
    print("🎯 ESTRATEGIA OPTIMIZADA - ALTA SELECTIVIDAD")
    print("="*50)
    
    bot = OptimizedTradingBot(1000)
    
    if bot.load_data("binance_BNBUSDT_1s_20251018_234757.csv"):
        results = bot.run_backtest()
        if results:
            bot.save_results()
            print(f"\n🏆 Comparación final:")
            print(f"   • Original: 1 trade (-0.37%)")
            print(f"   • Agresiva: 2,420 trades (-99%)")
            print(f"   • Balanceada: 169 trades (-28%)")
            print(f"   • Optimizada: {results['total_trades']} trades ({results['total_return_pct']:+.2f}%)")

if __name__ == "__main__":
    main()