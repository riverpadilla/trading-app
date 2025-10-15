"""Interacciones básicas con la API de Binance Testnet para trading spot."""
import time
import hmac
import hashlib
import requests

API_KEY = '7ZPT9vq9NRD8rDcV87ykvrPWBPQzPuZ9QkLKLLxGguQaDvT5mACl4nQSP8uwGxBH'
API_SECRET = 'SpCz5aKF9c16gpJec6EQ3r0BC4GAqjmTO1Bevh2193mvVEEdClpIhP2jx7Wf1QFO'
BASE_URL = 'https://testnet.binance.vision/api'

def sign(params, secret):
    """_summary_ Firma los parámetros para las solicitudes autenticadas."""
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    return hmac.new(secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

def get_headers():
    """_summary_ Obtiene los encabezados necesarios para las solicitudes."""
    return {
        'X-MBX-APIKEY': API_KEY
    }

def get_account_info():
    """_summary_ Consulta y devuelve la información de la cuenta."""
    timestamp = int(time.time() * 1000)
    params = {
        'timestamp': timestamp
    }
    params['signature'] = sign(params, API_SECRET)
    url = f"{BASE_URL}/v3/account"
    response = requests.get(url, headers=get_headers(), params=params)
    return response.json()

def deposit(asset, amount):
    """_summary_ Incrementa el saldo de una moneda específica (solo en testnet)."""
    # La testnet de Binance no permite incrementar saldos directamente.
    # Puedes usar la API de faucet: https://testnet.binance.vision/faucet
    print("Para incrementar saldos, usa el faucet: https://testnet.binance.vision/faucet")

def create_order(symbol, side, quantity, price):
    """_summary_ Crea una orden spot."""
    timestamp = int(time.time() * 1000)
    params = {
        'symbol': symbol,
        'side': side,
        'type': 'LIMIT',
        'timeInForce': 'GTC',
        'quantity': quantity,
        'price': price,
        'timestamp': timestamp
    }
    params['signature'] = sign(params, API_SECRET)
    url = f"{BASE_URL}/v3/order"
    response = requests.post(url, headers=get_headers(), params=params)
    return response.json()

def cancel_order(symbol, orderId):
    """_summary_ Cancela una orden spot existente."""
    timestamp = int(time.time() * 1000)
    params = {
        'symbol': symbol,
        'orderId': orderId,
        'timestamp': timestamp
    }
    params['signature'] = sign(params, API_SECRET)
    url = f"{BASE_URL}/v3/order"
    response = requests.delete(url, headers=get_headers(), params=params)
    return response.json()

if __name__ == "__main__":
    # Consultar saldos
    print("Saldos:")
    print(get_account_info())

    # Incrementar saldos (solo posible con faucet en testnet)
    deposit('BTC', 1)

    # Crear orden spot
    order = create_order('BTCUSDT', 'BUY', 0.001, 30000)
    print("Orden creada:")
    print(order)

      # Cancelar orden spot
    if 'orderId' in order:
        cancel = cancel_order('BTCUSDT', order['orderId'])
        print("Orden cancelada:")
        print(cancel)
        