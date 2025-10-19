#!/usr/bin/env python3
"""
Bot MA Convergence para Trading en Tiempo Real con Binance Testnet
Usa la configuración optimizada y ejecuta trades automáticos
"""

import time
import pandas as pd
from datetime import datetime, timedelta
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from ma_convergence_bot import MAConvergenceBot
import numpy as np
import talib

class MAConvergenceLiveBot:
    def __init__(self, api_key, api_secret, symbol="BNBUSDT", testnet=True):
        """
        Inicializa el bot de trading en vivo
        
        Args:
            api_key: API key de Binance
            api_secret: API secret de Binance
            symbol: Par de trading (BNBUSDT por defecto)
            testnet: Si usar testnet (True por defecto para pruebas)
        """
        # Cliente Binance
        self.client = Client(api_key, api_secret, testnet=testnet)
        self.symbol = symbol
        self.testnet = testnet
        
        # Bot MA Convergence con configuración optimizada
        self.ma_bot = MAConvergenceBot(verbose=True)
        config = self.ma_bot.get_optimized_config()
        print(f"🎯 Configuración optimizada cargada:")
        print(f"   MA1: {config['umbral_ma1']} | MA2: {config['umbral_ma2']}")
        print(f"   Retorno esperado: +{config['expected_return_pct']}%")
        
        # Estado del bot
        self.is_running = False
        self.position = None  # 'LONG' o None
        self.entry_price = 0.0
        self.last_check_time = None
        
        # Configuración
        self.check_interval = 5  # segundos entre checks
        self.data_window = 200   # velas para análisis (suficiente para MA99)
        
    def get_account_info(self):
        """Obtiene información de la cuenta"""
        try:
            account = self.client.get_account()
            balances = {}
            for balance in account['balances']:
                if float(balance['free']) > 0 or float(balance['locked']) > 0:
                    balances[balance['asset']] = {
                        'free': float(balance['free']),
                        'locked': float(balance['locked'])
                    }
            return balances
        except Exception as e:
            print(f"❌ Error obteniendo info cuenta: {e}")
            return {}
    
    def get_current_price(self):
        """Obtiene precio actual del símbolo"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=self.symbol)
            return float(ticker['price'])
        except Exception as e:
            print(f"❌ Error obteniendo precio: {e}")
            return None
    
    def get_klines_data(self, interval='1m', limit=200):
        """Obtiene datos de velas recientes"""
        try:
            klines = self.client.get_klines(
                symbol=self.symbol,
                interval=interval,
                limit=limit
            )
            
            # Convertir a DataFrame
            df = pd.DataFrame(klines, columns=[
                'Open time', 'Open', 'High', 'Low', 'Close', 'Volume',
                'Close time', 'Quote asset volume', 'Number of trades',
                'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'
            ])
            
            # Convertir tipos
            df['Open time'] = pd.to_datetime(df['Open time'], unit='ms')
            df['Open'] = df['Open'].astype(float)
            df['High'] = df['High'].astype(float)
            df['Low'] = df['Low'].astype(float)
            df['Close'] = df['Close'].astype(float)
            df['Volume'] = df['Volume'].astype(float)
            
            return df
            
        except Exception as e:
            print(f"❌ Error obteniendo datos: {e}")
            return None
    
    def analyze_market(self):
        """Analiza el mercado usando la lógica de MA Convergence"""
        try:
            # Obtener datos recientes
            df = self.get_klines_data(interval='1m', limit=self.data_window)
            if df is None or len(df) < 100:
                print("⚠️ Datos insuficientes para análisis")
                return None
            
            # Preparar datos para el bot MA
            df.set_index('Open time', inplace=True)
            
            # Calcular indicadores necesarios
            for period in [3, 7, 14, 25, 50, 99]:
                df[f'MA{period}'] = talib.SMA(df['Close'].values, timeperiod=period)
            
            # Asignar datos al bot
            self.ma_bot.data = df
            
            # Usar la lógica interna del bot para detectar señales
            segmentos_ma1 = self.ma_bot._calculate_ma_segments('MA7', self.ma_bot.umbral_ma1)
            segmentos_ma2 = self.ma_bot._calculate_ma_segments('MA25', self.ma_bot.umbral_ma2)
            
            if not segmentos_ma1 or not segmentos_ma2:
                return None
            
            # Detectar convergencias
            convergencias = self.ma_bot._detect_convergences(segmentos_ma1, segmentos_ma2)
            convergencias_filtradas = self.ma_bot._filter_consecutive_signals(convergencias)
            
            if not convergencias_filtradas:
                return None
            
            # Obtener la convergencia más reciente
            convergencias_ordenadas = sorted(convergencias_filtradas, 
                                           key=lambda x: pd.Timestamp(x['timestamp']))
            
            ultima_convergencia = convergencias_ordenadas[-1]
            tiempo_convergencia = pd.Timestamp(ultima_convergencia['timestamp'])
            tiempo_actual = df.index[-1]
            
            # Verificar si la convergencia es reciente (últimos 10 minutos)
            if (tiempo_actual - tiempo_convergencia).total_seconds() <= 600:
                return ultima_convergencia
            
            return None
            
        except Exception as e:
            print(f"❌ Error en análisis: {e}")
            return None
    
    def execute_buy_order(self, price):
        """Ejecuta orden de compra"""
        try:
            # Calcular cantidad basada en balance USDT
            balances = self.get_account_info()
            usdt_balance = balances.get('USDT', {}).get('free', 0)
            
            if usdt_balance < 10:  # Mínimo $10 para operar
                print(f"⚠️ Balance USDT insuficiente: ${usdt_balance:.2f}")
                return False
            
            # Usar 90% del balance disponible
            quantity = (usdt_balance * 0.9) / price
            quantity = round(quantity, 6)  # Redondear a 6 decimales
            
            if self.testnet:
                print(f"🧪 TESTNET - Simulando compra:")
                print(f"   Cantidad: {quantity} BNB")
                print(f"   Precio: ${price:.4f}")
                print(f"   Total: ${quantity * price:.2f}")
                
                # Simular orden exitosa
                self.position = 'LONG'
                self.entry_price = price
                return True
            else:
                # Orden real (cuando esté listo para producción)
                order = self.client.order_market_buy(
                    symbol=self.symbol,
                    quoteOrderQty=usdt_balance * 0.9
                )
                print(f"✅ Orden de compra ejecutada: {order}")
                self.position = 'LONG'
                self.entry_price = price
                return True
                
        except Exception as e:
            print(f"❌ Error ejecutando compra: {e}")
            return False
    
    def execute_sell_order(self, price):
        """Ejecuta orden de venta"""
        try:
            # Obtener balance BNB
            balances = self.get_account_info()
            bnb_balance = balances.get('BNB', {}).get('free', 0)
            
            if bnb_balance < 0.001:  # Mínimo para vender
                print(f"⚠️ Balance BNB insuficiente: {bnb_balance}")
                return False
            
            if self.testnet:
                print(f"🧪 TESTNET - Simulando venta:")
                print(f"   Cantidad: {bnb_balance} BNB")
                print(f"   Precio: ${price:.4f}")
                print(f"   Total: ${bnb_balance * price:.2f}")
                
                # Calcular P&L
                if self.entry_price > 0:
                    pnl_pct = ((price - self.entry_price) / self.entry_price) * 100
                    print(f"   P&L: {pnl_pct:+.2f}%")
                
                # Simular orden exitosa
                self.position = None
                self.entry_price = 0.0
                return True
            else:
                # Orden real (cuando esté listo para producción)
                order = self.client.order_market_sell(
                    symbol=self.symbol,
                    quantity=bnb_balance
                )
                print(f"✅ Orden de venta ejecutada: {order}")
                self.position = None
                self.entry_price = 0.0
                return True
                
        except Exception as e:
            print(f"❌ Error ejecutando venta: {e}")
            return False
    
    def run(self):
        """Ejecuta el bot en bucle continuo"""
        print(f"🚀 INICIANDO MA CONVERGENCE BOT - {self.symbol}")
        print(f"🔄 Modo: {'TESTNET' if self.testnet else 'PRODUCCIÓN'}")
        print(f"⏱️ Intervalo de check: {self.check_interval}s")
        print("=" * 60)
        
        self.is_running = True
        check_count = 0
        
        try:
            while self.is_running:
                check_count += 1
                current_time = datetime.now()
                current_price = self.get_current_price()
                
                if current_price is None:
                    time.sleep(self.check_interval)
                    continue
                
                print(f"[{check_count:4d}] {current_time.strftime('%H:%M:%S')} | "
                      f"Precio: ${current_price:.4f} | "
                      f"Posición: {self.position or 'None'}")
                
                # Analizar mercado
                signal = self.analyze_market()
                
                if signal:
                    print(f"🎯 Señal detectada: {signal['tipo']}")
                    
                    if signal['tipo'] == 'COMPRA_CONVERGENCIA' and self.position is None:
                        print(f"📈 Ejecutando COMPRA...")
                        if self.execute_buy_order(current_price):
                            print(f"✅ Posición LONG abierta en ${current_price:.4f}")
                    
                    elif signal['tipo'] == 'VENTA_CONVERGENCIA' and self.position == 'LONG':
                        print(f"📉 Ejecutando VENTA...")
                        if self.execute_sell_order(current_price):
                            print(f"✅ Posición cerrada en ${current_price:.4f}")
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print(f"\n⏹️ Bot detenido por usuario")
        except Exception as e:
            print(f"\n❌ Error en bot: {e}")
        finally:
            self.is_running = False
            print(f"🔚 Bot detenido")

def main():
    """Función principal"""
    # Configuración de API (Testnet)
    API_KEY = '7ZPT9vq9NRD8rDcV87ykvrPWBPQzPuZ9QkLKLLxGguQaDvT5mACl4nQSP8uwGxBH'
    API_SECRET = 'SpCz5aKF9c16gpJec6EQ3r0BC4GAqjmTO1Bevh2193mvVEEdClpIhP2jx7Wf1QFO'
    
    print("🤖 MA CONVERGENCE LIVE BOT - BINANCE TESTNET")
    print("=" * 60)
    
    # Crear y ejecutar bot
    bot = MAConvergenceLiveBot(
        api_key=API_KEY,
        api_secret=API_SECRET,
        symbol="BNBUSDT",
        testnet=True  # Usar testnet para pruebas
    )
    
    # Mostrar info de cuenta
    balances = bot.get_account_info()
    print(f"💰 Balances disponibles:")
    for asset, balance in balances.items():
        if balance['free'] > 0:
            print(f"   {asset}: {balance['free']:.6f}")
    print()
    
    # Precio actual
    current_price = bot.get_current_price()
    print(f"📊 Precio actual {bot.symbol}: ${current_price:.4f}")
    print()
    
    # Confirmar inicio
    response = input("¿Iniciar bot? (s/N): ").lower()
    if response == 's':
        bot.run()
    else:
        print("Bot cancelado")

if __name__ == "__main__":
    main()