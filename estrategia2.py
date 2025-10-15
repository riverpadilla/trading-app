import pandas as pd

def calcular_estadisticas(df):
    """
    Calcula estadísticas segundo a segundo:
    - Máxima y mínima variación absoluta entre apertura y cierre (con fecha, hora, apertura, cierre)
    - Máxima y mínima diferencia absoluta entre alto y bajo (con fecha, hora, high, low)
    - Promedio de la variación absoluta entre apertura y cierre
    - Porcentaje de datos de variación absoluta por encima del promedio
    - Promedio de la diferencia absoluta entre high y low
    - Porcentaje de datos de diferencia absoluta por encima del promedio
    Retorna un DataFrame con las estadísticas.
    """
    # Asegura que el índice sea datetime si existe columna de tiempo
    if 'Close time' in df.columns:
        df = df.set_index('Close time')

    # Variaciones absolutas entre apertura y cierre
    df['Var_Apertura_Cierre'] = (df['Close'] - df['Open']).abs()
    
    # Máxima y mínima variación
    idx_max_var_ac = df['Var_Apertura_Cierre'].idxmax()
    idx_min_var_ac = df['Var_Apertura_Cierre'].idxmin()
    max_var_ac = df.loc[idx_max_var_ac]
    min_var_ac = df.loc[idx_min_var_ac]

    # Diferencias absolutas entre alto y bajo
    df['Diff_High_Low'] = (df['High'] - df['Low']).abs()
    
    # Máxima y mínima diferencia
    idx_max_diff_hl = df['Diff_High_Low'].idxmax()
    idx_min_diff_hl = df['Diff_High_Low'].idxmin()
    max_diff_hl = df.loc[idx_max_diff_hl]
    min_diff_hl = df.loc[idx_min_diff_hl]

    # Promedios de valores absolutos
    promedio_var_ac = df['Var_Apertura_Cierre'].mean()
    promedio_diff_hl = df['Diff_High_Low'].mean()

    # Porcentajes por encima del promedio
    porcentaje_var_ac_sobre_promedio = (df['Var_Apertura_Cierre'] > promedio_var_ac).sum() / len(df) * 100
    porcentaje_diff_hl_sobre_promedio = (df['Diff_High_Low'] > promedio_diff_hl).sum() / len(df) * 100

    # Tabla de estadísticas
    stats = []

    # Máxima variación apertura-cierre
    stats.append({
        'Estadística': 'Máxima variación absoluta (Apertura-Cierre)',
        'Valor': max_var_ac['Var_Apertura_Cierre'],
        'Fecha/Hora': str(idx_max_var_ac),
        'Open/High': max_var_ac['Open'],
        'Close/Low': max_var_ac['Close']
    })

    # Mínima variación apertura-cierre
    stats.append({
        'Estadística': 'Mínima variación absoluta (Apertura-Cierre)',
        'Valor': min_var_ac['Var_Apertura_Cierre'],
        'Fecha/Hora': str(idx_min_var_ac),
        'Open/High': min_var_ac['Open'],
        'Close/Low': min_var_ac['Close']
    })

    # Máxima diferencia high-low
    stats.append({
        'Estadística': 'Máxima diferencia absoluta (High-Low)',
        'Valor': max_diff_hl['Diff_High_Low'],
        'Fecha/Hora': str(idx_max_diff_hl),
        'Open/High': max_diff_hl['High'],
        'Close/Low': max_diff_hl['Low']
    })

    # Mínima diferencia high-low
    stats.append({
        'Estadística': 'Mínima diferencia absoluta (High-Low)',
        'Valor': min_diff_hl['Diff_High_Low'],
        'Fecha/Hora': str(idx_min_diff_hl),
        'Open/High': min_diff_hl['High'],
        'Close/Low': min_diff_hl['Low']
    })

    # Promedio de variación absoluta apertura-cierre
    stats.append({
        'Estadística': 'Promedio variación absoluta (Apertura-Cierre)',
        'Valor': promedio_var_ac,
        'Fecha/Hora': '',
        'Open/High': '',
        'Close/Low': ''
    })

    # Porcentaje sobre promedio variación
    stats.append({
        'Estadística': '% datos sobre promedio variación (Apertura-Cierre)',
        'Valor': porcentaje_var_ac_sobre_promedio,
        'Fecha/Hora': '',
        'Open/High': '',
        'Close/Low': ''
    })

    # Promedio de diferencia absoluta high-low
    stats.append({
        'Estadística': 'Promedio diferencia absoluta (High-Low)',
        'Valor': promedio_diff_hl,
        'Fecha/Hora': '',
        'Open/High': '',
        'Close/Low': ''
    })

    # Porcentaje sobre promedio diferencia
    stats.append({
        'Estadística': '% datos sobre promedio diferencia (High-Low)',
        'Valor': porcentaje_diff_hl_sobre_promedio,
        'Fecha/Hora': '',
        'Open/High': '',
        'Close/Low': ''
    })

    return pd.DataFrame(stats)