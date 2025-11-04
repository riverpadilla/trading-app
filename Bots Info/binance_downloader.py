"""
Script para descargar datos históricos de Binance
Este script descarga velas de 1 segundo y las guarda en CSV para backtesting
"""

import pandas as pd
from binance.client import Client
import datetime
import time
import os

def download_binance_data(symbol='BNBUSDT', interval='1s', num_candles=20000):
    """
    Descarga datos históricos de Binance
    
    Args:
        symbol: Par de trading (ej: 'BNBUSDT')
        interval: Intervalo de tiempo ('1s', '1m', '5m', etc.)
        num_candles: Número total de velas a descargar
    
    Returns:
        list: Lista de datos de velas
    """
    
    # Cliente público de Binance (no requiere API keys)
    client = Client()
    
    print(f"🚀 Iniciando descarga de {num_candles} velas de {interval} para {symbol}")
    print("-" * 60)
    
    all_data = []
    downloaded = 0
    batch_size = 1000  # Límite de Binance por request
    
    # Timestamp actual
    end_time = int(time.time() * 1000)
    
    while downloaded < num_candles:
        # Calcular cuántas velas necesitamos en este batch
        remaining = num_candles - downloaded
        limit = min(batch_size, remaining)
        
        try:
            print(f"📥 Descargando batch: {limit} velas (Total: {downloaded}/{num_candles})")
            
            # Solicitar datos a Binance
            klines = client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit,
                endTime=end_time
            )
            
            if not klines:
                print("⚠️  No hay más datos disponibles")
                break
            
            # Agregar a la lista principal
            all_data.extend(klines)
            downloaded += len(klines)
            
            # Actualizar end_time para el siguiente batch
            end_time = klines[0][0] - 1  # Usar el timestamp de la primera vela
            
            print(f"✅ Descargadas {len(klines)} velas. Progreso: {downloaded}/{num_candles}")
            
            # Pausa para evitar rate limiting
            time.sleep(0.2)
            
        except Exception as e:
            print(f"❌ Error en la descarga: {e}")
            break
    
    print(f"\n🎉 Descarga completada! Total de velas: {len(all_data)}")
    return all_data

def process_and_save_data(klines_data, symbol, interval):
    """
    Procesa los datos y los guarda en CSV
    
    Args:
        klines_data: Datos de velas de Binance
        symbol: Símbolo del par
        interval: Intervalo de tiempo
    
    Returns:
        tuple: (nombre_archivo, dataframe)
    """
    
    print("\n📊 Procesando datos...")
    
    # Crear DataFrame con nombres de columnas descriptivos
    columns = [
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades_count',
        'taker_buy_volume', 'taker_buy_quote_volume', 'ignore'
    ]
    
    df = pd.DataFrame(klines_data, columns=columns)
    
    # Convertir a tipos numéricos
    price_volume_cols = ['open', 'high', 'low', 'close', 'volume', 
                        'quote_volume', 'taker_buy_volume', 'taker_buy_quote_volume']
    
    for col in price_volume_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df['trades_count'] = pd.to_numeric(df['trades_count'], errors='coerce')
    
    # Convertir timestamps a datetime
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['close_datetime'] = pd.to_datetime(df['close_time'], unit='ms')
    
    # Ordenar por tiempo
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Remover columnas innecesarias para backtesting
    df_clean = df[['datetime', 'open', 'high', 'low', 'close', 'volume', 'trades_count']].copy()
    
    # Crear nombre de archivo
    now = datetime.datetime.now()
    filename = f"binance_{symbol}_{interval}_{now.strftime('%Y%m%d_%H%M%S')}.csv"
    
    # Guardar CSV
    df_clean.to_csv(filename, index=False)
    
    # Mostrar estadísticas
    print(f"\n📁 Archivo guardado: {filename}")
    print(f"📅 Período: {df_clean['datetime'].min()} a {df_clean['datetime'].max()}")
    print(f"📈 Registros: {len(df_clean):,}")
    print(f"💰 Rango de precios: ${df_clean['low'].min():.8f} - ${df_clean['high'].max():.8f}")
    print(f"📊 Precio final: ${df_clean['close'].iloc[-1]:.8f}")
    print(f"🔄 Volumen total: {df_clean['volume'].sum():,.2f}")
    
    return filename, df_clean

def show_data_sample(df, n=5):
    """Muestra una muestra de los datos"""
    print(f"\n📋 Primeras {n} filas del dataset:")
    print("-" * 80)
    display_cols = ['datetime', 'open', 'high', 'low', 'close', 'volume']
    print(df[display_cols].head(n).to_string(index=False))
    
    print(f"\n📋 Últimas {n} filas del dataset:")
    print("-" * 80)
    print(df[display_cols].tail(n).to_string(index=False))

def select_interval():
    """Permite seleccionar el intervalo de tiempo"""
    intervals = {
        '1': ('1s', '1 segundo'),
        '2': ('1m', '1 minuto'),
        '3': ('5m', '5 minutos'),
        '4': ('15m', '15 minutos'),
        '5': ('1h', '1 hora'),
        '6': ('4h', '4 horas')
    }
    
    print("\n⏱️  SELECCIONAR INTERVALO DE TIEMPO:")
    print("-" * 40)
    for key, (interval, description) in intervals.items():
        print(f"{key}. {description} ({interval})")
    print("-" * 40)
    
    while True:
        choice = input("Selecciona una opción (1-6): ").strip()
        if choice in intervals:
            selected_interval, description = intervals[choice]
            print(f"✅ Seleccionado: {description} ({selected_interval})")
            return selected_interval
        else:
            print("❌ Opción inválida. Por favor selecciona 1-6.")

def select_num_candles():
    """Permite seleccionar el número de velas"""
    candle_options = {
        '1': 10000,
        '2': 20000,
        '3': 30000,
        '4': 40000,
        '5': 50000,
        '6': 60000,
        '7': 70000,
        '8': 80000,
        '9': 90000,
        '10': 100000
    }
    
    print("\n📊 SELECCIONAR NÚMERO DE VELAS:")
    print("-" * 40)
    for key, num_candles in candle_options.items():
        print(f"{key:2}. {num_candles:,} velas")
    print("-" * 40)
    
    while True:
        choice = input("Selecciona una opción (1-10): ").strip()
        if choice in candle_options:
            selected_candles = candle_options[choice]
            print(f"✅ Seleccionado: {selected_candles:,} velas")
            return selected_candles
        else:
            print("❌ Opción inválida. Por favor selecciona 1-10.")

def estimate_download_time(interval, num_candles):
    """Estima el tiempo de descarga basado en el intervalo y número de velas"""
    # Estimaciones aproximadas basadas en el número de requests necesarios
    batch_size = 1000
    num_batches = (num_candles + batch_size - 1) // batch_size
    
    # Tiempo base por batch (incluye rate limiting)
    base_time_per_batch = 0.3  # segundos
    
    # Factor de ajuste según el intervalo (más datos = más tiempo)
    interval_factors = {
        '1s': 1.0,
        '1m': 0.8,
        '5m': 0.6,
        '15m': 0.5,
        '1h': 0.4,
        '4h': 0.3
    }
    
    factor = interval_factors.get(interval, 1.0)
    estimated_time = num_batches * base_time_per_batch * factor
    
    return estimated_time

def main():
    """Función principal"""
    
    print("=" * 60)
    print("🏦 DESCARGADOR DE DATOS DE BINANCE")
    print("=" * 60)
    print("🎯 Símbolo: BNBUSDT (fijo)")
    print("⚙️  Configuración interactiva habilitada")
    print("=" * 60)
    
    # Configuración interactiva
    SYMBOL = 'BNBUSDT'  # Par de trading (fijo)
    
    # Seleccionar intervalo
    INTERVAL = select_interval()
    
    # Seleccionar número de velas
    NUM_CANDLES = select_num_candles()
    
    # Mostrar estimación de tiempo
    estimated_time = estimate_download_time(INTERVAL, NUM_CANDLES)
    
    print(f"\n📋 RESUMEN DE CONFIGURACIÓN:")
    print("-" * 40)
    print(f"🎯 Símbolo: {SYMBOL}")
    print(f"⏱️  Intervalo: {INTERVAL}")
    print(f"📊 Cantidad: {NUM_CANDLES:,} velas")
    print(f"⏳ Tiempo estimado: ~{estimated_time:.1f} segundos")
    print("-" * 40)
    
    # Confirmación
    confirm = input("\n¿Proceder con la descarga? (s/n): ").strip().lower()
    if confirm not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Descarga cancelada.")
        return
    
    print("\n🚀 Iniciando descarga...")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Paso 1: Descargar datos
        klines_data = download_binance_data(SYMBOL, INTERVAL, NUM_CANDLES)
        
        if not klines_data:
            print("❌ No se pudieron descargar datos")
            return
        
        # Paso 2: Procesar y guardar
        filename, df = process_and_save_data(klines_data, SYMBOL, INTERVAL)
        
        # Paso 3: Mostrar muestra
        show_data_sample(df)
        
        # Tiempo total
        elapsed = time.time() - start_time
        print(f"\n⏱️  Tiempo total: {elapsed:.2f} segundos")
        print(f"📁 Archivo guardado: {filename}")
        print(f"🎯 ¡Listo para backtesting!")
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()