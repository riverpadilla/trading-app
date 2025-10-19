#!/usr/bin/env python3
"""
Bot MA Convergence - Versión Console para ejecución independiente
Ejecuta sin GUI y puede seguir funcionando aunque se cierre VS Code
"""

import time
import signal
import sys
import os
from datetime import datetime
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from ma_convergence_bot import MAConvergenceBot
import pandas as pd
import talib

class MAConvergenceConsoleBot:
    def __init__(self):
        """Bot de consola independiente"""
        # API keys (testnet)
        self.api_key = '7ZPT9vq9NRD8rDcV87ykvrPWBPQzPuZ9QkLKLLxGguQaDvT5mACl4nQSP8uwGxBH'
        self.api_secret = 'SpCz5aKF9c16gpJec6EQ3r0BC4GAqjmTO1Bevh2193mvVEEdClpIhP2jx7Wf1QFO'
        
        # Cliente Binance
        self.client = Client(self.api_key, self.api_secret, testnet=True)
        
        # Configuración
        self.symbol = "BNBUSDT"
        self.is_running = False
        self.position = None
        self.entry_price = 0.0
        
        # Bot MA con config optimizada
        self.ma_bot = MAConvergenceBot(verbose=False)  # Sin verbose para consola
        
        # Configurar signal handlers para cierre limpio
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Manejo limpio de cierre"""
        print(f"\n🛑 Señal {signum} recibida. Cerrando bot...")
        self.is_running = False
        
    def log(self, message):
        """Log con timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def get_balances(self):
        """Obtener balances de la cuenta"""
        try:
            account = self.client.get_account()
            balances = {}
            for balance in account['balances']:
                if float(balance['free']) > 0:
                    balances[balance['asset']] = float(balance['free'])
            return balances
        except Exception as e:
            self.log(f"❌ Error obteniendo balances: {e}")
            return {}
    
    def analyze_market(self):
        """Analizar mercado y retornar señal"""
        try:
            # Obtener datos históricos
            klines = self.client.get_klines(
                symbol=self.symbol,
                interval=Client.KLINE_INTERVAL_1MINUTE,
                limit=100
            )
            
            # Preparar DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            df['Close'] = df['close'].astype(float)
            df['Open'] = df['open'].astype(float)
            df['High'] = df['high'].astype(float)
            df['Low'] = df['low'].astype(float)
            df['Volume'] = df['volume'].astype(float)
            df['Date'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.index = df['Date']
            
            # Asignar al bot
            self.ma_bot.data = df
            
            # Calcular indicadores
            self.ma_bot._calculate_indicators()
            
            # Análisis simplificado
            ma7_values = self.ma_bot.data[f'MA{self.ma_bot.ma1_value}'].dropna()
            ma25_values = self.ma_bot.data[f'MA{self.ma_bot.ma2_value}'].dropna()
            
            if len(ma7_values) >= 5 and len(ma25_values) >= 5:
                # Calcular pendientes
                ma7_slope = (ma7_values.iloc[-1] - ma7_values.iloc[-3]) / ma7_values.iloc[-3]
                ma25_slope = (ma25_values.iloc[-1] - ma25_values.iloc[-3]) / ma25_values.iloc[-3]
                
                current_price = float(df['close'].iloc[-1])
                
                # Señal de compra
                if (ma7_slope > self.ma_bot.umbral_ma1 and 
                    ma25_slope > self.ma_bot.umbral_ma2 and 
                    self.position is None):
                    return 'BUY', current_price, ma7_slope, ma25_slope
                
                # Señal de venta
                elif self.position == 'LONG':
                    profit_pct = (current_price - self.entry_price) / self.entry_price
                    if profit_pct > 0.002:  # Take profit
                        return 'SELL', current_price, profit_pct, 'PROFIT'
                    elif profit_pct < -0.001:  # Stop loss
                        return 'SELL', current_price, profit_pct, 'LOSS'
                
                return 'HOLD', current_price, ma7_slope, ma25_slope
            
        except Exception as e:
            self.log(f"❌ Error en análisis: {e}")
            return 'ERROR', 0, 0, 0
    
    def execute_trade(self, signal, price):
        """Ejecutar operación (simulada en testnet)"""
        if signal == 'BUY':
            self.position = 'LONG'
            self.entry_price = price
            self.log(f"🟢 COMPRA ejecutada a ${price:.4f}")
            
        elif signal == 'SELL':
            if self.position == 'LONG':
                profit_pct = (price - self.entry_price) / self.entry_price * 100
                self.position = None
                self.entry_price = 0.0
                self.log(f"🔴 VENTA ejecutada a ${price:.4f} | P&L: {profit_pct:+.2f}%")
    
    def run(self):
        """Ejecutar bot principal"""
        print("🤖 MA CONVERGENCE CONSOLE BOT")
        print("=" * 50)
        print("🔧 Configuración optimizada cargada")
        print(f"📊 Par: {self.symbol}")
        print(f"🎯 Umbrales: MA1={self.ma_bot.umbral_ma1}, MA2={self.ma_bot.umbral_ma2}")
        print("=" * 50)
        
        # Mostrar balances iniciales
        balances = self.get_balances()
        if balances:
            self.log("💰 Balances iniciales:")
            for asset, amount in balances.items():
                if asset in ['USDT', 'BNB'] or amount > 1:
                    self.log(f"   {asset}: {amount:.6f}")
        
        self.is_running = True
        iteration = 0
        
        try:
            while self.is_running:
                iteration += 1
                
                # Analizar mercado
                signal, price, param1, param2 = self.analyze_market()
                
                if signal == 'BUY':
                    self.execute_trade('BUY', price)
                    self.log(f"📈 Señal COMPRA: MA7={param1:.4f}, MA25={param2:.4f}")
                    
                elif signal == 'SELL':
                    self.execute_trade('SELL', price)
                    reason = param2 if isinstance(param2, str) else 'SIGNAL'
                    
                elif signal == 'HOLD':
                    # Log cada minuto
                    if iteration % 12 == 1:
                        pos_text = self.position if self.position else "None"
                        self.log(f"[{iteration:4d}] Precio: ${price:.4f} | Posición: {pos_text}")
                
                # Actualizar balances cada 5 minutos
                if iteration % 60 == 1:
                    balances = self.get_balances()
                    if 'USDT' in balances:
                        self.log(f"💰 Balance USDT: ${balances['USDT']:.2f}")
                
                time.sleep(5)  # 5 segundos entre checks
                
        except KeyboardInterrupt:
            self.log("🛑 Bot detenido por usuario")
        except Exception as e:
            self.log(f"❌ Error crítico: {e}")
        finally:
            self.is_running = False
            self.log("🔚 Bot finalizado")

def main():
    """Función principal"""
    print("Iniciando MA Convergence Console Bot...")
    print("Presiona Ctrl+C para detener")
    
    bot = MAConvergenceConsoleBot()
    bot.run()

if __name__ == "__main__":
    main()