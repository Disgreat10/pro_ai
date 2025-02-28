from rest_framework import serializers
from django.utils import timezone
from .models import (
    Order, Trade, TradingPair, OrderBook, TestExchangeAPI, TestTrade,
    OrderType, OrderSide, OrderStatus
)

class TradingPairSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradingPair
        fields = [
            'id', 'base_asset', 'quote_asset', 'min_trade_size',
            'price_precision', 'is_active', 'last_price'
        ]

class OrderSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'trading_pair', 'order_type', 'side', 'status',
            'price', 'stop_price', 'quantity', 'filled_quantity',
            'remaining_quantity', 'created_at', 'updated_at', 'expires_at',
            'average_fill_price', 'total_filled_amount', 'fees',
            'client_order_id', 'api_key_id', 'ip_address', 'user_agent'
        ]
        read_only_fields = [
            'status', 'filled_quantity', 'remaining_quantity',
            'average_fill_price', 'total_filled_amount', 'fees'
        ]

    def validate(self, data):
        """Validate order parameters"""
        # Check required fields based on order type
        if data['order_type'] == OrderType.LIMIT and not data.get('price'):
            raise serializers.ValidationError(
                {'price': 'Price is required for limit orders'}
            )
        
        if data['order_type'] in [OrderType.STOP_LOSS, OrderType.STOP_LIMIT] and not data.get('stop_price'):
            raise serializers.ValidationError(
                {'stop_price': 'Stop price is required for stop orders'}
            )
            
        if data['order_type'] == OrderType.STOP_LIMIT and not data.get('price'):
            raise serializers.ValidationError(
                {'price': 'Price is required for stop-limit orders'}
            )

        # Check price precision
        if data.get('price'):
            decimal_places = len(str(data['price']).split('.')[-1])
            if decimal_places > data['trading_pair'].price_precision:
                raise serializers.ValidationError(
                    {'price': f'Price exceeds maximum precision of {data["trading_pair"].price_precision} decimals'}
                )

        # Check minimum trade size
        if data['quantity'] < data['trading_pair'].min_trade_size:
            raise serializers.ValidationError(
                {'quantity': f'Quantity below minimum trade size of {data["trading_pair"].min_trade_size}'}
            )

        # Set remaining quantity on creation
        if not self.instance:  # New order
            data['remaining_quantity'] = data['quantity']

        return data

class TradeSerializer(serializers.ModelSerializer):
    maker_order_id = serializers.IntegerField(source='maker_order.id', read_only=True)
    taker_order_id = serializers.IntegerField(source='taker_order.id', read_only=True)
    trading_pair_symbol = serializers.CharField(source='trading_pair.__str__', read_only=True)
    
    class Meta:
        model = Trade
        fields = [
            'id', 'maker_order_id', 'taker_order_id', 'trading_pair_symbol',
            'price', 'quantity', 'timestamp', 'maker_fee', 'taker_fee'
        ]

class OrderBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderBook
        fields = [
            'trading_pair', 'side', 'price', 'quantity',
            'order_count', 'last_updated'
        ]

class TestExchangeAPISerializer(serializers.ModelSerializer):
    class Meta:
        model = TestExchangeAPI
        fields = [
            'id', 'name', 'api_key', 'api_secret', 'base_url',
            'is_active', 'requests_per_minute', 'requests_per_hour',
            'timeout', 'use_test_net', 'created_at', 'last_used'
        ]
        extra_kwargs = {
            'api_secret': {'write_only': True}
        }

    def validate(self, data):
        """Validate API configuration"""
        if data.get('requests_per_minute', 0) > data.get('requests_per_hour', 0):
            raise serializers.ValidationError(
                'Requests per minute cannot exceed requests per hour'
            )
        return data

class TestTradeSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    exchange_name = serializers.CharField(source='exchange_api.name', read_only=True)
    
    class Meta:
        model = TestTrade
        fields = [
            'id', 'order_id', 'exchange_name', 'exchange_trade_id',
            'price', 'quantity', 'timestamp', 'is_simulated',
            'simulation_delay', 'raw_response'
        ]

class OrderBookSnapshotSerializer(serializers.Serializer):
    bids = serializers.ListField(
        child=serializers.ListField(
            child=serializers.DecimalField(max_digits=18, decimal_places=8)
        )
    )
    asks = serializers.ListField(
        child=serializers.ListField(
            child=serializers.DecimalField(max_digits=18, decimal_places=8)
        )
    )
    timestamp = serializers.DateTimeField(default=timezone.now)

class MarketDepthSerializer(serializers.Serializer):
    price = serializers.DecimalField(max_digits=18, decimal_places=8)
    quantity = serializers.DecimalField(max_digits=18, decimal_places=8)
    total = serializers.DecimalField(max_digits=18, decimal_places=8)
    count = serializers.IntegerField()

class TradingPairStatsSerializer(serializers.Serializer):
    symbol = serializers.CharField()
    last_price = serializers.DecimalField(max_digits=18, decimal_places=8)
    high_24h = serializers.DecimalField(max_digits=18, decimal_places=8)
    low_24h = serializers.DecimalField(max_digits=18, decimal_places=8)
    volume_24h = serializers.DecimalField(max_digits=18, decimal_places=8)
    price_change_24h = serializers.DecimalField(max_digits=18, decimal_places=8)
    price_change_percent_24h = serializers.DecimalField(max_digits=5, decimal_places=2)
