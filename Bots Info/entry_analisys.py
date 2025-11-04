"""Module for fetching and analyzing Binance historical data."""
import requests
import pandas as pd


def obtener_historico_binance(symbol, interval, limit=1000):
    """_summary_Obtiene datos historicos de Binance y los devuelve en un DataFrame de pandas."""
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
    response = requests.get(url, params=params,timeout=10)  # Timeout set to 10 seconds
    data = response.json()

    df = pd.DataFrame(
        data,
        columns=[
            "Open time",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "Close time",
            "Quote asset volume",
            "Number of trades",
            "Taker buy base asset volume",
            "Taker buy quote asset volume",
            "Ignore",
        ],
    )

    df["Open time"] = pd.to_datetime(df["Open time"], unit="ms")
    df["Close time"] = pd.to_datetime(df["Close time"], unit="ms")
    df["Open"] = df["Open"].astype(float)
    df["High"] = df["High"].astype(float)
    df["Low"] = df["Low"].astype(float)
    df["Close"] = df["Close"].astype(float)
    df["Volume"] = df["Volume"].astype(float)

    df.set_index("Close time", inplace=True)
    return df


# Calcular indicadores técnicos
def sma(values, window):
    """_summary_Calcula la media móvil simple (SMA)."""
    return values.rolling(window=window).mean()

def rsi(values, window=14):
    """_summary_Calcula el Índice de Fuerza Relativa (RSI)."""

    delta = values.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def macd(values, fast=12, slow=26, signal=9):
    """_summary_Calcula el MACD y la línea de señal."""

    exp1 = values.ewm(span=fast, adjust=False).mean()
    exp2 = values.ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line


# Aplicar la estrategia y generar señales
def backtest_estrategia(df):
    """_summary_Aplica la estrategia de trading y genera señales de compra/venta."""

    window_ma = 50
    window_rsi = 14

    df["MA"] = sma(df["Close"], window_ma)
    df["RSI"] = rsi(df["Close"], window_rsi)
    df["MACD"], df["Signal"] = macd(df["Close"])

    df["Buy"] = False
    df["Sell"] = False

    for i in range(1, len(df)):
        if df["Close"].iloc[i] > df["MA"].iloc[i]:  # Precio arriba MA
            if (
                df["RSI"].iloc[i - 1] < 30 and df["RSI"].iloc[i] >= 30
            ):  # RSI cruza sobre 30
                if (
                    df["MACD"].iloc[i] > df["Signal"].iloc[i]
                    and df["MACD"].iloc[i - 1] <= df["Signal"].iloc[i - 1]
                ):  # Cruce MACD alcista
                    df["Buy"].iloc[i] = True

        if df["Close"].iloc[i] < df["MA"].iloc[i]:  # Precio abajo MA
            if (
                df["RSI"].iloc[i - 1] > 70 and df["RSI"].iloc[i] <= 70
            ):  # RSI cruza bajo 70
                if (
                    df["MACD"].iloc[i] < df["Signal"].iloc[i]
                    and df["MACD"].iloc[i - 1] >= df["Signal"].iloc[i - 1]
                ):  # Cruce MACD bajista
                    df["Sell"].iloc[i] = True

    return df

# Ejecución principal
if __name__ == "__main__":
    import sys

    # Permite pasar símbolo e intervalo como argumentos desde chart_ui.py
    if len(sys.argv) >= 3:
        SYMBOL = sys.argv[1]
        INTERVAL = sys.argv[2]
    else:
        SYMBOL = "BNBUSDT"
        INTERVAL = "1h"

    print(f"Descargando datos históricos de Binance para {SYMBOL} en intervalo {INTERVAL}...")
    df_main = obtener_historico_binance(SYMBOL, INTERVAL)
    print("Calculando indicadores y aplicando estrategia...")
    df_result = backtest_estrategia(df_main)
    print(df_result[["Close", "MA", "RSI", "MACD", "Signal", "Buy", "Sell"]].tail(20))

    # Guardar resultados a CSV
    df_result.to_csv(f"backtest_binance_{SYMBOL.lower()}.csv")
    print(f"Backtest terminado. Resultados guardados en backtest_binance_{SYMBOL.lower()}.csv")
