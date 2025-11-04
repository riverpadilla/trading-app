"""Interacciones optimizadas con la API de Binance Testnet usando python-binance."""
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
import json

# Configuración para testnet
API_KEY = '7ZPT9vq9NRD8rDcV87ykvrPWBPQzPuZ9QkLKLLxGguQaDvT5mACl4nQSP8uwGxBH'
API_SECRET = 'SpCz5aKF9c16gpJec6EQ3r0BC4GAqjmTO1Bevh2193mvVEEdClpIhP2jx7Wf1QFO'

# Crear cliente para testnet
client = Client(API_KEY, API_SECRET, testnet=True)

def get_account_info():
    """Consulta y devuelve la información de la cuenta."""
    try:
        account = client.get_account()
        return account
    except BinanceAPIException as e:
        print(f"Error al obtener información de cuenta: {e}")
        return None

def get_balances():
    """Obtiene solo los saldos con balance > 0."""
    try:
        account = client.get_account()
        balances = []
        for balance in account['balances']:
            if float(balance['free']) > 0 or float(balance['locked']) > 0:
                balances.append({
                    'asset': balance['asset'],
                    'free': balance['free'],
                    'locked': balance['locked']
                })
        return balances
    except BinanceAPIException as e:
        print(f"Error al obtener saldos: {e}")
        return []

def get_symbol_info(symbol):
    """Obtiene información del símbolo (precio, filtros, etc.)."""
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        exchange_info = client.get_exchange_info()
        
        symbol_info = None
        for s in exchange_info['symbols']:
            if s['symbol'] == symbol:
                symbol_info = s
                break
        
        return {
            'price': ticker['price'],
            'symbol_info': symbol_info
        }
    except BinanceAPIException as e:
        print(f"Error al obtener información del símbolo: {e}")
        return None

def create_buy_order(symbol, quantity, price=None):
    """Crea una orden de compra (market o limit)."""
    try:
        if price is None:
            # Orden market
            order = client.order_market_buy(
                symbol=symbol,
                quantity=quantity
            )
        else:
            # Orden limit
            order = client.order_limit_buy(
                symbol=symbol,
                quantity=quantity,
                price=str(price)
            )
        return order
    except BinanceOrderException as e:
        print(f"Error en la orden: {e}")
        return None
    except BinanceAPIException as e:
        print(f"Error de API: {e}")
        return None

def create_sell_order(symbol, quantity, price=None):
    """Crea una orden de venta (market o limit)."""
    try:
        if price is None:
            # Orden market
            order = client.order_market_sell(
                symbol=symbol,
                quantity=quantity
            )
        else:
            # Orden limit
            order = client.order_limit_sell(
                symbol=symbol,
                quantity=quantity,
                price=str(price)
            )
        return order
    except BinanceOrderException as e:
        print(f"Error en la orden: {e}")
        return None
    except BinanceAPIException as e:
        print(f"Error de API: {e}")
        return None

def cancel_order(symbol, order_id):
    """Cancela una orden existente."""
    try:
        result = client.cancel_order(
            symbol=symbol,
            orderId=order_id
        )
        return result
    except BinanceAPIException as e:
        print(f"Error al cancelar orden: {e}")
        return None

def get_open_orders(symbol=None):
    """Obtiene todas las órdenes abiertas o de un símbolo específico."""
    try:
        orders = client.get_open_orders(symbol=symbol)
        return orders
    except BinanceAPIException as e:
        print(f"Error al obtener órdenes abiertas: {e}")
        return []

def get_order_status(symbol, order_id):
    """Consulta el estado de una orden específica."""
    try:
        order = client.get_order(
            symbol=symbol,
            orderId=order_id
        )
        return order
    except BinanceAPIException as e:
        print(f"Error al consultar orden: {e}")
        return None

def get_recent_trades(symbol, limit=500):
    """Obtiene las transacciones recientes de la cuenta."""
    try:
        trades = client.get_my_trades(symbol=symbol, limit=limit)
        return trades
    except BinanceAPIException as e:
        print(f"Error al obtener trades: {e}")
        return []

def get_klines(symbol, interval='1h', limit=100):
    """Obtiene datos de velas (candlestick)."""
    try:
        klines = client.get_klines(
            symbol=symbol,
            interval=interval,
            limit=limit
        )
        return klines
    except BinanceAPIException as e:
        print(f"Error al obtener klines: {e}")
        return []

def pretty_print(data):
    """Imprime datos en formato JSON legible."""
    print(json.dumps(data, indent=2, default=str))

if __name__ == "__main__":
    print("=== INFORMACIÓN DE CUENTA ===")
    account_info = get_account_info()
    if account_info:
        print(f"Tipo de cuenta: {account_info.get('accountType')}")
        print(f"Comisiones maker: {account_info.get('makerCommission')}")
        print(f"Comisiones taker: {account_info.get('takerCommission')}")
    
    print("\n=== SALDOS DISPONIBLES ===")
    balances = get_balances()
    for balance in balances:
        print(f"{balance['asset']}: {balance['free']} (libre) + {balance['locked']} (bloqueado)")
    
    print("\n=== INFORMACIÓN DE SÍMBOLO (BTCUSDT) ===")
    symbol_info = get_symbol_info('BTCUSDT')
    if symbol_info:
        print(f"Precio actual: {symbol_info['price']}")
    
    print("\n=== ÓRDENES ABIERTAS ===")
    open_orders = get_open_orders()
    print(f"Órdenes abiertas: {len(open_orders)}")
    for order in open_orders[:5]:  # Mostrar solo las primeras 5
        print(f"- {order['symbol']} {order['side']} {order['origQty']} @ {order['price']}")
    
    print("\n=== EJEMPLO DE ORDEN LIMIT ===")
    # Crear una orden de compra con precio bajo (no se ejecutará)
    order = create_buy_order('BTCUSDT', '0.001', '30000')
    if order:
        print("Orden creada exitosamente:")
        pretty_print(order)
        
        # Cancelar la orden inmediatamente
        print("\n=== CANCELANDO ORDEN ===")
        cancel_result = cancel_order('BTCUSDT', order['orderId'])
        if cancel_result:
            print("Orden cancelada exitosamente:")
            pretty_print(cancel_result)