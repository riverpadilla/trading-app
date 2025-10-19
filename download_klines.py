import pandas as pd
from binance.client import Client
import datetime
import time
import os

def download_klines_data(symbol='BNBUSDT', interval='1s', limit=20000):
    """
    Descarga datos de velas (klines) desde Binance API
    
    Parameters:
    - symbol: Par de trading (ej: 'BTCUSDT', 'BNBUSDT')
    - interval: Intervalo de tiempo ('1s', '1m', '5m', etc.)
    - limit: Número de velas a descargar (máximo 1000 por request)
    """
    
    # Inicializar cliente de Binance (no requiere API keys para datos públicos)
    client = Client()
    
    print(f"Descargando {limit} velas de {interval} para {symbol}...")
    
    all_klines = []
    total_downloaded = 0
    
    # Binance API limita a 1000 velas por request
    batch_size = 1000
    
    # Calcular número de batches necesarios
    num_batches = (limit + batch_size - 1) // batch_size
    
    # Obtener timestamp actual
    end_time = int(time.time() * 1000)
    
    for batch in range(num_batches):
        try:
            # Calcular cuántas velas necesitamos en este batch
            current_limit = min(batch_size, limit - total_downloaded)
            
            print(f"Descargando batch {batch + 1}/{num_batches} ({current_limit} velas)...")
            
            # Descargar klines
            klines = client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=current_limit,
                endTime=end_time
            )
            
            if not klines:
                print("No se encontraron más datos")
                break
            
            all_klines.extend(klines)
            total_downloaded += len(klines)
            
            # Actualizar end_time para el siguiente batch (usar el timestamp de la primera vela del batch actual)
            end_time = klines[0][0] - 1
            
            print(f"Descargadas {len(klines)} velas. Total: {total_downloaded}")
            
            # Pequeña pausa para evitar rate limiting
            time.sleep(0.1)
            
            if total_downloaded >= limit:
                break
                
        except Exception as e:
            print(f"Error descargando batch {batch + 1}: {e}")
            break
    
    print(f"Descarga completada. Total de velas: {len(all_klines)}")
    return all_klines

def save_to_csv(klines_data, symbol='BTCUSDT', interval='1s'):
    """
    Guarda los datos de klines en un archivo CSV
    """
    
    # Convertir a DataFrame
    df = pd.DataFrame(klines_data, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    
    # Convertir tipos de datos
    numeric_columns = ['open', 'high', 'low', 'close', 'volume', 
                      'quote_asset_volume', 'number_of_trades',
                      'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume']
    
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Convertir timestamps a datetime
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
    
    # Ordenar por tiempo (más antiguo primero)
    df = df.sort_values('open_time')
    
    # Crear nombre del archivo
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"klines_{symbol}_{interval}_{timestamp}.csv"
    
    # Guardar CSV
    df.to_csv(filename, index=False)
    
    print(f"Datos guardados en: {filename}")
    print(f"Período de datos: {df['open_time'].min()} a {df['open_time'].max()}")
    print(f"Número de registros: {len(df)}")
    
    # Mostrar estadísticas básicas
    print("\nEstadísticas básicas:")
    print(f"Precio mínimo: ${df['low'].min():.8f}")
    print(f"Precio máximo: ${df['high'].max():.8f}")
    print(f"Precio de cierre final: ${df['close'].iloc[-1]:.8f}")
    print(f"Volumen total: {df['volume'].sum():.2f} {symbol.replace('USDT', '')}")
    
    return filename, df

def main():
    """
    Función principal
    """
    # Configuración
    SYMBOL = 'BTCUSDT'  # Cambiar por el par deseado
    INTERVAL = '1s'     # Intervalo de 1 segundo
    LIMIT = 20000       # Número de velas a descargar
    
    print("=== Descargador de Datos de Binance ===")
    print(f"Símbolo: {SYMBOL}")
    print(f"Intervalo: {INTERVAL}")
    print(f"Cantidad: {LIMIT} velas")
    print("=" * 40)
    
    try:
        # Descargar datos
        klines_data = download_klines_data(
            symbol=SYMBOL, 
            interval=INTERVAL, 
            limit=LIMIT
        )
        
        if klines_data:
            # Guardar en CSV
            filename, df = save_to_csv(klines_data, SYMBOL, INTERVAL)
            
            print(f"\n✅ Descarga exitosa!")
            print(f"📁 Archivo: {filename}")
            print(f"📊 {len(df)} velas guardadas")
            
            # Mostrar las primeras 5 filas
            print("\nPrimeras 5 filas del dataset:")
            print(df[['open_time', 'open', 'high', 'low', 'close', 'volume']].head())
            
        else:
            print("❌ No se pudieron descargar datos")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()