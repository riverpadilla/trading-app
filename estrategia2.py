import pandas as pd
import numpy as np

def calcular_deciles(valores: pd.Series) -> list:
    """
    Agrupa una serie en 10 percentiles (deciles) y retorna información de cada uno.
    
    Devuelve lista de dicts, cada uno con:
        'percentil': nombre del rango (ej: 'P0-10', 'P10-20', ...)
        'rango': (valor_min, valor_max) del bin
        'frecuencia': cantidad de elementos en el bin
        'porcentaje': frecuencia en % respecto al total
    """
    n = int(len(valores))
    if n == 0:
        return []

    serie = valores.dropna()
    if serie.empty:
        return []

    # 10 percentiles: P0, P10, P20, ..., P100
    percentiles = list(range(0, 101, 10))
    pvals = np.percentile(serie.values, percentiles)

    resultados = []
    for i in range(len(pvals) - 1):
        low = float(pvals[i])
        high = float(pvals[i + 1])
        # Incluir el límite inferior solo en el primer bin
        if i == 0:
            mask = (serie >= low) & (serie <= high)
        else:
            mask = (serie > low) & (serie <= high)
        freq = int(mask.sum())
        
        resultados.append({
            'percentil': f'P{i*10}-{(i+1)*10}',
            'rango': (low, high),
            'frecuencia': freq,
            'porcentaje': (freq / n) * 100.0 if n > 0 else 0.0
        })
    
    return resultados


def calcular_estadisticas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula estadísticas base y agrupa variaciones y diferencias en 10 percentiles (deciles).
    
    Devuelve un DataFrame con filas de estadísticas listas para mostrar en la UI.
    """
    if df is None or df.empty:
        return pd.DataFrame([])

    # Usar 'Close time' como índice si existe para mostrar fecha/hora en extremos
    work = df.copy()
    if 'Close time' in work.columns:
        work = work.set_index('Close time')

    # Métricas base
    work['Var_Apertura_Cierre'] = (work['Close'] - work['Open']).abs()
    work['Diff_High_Low'] = (work['High'] - work['Low']).abs()

    # Extremos (manejar posibles vacíos)
    if work['Var_Apertura_Cierre'].notna().any():
        idx_max_var_ac = work['Var_Apertura_Cierre'].idxmax()
        idx_min_var_ac = work['Var_Apertura_Cierre'].idxmin()
        max_var_ac = work.loc[idx_max_var_ac]
        min_var_ac = work.loc[idx_min_var_ac]
    else:
        idx_max_var_ac = idx_min_var_ac = ''
        max_var_ac = min_var_ac = {'Var_Apertura_Cierre': 0.0, 'Open': '', 'Close': ''}

    if work['Diff_High_Low'].notna().any():
        idx_max_diff_hl = work['Diff_High_Low'].idxmax()
        idx_min_diff_hl = work['Diff_High_Low'].idxmin()
        max_diff_hl = work.loc[idx_max_diff_hl]
        min_diff_hl = work.loc[idx_min_diff_hl]
    else:
        idx_max_diff_hl = idx_min_diff_hl = ''
        max_diff_hl = min_diff_hl = {'Diff_High_Low': 0.0, 'High': '', 'Low': ''}

    # Promedios y % sobre promedio
    promedio_var_ac = float(work['Var_Apertura_Cierre'].mean()) if work['Var_Apertura_Cierre'].notna().any() else 0.0
    promedio_diff_hl = float(work['Diff_High_Low'].mean()) if work['Diff_High_Low'].notna().any() else 0.0
    porcentaje_var_ac_sobre_promedio = (work['Var_Apertura_Cierre'] > promedio_var_ac).sum() / len(work) * 100.0 if len(work) else 0.0
    porcentaje_diff_hl_sobre_promedio = (work['Diff_High_Low'] > promedio_diff_hl).sum() / len(work) * 100.0 if len(work) else 0.0

    # Calcular deciles (10 percentiles)
    deciles_var = calcular_deciles(work['Var_Apertura_Cierre'])
    deciles_diff = calcular_deciles(work['Diff_High_Low'])

    # Tabla de estadísticas
    stats = []

    stats.append({
        'Estadística': 'Máxima variación absoluta (Apertura-Cierre)',
        'Valor': float(max_var_ac['Var_Apertura_Cierre']) if 'Var_Apertura_Cierre' in max_var_ac else 0.0,
        'Fecha/Hora': str(idx_max_var_ac),
        'Open/High': float(max_var_ac['Open']) if 'Open' in max_var_ac else '',
        'Close/Low': float(max_var_ac['Close']) if 'Close' in max_var_ac else ''
    })

    stats.append({
        'Estadística': 'Mínima variación absoluta (Apertura-Cierre)',
        'Valor': float(min_var_ac['Var_Apertura_Cierre']) if 'Var_Apertura_Cierre' in min_var_ac else 0.0,
        'Fecha/Hora': str(idx_min_var_ac),
        'Open/High': float(min_var_ac['Open']) if 'Open' in min_var_ac else '',
        'Close/Low': float(min_var_ac['Close']) if 'Close' in min_var_ac else ''
    })

    # Agregar los 10 deciles de variación
    for decil in deciles_var:
        stats.append({
            'Estadística': f"Variación {decil['percentil']} (Apertura-Cierre)",
            'Valor': f"{decil['rango'][0]:.6f} – {decil['rango'][1]:.6f}",
            'Fecha/Hora': f"{decil['frecuencia']} ocurrencias",
            'Open/High': '',
            'Close/Low': f"{decil['porcentaje']:.2f}%"
        })

    stats.append({
        'Estadística': 'Máxima diferencia absoluta (High-Low)',
        'Valor': float(max_diff_hl['Diff_High_Low']) if 'Diff_High_Low' in max_diff_hl else 0.0,
        'Fecha/Hora': str(idx_max_diff_hl),
        'Open/High': float(max_diff_hl['High']) if 'High' in max_diff_hl else '',
        'Close/Low': float(max_diff_hl['Low']) if 'Low' in max_diff_hl else ''
    })

    stats.append({
        'Estadística': 'Mínima diferencia absoluta (High-Low)',
        'Valor': float(min_diff_hl['Diff_High_Low']) if 'Diff_High_Low' in min_diff_hl else 0.0,
        'Fecha/Hora': str(idx_min_diff_hl),
        'Open/High': float(min_diff_hl['High']) if 'High' in min_diff_hl else '',
        'Close/Low': float(min_diff_hl['Low']) if 'Low' in min_diff_hl else ''
    })

    # Agregar los 10 deciles de diferencia
    for decil in deciles_diff:
        stats.append({
            'Estadística': f"Diferencia {decil['percentil']} (High-Low)",
            'Valor': f"{decil['rango'][0]:.6f} – {decil['rango'][1]:.6f}",
            'Fecha/Hora': f"{decil['frecuencia']} ocurrencias",
            'Open/High': '',
            'Close/Low': f"{decil['porcentaje']:.2f}%"
        })

    stats.append({
        'Estadística': 'Promedio variación absoluta (Apertura-Cierre)',
        'Valor': promedio_var_ac,
        'Fecha/Hora': '',
        'Open/High': '',
        'Close/Low': ''
    })

    stats.append({
        'Estadística': '% datos sobre promedio variación (Apertura-Cierre)',
        'Valor': porcentaje_var_ac_sobre_promedio,
        'Fecha/Hora': '',
        'Open/High': '',
        'Close/Low': ''
    })

    stats.append({
        'Estadística': 'Promedio diferencia absoluta (High-Low)',
        'Valor': promedio_diff_hl,
        'Fecha/Hora': '',
        'Open/High': '',
        'Close/Low': ''
    })

    stats.append({
        'Estadística': '% datos sobre promedio diferencia (High-Low)',
        'Valor': porcentaje_diff_hl_sobre_promedio,
        'Fecha/Hora': '',
        'Open/High': '',
        'Close/Low': ''
    })

    return pd.DataFrame(stats)

