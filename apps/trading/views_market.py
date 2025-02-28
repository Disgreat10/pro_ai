from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .models import TradingPair
from apps.analytics.models import MarketPrediction, SentimentAnalysis

class MarketWatchView(TemplateView):
    template_name = 'trading/market_watch.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trading_pairs'] = TradingPair.objects.filter(
            is_active=True
        ).order_by('base_asset')
        return context

class AIPredictionView(TemplateView):
    """View for AI-powered trading and market research page"""
    template_name = 'trading/ai_prediction.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get recent trade suggestions
        context['trade_suggestions'] = MarketPrediction.objects.filter(
            prediction_type='PRICE',
            timestamp__gte=timezone.now() - timezone.timedelta(hours=24)
        ).order_by('-timestamp')[:5]

        # Get sentiment analysis data
        context['sentiment_data'] = {
            'BTC/USD': {'score': 0.75, 'confidence': 0.85},
            'ETH/USD': {'score': -0.25, 'confidence': 0.70},
            'XRP/USD': {'score': 0.15, 'confidence': 0.65}
        }

        # Sample on-chain data
        context['on_chain_data'] = [
            {
                'title': 'Whale Transactions',
                'value': '125 transactions',
                'change': 15,
                'description': 'Large transfers in the last 24h'
            },
            {
                'title': 'Network Activity',
                'value': '1.2M transactions',
                'change': -5,
                'description': 'Total blockchain transactions'
            },
            {
                'title': 'Active Addresses',
                'value': '850K',
                'change': 10,
                'description': 'Unique active addresses'
            }
        ]

        # Sample economic calendar
        context['economic_calendar'] = [
            {
                'date': '2024-03-01',
                'title': 'Fed Interest Rate Decision',
                'description': 'Federal Reserve interest rate announcement',
                'impact': 'High Impact'
            },
            {
                'date': '2024-03-02',
                'title': 'NFP Report',
                'description': 'US Non-Farm Payrolls Report',
                'impact': 'High Impact'
            },
            {
                'date': '2024-03-03',
                'title': 'GDP Data',
                'description': 'Quarterly GDP Growth Rate',
                'impact': 'Medium Impact'
            }
        ]

        return context

def market_data_api(request):
    """API endpoint for getting all market data"""
    pairs = TradingPair.objects.filter(is_active=True)
    data = []
    
    for pair in pairs:
        data.append({
            'symbol': f"{pair.base_asset}/{pair.quote_asset}",
            'last_price': str(pair.last_price) if pair.last_price else None,
            'bid_price': str(pair.bid_price) if pair.bid_price else None,
            'ask_price': str(pair.ask_price) if pair.ask_price else None,
            'high_price': str(pair.high_price) if pair.high_price else None,
            'low_price': str(pair.low_price) if pair.low_price else None,
            'open_price': str(pair.open_price) if pair.open_price else None,
            'close_price': str(pair.close_price) if pair.close_price else None,
            'volume_24h': str(pair.volume_24h) if pair.volume_24h else '0',
            'last_updated': pair.last_updated.isoformat() if pair.last_updated else None
        })
    
    return JsonResponse({
        'data': data,
        'timestamp': timezone.now().isoformat()
    })
