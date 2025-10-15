import pandas as pd

def calcular_estadisticas(df):
    """
    Calcula estadísticas segundo a segundo:
    - Las 10 variaciones máximas absolutas entre apertura y cierre (con fecha, hora, apertura, cierre, RSI, MACD, MA50)
    - Variación mínima absoluta entre apertura y cierre (con fecha, hora, apertura, cierre, RSI, MACD, MA50)
    - Las 10 diferencias máximas absolutas entre alto y bajo (con fecha, hora, high, low, RSI, MACD, MA50)
    - Máxima y mínima diferencia absoluta entre alto y bajo (con fecha, hora, high, low, RSI, MACD, MA50)
    Retorna un DataFrame con las estadísticas.
    """
    # Asegura que el índice sea datetime si existe columna de tiempo
    if 'Close time' in df.columns:
        df = df.set_index('Close time')

    # Variaciones absolutas entre apertura y cierre
    df['Var_Apertura_Cierre'] = (df['Close'] - df['Open']).abs()
    top10_var_ac = df.nlargest(10, 'Var_Apertura_Cierre')
    min_var_ac = df['Var_Apertura_Cierre'].min()
    fecha_min_var_ac = df['Var_Apertura_Cierre'].idxmin()
    open_min_var_ac = df.loc[fecha_min_var_ac, 'Open']
    close_min_var_ac = df.loc[fecha_min_var_ac, 'Close']
    rsi_min_var_ac = df.loc[fecha_min_var_ac, 'RSI'] if 'RSI' in df.columns else ''
    macd_min_var_ac = df.loc[fecha_min_var_ac, 'MACD'] if 'MACD' in df.columns else ''
    ma50_min_var_ac = df.loc[fecha_min_var_ac, 'MA50'] if 'MA50' in df.columns else ''

    # Diferencias absolutas entre alto y bajo
    df['Diff_High_Low'] = (df['High'] - df['Low']).abs()
    top10_diff_hl = df.nlargest(10, 'Diff_High_Low')
    max_diff_hl = df['Diff_High_Low'].max()
    min_diff_hl = df['Diff_High_Low'].min()
    fecha_max_diff_hl = df['Diff_High_Low'].idxmax()
    fecha_min_diff_hl = df['Diff_High_Low'].idxmin()
    high_max_diff_hl = df.loc[fecha_max_diff_hl, 'High']
    low_max_diff_hl = df.loc[fecha_max_diff_hl, 'Low']
    rsi_max_diff_hl = df.loc[fecha_max_diff_hl, 'RSI'] if 'RSI' in df.columns else ''
    macd_max_diff_hl = df.loc[fecha_max_diff_hl, 'MACD'] if 'MACD' in df.columns else ''
    ma50_max_diff_hl = df.loc[fecha_max_diff_hl, 'MA50'] if 'MA50' in df.columns else ''
    high_min_diff_hl = df.loc[fecha_min_diff_hl, 'High']
    low_min_diff_hl = df.loc[fecha_min_diff_hl, 'Low']
    rsi_min_diff_hl = df.loc[fecha_min_diff_hl, 'RSI'] if 'RSI' in df.columns else ''
    macd_min_diff_hl = df.loc[fecha_min_diff_hl, 'MACD'] if 'MACD' in df.columns else ''
    ma50_min_diff_hl = df.loc[fecha_min_diff_hl, 'MA50'] if 'MA50' in df.columns else ''

    # Tabla de estadísticas
    stats = []

    # Top 10 variaciones máximas apertura-cierre
    for idx, row in top10_var_ac.iterrows():
        stats.append({
            'Estadística': 'Top variación absoluta (Apertura-Cierre)',
            'Valor': row['Var_Apertura_Cierre'],
            'Fecha/Hora': str(idx),
            'Apertura': row['Open'],
            'Cierre': row['Close'],
            'High': '',
            'Low': '',
            'RSI': row['RSI'] if 'RSI' in row else '',
            'MACD': row['MACD'] if 'MACD' in row else '',
            'MA50': row['MA50'] if 'MA50' in row else ''
        })

    # Variación mínima absoluta apertura-cierre
    stats.append({
        'Estadística': 'Variación mínima absoluta (Apertura-Cierre)',
        'Valor': min_var_ac,
        'Fecha/Hora': str(fecha_min_var_ac),
        'Apertura': open_min_var_ac,
        'Cierre': close_min_var_ac,
        'High': '',
        'Low': '',
        'RSI': rsi_min_var_ac,
        'MACD': macd_min_var_ac,
        'MA50': ma50_min_var_ac
    })

    # Top 10 diferencias máximas high-low
    for idx, row in top10_diff_hl.iterrows():
        stats.append({
            'Estadística': 'Top diferencia absoluta (High-Low)',
            'Valor': row['Diff_High_Low'],
            'Fecha/Hora': str(idx),
            'Apertura': '',
            'Cierre': '',
            'High': row['High'],
            'Low': row['Low'],
            'RSI': row['RSI'] if 'RSI' in row else '',
            'MACD': row['MACD'] if 'MACD' in row else '',
            'MA50': row['MA50'] if 'MA50' in row else ''
        })

    # Máxima diferencia high-low
    stats.append({
        'Estadística': 'Máxima diferencia absoluta (High-Low)',
        'Valor': max_diff_hl,
        'Fecha/Hora': str(fecha_max_diff_hl),
        'Apertura': '',
        'Cierre': '',
        'High': high_max_diff_hl,
        'Low': low_max_diff_hl,
        'RSI': rsi_max_diff_hl,
        'MACD': macd_max_diff_hl,
        'MA50': ma50_max_diff_hl
    })

    # Mínima diferencia high-low
    stats.append({
        'Estadística': 'Mínima diferencia absoluta (High-Low)',
        'Valor': min_diff_hl,
        'Fecha/Hora': str(fecha_min_diff_hl),
        'Apertura': '',
        'Cierre': '',
        'High': high_min_diff_hl,
        'Low': low_min_diff_hl,
        'RSI': rsi_min_diff_hl,
        'MACD': macd_min_diff_hl,
        'MA50': ma50_min_diff_hl
    })

    return pd.DataFrame(stats)