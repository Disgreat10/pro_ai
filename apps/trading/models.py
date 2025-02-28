from django.db import models
from django.utils import timezone
from django.conf import settings
from decimal import Decimal

class OrderType(models.TextChoices):
    LIMIT = 'LIMIT', 'Limit Order'
    MARKET = 'MARKET', 'Market Order'
    STOP_LOSS = 'STOP_LOSS', 'Stop Loss'
    STOP_LIMIT = 'STOP_LIMIT', 'Stop Limit'

class OrderSide(models.TextChoices):
    BUY = 'BUY', 'Buy'
    SELL = 'SELL', 'Sell'

class OrderStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    OPEN = 'OPEN', 'Open'
    PARTIALLY_FILLED = 'PARTIALLY_FILLED', 'Partially Filled'
    FILLED = 'FILLED', 'Filled'
    CANCELLED = 'CANCELLED', 'Cancelled'
    REJECTED = 'REJECTED', 'Rejected'
    EXPIRED = 'EXPIRED', 'Expired'

class TradingPair(models.Model):
    base_asset = models.CharField(max_length=10)
    quote_asset = models.CharField(max_length=10)
    min_trade_size = models.DecimalField(max_digits=18, decimal_places=8)
    price_precision = models.IntegerField(default=8)
    is_active = models.BooleanField(default=True)
    
    # Market Data
    last_price = models.DecimalField(max_digits=18, decimal_places=8, null=True)
    bid_price = models.DecimalField(max_digits=18, decimal_places=8, null=True)
    ask_price = models.DecimalField(max_digits=18, decimal_places=8, null=True)
    high_price = models.DecimalField(max_digits=18, decimal_places=8, null=True)
    low_price = models.DecimalField(max_digits=18, decimal_places=8, null=True)
    open_price = models.DecimalField(max_digits=18, decimal_places=8, null=True)
    close_price = models.DecimalField(max_digits=18, decimal_places=8, null=True)
    volume_24h = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    last_updated = models.DateTimeField(null=True)
    
    class Meta:
        unique_together = ('base_asset', 'quote_asset')

    def __str__(self):
        return f"{self.base_asset}/{self.quote_asset}"

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    trading_pair = models.ForeignKey(TradingPair, on_delete=models.CASCADE)
    order_type = models.CharField(max_length=20, choices=OrderType.choices)
    side = models.CharField(max_length=4, choices=OrderSide.choices)
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    
    price = models.DecimalField(max_digits=18, decimal_places=8, null=True)
    stop_price = models.DecimalField(max_digits=18, decimal_places=8, null=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=8)
    filled_quantity = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0'))
    remaining_quantity = models.DecimalField(max_digits=18, decimal_places=8)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True)
    
    # Execution tracking
    average_fill_price = models.DecimalField(max_digits=18, decimal_places=8, null=True)
    total_filled_amount = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0'))
    fees = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0'))
    
    # Additional metadata
    client_order_id = models.CharField(max_length=50, null=True)
    api_key_id = models.CharField(max_length=50, null=True)  # For API orders
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(null=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['trading_pair', 'status', 'side']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status', 'expires_at']),
        ]

    def __str__(self):
        return f"{self.side} {self.quantity} {self.trading_pair} @ {self.price}"

    def save(self, *args, **kwargs):
        if not self.pk:  # New order
            self.remaining_quantity = self.quantity
        super().save(*args, **kwargs)

class Trade(models.Model):
    maker_order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='maker_trades')
    taker_order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='taker_trades')
    trading_pair = models.ForeignKey(TradingPair, on_delete=models.CASCADE)
    
    price = models.DecimalField(max_digits=18, decimal_places=8)
    quantity = models.DecimalField(max_digits=18, decimal_places=8)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    maker_fee = models.DecimalField(max_digits=18, decimal_places=8)
    taker_fee = models.DecimalField(max_digits=18, decimal_places=8)
    
    class Meta:
        indexes = [
            models.Index(fields=['trading_pair', 'timestamp']),
            models.Index(fields=['maker_order', 'timestamp']),
            models.Index(fields=['taker_order', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.quantity} @ {self.price}"

class OrderBook(models.Model):
    trading_pair = models.ForeignKey(TradingPair, on_delete=models.CASCADE)
    side = models.CharField(max_length=4, choices=OrderSide.choices)
    price = models.DecimalField(max_digits=18, decimal_places=8)
    quantity = models.DecimalField(max_digits=18, decimal_places=8)
    order_count = models.IntegerField(default=1)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('trading_pair', 'side', 'price')
        indexes = [
            models.Index(fields=['trading_pair', 'side', 'price']),
        ]

    def __str__(self):
        return f"{self.side} {self.quantity} @ {self.price}"

class TestExchangeAPI(models.Model):
    name = models.CharField(max_length=50)
    api_key = models.CharField(max_length=100)
    api_secret = models.CharField(max_length=100)
    base_url = models.URLField()
    is_active = models.BooleanField(default=True)
    
    # Rate limiting settings
    requests_per_minute = models.IntegerField(default=60)
    requests_per_hour = models.IntegerField(default=1200)
    
    # Connection settings
    timeout = models.IntegerField(default=30)  # seconds
    use_test_net = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True)
    
    def __str__(self):
        return f"{self.name} ({'Test' if self.use_test_net else 'Live'})"

class TestTrade(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    exchange_api = models.ForeignKey(TestExchangeAPI, on_delete=models.CASCADE)
    exchange_trade_id = models.CharField(max_length=100)
    
    price = models.DecimalField(max_digits=18, decimal_places=8)
    quantity = models.DecimalField(max_digits=18, decimal_places=8)
    timestamp = models.DateTimeField()
    
    is_simulated = models.BooleanField(default=False)
    simulation_delay = models.IntegerField(null=True)  # milliseconds
    
    raw_response = models.JSONField(null=True)
    
    def __str__(self):
        return f"Test Trade: {self.quantity} @ {self.price}"
