#!/usr/bin/env python3
"""
Análisis de resultados de la matriz MA1 x MA2
"""

import pandas as pd
import numpy as np

def analyze_results():
    # Cargar resultados
    df = pd.read_csv('ma_matrix_results_20251019_165755.csv')
    
    print('📊 RESULTADOS MATRIZ COMPLETA MA1 x MA2')
    print('=' * 80)
    print(f'📈 Total combinaciones: {len(df)}')
    
    # Filtrar rentables
    rentables = df[df['retorno_pct'] > 0].copy()
    print(f'💰 Configuraciones rentables: {len(rentables)}/{len(df)} ({len(rentables)/len(df)*100:.1f}%)')
    
    if len(rentables) > 0:
        # Top 10 mejores
        top_10 = rentables.nlargest(10, 'retorno_pct')
        
        print(f'\n🏆 TOP 10 MEJORES CONFIGURACIONES:')
        for i, (idx, row) in enumerate(top_10.iterrows(), 1):
            print(f'{i:2d}. MA1={row["umbral_ma1"]:.4f} | MA2={row["umbral_ma2"]:.4f} | ' + 
                  f'Retorno: {row["retorno_pct"]:+.3f}% | Trades: {int(row["total_trades"])} | ' + 
                  f'Win Rate: {row["win_rate"]:.1f}%')
        
        print(f'\n📊 ESTADÍSTICAS DE CONFIGURACIONES RENTABLES:')
        print(f'   Retorno promedio: {rentables["retorno_pct"].mean():.3f}%')
        print(f'   Retorno máximo: {rentables["retorno_pct"].max():.3f}%')
        print(f'   Retorno mínimo: {rentables["retorno_pct"].min():.3f}%')
        print(f'   Trades promedio: {rentables["total_trades"].mean():.1f}')
        print(f'   Win rate promedio: {rentables["win_rate"].mean():.1f}%')
        
        # Análisis por rangos de MA1
        print(f'\n🔍 ANÁLISIS POR RANGOS DE MA1:')
        ma1_ranges = [
            (0.0001, 0.01, 'Muy Bajo'),
            (0.01, 0.05, 'Bajo'),
            (0.05, 0.08, 'Medio'),
            (0.08, 0.1, 'Alto')
        ]
        
        for min_val, max_val, label in ma1_ranges:
            subset = rentables[(rentables['umbral_ma1'] >= min_val) & 
                             (rentables['umbral_ma1'] < max_val)]
            if len(subset) > 0:
                print(f'   {label} ({min_val:.3f}-{max_val:.3f}): {len(subset)} rentables, ' + 
                      f'retorno prom: {subset["retorno_pct"].mean():.3f}%')
        
        # Mejor configuración general
        best = rentables.loc[rentables['retorno_pct'].idxmax()]
        print(f'\n🎯 CONFIGURACIÓN ÓPTIMA RECOMENDADA:')
        print(f'   MA1: {best["umbral_ma1"]:.4f}')
        print(f'   MA2: {best["umbral_ma2"]:.4f}')
        print(f'   Retorno: {best["retorno_pct"]:+.3f}%')
        print(f'   Trades: {int(best["total_trades"])}')
        print(f'   Win Rate: {best["win_rate"]:.1f}%')
        print(f'   Convergencias detectadas: {int(best["convergencias_detectadas"])}')
        print(f'   Convergencias filtradas: {int(best["convergencias_filtradas"])}')
        
    else:
        print('❌ No se encontraron configuraciones rentables')
    
    # Estadísticas generales
    print(f'\n📋 ESTADÍSTICAS GENERALES:')
    print(f'   Promedio general: {df["retorno_pct"].mean():.3f}%')
    print(f'   Configuraciones con 0 trades: {len(df[df["total_trades"] == 0])}')
    print(f'   Configuraciones con pérdidas: {len(df[df["retorno_pct"] < 0])}')

if __name__ == "__main__":
    analyze_results()