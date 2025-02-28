import hmac
import hashlib
import time
import json
import logging
import requests
from typing import Dict, Optional, List
from decimal import Decimal
from django.conf import settings
from .models import TestExchangeAPI, TestTrade, Order, TradingPair

logger = logging.getLogger(__name__)

class TestExchangeClient:
    """Client for interacting with test exchanges (e.g. Binance Testnet, FTX Testnet)"""
    
    def __init__(self, api: TestExchangeAPI):
        self.api = api
        self.session = requests.Session()
        self.last_request_time = 0
        self.request_count = 0

    def _generate_signature(self, data: Dict) -> str:
        """Generate HMAC signature for API request"""
        message = '&'.join([f"{k}={v}" for k, v in sorted(data.items())])
        signature = hmac.new(
            self.api.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _make_request(self, method: str, endpoint: str, params: Dict = None, 
                     signed: bool = False) -> Optional[Dict]:
        """Make HTTP request to exchange API with rate limiting and error handling"""
        try:
            # Rate limiting
            current_time = time.time()
            if current_time - self.last_request_time < 1:  # Minimum 1 second between requests
                time.sleep(1 - (current_time - self.last_request_time))
            
            # Prepare request
            url = f"{self.api.base_url}{endpoint}"
            headers = {'X-MBX-APIKEY': self.api.api_key}
            
            if signed:
                params['timestamp'] = int(time.time() * 1000)
                params['signature'] = self._generate_signature(params)
            
            # Make request
            if method == 'GET':
                response = self.session.get(
                    url, params=params, headers=headers, 
                    timeout=self.api.timeout
                )
            else:
                response = self.session.post(
                    url, json=params, headers=headers, 
                    timeout=self.api.timeout
                )
            
            # Update rate limiting counters
            self.last_request_time = time.time()
            self.request_count += 1
            
            # Handle response
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"API request failed: {response.status_code} - {response.text}"
                )
                return None
                
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            return None

    def get_exchange_info(self) -> Optional[Dict]:
        """Get exchange information and trading rules"""
        return self._make_request('GET', '/api/v3/exchangeInfo')

    def get_order_book(self, symbol: str, limit: int = 100) -> Optional[Dict]:
        """Get current order book"""
        params = {'symbol': symbol, 'limit': limit}
        return self._make_request('GET', '/api/v3/depth', params)

    def get_recent_trades(self, symbol: str, limit: int = 500) -> Optional[List[Dict]]:
        """Get recent trades"""
        params = {'symbol': symbol, 'limit': limit}
        return self._make_request('GET', '/api/v3/trades', params)

    def place_test_order(self, order: Order) -> Optional[TestTrade]:
        """Place a test order on the exchange"""
        try:
            # Convert order to exchange format
            params = {
                'symbol': f"{order.trading_pair.base_asset}{order.trading_pair.quote_asset}",
                'side': order.side,
                'type': order.order_type,
                'quantity': str(order.quantity),
                'timestamp': int(time.time() * 1000)
            }
            
            if order.order_type == 'LIMIT':
                params['price'] = str(order.price)
                params['timeInForce'] = 'GTC'  # Good Till Cancel
            elif order.order_type in ['STOP_LOSS', 'STOP_LIMIT']:
                params['stopPrice'] = str(order.stop_price)
                if order.order_type == 'STOP_LIMIT':
                    params['price'] = str(order.price)
                    params['timeInForce'] = 'GTC'
            
            # Simulate network latency
            time.sleep(0.1)  # 100ms delay
            
            # Make API request
            response = self._make_request(
                'POST', '/api/v3/order/test', 
                params=params, signed=True
            )
            
            if response:
                # Create test trade record
                test_trade = TestTrade.objects.create(
                    order=order,
                    exchange_api=self.api,
                    exchange_trade_id=str(response.get('orderId')),
                    price=order.price or self._get_market_price(order),
                    quantity=order.quantity,
                    timestamp=timezone.now(),
                    is_simulated=True,
                    simulation_delay=100,  # 100ms
                    raw_response=response
                )
                return test_trade
            
            return None
            
        except Exception as e:
            logger.error(f"Error placing test order: {str(e)}")
            return None

    def _get_market_price(self, order: Order) -> Decimal:
        """Get current market price for an asset"""
        symbol = f"{order.trading_pair.base_asset}{order.trading_pair.quote_asset}"
        trades = self.get_recent_trades(symbol, limit=1)
        if trades:
            return Decimal(str(trades[0]['price']))
        return order.trading_pair.last_price or Decimal('0')

    def cancel_test_order(self, order_id: str, symbol: str) -> bool:
        """Cancel a test order"""
        params = {
            'symbol': symbol,
            'orderId': order_id,
            'timestamp': int(time.time() * 1000)
        }
        
        response = self._make_request(
            'DELETE', '/api/v3/order', 
            params=params, signed=True
        )
        
        return response is not None

    def get_test_order_status(self, order_id: str, symbol: str) -> Optional[Dict]:
        """Get status of a test order"""
        params = {
            'symbol': symbol,
            'orderId': order_id,
            'timestamp': int(time.time() * 1000)
        }
        
        return self._make_request(
            'GET', '/api/v3/order', 
            params=params, signed=True
        )

class TestExchangeManager:
    """Manager class for handling multiple test exchange connections"""
    
    def __init__(self):
        self.clients = {}
        self.load_exchanges()

    def load_exchanges(self):
        """Load all active test exchange APIs"""
        for api in TestExchangeAPI.objects.filter(is_active=True):
            self.clients[api.id] = TestExchangeClient(api)

    def get_client(self, api_id: int) -> Optional[TestExchangeClient]:
        """Get client for specific exchange API"""
        if api_id not in self.clients:
            try:
                api = TestExchangeAPI.objects.get(id=api_id, is_active=True)
                self.clients[api_id] = TestExchangeClient(api)
            except TestExchangeAPI.DoesNotExist:
                return None
        return self.clients.get(api_id)

    def place_test_order(self, order: Order, api_id: int) -> Optional[TestTrade]:
        """Place test order using specified exchange API"""
        client = self.get_client(api_id)
        if client:
            return client.place_test_order(order)
        return None

    def cancel_test_order(self, test_trade: TestTrade) -> bool:
        """Cancel test order"""
        client = self.get_client(test_trade.exchange_api_id)
        if client:
            symbol = f"{test_trade.order.trading_pair.base_asset}{test_trade.order.trading_pair.quote_asset}"
            return client.cancel_test_order(test_trade.exchange_trade_id, symbol)
        return False

    def get_test_order_status(self, test_trade: TestTrade) -> Optional[Dict]:
        """Get status of test order"""
        client = self.get_client(test_trade.exchange_api_id)
        if client:
            symbol = f"{test_trade.order.trading_pair.base_asset}{test_trade.order.trading_pair.quote_asset}"
            return client.get_test_order_status(test_trade.exchange_trade_id, symbol)
        return None

# Global instance
test_exchange_manager = TestExchangeManager()
