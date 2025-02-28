from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, views_market

router = DefaultRouter()
router.register(r'trading-pairs', views.TradingPairViewSet, basename='trading-pair')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'trades', views.TradeViewSet, basename='trade')
router.register(r'test-exchanges', views.TestExchangeAPIViewSet, basename='test-exchange')

# API URLs
api_urlpatterns = [
    path('', include(router.urls)),
    path('market-data/', views_market.market_data_api, name='market-data-api'),
]

# Frontend URLs
frontend_urlpatterns = [
    path('market-watch/', views_market.MarketWatchView.as_view(), name='market-watch'),
    path('ai-prediction/', views_market.AIPredictionView.as_view(), name='ai-prediction'),
]

# Use different app_names based on where these URLs are included
app_name = 'trading'
urlpatterns = frontend_urlpatterns  # For frontend routes
api_patterns = api_urlpatterns      # For API routes
