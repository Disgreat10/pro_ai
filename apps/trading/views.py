from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import (
    Order, Trade, TradingPair, OrderBook, TestExchangeAPI,
    OrderType, OrderSide, OrderStatus
)
from .engine import MatchingEngine
from .test_exchange import test_exchange_manager
from .serializers import (
    OrderSerializer, TradeSerializer, TradingPairSerializer,
    OrderBookSerializer, TestExchangeAPISerializer
)

class TradingPairViewSet(viewsets.ModelViewSet):
    queryset = TradingPair.objects.filter(is_active=True)
    serializer_class = TradingPairSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def order_book(self, request, pk=None):
        """Get order book for trading pair"""
        pair = self.get_object()
        engine = MatchingEngine(pair)
        snapshot = engine.get_order_book_snapshot()
        return Response(snapshot)

    @action(detail=True, methods=['get'])
    def recent_trades(self, request, pk=None):
        """Get recent trades for trading pair"""
        pair = self.get_object()
        trades = Trade.objects.filter(trading_pair=pair).order_by('-timestamp')[:100]
        return Response(TradeSerializer(trades, many=True).data)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter orders by user unless admin/moderator"""
        if self.request.user.role in ['ADMIN', 'MODERATOR']:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Place a new order"""
        data = request.data.copy()
        data['user'] = request.user.id
        
        # Add client IP and user agent
        data['ip_address'] = request.META.get('REMOTE_ADDR')
        data['user_agent'] = request.META.get('HTTP_USER_AGENT')
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        # Process order through matching engine
        engine = MatchingEngine(order.trading_pair)
        trades = engine.process_order(order)
        
        # If test mode is enabled, place test order
        if 'test_exchange_api' in data:
            try:
                test_trade = test_exchange_manager.place_test_order(
                    order, data['test_exchange_api']
                )
                if test_trade:
                    order.client_order_id = test_trade.exchange_trade_id
                    order.save()
            except Exception as e:
                # Log error but don't fail the order
                logger.error(f"Test order placement failed: {str(e)}")
        
        response_data = serializer.data
        response_data['trades'] = TradeSerializer(trades, many=True).data
        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order"""
        order = self.get_object()
        
        # Check if order can be cancelled
        if order.status not in [OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]:
            return Response(
                {'error': 'Order cannot be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cancel test order if applicable
        if order.client_order_id:
            test_trades = order.testtrade_set.all()
            for test_trade in test_trades:
                test_exchange_manager.cancel_test_order(test_trade)
        
        # Cancel order in matching engine
        engine = MatchingEngine(order.trading_pair)
        if engine.cancel_order(order):
            return Response({'status': 'Order cancelled'})
        return Response(
            {'error': 'Failed to cancel order'},
            status=status.HTTP_400_BAD_REQUEST
        )

class TradeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TradeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter trades by user unless admin/moderator"""
        if self.request.user.role in ['ADMIN', 'MODERATOR']:
            return Trade.objects.all()
        return Trade.objects.filter(
            maker_order__user=self.request.user
        ) | Trade.objects.filter(
            taker_order__user=self.request.user
        )

class TestExchangeAPIViewSet(viewsets.ModelViewSet):
    queryset = TestExchangeAPI.objects.all()
    serializer_class = TestExchangeAPISerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Only admins can see all APIs"""
        if self.request.user.role == 'ADMIN':
            return TestExchangeAPI.objects.all()
        return TestExchangeAPI.objects.filter(is_active=True)

    @action(detail=True, methods=['get'])
    def test_connection(self, request, pk=None):
        """Test connection to exchange API"""
        api = self.get_object()
        client = test_exchange_manager.get_client(api.id)
        if client:
            info = client.get_exchange_info()
            if info:
                api.last_used = timezone.now()
                api.save()
                return Response({'status': 'Connection successful', 'info': info})
        return Response(
            {'error': 'Connection failed'},
            status=status.HTTP_400_BAD_REQUEST
        )
