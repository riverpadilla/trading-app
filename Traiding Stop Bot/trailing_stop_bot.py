"""
Bot de Trading con Trailing Stop Market
Inicia vendiendo BNB y alterna entre órdenes de compra/venta con trailing stop
"""
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
import time
import logging
from datetime import datetime
from decimal import Decimal, ROUND_DOWN
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class TrailingStopBot:
    def __init__(self, api_key, api_secret, testnet=True):
        """Inicializa el bot de trading."""
        self.client = Client(api_key, api_secret, testnet=testnet)
        self.symbol = "BNBUSDT"
        self.is_running = False
        self.current_state = "IDLE"  # IDLE, SELLING, WAITING_BUY, BUYING, WAITING_SELL
        self.thread = None
        
        # Parámetros configurables
        self.initial_bnb_quantity = 0.0
        self.stop_loss_percent = 2.0  # % para stop loss fijo (limitar pérdidas)
        self.trailing_percent_buy = 1.0  # % para trailing stop dinámico de compra
        self.trailing_percent_sell = 1.0  # % para trailing stop dinámico de venta
        
        # Tracking de precios para trailing dinámico
        self.buy_entry_price = 0.0  # Precio al que se compró
        self.sell_entry_price = 0.0  # Precio al que se vendió
        self.highest_price_since_buy = 0.0  # Precio más alto desde la compra
        self.lowest_price_since_sell = 0.0  # Precio más bajo desde la venta
        
        # Stop loss y trailing stop IDs
        self.stop_loss_order_id = None
        self.trailing_stop_order_id = None
        
        # Tracking de operaciones
        self.initial_usdt_balance = 0.0
        self.current_usdt_balance = 0.0
        self.current_bnb_balance = 0.0
        self.sell_proceeds = 0.0  # USDT obtenido de la venta inicial
        self.total_trades = 0
        self.successful_trades = 0
        self.failed_trades = 0
        self.trade_history = []
        
        # P&L tracking
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0
        self.total_pnl = 0.0
        
        # Última orden
        self.last_order_id = None
        self.last_buy_price = 0.0
        self.last_sell_price = 0.0
        
    def get_symbol_info(self):
        """Obtiene información del símbolo y filtros."""
        try:
            info = self.client.get_symbol_info(self.symbol)
            filters = {f['filterType']: f for f in info['filters']}
            return {
                'status': info['status'],
                'stepSize': float(filters['LOT_SIZE']['stepSize']),
                'minQty': float(filters['LOT_SIZE']['minQty']),
                'maxQty': float(filters['LOT_SIZE']['maxQty']),
                'tickSize': float(filters['PRICE_FILTER']['tickSize']),
                'minPrice': float(filters['PRICE_FILTER']['minPrice']),
                'maxPrice': float(filters['PRICE_FILTER']['maxPrice']),
            }
        except Exception as e:
            logging.error(f"Error obteniendo info del símbolo: {e}")
            return None
    
    def format_quantity(self, quantity, step_size):
        """Formatea la cantidad según el step_size."""
        precision = len(str(step_size).split('.')[-1].rstrip('0'))
        return float(Decimal(str(quantity)).quantize(
            Decimal(str(step_size)), 
            rounding=ROUND_DOWN
        ))
    
    def format_price(self, price, tick_size):
        """Formatea el precio según el tick_size."""
        precision = len(str(tick_size).split('.')[-1].rstrip('0'))
        return float(Decimal(str(price)).quantize(
            Decimal(str(tick_size)), 
            rounding=ROUND_DOWN
        ))
    
    def get_current_price(self):
        """Obtiene el precio actual del símbolo."""
        try:
            ticker = self.client.get_symbol_ticker(symbol=self.symbol)
            return float(ticker['price'])
        except Exception as e:
            logging.error(f"Error obteniendo precio: {e}")
            return None
    
    def get_balances(self):
        """Obtiene los balances de BNB y USDT."""
        try:
            account = self.client.get_account()
            balances = {}
            for balance in account['balances']:
                if balance['asset'] in ['BNB', 'USDT']:
                    balances[balance['asset']] = {
                        'free': float(balance['free']),
                        'locked': float(balance['locked'])
                    }
            return balances
        except Exception as e:
            logging.error(f"Error obteniendo balances: {e}")
            return None
    
    def initial_sell(self):
        """Ejecuta la venta inicial de BNB."""
        try:
            logging.info(f"=== Iniciando venta de {self.initial_bnb_quantity} BNB ===")
            self.current_state = "SELLING"
            
            # Obtener info del símbolo
            symbol_info = self.get_symbol_info()
            if not symbol_info:
                raise Exception("No se pudo obtener información del símbolo")
            
            # Formatear cantidad
            quantity = self.format_quantity(
                self.initial_bnb_quantity, 
                symbol_info['stepSize']
            )
            
            # Ejecutar orden de venta market
            order = self.client.order_market_sell(
                symbol=self.symbol,
                quantity=quantity
            )
            
            logging.info(f"Orden de venta ejecutada: {order['orderId']}")
            self.last_order_id = order['orderId']
            self.total_trades += 1
            
            # Esperar a que se complete
            time.sleep(2)
            
            # Verificar orden
            order_status = self.client.get_order(
                symbol=self.symbol,
                orderId=order['orderId']
            )
            
            if order_status['status'] == 'FILLED':
                self.successful_trades += 1
                executed_qty = float(order_status['executedQty'])
                cumulative_quote = float(order_status['cummulativeQuoteQty'])
                avg_price = cumulative_quote / executed_qty if executed_qty > 0 else 0
                
                self.sell_proceeds = cumulative_quote
                self.last_sell_price = avg_price
                self.initial_usdt_balance = cumulative_quote
                self.current_usdt_balance = cumulative_quote
                
                logging.info(f"✓ Venta completada: {executed_qty} BNB a ${avg_price:.2f}")
                logging.info(f"✓ USDT obtenido: ${cumulative_quote:.2f}")
                
                # Registrar en historial
                self.trade_history.append({
                    'timestamp': datetime.now(),
                    'type': 'SELL',
                    'quantity': executed_qty,
                    'price': avg_price,
                    'total': cumulative_quote,
                    'order_id': order['orderId']
                })
                
                return True
            else:
                logging.error(f"Orden de venta no completada: {order_status['status']}")
                self.failed_trades += 1
                return False
                
        except Exception as e:
            logging.error(f"Error en venta inicial: {e}")
            self.failed_trades += 1
            self.current_state = "IDLE"
            return False
    
    def create_stop_loss_buy(self, quantity, entry_price):
        """Crea un stop loss FIJO para proteger en caso de pérdida (para posición en USDT esperando comprar)."""
        try:
            symbol_info = self.get_symbol_info()
            
            # Stop loss para COMPRA: si el precio SUBE más del stop_loss_percent, comprar para no perder más
            stop_loss_price = entry_price * (1 + self.stop_loss_percent / 100)
            stop_loss_price = self.format_price(stop_loss_price, symbol_info['tickSize'])
            
            limit_price = stop_loss_price * 1.002
            limit_price = self.format_price(limit_price, symbol_info['tickSize'])
            
            logging.info(f"🛡️ Stop Loss FIJO para compra: ${stop_loss_price:.2f}")
            
            order = self.client.create_order(
                symbol=self.symbol,
                side='BUY',
                type='STOP_LOSS_LIMIT',
                timeInForce='GTC',
                quantity=quantity,
                price=str(limit_price),
                stopPrice=str(stop_loss_price)
            )
            
            self.stop_loss_order_id = order['orderId']
            logging.info(f"✓ Stop Loss BUY creado: {order['orderId']}")
            return order['orderId']
            
        except Exception as e:
            logging.error(f"Error creando stop loss buy: {e}")
            return None
    
    def create_trailing_stop_buy(self, quantity, initial_price):
        """Crea trailing stop DINÁMICO para compra (se actualiza con el precio más bajo)."""
        try:
            symbol_info = self.get_symbol_info()
            
            # Trailing stop inicial: comprar si sube trailing% desde el precio actual
            trailing_price = initial_price * (1 + self.trailing_percent_buy / 100)
            trailing_price = self.format_price(trailing_price, symbol_info['tickSize'])
            
            limit_price = trailing_price * 1.001
            limit_price = self.format_price(limit_price, symbol_info['tickSize'])
            
            logging.info(f"📈 Trailing Stop DINÁMICO para compra: ${trailing_price:.2f}")
            
            order = self.client.create_order(
                symbol=self.symbol,
                side='BUY',
                type='STOP_LOSS_LIMIT',
                timeInForce='GTC',
                quantity=quantity,
                price=str(limit_price),
                stopPrice=str(trailing_price)
            )
            
            self.trailing_stop_order_id = order['orderId']
            logging.info(f"✓ Trailing Stop BUY creado: {order['orderId']}")
            return order['orderId']
            
        except Exception as e:
            logging.error(f"Error creando trailing stop buy: {e}")
            return None
    
    def setup_buy_orders(self):
        """Configura las órdenes de compra: stop loss fijo + trailing stop dinámico."""
        try:
            logging.info("=== Configurando órdenes de COMPRA ===")
            self.current_state = "WAITING_BUY"
            
            # Calcular cantidad a comprar
            current_price = self.get_current_price()
            if not current_price:
                raise Exception("No se pudo obtener precio actual")
            
            usdt_to_spend = self.sell_proceeds * 0.995
            estimated_bnb = usdt_to_spend / current_price
            
            symbol_info = self.get_symbol_info()
            # Dividir en dos órdenes: 50% para stop loss, 50% para trailing
            quantity_per_order = self.format_quantity(estimated_bnb / 2, symbol_info['stepSize'])
            
            logging.info(f"Precio actual: ${current_price:.2f}")
            logging.info(f"USDT disponible: ${usdt_to_spend:.2f}")
            logging.info(f"Cantidad por orden: {quantity_per_order} BNB")
            logging.info(f"Stop Loss: {self.stop_loss_percent}% | Trailing: {self.trailing_percent_buy}%")
            
            # Guardar precio de entrada
            self.sell_entry_price = current_price
            self.lowest_price_since_sell = current_price
            
            # Crear stop loss fijo
            self.create_stop_loss_buy(quantity_per_order, current_price)
            
            # Crear trailing stop dinámico
            self.create_trailing_stop_buy(quantity_per_order, current_price)
            
            return True
            
        except Exception as e:
            logging.error(f"Error configurando órdenes de compra: {e}")
            return False
    
    def create_stop_loss_sell(self, quantity, entry_price):
        """Crea un stop loss FIJO para proteger en caso de pérdida (para posición en BNB)."""
        try:
            symbol_info = self.get_symbol_info()
            
            # Stop loss para VENTA: si el precio BAJA más del stop_loss_percent, vender para no perder más
            stop_loss_price = entry_price * (1 - self.stop_loss_percent / 100)
            stop_loss_price = self.format_price(stop_loss_price, symbol_info['tickSize'])
            
            limit_price = stop_loss_price * 0.998
            limit_price = self.format_price(limit_price, symbol_info['tickSize'])
            
            logging.info(f"🛡️ Stop Loss FIJO para venta: ${stop_loss_price:.2f}")
            
            order = self.client.create_order(
                symbol=self.symbol,
                side='SELL',
                type='STOP_LOSS_LIMIT',
                timeInForce='GTC',
                quantity=quantity,
                price=str(limit_price),
                stopPrice=str(stop_loss_price)
            )
            
            self.stop_loss_order_id = order['orderId']
            logging.info(f"✓ Stop Loss SELL creado: {order['orderId']}")
            return order['orderId']
            
        except Exception as e:
            logging.error(f"Error creando stop loss sell: {e}")
            return None
    
    def create_trailing_stop_sell(self, quantity, initial_price):
        """Crea trailing stop DINÁMICO para venta (se actualiza con el precio más alto)."""
        try:
            symbol_info = self.get_symbol_info()
            
            # Trailing stop inicial: vender si baja trailing% desde el precio actual
            trailing_price = initial_price * (1 - self.trailing_percent_sell / 100)
            trailing_price = self.format_price(trailing_price, symbol_info['tickSize'])
            
            limit_price = trailing_price * 0.999
            limit_price = self.format_price(limit_price, symbol_info['tickSize'])
            
            logging.info(f"📉 Trailing Stop DINÁMICO para venta: ${trailing_price:.2f}")
            
            order = self.client.create_order(
                symbol=self.symbol,
                side='SELL',
                type='STOP_LOSS_LIMIT',
                timeInForce='GTC',
                quantity=quantity,
                price=str(limit_price),
                stopPrice=str(trailing_price)
            )
            
            self.trailing_stop_order_id = order['orderId']
            logging.info(f"✓ Trailing Stop SELL creado: {order['orderId']}")
            return order['orderId']
            
        except Exception as e:
            logging.error(f"Error creando trailing stop sell: {e}")
            return None
    
    def setup_sell_orders(self):
        """Configura las órdenes de venta: stop loss fijo + trailing stop dinámico."""
        try:
            logging.info("=== Configurando órdenes de VENTA ===")
            self.current_state = "WAITING_SELL"
            
            # Obtener balance de BNB
            balances = self.get_balances()
            if not balances or 'BNB' not in balances:
                raise Exception("No se pudo obtener balance de BNB")
            
            bnb_balance = balances['BNB']['free']
            current_price = self.get_current_price()
            
            symbol_info = self.get_symbol_info()
            # Dividir en dos órdenes: 50% para stop loss, 50% para trailing
            quantity_per_order = self.format_quantity(bnb_balance * 0.499, symbol_info['stepSize'])
            
            logging.info(f"Precio actual: ${current_price:.2f}")
            logging.info(f"BNB disponible: {bnb_balance:.4f}")
            logging.info(f"Cantidad por orden: {quantity_per_order} BNB")
            logging.info(f"Stop Loss: {self.stop_loss_percent}% | Trailing: {self.trailing_percent_sell}%")
            
            # Guardar precio de entrada
            self.buy_entry_price = current_price
            self.highest_price_since_buy = current_price
            
            # Crear stop loss fijo
            self.create_stop_loss_sell(quantity_per_order, current_price)
            
            # Crear trailing stop dinámico
            self.create_trailing_stop_sell(quantity_per_order, current_price)
            
            return True
            
        except Exception as e:
            logging.error(f"Error configurando órdenes de venta: {e}")
            return False
    
    def update_trailing_stop_buy(self, current_price):
        """Actualiza el trailing stop de compra si el precio baja (nuevo mínimo)."""
        try:
            # Si el precio actual es menor que el mínimo registrado
            if current_price < self.lowest_price_since_sell:
                self.lowest_price_since_sell = current_price
                
                # Cancelar trailing stop anterior
                if self.trailing_stop_order_id:
                    try:
                        self.client.cancel_order(
                            symbol=self.symbol,
                            orderId=self.trailing_stop_order_id
                        )
                        logging.info(f"🔄 Trailing stop anterior cancelado")
                    except:
                        pass
                
                # Obtener cantidad de la orden
                balances = self.get_balances()
                usdt_balance = balances.get('USDT', {}).get('free', 0)
                estimated_bnb = (usdt_balance * 0.5) / current_price
                
                symbol_info = self.get_symbol_info()
                quantity = self.format_quantity(estimated_bnb, symbol_info['stepSize'])
                
                # Crear nuevo trailing stop en el nuevo nivel
                new_trailing_order = self.create_trailing_stop_buy(quantity, current_price)
                
                if new_trailing_order:
                    logging.info(f"✅ Trailing stop actualizado en ${current_price:.2f}")
                    
        except Exception as e:
            logging.error(f"Error actualizando trailing stop buy: {e}")
    
    def update_trailing_stop_sell(self, current_price):
        """Actualiza el trailing stop de venta si el precio sube (nuevo máximo)."""
        try:
            # Si el precio actual es mayor que el máximo registrado
            if current_price > self.highest_price_since_buy:
                self.highest_price_since_buy = current_price
                
                # Cancelar trailing stop anterior
                if self.trailing_stop_order_id:
                    try:
                        self.client.cancel_order(
                            symbol=self.symbol,
                            orderId=self.trailing_stop_order_id
                        )
                        logging.info(f"🔄 Trailing stop anterior cancelado")
                    except:
                        pass
                
                # Obtener cantidad de BNB
                balances = self.get_balances()
                bnb_balance = balances.get('BNB', {}).get('free', 0)
                
                symbol_info = self.get_symbol_info()
                quantity = self.format_quantity(bnb_balance * 0.5, symbol_info['stepSize'])
                
                # Crear nuevo trailing stop en el nuevo nivel
                new_trailing_order = self.create_trailing_stop_sell(quantity, current_price)
                
                if new_trailing_order:
                    logging.info(f"✅ Trailing stop actualizado en ${current_price:.2f}")
                    
        except Exception as e:
            logging.error(f"Error actualizando trailing stop sell: {e}")
    
    def check_order_status(self, order_id):
        """Verifica el estado de una orden."""
        try:
            order = self.client.get_order(
                symbol=self.symbol,
                orderId=order_id
            )
            return order
        except Exception as e:
            logging.error(f"Error verificando orden: {e}")
            return None
    
    def update_pnl(self):
        """Actualiza el cálculo de P&L."""
        try:
            balances = self.get_balances()
            if not balances:
                return
            
            current_price = self.get_current_price()
            if not current_price:
                return
            
            # Balance actual en USDT
            usdt_balance = balances.get('USDT', {}).get('free', 0)
            bnb_balance = balances.get('BNB', {}).get('free', 0)
            
            # Valor total actual
            total_value = usdt_balance + (bnb_balance * current_price)
            
            # P&L realizado (basado en el balance inicial)
            if self.initial_usdt_balance > 0:
                self.realized_pnl = usdt_balance - self.initial_usdt_balance
                self.total_pnl = total_value - self.initial_usdt_balance
                self.unrealized_pnl = self.total_pnl - self.realized_pnl
            
            self.current_usdt_balance = usdt_balance
            self.current_bnb_balance = bnb_balance
            
        except Exception as e:
            logging.error(f"Error actualizando P&L: {e}")
    
    def monitor_orders(self):
        """Monitorea las órdenes y ejecuta el ciclo de trading."""
        logging.info("Iniciando monitoreo de órdenes...")
        
        while self.is_running:
            try:
                # Obtener precio actual para actualizar trailing stops
                current_price = self.get_current_price()
                
                if self.current_state == "WAITING_BUY":
                    # Actualizar trailing stop si el precio baja (nuevo mínimo)
                    if current_price and self.trailing_stop_order_id:
                        self.update_trailing_stop_buy(current_price)
                    
                    # Verificar si alguna orden se completó (stop loss o trailing)
                    orders_to_check = []
                    if self.stop_loss_order_id:
                        orders_to_check.append(self.stop_loss_order_id)
                    if self.trailing_stop_order_id:
                        orders_to_check.append(self.trailing_stop_order_id)
                    
                    for order_id in orders_to_check:
                        order = self.check_order_status(order_id)
                        
                        if order and order['status'] == 'FILLED':
                            self.current_state = "BUYING"
                            executed_qty = float(order['executedQty'])
                            cumulative_quote = float(order['cummulativeQuoteQty'])
                            avg_price = cumulative_quote / executed_qty if executed_qty > 0 else 0
                            
                            self.last_buy_price = avg_price
                            self.successful_trades += 1
                            
                            order_type = "🛡️ STOP LOSS" if order_id == self.stop_loss_order_id else "📈 TRAILING STOP"
                            logging.info(f"✓ COMPRA completada ({order_type}): {executed_qty} BNB a ${avg_price:.2f}")
                            logging.info(f"✓ Total gastado: ${cumulative_quote:.2f}")
                            
                            # Registrar en historial
                            self.trade_history.append({
                                'timestamp': datetime.now(),
                                'type': 'BUY',
                                'quantity': executed_qty,
                                'price': avg_price,
                                'total': cumulative_quote,
                                'order_id': order['orderId'],
                                'trigger': order_type
                            })
                            
                            # Cancelar la otra orden pendiente
                            other_order_id = self.trailing_stop_order_id if order_id == self.stop_loss_order_id else self.stop_loss_order_id
                            if other_order_id:
                                try:
                                    self.client.cancel_order(symbol=self.symbol, orderId=other_order_id)
                                    logging.info(f"✓ Orden complementaria cancelada")
                                except:
                                    pass
                            
                            # Calcular P&L de este ciclo
                            if self.last_sell_price > 0:
                                cycle_pnl = self.sell_proceeds - cumulative_quote
                                logging.info(f"P&L del ciclo: ${cycle_pnl:.2f}")
                            
                            # Esperar un momento y crear órdenes de venta
                            time.sleep(2)
                            self.setup_sell_orders()
                            break
                        
                elif self.current_state == "WAITING_SELL":
                    # Actualizar trailing stop si el precio sube (nuevo máximo)
                    if current_price and self.trailing_stop_order_id:
                        self.update_trailing_stop_sell(current_price)
                    
                    # Verificar si alguna orden se completó (stop loss o trailing)
                    orders_to_check = []
                    if self.stop_loss_order_id:
                        orders_to_check.append(self.stop_loss_order_id)
                    if self.trailing_stop_order_id:
                        orders_to_check.append(self.trailing_stop_order_id)
                    
                    for order_id in orders_to_check:
                        order = self.check_order_status(order_id)
                        
                        if order and order['status'] == 'FILLED':
                            self.current_state = "SELLING"
                            executed_qty = float(order['executedQty'])
                            cumulative_quote = float(order['cummulativeQuoteQty'])
                            avg_price = cumulative_quote / executed_qty if executed_qty > 0 else 0
                            
                            self.last_sell_price = avg_price
                            self.sell_proceeds = cumulative_quote
                            self.successful_trades += 1
                            
                            order_type = "🛡️ STOP LOSS" if order_id == self.stop_loss_order_id else "📉 TRAILING STOP"
                            logging.info(f"✓ VENTA completada ({order_type}): {executed_qty} BNB a ${avg_price:.2f}")
                            logging.info(f"✓ USDT obtenido: ${cumulative_quote:.2f}")
                            
                            # Registrar en historial
                            self.trade_history.append({
                                'timestamp': datetime.now(),
                                'type': 'SELL',
                                'quantity': executed_qty,
                                'price': avg_price,
                                'total': cumulative_quote,
                                'order_id': order['orderId'],
                                'trigger': order_type
                            })
                            
                            # Cancelar la otra orden pendiente
                            other_order_id = self.trailing_stop_order_id if order_id == self.stop_loss_order_id else self.stop_loss_order_id
                            if other_order_id:
                                try:
                                    self.client.cancel_order(symbol=self.symbol, orderId=other_order_id)
                                    logging.info(f"✓ Orden complementaria cancelada")
                                except:
                                    pass
                            
                            # Calcular P&L de este ciclo
                            if self.last_buy_price > 0:
                                cycle_pnl = cumulative_quote - (executed_qty * self.last_buy_price)
                                logging.info(f"P&L del ciclo: ${cycle_pnl:.2f}")
                            
                            # Esperar un momento y crear órdenes de compra
                            time.sleep(2)
                            self.setup_buy_orders()
                            break
                
                # Actualizar P&L
                self.update_pnl()
                
                # Esperar antes de la próxima verificación
                time.sleep(5)
                
            except Exception as e:
                logging.error(f"Error en monitor_orders: {e}")
                time.sleep(10)
    
    def start(self, initial_bnb, stop_loss_pct, trailing_buy_pct, trailing_sell_pct):
        """Inicia el bot de trading."""
        if self.is_running:
            logging.warning("El bot ya está ejecutándose")
            return False
        
        self.initial_bnb_quantity = initial_bnb
        self.stop_loss_percent = stop_loss_pct
        self.trailing_percent_buy = trailing_buy_pct
        self.trailing_percent_sell = trailing_sell_pct
        self.is_running = True
        
        # Ejecutar venta inicial
        if not self.initial_sell():
            self.is_running = False
            return False
        
        # Crear órdenes de compra (stop loss + trailing stop)
        if not self.setup_buy_orders():
            self.is_running = False
            return False
        
        # Iniciar monitoreo en thread separado
        self.thread = threading.Thread(target=self.monitor_orders, daemon=True)
        self.thread.start()
        
        logging.info("✓ Bot iniciado correctamente")
        return True
    
    def stop(self):
        """Detiene el bot de trading."""
        logging.info("Deteniendo bot...")
        self.is_running = False
        
        # Cancelar órdenes pendientes
        orders_to_cancel = []
        if self.stop_loss_order_id:
            orders_to_cancel.append(self.stop_loss_order_id)
        if self.trailing_stop_order_id:
            orders_to_cancel.append(self.trailing_stop_order_id)
        
        for order_id in orders_to_cancel:
            try:
                self.client.cancel_order(
                    symbol=self.symbol,
                    orderId=order_id
                )
                logging.info(f"Orden {order_id} cancelada")
            except Exception as e:
                logging.warning(f"No se pudo cancelar orden {order_id}: {e}")
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        self.current_state = "IDLE"
        logging.info("✓ Bot detenido")
    
    def get_status(self):
        """Retorna el estado actual del bot."""
        return {
            'is_running': self.is_running,
            'state': self.current_state,
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'failed_trades': self.failed_trades,
            'current_usdt': self.current_usdt_balance,
            'current_bnb': self.current_bnb_balance,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.unrealized_pnl,
            'total_pnl': self.total_pnl,
            'last_buy_price': self.last_buy_price,
            'last_sell_price': self.last_sell_price
        }
