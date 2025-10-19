#!/usr/bin/env python3
"""
Análisis de umbrales óptimos para pendientes de MA
"""
import requests
import pandas as pd
import talib
import numpy as np

def sma(values, window):
    return pd.Series(talib.SMA(values.values, timeperiod=window), index=values.index)

def obtener_historico_binance(symbol="BNBUSDT", interval="1s", limit=600):
    """Obtener datos de Binance para análisis"""
    BINANCE_URL = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
    response = requests.get(BINANCE_URL, params=params, timeout=10)
    data = response.json()
    
    df = pd.DataFrame(
        data,
        columns=[
            "Open time", "Open", "High", "Low", "Close", "Volume",
            "Close time", "Quote asset volume", "Number of trades",
            "Taker buy base asset volume", "Taker buy quote asset volume", "Ignore"
        ]
    )
    df["Close time"] = pd.to_datetime(df["Close time"], unit="ms")
    df["Close"] = df["Close"].astype(float)
    df.set_index("Close time", inplace=True)
    
    return df

def calcular_pendientes_ma(df, periodo_ma):
    """Calcula pendientes de una MA específica"""
    ma_values = sma(df["Close"], periodo_ma).dropna()
    
    if len(ma_values) < 10:
        return []
    
    ventana = 3
    pendientes = []
    
    for i in range(ventana, len(ma_values) - ventana):
        inicio_idx = i - ventana // 2
        fin_idx = i + ventana // 2
        
        x_window = np.arange(fin_idx - inicio_idx + 1)
        y_window = ma_values.iloc[inicio_idx:fin_idx+1].values
        
        if len(x_window) > 1 and not np.any(np.isnan(y_window)):
            pendiente = np.polyfit(x_window, y_window, 1)[0]
            pendientes.append(pendiente)
    
    return pendientes

def analizar_umbrales():
    """Analiza los rangos de umbrales óptimos"""
    print("🔍 ANÁLISIS DE UMBRALES ÓPTIMOS")
    print("=" * 50)
    
    # Obtener datos
    df = obtener_historico_binance()
    print(f"📊 Datos obtenidos: {len(df)} registros")
    
    # Analizar diferentes MAs
    periodos_ma = [7, 14, 25, 50, 99]
    
    todas_pendientes = []
    
    for periodo in periodos_ma:
        pendientes = calcular_pendientes_ma(df, periodo)
        if pendientes:
            todas_pendientes.extend(pendientes)
            
            min_p = min(pendientes)
            max_p = max(pendientes)
            std_p = np.std(pendientes)
            percentil_95 = np.percentile(np.abs(pendientes), 95)
            
            print(f"\n📈 MA{periodo}:")
            print(f"   Min: {min_p:.8f}")
            print(f"   Max: {max_p:.8f}")
            print(f"   Std: {std_p:.8f}")
            print(f"   95% de pendientes están bajo: ±{percentil_95:.8f}")
    
    if todas_pendientes:
        print(f"\n🎯 ANÁLISIS GLOBAL:")
        min_global = min(todas_pendientes)
        max_global = max(todas_pendientes)
        std_global = np.std(todas_pendientes)
        
        print(f"   Rango total: {min_global:.8f} a {max_global:.8f}")
        print(f"   Desviación estándar: {std_global:.8f}")
        
        # Percentiles para recomendaciones
        percentiles = [50, 75, 90, 95, 99]
        abs_pendientes = [abs(p) for p in todas_pendientes]
        
        print(f"\n📊 PERCENTILES (valores absolutos):")
        for p in percentiles:
            valor = np.percentile(abs_pendientes, p)
            print(f"   {p:2d}%: {valor:.8f}")
        
        print(f"\n💡 RECOMENDACIONES DE UMBRAL:")
        print(f"   🔥 Muy sensible (detecta 50% de cambios): {np.percentile(abs_pendientes, 50):.8f}")
        print(f"   ⚡ Sensible (detecta 25% de cambios): {np.percentile(abs_pendientes, 75):.8f}")
        print(f"   🎯 Balanceado (detecta 10% de cambios): {np.percentile(abs_pendientes, 90):.8f}")
        print(f"   🛡️ Conservador (detecta 5% de cambios): {np.percentile(abs_pendientes, 95):.8f}")
        print(f"   🏔️ Muy conservador (detecta 1% de cambios): {np.percentile(abs_pendientes, 99):.8f}")
        
        # Valor máximo práctico
        max_practico = np.percentile(abs_pendientes, 99.5)
        print(f"\n🚫 UMBRAL MÁXIMO PRÁCTICO: {max_practico:.8f}")
        print(f"   (Usar valores mayores haría que TODO sea lateral)")

if __name__ == "__main__":
    analizar_umbrales()