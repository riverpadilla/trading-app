import pandas as pd
import numpy as np
from binance.client import Client
from datetime import datetime, timedelta
import json
import os

# ============================================================================
# CONFIGURACIÓN INICIAL
# ============================================================================

# OPCIÓN 1: API Keys (SOL Trading Anaysis Key)
API_KEY = "ghf17lXepHDblRsp1Q2i9XPdPVCrzx7TO74SWDbhaNB6bKSGlQOXlHew5YTuer34" 
API_SECRET = "x2b0OIBDxV4W34mvWXn4ndu3KYIU7vMHCA1RyK8VaYmlrUWjZzVqqTziQ4LJb1Kj" 

# OPCIÓN 2: Sin API keys (limitado a 1200 requests/minuto)
# Descomenta la siguiente línea si no tienes API keys
# client = Client()

# Con API keys (mejor para análisis)
client = Client(api_key=API_KEY, api_secret=API_SECRET)

# ============================================================================
# 1. DESCARGAR DATOS DE VELAS (KLINES)
# ============================================================================

def descargar_klines(symbol, interval, limit=500):
    """
    Descarga datos de velas desde Binance
    Timeframes disponibles: 1m, 5m, 15m, 1h, 4h, 1d
    """
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        
        # Convertir a DataFrame
        df = pd.DataFrame(klines, columns=[
            'Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume',
            'Close_Time', 'Quote_Asset_Volume', 'Number_of_Trades',
            'Taker_Buy_Base', 'Taker_Buy_Quote', 'Ignore'
        ])
        
        # Convertir a tipos de datos correctos
        df['Open_Time'] = pd.to_datetime(df['Open_Time'], unit='ms')
        df['Close_Time'] = pd.to_datetime(df['Close_Time'], unit='ms')
        df['Open'] = df['Open'].astype(float)
        df['High'] = df['High'].astype(float)
        df['Low'] = df['Low'].astype(float)
        df['Close'] = df['Close'].astype(float)
        df['Volume'] = df['Volume'].astype(float)
        
        return df
    except Exception as e:
        print(f"Error descargando {interval}: {e}")
        return None

# Descargar múltiples timeframes
print("📊 Descargando datos de velas...")
print("-" * 60)

df_1m = descargar_klines('SOLUSDT', Client.KLINE_INTERVAL_1MINUTE, limit=1000)
print(f"✓ 1m: {len(df_1m)} velas")

df_5m = descargar_klines('SOLUSDT', Client.KLINE_INTERVAL_5MINUTE, limit=1000)
print(f"✓ 5m: {len(df_5m)} velas")

df_15m = descargar_klines('SOLUSDT', Client.KLINE_INTERVAL_15MINUTE, limit=1000)
print(f"✓ 15m: {len(df_15m)} velas")

df_1h = descargar_klines('SOLUSDT', Client.KLINE_INTERVAL_1HOUR, limit=1000)
print(f"✓ 1h: {len(df_1h)} velas")

df_4h = descargar_klines('SOLUSDT', Client.KLINE_INTERVAL_4HOUR, limit=1000)
print(f"✓ 4h: {len(df_4h)} velas")

df_1d = descargar_klines('SOLUSDT', Client.KLINE_INTERVAL_1DAY, limit=300)
print(f"✓ 1d: {len(df_1d)} velas")

# ============================================================================
# 2. CALCULAR INDICADORES TÉCNICOS
# ============================================================================

def calcular_indicadores(df):
    """Calcula RSI, MACD, Medias Móviles, ATR, Bandas de Bollinger"""
    
    # RSI(14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD (12, 26, 9)
    ema12 = df['Close'].ewm(span=12).mean()
    ema26 = df['Close'].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
    df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
    
    # Medias Móviles
    df['MA7'] = df['Close'].rolling(window=7).mean()
    df['MA25'] = df['Close'].rolling(window=25).mean()
    df['MA99'] = df['Close'].rolling(window=99).mean()
    
    # Bandas de Bollinger
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['StdDev'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['MA20'] + (df['StdDev'] * 2)
    df['BB_Lower'] = df['MA20'] - (df['StdDev'] * 2)
    
    # ATR (Average True Range)
    df['TR'] = np.maximum(
        df['High'] - df['Low'],
        np.maximum(
            abs(df['High'] - df['Close'].shift()),
            abs(df['Low'] - df['Close'].shift())
        )
    )
    df['ATR'] = df['TR'].rolling(window=14).mean()
    
    # Accumulation/Distribution
    df['Accum_Dist'] = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low']) * df['Volume']
    df['Accum_Dist_Line'] = df['Accum_Dist'].cumsum()
    
    return df

print("\n📈 Calculando indicadores técnicos...")
print("-" * 60)

dataframes = {'1m': df_1m, '5m': df_5m, '15m': df_15m, '1h': df_1h, '4h': df_4h, '1d': df_1d}
for timeframe, df in dataframes.items():
    if df is not None:
        df = calcular_indicadores(df)
        dataframes[timeframe] = df
        print(f"✓ Indicadores calculados para {timeframe}")

# ============================================================================
# 3. OBTENER INFORMACIÓN DE MERCADO EN TIEMPO REAL
# ============================================================================

print("\n💹 Obteniendo datos de mercado en tiempo real...")
print("-" * 60)

# Ticker information
ticker = client.get_ticker(symbol='SOLUSDT')
print(f"Precio actual: ${ticker['lastPrice']}")
print(f"Cambio 24h: {ticker['priceChangePercent']}%")
print(f"Alto 24h: ${ticker['highPrice']}")
print(f"Bajo 24h: ${ticker['lowPrice']}")
print(f"Volumen 24h: {ticker['volume']} SOL")

# Order Book (primeros 20 niveles)
order_book = client.get_order_book(symbol='SOLUSDT', limit=20)
print(f"\nBids (Compras - primeras 5):")
for bid in order_book['bids'][:5]:
    print(f"  Precio: ${bid[0]}, Cantidad: {bid[1]} SOL")

print(f"\nAsks (Ventas - primeras 5):")
for ask in order_book['asks'][:5]:
    print(f"  Precio: ${ask[0]}, Cantidad: {ask[1]} SOL")

# ============================================================================
# 4. EXPORTAR DATOS A CSV
# ============================================================================

print("\n💾 Exportando datos a archivos CSV...")
print("-" * 60)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

for timeframe, df in dataframes.items():
    if df is not None:
        filename = f"SOLUSDT_{timeframe}_{timestamp}.csv"
        df.to_csv(filename, index=False)
        print(f"✓ {filename}")

# ============================================================================
# 5. CREAR RESUMEN ANALÍTICO COMPLETO
# ============================================================================

print("\n📊 RESUMEN TÉCNICO COMPLETO")
print("=" * 70)

summary_data = {
    "Timestamp": datetime.now().isoformat(),
    "Precio Actual": float(ticker['lastPrice']),
    "Cambio 24h (%)": float(ticker['priceChangePercent']),
    "Alto 24h": float(ticker['highPrice']),
    "Bajo 24h": float(ticker['lowPrice']),
    "Volumen 24h (SOL)": float(ticker['volume']),
}

# Indicadores por timeframe
for timeframe, df in dataframes.items():
    if df is not None and len(df) > 0:
        latest = df.iloc[-1]
        summary_data[f"{timeframe}_data"] = {
            "Close": float(latest['Close']),
            "High": float(latest['High']),
            "Low": float(latest['Low']),
            "Volume": float(latest['Volume']),
            "RSI": float(latest['RSI']) if not pd.isna(latest['RSI']) else None,
            "MACD": float(latest['MACD']) if not pd.isna(latest['MACD']) else None,
            "MACD_Signal": float(latest['MACD_Signal']) if not pd.isna(latest['MACD_Signal']) else None,
            "MACD_Histogram": float(latest['MACD_Histogram']) if not pd.isna(latest['MACD_Histogram']) else None,
            "MA7": float(latest['MA7']) if not pd.isna(latest['MA7']) else None,
            "MA25": float(latest['MA25']) if not pd.isna(latest['MA25']) else None,
            "MA99": float(latest['MA99']) if not pd.isna(latest['MA99']) else None,
            "BB_Upper": float(latest['BB_Upper']) if not pd.isna(latest['BB_Upper']) else None,
            "BB_Lower": float(latest['BB_Lower']) if not pd.isna(latest['BB_Lower']) else None,
            "ATR": float(latest['ATR']) if not pd.isna(latest['ATR']) else None,
            "Accum_Dist_Line": float(latest['Accum_Dist_Line']) if not pd.isna(latest['Accum_Dist_Line']) else None,
        }

# Order Book Analysis
bid_prices = [float(bid[0]) for bid in order_book['bids']]
ask_prices = [float(ask[0]) for ask in order_book['asks']]
bid_volumes = [float(bid[1]) for bid in order_book['bids']]
ask_volumes = [float(ask[1]) for ask in order_book['asks']]

summary_data["OrderBook"] = {
    "Bid_Pressure": sum(bid_volumes[:5]),
    "Ask_Pressure": sum(ask_volumes[:5]),
    "Bid_Ask_Ratio": sum(bid_volumes[:5]) / sum(ask_volumes[:5]) if sum(ask_volumes[:5]) > 0 else 0,
    "Top_Bid": bid_prices[0] if bid_prices else None,
    "Top_Ask": ask_prices[0] if ask_prices else None,
}

# Guardar resumen en JSON
summary_filename = f"SOLUSDT_SUMMARY_{timestamp}.json"
with open(summary_filename, 'w') as f:
    json.dump(summary_data, f, indent=2)
print(f"✓ {summary_filename} creado")

# Imprimir resumen formateado
print(json.dumps(summary_data, indent=2))

print("\n✅ ANÁLISIS COMPLETADO")
print(f"Archivos generados con timestamp: {timestamp}")
print("Archivos CSV: SOLUSDT_[timeframe]_[timestamp].csv")
print("Resumen JSON: SOLUSDT_SUMMARY_[timestamp].json")