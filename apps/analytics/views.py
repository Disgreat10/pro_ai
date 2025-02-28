from rest_framework import viewsets, views, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum, Avg, Count, Q
from datetime import timedelta
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import logging

logger = logging.getLogger('django')

from .models import (
    TradeAnalytics, RevenueReport, RiskExposure,
    ProfitLoss, CustomReport, AnalyticsSnapshot,
    MarketPrediction, SentimentAnalysis, SystemHealth
)
from .serializers import (
    TradeAnalyticsSerializer, RevenueReportSerializer,
    RiskExposureSerializer, ProfitLossSerializer,
    CustomReportSerializer, AnalyticsSnapshotSerializer,
    TradeAnalyticsSummarySerializer, RevenueAnalyticsSerializer,
    RiskMetricsSerializer, MarketPredictionSerializer,
    SentimentAnalysisSerializer, SystemHealthSerializer,
    MarketInsightsSerializer, AITradeSuggestionSerializer
)
from apps.users.permissions import IsModeratorOrAdmin

class TradeAnalyticsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing trade analytics data.
    """
    queryset = TradeAnalytics.objects.all()
    serializer_class = TradeAnalyticsSerializer
    permission_classes = [IsModeratorOrAdmin]

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get summarized trade analytics for different time periods.
        """
        now = timezone.now()
        periods = {
            'daily': now - timedelta(days=1),
            'weekly': now - timedelta(days=7),
            'monthly': now - timedelta(days=30)
        }
        
        summaries = []
        for period_name, start_time in periods.items():
            period_data = self.queryset.filter(timestamp__gte=start_time).aggregate(
                total_volume=Sum('trading_volume'),
                trade_count=Sum('number_of_trades'),
                unique_traders=Avg('active_traders')
            )
            
            # Get popular assets
            popular_assets = (
                self.queryset.filter(timestamp__gte=start_time)
                .values('most_traded_asset')
                .annotate(count=Count('most_traded_asset'))
                .order_by('-count')[:5]
            )
            
            summary = {
                'period': period_name,
                'total_volume': period_data['total_volume'] or 0,
                'trade_count': period_data['trade_count'] or 0,
                'unique_traders': int(period_data['unique_traders'] or 0),
                'popular_assets': list(popular_assets)
            }
            summaries.append(summary)
        
        serializer = TradeAnalyticsSummarySerializer(summaries, many=True)
        return Response(serializer.data)

class RevenueReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing revenue reports.
    """
    queryset = RevenueReport.objects.all()
    serializer_class = RevenueReportSerializer
    permission_classes = [IsModeratorOrAdmin]

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """
        Get revenue analytics with trends and growth rates.
        """
        now = timezone.now()
        periods = {
            'daily': now - timedelta(days=1),
            'weekly': now - timedelta(days=7),
            'monthly': now - timedelta(days=30)
        }
        
        analytics_data = []
        for period_name, start_time in periods.items():
            period_data = self.queryset.filter(start_time__gte=start_time).aggregate(
                total_revenue=Sum('total_revenue'),
                commission=Sum('commission_earnings'),
                spread=Sum('spread_revenue'),
                withdrawal=Sum('withdrawal_fees'),
                other=Sum('other_fees')
            )
            
            # Calculate growth rate
            previous_period = self.queryset.filter(
                start_time__lt=start_time,
                start_time__gte=start_time - timedelta(days=30)
            ).aggregate(prev_revenue=Sum('total_revenue'))
            
            prev_revenue = previous_period['prev_revenue'] or 0
            current_revenue = period_data['total_revenue'] or 0
            growth_rate = ((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue else 0
            
            analytics = {
                'period': period_name,
                'total_revenue': current_revenue,
                'revenue_breakdown': {
                    'commission': period_data['commission'] or 0,
                    'spread': period_data['spread'] or 0,
                    'withdrawal': period_data['withdrawal'] or 0,
                    'other': period_data['other'] or 0
                },
                'growth_rate': growth_rate,
                'trends': self._calculate_trends(start_time)
            }
            analytics_data.append(analytics)
        
        serializer = RevenueAnalyticsSerializer(analytics_data, many=True)
        return Response(serializer.data)

    def _calculate_trends(self, start_time):
        """Calculate revenue trends for the period."""
        data = self.queryset.filter(start_time__gte=start_time).values('start_time', 'total_revenue')
        df = pd.DataFrame(data)
        if not df.empty:
            df['trend'] = df['total_revenue'].pct_change()
            return df['trend'].tolist()
        return []

class RiskExposureViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing risk exposure data.
    """
    queryset = RiskExposure.objects.all()
    serializer_class = RiskExposureSerializer
    permission_classes = [IsModeratorOrAdmin]

    @action(detail=False, methods=['get'])
    def metrics(self, request):
        """
        Get aggregated risk metrics and recommendations.
        """
        latest = self.queryset.first()
        if not latest:
            return Response({'error': 'No risk data available'}, status=status.HTTP_404_NOT_FOUND)
        
        # Calculate risk distribution
        risk_distribution = {
            'high': self.queryset.filter(risk_level='HIGH').count(),
            'medium': self.queryset.filter(risk_level='MEDIUM').count(),
            'low': self.queryset.filter(risk_level='LOW').count()
        }
        
        # Generate risk score (0-100)
        risk_score = (
            (risk_distribution['high'] * 100 +
             risk_distribution['medium'] * 50 +
             risk_distribution['low'] * 10) /
            self.queryset.count()
        )
        
        metrics = {
            'total_exposure': latest.total_leveraged_positions,
            'risk_distribution': risk_distribution,
            'high_risk_positions': risk_distribution['high'],
            'risk_score': risk_score,
            'recommendations': self._generate_recommendations(risk_score, latest)
        }
        
        serializer = RiskMetricsSerializer(metrics)
        return Response(serializer.data)

    def _generate_recommendations(self, risk_score, latest_data):
        """Generate risk management recommendations."""
        recommendations = []
        
        if risk_score > 70:
            recommendations.append("Reduce overall leverage exposure")
        if latest_data.max_leverage_ratio > 20:
            recommendations.append("Consider lowering maximum leverage ratio")
        if latest_data.total_margin_used / latest_data.available_margin > 0.8:
            recommendations.append("High margin usage detected - monitor closely")
            
        return recommendations

class ProfitLossViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing profit and loss data.
    """
    queryset = ProfitLoss.objects.all()
    serializer_class = ProfitLossSerializer
    permission_classes = [IsModeratorOrAdmin]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """
        Get P&L dashboard data with market analysis.
        """
        period = request.query_params.get('period', 'monthly')
        if period == 'monthly':
            start_date = timezone.now() - timedelta(days=30)
        elif period == 'weekly':
            start_date = timezone.now() - timedelta(days=7)
        else:
            start_date = timezone.now() - timedelta(days=1)
            
        data = self.queryset.filter(date__gte=start_date).aggregate(
            total_profit=Sum('net_profit'),
            avg_win_rate=Avg('win_rate'),
            total_volume=Sum('trading_volume')
        )
        
        return Response({
            'period': period,
            'total_profit': data['total_profit'] or 0,
            'average_win_rate': data['avg_win_rate'] or 0,
            'total_volume': data['total_volume'] or 0,
            'market_analysis': self._analyze_market_conditions(start_date)
        })

    def _analyze_market_conditions(self, start_date):
        """Analyze market conditions for the period."""
        conditions = self.queryset.filter(date__gte=start_date).values('market_conditions')
        if not conditions:
            return {}
            
        # Aggregate market conditions
        analysis = {
            'volatility': 0,
            'trend': 'neutral',
            'volume': 0
        }
        
        for condition in conditions:
            mc = condition['market_conditions']
            analysis['volatility'] += mc.get('volatility', 0)
            analysis['volume'] += mc.get('volume', 0)
            
        count = len(conditions)
        if count > 0:
            analysis['volatility'] /= count
            analysis['volume'] /= count
            
        return analysis

class CustomReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing custom reports.
    """
    queryset = CustomReport.objects.all()
    serializer_class = CustomReportSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """
        Generate the report based on specified parameters.
        """
        report = self.get_object()
        try:
            # Generate report based on type and parameters
            # This would typically involve more complex logic
            result_data = self._generate_report_data(report)
            report.result_data = result_data
            report.save()
            
            return Response({
                'status': 'success',
                'message': 'Report generated successfully',
                'data': result_data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _generate_report_data(self, report):
        """Generate report data based on type and parameters."""
        # Implementation would depend on report type
        # This is a placeholder for the actual implementation
        return {'status': 'generated', 'timestamp': timezone.now().isoformat()}

class AnalyticsSnapshotViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing analytics snapshots.
    """
    queryset = AnalyticsSnapshot.objects.all()
    serializer_class = AnalyticsSnapshotSerializer
    permission_classes = [IsModeratorOrAdmin]

    @action(detail=False, methods=['post'])
    def create_snapshot(self, request):
        """
        Create a new analytics snapshot with current metrics.
        """
        try:
            snapshot_type = request.data.get('snapshot_type')
            metrics = self._gather_current_metrics(snapshot_type)
            
            serializer = self.get_serializer(data={
                'snapshot_type': snapshot_type,
                'metrics': metrics
            })
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating analytics snapshot: {str(e)}")
            return Response(
                {'error': 'Failed to create analytics snapshot'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _gather_current_metrics(self, snapshot_type):
        """Gather current metrics based on snapshot type."""
        if snapshot_type == 'TRADING':
            return self._gather_trading_metrics()
        elif snapshot_type == 'FINANCIAL':
            return self._gather_financial_metrics()
        elif snapshot_type == 'RISK':
            return self._gather_risk_metrics()
        return {}

    def _gather_trading_metrics(self):
        """Gather current trading metrics with AI insights."""
        latest_analytics = TradeAnalytics.objects.first()
        if not latest_analytics:
            return {}
            
        # Get recent market predictions
        recent_predictions = MarketPrediction.objects.filter(
            timestamp__gte=timezone.now() - timedelta(hours=24)
        ).values('prediction_type', 'prediction_value', 'confidence_score')
        
        return {
            'volume': float(latest_analytics.trading_volume),
            'active_users': latest_analytics.active_traders,
            'open_positions': 0,  # This would come from the trading system
            'market_predictions': list(recent_predictions)
        }

    def _gather_financial_metrics(self):
        """Gather current financial metrics with sentiment analysis."""
        latest_revenue = RevenueReport.objects.first()
        if not latest_revenue:
            return {}
            
        # Get recent sentiment data
        recent_sentiment = SentimentAnalysis.objects.filter(
            timestamp__gte=timezone.now() - timedelta(hours=24)
        ).aggregate(Avg('sentiment_score'))
        
        return {
            'revenue': float(latest_revenue.total_revenue),
            'profit': 0,  # This would come from P&L calculations
            'expenses': 0,  # This would come from expense tracking
            'market_sentiment': recent_sentiment['sentiment_score__avg'] or 0
        }

    def _gather_risk_metrics(self):
        """Gather current risk metrics with system health data."""
        latest_risk = RiskExposure.objects.first()
        if not latest_risk:
            return {}
            
        # Get system health status
        system_health = SystemHealth.objects.filter(
            timestamp__gte=timezone.now() - timedelta(minutes=5)
        ).values('component', 'status')
        
        return {
            'exposure': float(latest_risk.total_leveraged_positions),
            'leverage': float(latest_risk.max_leverage_ratio),
            'margin': float(latest_risk.total_margin_used),
            'system_health': list(system_health)
        }

class MarketPredictionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing market predictions.
    """
    queryset = MarketPrediction.objects.all()
    serializer_class = MarketPredictionSerializer
    permission_classes = [IsModeratorOrAdmin]

    @action(detail=False, methods=['get'])
    def asset_predictions(self, request):
        """
        Get predictions for a specific asset.
        """
        try:
            asset = request.query_params.get('asset')
            if not asset:
                return Response(
                    {'error': 'Asset parameter is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            predictions = self.queryset.filter(
                asset=asset,
                timestamp__gte=timezone.now() - timedelta(days=7)
            ).order_by('-timestamp')

            serializer = self.get_serializer(predictions, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching asset predictions: {str(e)}")
            return Response(
                {'error': 'Failed to fetch predictions'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def generate_suggestions(self, request):
        """
        Generate AI-powered trade suggestions based on predictions.
        """
        try:
            asset = request.query_params.get('asset')
            if not asset:
                return Response(
                    {'error': 'Asset parameter is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get recent predictions and sentiment data
            predictions = self.queryset.filter(
                asset=asset,
                timestamp__gte=timezone.now() - timedelta(hours=24)
            )
            sentiment = SentimentAnalysis.objects.filter(
                asset=asset,
                timestamp__gte=timezone.now() - timedelta(hours=24)
            ).aggregate(Avg('sentiment_score'))

            if not predictions:
                return Response(
                    {'error': 'No recent predictions available'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Simple algorithm to generate trade suggestion
            avg_prediction = predictions.aggregate(
                Avg('prediction_value'),
                Avg('confidence_score')
            )
            sentiment_score = sentiment['sentiment_score__avg'] or 0

            suggestion = self._generate_trade_suggestion(
                avg_prediction['prediction_value__avg'],
                sentiment_score
            )

            serializer = AITradeSuggestionSerializer(data={
                'asset': asset,
                'suggestion': suggestion['action'],
                'confidence_score': suggestion['confidence'],
                'supporting_data': {
                    'prediction_avg': float(avg_prediction['prediction_value__avg']),
                    'sentiment_score': float(sentiment_score)
                },
                'generated_at': timezone.now(),
                'expiry_time': timezone.now() + timedelta(hours=1),
                'risk_level': suggestion['risk_level']
            })
            serializer.is_valid(raise_exception=True)
            
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error generating trade suggestions: {str(e)}")
            return Response(
                {'error': 'Failed to generate suggestions'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _generate_trade_suggestion(self, prediction_value, sentiment_score):
        """Generate trade suggestion based on predictions and sentiment."""
        # Normalize prediction value to -1 to 1 range
        normalized_prediction = min(max(prediction_value / 100, -1), 1)
        
        # Combine prediction and sentiment with weights
        combined_signal = (normalized_prediction * 0.7) + (sentiment_score * 0.3)
        
        # Determine action based on combined signal
        if combined_signal > 0.3:
            action = 'BUY'
        elif combined_signal < -0.3:
            action = 'SELL'
        else:
            action = 'HOLD'
            
        # Calculate confidence and risk level
        confidence = abs(combined_signal)
        if confidence > 0.7:
            risk_level = 'LOW'
        elif confidence > 0.4:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'HIGH'
            
        return {
            'action': action,
            'confidence': min(confidence, 1.0),
            'risk_level': risk_level
        }

class SentimentAnalysisViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing sentiment analysis data.
    """
    queryset = SentimentAnalysis.objects.all()
    serializer_class = SentimentAnalysisSerializer
    permission_classes = [IsModeratorOrAdmin]

    @action(detail=False, methods=['get'])
    def market_mood(self, request):
        """
        Get overall market mood based on sentiment analysis.
        """
        try:
            # Get sentiment data for the last 24 hours
            start_time = timezone.now() - timedelta(hours=24)
            sentiments = self.queryset.filter(timestamp__gte=start_time)
            
            if not sentiments:
                return Response(
                    {'error': 'No recent sentiment data available'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Calculate mood by source type
            mood_by_source = {}
            for source in ['NEWS', 'SOCIAL', 'TRADING']:
                source_sentiment = sentiments.filter(source_type=source).aggregate(
                    avg_score=Avg('sentiment_score'),
                    confidence=Avg('confidence_score')
                )
                if source_sentiment['avg_score'] is not None:
                    mood_by_source[source] = {
                        'score': float(source_sentiment['avg_score']),
                        'confidence': float(source_sentiment['confidence'])
                    }
            
            # Calculate overall market mood
            overall_sentiment = sentiments.aggregate(
                avg_score=Avg('sentiment_score'),
                confidence=Avg('confidence_score')
            )
            
            return Response({
                'overall_mood': {
                    'score': float(overall_sentiment['avg_score']),
                    'confidence': float(overall_sentiment['confidence']),
                    'interpretation': self._interpret_sentiment(
                        overall_sentiment['avg_score']
                    )
                },
                'mood_by_source': mood_by_source,
                'timestamp': timezone.now()
            })
        except Exception as e:
            logger.error(f"Error calculating market mood: {str(e)}")
            return Response(
                {'error': 'Failed to calculate market mood'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _interpret_sentiment(self, sentiment_score):
        """Interpret sentiment score into market mood."""
        if sentiment_score > 0.5:
            return 'VERY_BULLISH'
        elif sentiment_score > 0.1:
            return 'BULLISH'
        elif sentiment_score > -0.1:
            return 'NEUTRAL'
        elif sentiment_score > -0.5:
            return 'BEARISH'
        else:
            return 'VERY_BEARISH'

class SystemHealthViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing system health monitoring.
    """
    queryset = SystemHealth.objects.all()
    serializer_class = SystemHealthSerializer
    permission_classes = [IsModeratorOrAdmin]

    @action(detail=False, methods=['get'])
    def system_status(self, request):
        """
        Get current system health status.
        """
        try:
            # Get latest health metrics for each component
            components = self.queryset.values('component').distinct()
            status_by_component = {}
            
            for comp in components:
                latest_metrics = self.queryset.filter(
                    component=comp['component']
                ).order_by('-timestamp').first()
                
                if latest_metrics:
                    status_by_component[comp['component']] = {
                        'status': latest_metrics.status,
                        'metrics': {
                            'type': latest_metrics.metric_type,
                            'value': float(latest_metrics.metric_value)
                        },
                        'last_updated': latest_metrics.timestamp
                    }
            
            # Calculate overall system health
            critical_count = self.queryset.filter(
                status='CRITICAL',
                timestamp__gte=timezone.now() - timedelta(minutes=5)
            ).count()
            warning_count = self.queryset.filter(
                status='WARNING',
                timestamp__gte=timezone.now() - timedelta(minutes=5)
            ).count()
            
            overall_status = 'HEALTHY'
            if critical_count > 0:
                overall_status = 'CRITICAL'
            elif warning_count > 0:
                overall_status = 'WARNING'
            
            return Response({
                'overall_status': overall_status,
                'components': status_by_component,
                'alerts': {
                    'critical': critical_count,
                    'warning': warning_count
                },
                'timestamp': timezone.now()
            })
        except Exception as e:
            logger.error(f"Error fetching system status: {str(e)}")
            return Response(
                {'error': 'Failed to fetch system status'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def performance_metrics(self, request):
        """
        Get system performance metrics over time.
        """
        try:
            # Get metrics for the last hour
            start_time = timezone.now() - timedelta(hours=1)
            metrics = self.queryset.filter(timestamp__gte=start_time)
            
            # Calculate metrics by component
            performance_data = {}
            for metric in metrics:
                if metric.component not in performance_data:
                    performance_data[metric.component] = {
                        'metrics': [],
                        'average': 0,
                        'peak': 0
                    }
                
                performance_data[metric.component]['metrics'].append({
                    'timestamp': metric.timestamp,
                    'value': float(metric.metric_value),
                    'type': metric.metric_type
                })
                
                # Update averages and peaks
                metrics_list = performance_data[metric.component]['metrics']
                values = [m['value'] for m in metrics_list]
                performance_data[metric.component]['average'] = sum(values) / len(values)
                performance_data[metric.component]['peak'] = max(values)
            
            return Response({
                'performance_data': performance_data,
                'time_range': {
                    'start': start_time,
                    'end': timezone.now()
                }
            })
        except Exception as e:
            logger.error(f"Error fetching performance metrics: {str(e)}")
            return Response(
                {'error': 'Failed to fetch performance metrics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
