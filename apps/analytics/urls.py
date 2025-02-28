from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'trade-analytics', views.TradeAnalyticsViewSet, basename='trade-analytics')
router.register(r'revenue-reports', views.RevenueReportViewSet, basename='revenue-reports')
router.register(r'risk-exposure', views.RiskExposureViewSet, basename='risk-exposure')
router.register(r'profit-loss', views.ProfitLossViewSet, basename='profit-loss')
router.register(r'custom-reports', views.CustomReportViewSet, basename='custom-reports')
router.register(r'snapshots', views.AnalyticsSnapshotViewSet, basename='snapshots')

# Register new AI analytics viewsets
router.register(r'market-predictions', views.MarketPredictionViewSet, basename='market-predictions')
router.register(r'sentiment-analysis', views.SentimentAnalysisViewSet, basename='sentiment-analysis')
router.register(r'system-health', views.SystemHealthViewSet, basename='system-health')

app_name = 'analytics'

urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),
    
    # Add any custom URLs here if needed
    # Example:
    # path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
]
