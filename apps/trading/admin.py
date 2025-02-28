from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    TradingPair, Order, Trade, OrderBook, 
    TestExchangeAPI, TestTrade
)

@admin.register(TradingPair)
class TradingPairAdmin(admin.ModelAdmin):
    list_display = (
        'symbol', 'last_price', 'bid_ask_spread', 'daily_change',
        'high_low', 'volume_24h', 'is_active', 'last_updated'
    )
    list_filter = ('is_active', 'base_asset', 'quote_asset')
    search_fields = ('base_asset', 'quote_asset')
    readonly_fields = (
        'last_price', 'bid_price', 'ask_price', 'high_price',
        'low_price', 'open_price', 'close_price', 'volume_24h',
        'last_updated'
    )
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('base_asset', 'quote_asset', 'min_trade_size', 'price_precision', 'is_active')
        }),
        ('Market Data', {
            'fields': (
                'last_price', 'bid_price', 'ask_price', 'high_price',
                'low_price', 'open_price', 'close_price', 'volume_24h',
                'last_updated'
            )
        })
    )
    
    def symbol(self, obj):
        return "{}/{}".format(obj.base_asset, obj.quote_asset)
    
    def bid_ask_spread(self, obj):
        if obj.bid_price and obj.ask_price:
            spread = obj.ask_price - obj.bid_price
            spread_pct = (spread / obj.ask_price * 100) if obj.ask_price else 0
            return format_html(
                '{} ({}%)',
                str(spread),
                str(round(spread_pct, 2))
            )
        return '-'
    bid_ask_spread.short_description = 'Spread'
    
    def daily_change(self, obj):
        if obj.last_price and obj.open_price and obj.open_price > 0:
            change = obj.last_price - obj.open_price
            change_pct = (change / obj.open_price) * 100
            color = 'green' if change >= 0 else 'red'
            sign = '+' if change >= 0 else ''
            return format_html(
                '<span style="color: {}">{}{} ({}%)</span>',
                color,
                sign,
                str(change),
                str(round(change_pct, 2))
            )
        return '-'
    daily_change.short_description = '24h Change'
    
    def high_low(self, obj):
        if obj.high_price and obj.low_price:
            return format_html(
                'H: {} / L: {}',
                str(obj.high_price),
                str(obj.low_price)
            )
        return '-'
    high_low.short_description = '24h High/Low'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'trading_pair_symbol', 'order_type', 'side',
        'status', 'price_display', 'quantity', 'filled_quantity',
        'created_at'
    )
    list_filter = ('status', 'order_type', 'side', 'trading_pair')
    search_fields = ('user__username', 'client_order_id')
    readonly_fields = (
        'filled_quantity', 'remaining_quantity', 'average_fill_price',
        'total_filled_amount', 'fees', 'created_at', 'updated_at'
    )
    
    def trading_pair_symbol(self, obj):
        return str(obj.trading_pair)
    
    def price_display(self, obj):
        if obj.order_type == 'MARKET':
            return 'MARKET'
        return str(round(obj.price, 8))
    price_display.short_description = 'Price'

@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'trading_pair', 'price', 'quantity',
        'maker_order_link', 'taker_order_link', 'timestamp'
    )
    list_filter = ('trading_pair', 'timestamp')
    search_fields = (
        'maker_order__user__username', 'taker_order__user__username',
        'maker_order__client_order_id', 'taker_order__client_order_id'
    )
    
    def maker_order_link(self, obj):
        return format_html(
            '<a href="/admin/trading/order/{}/">{}</a>',
            obj.maker_order.id,
            "#{} ({})".format(obj.maker_order.id, obj.maker_order.user.username)
        )
    maker_order_link.short_description = 'Maker Order'
    
    def taker_order_link(self, obj):
        return format_html(
            '<a href="/admin/trading/order/{}/">{}</a>',
            obj.taker_order.id,
            "#{} ({})".format(obj.taker_order.id, obj.taker_order.user.username)
        )
    taker_order_link.short_description = 'Taker Order'

@admin.register(OrderBook)
class OrderBookAdmin(admin.ModelAdmin):
    list_display = (
        'trading_pair', 'side', 'price', 'quantity',
        'order_count', 'last_updated'
    )
    list_filter = ('trading_pair', 'side')
    ordering = ('trading_pair', 'side', '-price')

@admin.register(TestExchangeAPI)
class TestExchangeAPIAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'is_active', 'use_test_net', 'requests_per_minute',
        'requests_per_hour', 'last_used'
    )
    list_filter = ('is_active', 'use_test_net')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'last_used')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return self.readonly_fields + ('api_key', 'api_secret')
        return self.readonly_fields

@admin.register(TestTrade)
class TestTradeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'order_link', 'exchange_api', 'price', 'quantity',
        'timestamp', 'is_simulated', 'simulation_delay'
    )
    list_filter = ('exchange_api', 'is_simulated', 'timestamp')
    search_fields = ('order__user__username', 'exchange_trade_id')
    readonly_fields = ('raw_response',)
    
    def order_link(self, obj):
        return format_html(
            '<a href="/admin/trading/order/{}/">{}</a>',
            obj.order.id,
            "#{} ({})".format(obj.order.id, obj.order.user.username)
        )
    order_link.short_description = 'Order'
