from django.urls import re_path
from . import consumers, consumers_market

websocket_urlpatterns = [
    re_path(r'ws/trading/market-data/$', consumers_market.MarketDataConsumer.as_asgi()),
    re_path(r'ws/trading/mcx-feed/$', consumers.MCXMarketDataConsumer.as_asgi()),
]
