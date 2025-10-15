import pandas as pd

def detectar_entradas(df):
    """
    Marca en el DataFrame las señales de compra/venta y salida según las reglas.
    Añade columnas 'Buy', 'Sell', 'Exit' y 'Region' (para sombrear).
    """
    df = df.copy()
    window_ma = 50

    df['MA50'] = df['Close'].rolling(window=window_ma).mean()
    df['Buy'] = False
    df['Sell'] = False
    df['Exit'] = False
    df['Region'] = None

    for i in range(1, len(df)):
        # --- Reglas de Compra ---
        if (
            df['Close'].iloc[i] > df['MA50'].iloc[i] and
            df['RSI'].iloc[i] < 70 and
            df['RSI'].iloc[i-1] < 30 and df['RSI'].iloc[i] >= 30 and
            df['MACD'].iloc[i] > df['Signal'].iloc[i] and
            df['MACD'].iloc[i-1] <= df['Signal'].iloc[i-1]
        ):
            df.at[df.index[i], 'Buy'] = True
            df.at[df.index[i], 'Region'] = 'buy'

        # --- Reglas de Venta ---
        if (
            df['Close'].iloc[i] < df['MA50'].iloc[i] and
            df['RSI'].iloc[i] > 30 and
            df['RSI'].iloc[i-1] > 70 and df['RSI'].iloc[i] <= 70 and
            df['MACD'].iloc[i] < df['Signal'].iloc[i] and
            df['MACD'].iloc[i-1] >= df['Signal'].iloc[i-1]
        ):
            df.at[df.index[i], 'Sell'] = True
            df.at[df.index[i], 'Region'] = 'sell'

        # --- Reglas de Salida ---
        # Salida de compra: RSI cruza por encima de 30 o MACD cruza bajista
        if (
            df['Buy'].iloc[i-1] and (
                df['RSI'].iloc[i-1] < 70 and df['RSI'].iloc[i] >= 70 or
                (df['MACD'].iloc[i] < df['Signal'].iloc[i] and df['MACD'].iloc[i-1] >= df['Signal'].iloc[i-1])
            )
        ):
            df.at[df.index[i], 'Exit'] = True

        # Salida de venta: RSI cruza por debajo de 30 o MACD cruza alcista
        if (
            df['Sell'].iloc[i-1] and (
                df['RSI'].iloc[i-1] > 30 and df['RSI'].iloc[i] <= 30 or
                (df['MACD'].iloc[i] > df['Signal'].iloc[i] and df['MACD'].iloc[i-1] <= df['Signal'].iloc[i-1])
            )
        ):
            df.at[df.index[i], 'Exit'] = True

    return df

def sombrear_regiones(axes, df):
    """
    Sombrea las regiones de compra (verde) y venta (rojo) en el gráfico de precios (axes[0]).
    Sombrea RSI (amarillo) en el gráfico de RSI (axes[1]).
    Sombrea MACD (azul) en el gráfico de MACD (axes[2]).
    Sombrea MA50 (violeta) en el gráfico de velas y MA (axes[0]).
    """
    # Panel 0: Compra/Venta y MA50
    for i in range(1, len(df)):
        if df['Region'].iloc[i] == 'buy':
            axes[0].axvspan(df.index[i-1], df.index[i], color='green', alpha=0.2)
        elif df['Region'].iloc[i] == 'sell':
            axes[0].axvspan(df.index[i-1], df.index[i], color='red', alpha=0.2)
        # MA50 cruce en panel de velas
        if (df['Close'].iloc[i] > df['MA50'].iloc[i] and df['Close'].iloc[i-1] <= df['MA50'].iloc[i-1]) or \
           (df['Close'].iloc[i] < df['MA50'].iloc[i] and df['Close'].iloc[i-1] >= df['MA50'].iloc[i-1]):
            axes[0].axvspan(df.index[i-1], df.index[i], color='violet', alpha=0.10)
    # Panel 1: RSI
    for i in range(1, len(df)):
        if (df['RSI'].iloc[i-1] < 30 and df['RSI'].iloc[i] >= 30) or (df['RSI'].iloc[i-1] > 70 and df['RSI'].iloc[i] <= 70):
            axes[1].axvspan(df.index[i-1], df.index[i], color='yellow', alpha=0.15)
    # Panel 2: MACD
    for i in range(1, len(df)):
        if (df['MACD'].iloc[i] > df['Signal'].iloc[i] and df['MACD'].iloc[i-1] <= df['Signal'].iloc[i-1]) or \
           (df['MACD'].iloc[i] < df['Signal'].iloc[i] and df['MACD'].iloc[i-1] >= df['Signal'].iloc[i-1]):
            axes[2].axvspan(df.index[i-1], df.index[i], color='blue', alpha=0.12)