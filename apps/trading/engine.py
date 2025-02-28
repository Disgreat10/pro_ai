import logging
from decimal import Decimal
from typing import List, Optional, Tuple
from django.db import transaction
from django.utils import timezone
from django.db.models import F
from .models import Order, Trade, OrderBook, OrderStatus, OrderSide, OrderType, TradingPair

logger = logging.getLogger(__name__)

class MatchingEngine:
    def __init__(self, trading_pair: TradingPair):
        self.trading_pair = trading_pair
        self.order_book = {
            'BUY': {},  # price -> [orders]
            'SELL': {}  # price -> [orders]
        }
        self.load_order_book()

    def load_order_book(self):
        """Load existing open orders into memory"""
        open_orders = Order.objects.filter(
            trading_pair=self.trading_pair,
            status__in=[OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]
        ).order_by('created_at')
        
        for order in open_orders:
            self.add_to_order_book(order)

    def add_to_order_book(self, order: Order):
        """Add an order to the in-memory order book"""
        if order.order_type == OrderType.MARKET:
            return  # Market orders are not added to the book
            
        price = str(order.price)  # Use string to avoid floating point issues
        if price not in self.order_book[order.side]:
            self.order_book[order.side][price] = []
        self.order_book[order.side][price].append(order)

    def remove_from_order_book(self, order: Order):
        """Remove an order from the in-memory order book"""
        price = str(order.price)
        if price in self.order_book[order.side]:
            self.order_book[order.side][price] = [
                o for o in self.order_book[order.side][price] if o.id != order.id
            ]
            if not self.order_book[order.side][price]:
                del self.order_book[order.side][price]

    @transaction.atomic
    def process_order(self, order: Order) -> List[Trade]:
        """Process a new order and generate trades"""
        trades = []
        
        # Validate order
        if not self.validate_order(order):
            order.status = OrderStatus.REJECTED
            order.save()
            return trades

        # Check if order has expired
        if order.expires_at and order.expires_at <= timezone.now():
            order.status = OrderStatus.EXPIRED
            order.save()
            return trades

        # Process market orders immediately
        if order.order_type == OrderType.MARKET:
            trades = self.match_market_order(order)
        
        # Process limit orders
        elif order.order_type == OrderType.LIMIT:
            trades = self.match_limit_order(order)
            
            # If order is not fully filled, add to order book
            if order.remaining_quantity > 0:
                order.status = OrderStatus.OPEN if order.filled_quantity == 0 else OrderStatus.PARTIALLY_FILLED
                order.save()
                self.add_to_order_book(order)
        
        # Process stop orders
        elif order.order_type in [OrderType.STOP_LOSS, OrderType.STOP_LIMIT]:
            if self.check_stop_price_triggered(order):
                trades = self.match_limit_order(order)
                if order.remaining_quantity > 0:
                    order.status = OrderStatus.OPEN if order.filled_quantity == 0 else OrderStatus.PARTIALLY_FILLED
                    order.save()
                    self.add_to_order_book(order)
            else:
                order.status = OrderStatus.PENDING
                order.save()

        return trades

    def validate_order(self, order: Order) -> bool:
        """Validate order parameters"""
        try:
            # Check minimum trade size
            if order.quantity < self.trading_pair.min_trade_size:
                logger.warning(f"Order {order.id} rejected: Below minimum trade size")
                return False

            # Check price precision
            if order.price and len(str(order.price).split('.')[-1]) > self.trading_pair.price_precision:
                logger.warning(f"Order {order.id} rejected: Invalid price precision")
                return False

            # Additional validations can be added here
            return True
            
        except Exception as e:
            logger.error(f"Order validation error: {str(e)}")
            return False

    def match_market_order(self, order: Order) -> List[Trade]:
        """Match a market order against the order book"""
        trades = []
        opposite_side = 'SELL' if order.side == 'BUY' else 'BUY'
        
        # Sort prices (ascending for buy, descending for sell)
        prices = sorted(
            self.order_book[opposite_side].keys(),
            key=lambda x: Decimal(x),
            reverse=(order.side == 'BUY')
        )
        
        for price_str in prices:
            if order.remaining_quantity <= 0:
                break
                
            price = Decimal(price_str)
            for maker_order in self.order_book[opposite_side][price_str][:]:
                if order.remaining_quantity <= 0:
                    break
                    
                trade = self.create_trade(maker_order, order, price)
                if trade:
                    trades.append(trade)
                    
                    # Update order book
                    if maker_order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
                        self.remove_from_order_book(maker_order)
        
        # Update order status
        if order.remaining_quantity == 0:
            order.status = OrderStatus.FILLED
        elif order.filled_quantity > 0:
            order.status = OrderStatus.PARTIALLY_FILLED
        else:
            order.status = OrderStatus.REJECTED
        order.save()
        
        return trades

    def match_limit_order(self, order: Order) -> List[Trade]:
        """Match a limit order against the order book"""
        trades = []
        opposite_side = 'SELL' if order.side == 'BUY' else 'BUY'
        
        # Sort prices (ascending for buy, descending for sell)
        prices = sorted(
            self.order_book[opposite_side].keys(),
            key=lambda x: Decimal(x),
            reverse=(order.side == 'BUY')
        )
        
        for price_str in prices:
            if order.remaining_quantity <= 0:
                break
                
            price = Decimal(price_str)
            # Check if price is acceptable
            if ((order.side == 'BUY' and price > order.price) or 
                (order.side == 'SELL' and price < order.price)):
                break
                
            for maker_order in self.order_book[opposite_side][price_str][:]:
                if order.remaining_quantity <= 0:
                    break
                    
                trade = self.create_trade(maker_order, order, price)
                if trade:
                    trades.append(trade)
                    
                    # Update order book
                    if maker_order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
                        self.remove_from_order_book(maker_order)
        
        return trades

    @transaction.atomic
    def create_trade(self, maker_order: Order, taker_order: Order, price: Decimal) -> Optional[Trade]:
        """Create a trade between two orders"""
        try:
            # Calculate trade quantity
            quantity = min(maker_order.remaining_quantity, taker_order.remaining_quantity)
            
            # Calculate fees
            maker_fee = self.calculate_fee(quantity, price, is_maker=True)
            taker_fee = self.calculate_fee(quantity, price, is_maker=False)
            
            # Create trade
            trade = Trade.objects.create(
                maker_order=maker_order,
                taker_order=taker_order,
                trading_pair=self.trading_pair,
                price=price,
                quantity=quantity,
                maker_fee=maker_fee,
                taker_fee=taker_fee
            )
            
            # Update orders
            for order in [maker_order, taker_order]:
                order.filled_quantity = F('filled_quantity') + quantity
                order.remaining_quantity = F('remaining_quantity') - quantity
                order.total_filled_amount = F('total_filled_amount') + (quantity * price)
                order.fees = F('fees') + (maker_fee if order == maker_order else taker_fee)
                
                # Update average fill price
                total_quantity = order.filled_quantity + quantity
                if total_quantity > 0:
                    order.average_fill_price = (
                        (order.average_fill_price or 0) * order.filled_quantity + price * quantity
                    ) / total_quantity
                
                # Update status
                if order.remaining_quantity == 0:
                    order.status = OrderStatus.FILLED
                else:
                    order.status = OrderStatus.PARTIALLY_FILLED
                
                order.save()
            
            # Update last price
            self.trading_pair.last_price = price
            self.trading_pair.save()
            
            return trade
            
        except Exception as e:
            logger.error(f"Error creating trade: {str(e)}")
            return None

    def calculate_fee(self, quantity: Decimal, price: Decimal, is_maker: bool) -> Decimal:
        """Calculate trading fee"""
        # Example fee calculation (can be customized)
        fee_rate = Decimal('0.001') if is_maker else Decimal('0.002')  # 0.1% maker, 0.2% taker
        return quantity * price * fee_rate

    def check_stop_price_triggered(self, order: Order) -> bool:
        """Check if stop price has been triggered"""
        if not order.stop_price:
            return False
            
        last_price = self.trading_pair.last_price
        if not last_price:
            return False
            
        if order.side == 'BUY':
            return last_price >= order.stop_price
        else:
            return last_price <= order.stop_price

    def cancel_order(self, order: Order) -> bool:
        """Cancel an open order"""
        try:
            if order.status not in [OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED, OrderStatus.PENDING]:
                return False
                
            order.status = OrderStatus.CANCELLED
            order.save()
            
            self.remove_from_order_book(order)
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return False

    def get_order_book_snapshot(self) -> dict:
        """Get current order book snapshot"""
        snapshot = {
            'bids': [],  # Buy orders
            'asks': []   # Sell orders
        }
        
        # Process buy orders
        for price_str in sorted(self.order_book['BUY'].keys(), key=lambda x: Decimal(x), reverse=True):
            total_quantity = sum(order.remaining_quantity for order in self.order_book['BUY'][price_str])
            snapshot['bids'].append([Decimal(price_str), total_quantity])
        
        # Process sell orders
        for price_str in sorted(self.order_book['SELL'].keys(), key=lambda x: Decimal(x)):
            total_quantity = sum(order.remaining_quantity for order in self.order_book['SELL'][price_str])
            snapshot['asks'].append([Decimal(price_str), total_quantity])
        
        return snapshot
