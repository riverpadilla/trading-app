#!/usr/bin/env python3
"""
Test rápido de matriz combinatoria MA1 x MA2 - VERSIÓN SILENCIOSA
Solo muestra progreso esencial y resultados finales
"""

import numpy as np
import pandas as pd
import time
from ma_convergence_bot import MAConvergenceBot

def main():
    # Configuración de la matriz
    umbral_start = 0.0002
    umbral_end = 0.1
    num_steps = 20
    
    # Generar arrays de umbrales usando logspace para mejor distribución
    umbrales_ma1 = np.logspace(np.log10(umbral_start), np.log10(umbral_end), num_steps)
    umbrales_ma2 = np.logspace(np.log10(umbral_start), np.log10(umbral_end), num_steps)
    
    total_combinations = len(umbrales_ma1) * len(umbrales_ma2)
    
    print(f"📁 Usando archivo: binance_BNBUSDT_1s_20251018_234757.csv")
    print(f"\n🧪 TEST MATRIZ COMBINATORIA MA1 x MA2 (OPTIMIZADA)")
    print(f"   MA1: MA7, MA2: MA25")
    print(f"   Rango umbrales: {umbral_start:.4f} - {umbral_end:.1f}")
    print(f"   Pasos: {num_steps} x {num_steps}")
    print(f"   Total combinaciones: {total_combinations}")
    print(f"=" * 80)
    
    start_time = time.time()
    results = []
    
    for i, umbral_ma1 in enumerate(umbrales_ma1):
        for j, umbral_ma2 in enumerate(umbrales_ma2):
            combination_num = i * len(umbrales_ma2) + j + 1
            elapsed = time.time() - start_time
            print(f"🔄 [{combination_num:3d}/400] MA1={umbral_ma1:.4f} | MA2={umbral_ma2:.4f} - {elapsed:.1f}s")
            
            try:
                # Crear bot con configuración específica
                bot = MAConvergenceBot(
                    ma1_period="MA7",
                    ma2_period="MA25",
                    umbral_ma1=umbral_ma1,
                    umbral_ma2=umbral_ma2,
                    take_profit=0.002,
                    stop_loss=0.001,
                    verbose=False  # CLAVE: Sin salida verbose
                )
                
                # Ejecutar backtest SIN output
                result = bot.run_backtest('binance_BNBUSDT_1s_20251018_234757.csv')
                
                # Verificar que el resultado no sea None
                if result is None:
                    result = {
                        'retorno_pct': 0.0,
                        'total_trades': 0,
                        'capital_final': 1000.0,
                        'win_rate': 0.0,
                        'convergencias_detectadas': 0,
                        'convergencias_filtradas': 0
                    }
                
                # Guardar solo los resultados esenciales
                results.append({
                    'umbral_ma1': umbral_ma1,
                    'umbral_ma2': umbral_ma2,
                    'retorno_pct': result.get('retorno_pct', 0.0),
                    'total_trades': result.get('total_trades', 0),
                    'capital_final': result.get('capital_final', 1000.0),
                    'win_rate': result.get('win_rate', 0.0),
                    'convergencias_detectadas': result.get('convergencias_detectadas', 0),
                    'convergencias_filtradas': result.get('convergencias_filtradas', 0)
                })
                
                # Mostrar resultado si es rentable
                retorno = result.get('retorno_pct', 0.0)
                trades = result.get('total_trades', 0)
                if retorno > 0:
                    print(f"    💰 RENTABLE: {retorno:+.2f}% | {trades} trades")
                
                # Mostrar estimación de tiempo restante cada 10 iteraciones
                if combination_num % 10 == 0:
                    avg_time_per_combo = elapsed / combination_num
                    remaining_combos = total_combinations - combination_num
                    eta_seconds = avg_time_per_combo * remaining_combos
                    eta_minutes = eta_seconds / 60
                    rentables_hasta_ahora = len([r for r in results if r['retorno_pct'] > 0])
                    print(f"    📊 Promedio: {avg_time_per_combo:.1f}s/combo | ETA: {eta_minutes:.1f}min | Rentables: {rentables_hasta_ahora}")
                
            except Exception as e:
                print(f"❌ Error en MA1={umbral_ma1:.4f}, MA2={umbral_ma2:.4f}: {str(e)}")
                results.append({
                    'umbral_ma1': umbral_ma1,
                    'umbral_ma2': umbral_ma2,
                    'retorno_pct': -999,  # Marca de error
                    'total_trades': 0,
                    'capital_final': 0,
                    'win_rate': 0,
                    'convergencias_detectadas': 0,
                    'convergencias_filtradas': 0
                })
    
    # Analizar resultados
    elapsed_time = time.time() - start_time
    df_results = pd.DataFrame(results)
    
    # Filtrar errores y obtener estadísticas
    df_valid = df_results[df_results['retorno_pct'] > -999]
    rentables = df_valid[df_valid['retorno_pct'] > 0]
    
    print(f"\n⏱️  TIEMPO TOTAL: {elapsed_time:.1f} segundos")
    print(f"📊 RESULTADOS DEL TEST:")
    print(f"=" * 50)
    
    if len(rentables) > 0:
        # Mejor resultado
        best = rentables.loc[rentables['retorno_pct'].idxmax()]
        print(f"🏆 MEJOR RESULTADO:")
        print(f"   MA1: {best['umbral_ma1']:.4f} | MA2: {best['umbral_ma2']:.4f}")
        print(f"   Retorno: {best['retorno_pct']:+.2f}%")
        print(f"   Trades: {best['total_trades']}")
        print(f"   Win Rate: {best['win_rate']:.1f}%")
        
        # Top 5 configuraciones
        top_5 = rentables.nlargest(5, 'retorno_pct')
        print(f"\n🔝 TOP 5 CONFIGURACIONES:")
        for idx, row in top_5.iterrows():
            print(f"   MA1: {row['umbral_ma1']:.4f} | MA2: {row['umbral_ma2']:.4f} | "
                  f"Retorno: {row['retorno_pct']:+.2f}% | Trades: {int(row['total_trades'])}")
        
        print(f"\n💰 CONFIGURACIONES RENTABLES: {len(rentables)}/{len(df_valid)}")
        
        # Estadísticas de rentabilidad
        print(f"📈 ESTADÍSTICAS DE RETORNO:")
        print(f"   Promedio: {rentables['retorno_pct'].mean():.3f}%")
        print(f"   Máximo: {rentables['retorno_pct'].max():.3f}%")
        print(f"   Mínimo: {rentables['retorno_pct'].min():.3f}%")
        
    else:
        print("❌ No se encontraron configuraciones rentables")
    
    # Guardar resultados completos
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"ma_matrix_results_{timestamp}.csv"
    df_results.to_csv(filename, index=False)
    print(f"\n💾 Resultados guardados en: {filename}")
    
    print(f"✅ Test completado exitosamente!")

if __name__ == "__main__":
    main()