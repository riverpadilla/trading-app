from binance.client import Client
from binance.exceptions import BinanceAPIException
import os
import time

# Configura tus claves API Binance

# BINANCE_API_KEY para SPOT TESTNET
API_KEY = os.getenv('7ZPT9vq9NRD8rDcV87ykvrPWBPQzPuZ9QkLKLLxGguQaDvT5mACl4nQSP8uwGxBH')

# BINANCE_API_SECRETY para SPOT TESTNET
API_SECRET = os.getenv('SpCz5aKF9c16gpJec6EQ3r0BC4GAqjmTO1Bevh2193mvVEEdClpIhP2jx7Wf1QFO')

client = Client(API_KEY, API_SECRET)

symbol = 'BNBUSDT'
quantity = 11.1

# Parámetros iniciales
price_limit_1 = '1083'
stop_price_1 = '1088'
stop_limit_price_1 = '1088.5'

# Nuevos parámetros si el precio baja a 1084
price_limit_2 = '1082'
stop_price_2 = '1087'
stop_limit_price_2 = '1087.5'

def crear_orden_oco(price_limit, stop_price, stop_limit_price):
    try:
        order = client.create_oco_order(
            symbol=symbol,
            side=Client.SIDE_BUY,
            quantity=quantity,
            price=price_limit,
            stopPrice=stop_price,
            stopLimitPrice=stop_limit_price,
            stopLimitTimeInForce=Client.TIME_IN_FORCE_GTC
        )
        print(f"Orden OCO creada con price_limit {price_limit}, stopPrice {stop_price}, stopLimitPrice {stop_limit_price}")
        return order
    except BinanceAPIException as e:
        print(f"Error creando la orden OCO: {e}")
        return None

def cancelar_ordenes_oco(order_list_id):
    try:
        result = client.cancel_oco_order(symbol=symbol, orderListId=order_list_id)
        print("Orden OCO cancelada.")
        return result
    except BinanceAPIException as e:
        print(f"Error cancelando la orden OCO: {e}")
        return None

try:
    ticker = client.get_symbol_ticker(symbol=symbol)
    current_price = float(ticker['price'])

    if current_price < 1085:
        # Crear primera orden OCO
        orden_1 = crear_orden_oco(price_limit_1, stop_price_1, stop_limit_price_1)

        while True:
            time.sleep(5)  # Espera 5 segundos antes de revisar el precio de nuevo
            ticker = client.get_symbol_ticker(symbol=symbol)
            current_price = float(ticker['price'])
            print(f"Precio actual: {current_price}")

            if current_price <= 1084 and orden_1 is not None:
                # Cancelar la primera orden OCO
                cancelar_ordenes_oco(orden_1['orderListId'])

                # Crear la segunda orden OCO con nuevos precios
                crear_orden_oco(price_limit_2, stop_price_2, stop_limit_price_2)
                break
    else:
        print(f"Precio actual {current_price} no es menor a 1085, no se crea la orden.")

except BinanceAPIException as e:
    print(f"Error con la API de Binance: {e}")

