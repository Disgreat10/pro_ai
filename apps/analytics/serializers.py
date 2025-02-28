from rest_framework import serializers
from .models import (
    TradeAnalytics, RevenueReport, RiskExposure,
    ProfitLoss, CustomReport, AnalyticsSnapshot,
    MarketPrediction, SentimentAnalysis, SystemHealth
)

class TradeAnalyticsSerializer(serializers.ModelSerializer):
    """
    Serializer for trade analytics data.
    """
    class Meta:
        model = TradeAnalytics
        fields = '__all__'
        read_only_fields = ['timestamp']

class RevenueReportSerializer(serializers.ModelSerializer):
    """
    Serializer for revenue reports.
    """
    class Meta:
        model = RevenueReport
        fields = '__all__'
        read_only_fields = ['total_revenue']

    def validate(self, data):
        """
        Validate that end_time is after start_time.
        """
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError("End time must be after start time")
        return data

class RiskExposureSerializer(serializers.ModelSerializer):
    """
    Serializer for risk exposure data.
    """
    class Meta:
        model = RiskExposure
        fields = '__all__'
        read_only_fields = ['timestamp']

    def validate_exposure_by_asset(self, value):
        """
        Validate the exposure_by_asset JSON structure.
        """
        required_keys = ['asset', 'exposure', 'risk_ratio']
        for asset_data in value:
            if not all(key in asset_data for key in required_keys):
                raise serializers.ValidationError(
                    f"Each asset exposure must contain: {', '.join(required_keys)}"
                )
        return value

class ProfitLossSerializer(serializers.ModelSerializer):
    """
    Serializer for profit and loss data.
    """
    class Meta:
        model = ProfitLoss
        fields = '__all__'
        read_only_fields = ['net_profit']

    def validate_market_conditions(self, value):
        """
        Validate the market_conditions JSON structure.
        """
        required_keys = ['volatility', 'trend', 'volume']
        if not all(key in value for key in required_keys):
            raise serializers.ValidationError(
                f"Market conditions must contain: {', '.join(required_keys)}"
            )
        return value

class CustomReportSerializer(serializers.ModelSerializer):
    """
    Serializer for custom generated reports.
    """
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = CustomReport
        fields = '__all__'
        read_only_fields = ['created_at', 'created_by', 'file_url']

    def validate_parameters(self, value):
        """
        Validate the report parameters based on report_type.
        """
        report_type = self.initial_data.get('report_type')
        required_params = {
            'TRADING': ['start_date', 'end_date', 'assets'],
            'REVENUE': ['period', 'categories'],
            'RISK': ['exposure_type', 'threshold'],
        }
        
        if report_type in required_params:
            missing_params = [
                param for param in required_params[report_type]
                if param not in value
            ]
            if missing_params:
                raise serializers.ValidationError(
                    f"Missing required parameters for {report_type}: {', '.join(missing_params)}"
                )
        return value

class AnalyticsSnapshotSerializer(serializers.ModelSerializer):
    """
    Serializer for analytics snapshots.
    """
    class Meta:
        model = AnalyticsSnapshot
        fields = '__all__'
        read_only_fields = ['timestamp']

    def validate_metrics(self, value):
        """
        Validate the metrics JSON structure based on snapshot_type.
        """
        snapshot_type = self.initial_data.get('snapshot_type')
        required_metrics = {
            'TRADING': ['volume', 'active_users', 'open_positions'],
            'FINANCIAL': ['revenue', 'profit', 'expenses'],
            'RISK': ['exposure', 'leverage', 'margin'],
        }
        
        if snapshot_type in required_metrics:
            missing_metrics = [
                metric for metric in required_metrics[snapshot_type]
                if metric not in value
            ]
            if missing_metrics:
                raise serializers.ValidationError(
                    f"Missing required metrics for {snapshot_type}: {', '.join(missing_metrics)}"
                )
        return value

# Additional serializers for specific analytics views

class TradeAnalyticsSummarySerializer(serializers.Serializer):
    """
    Serializer for summarized trade analytics data.
    """
    period = serializers.CharField()
    total_volume = serializers.DecimalField(max_digits=20, decimal_places=8)
    trade_count = serializers.IntegerField()
    unique_traders = serializers.IntegerField()
    popular_assets = serializers.ListField(child=serializers.DictField())

class RevenueAnalyticsSerializer(serializers.Serializer):
    """
    Serializer for revenue analytics data.
    """
    period = serializers.CharField()
    total_revenue = serializers.DecimalField(max_digits=20, decimal_places=8)
    revenue_breakdown = serializers.DictField()
    growth_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    trends = serializers.ListField()

class RiskMetricsSerializer(serializers.Serializer):
    """
    Serializer for aggregated risk metrics.
    """
    total_exposure = serializers.DecimalField(max_digits=20, decimal_places=8)
    risk_distribution = serializers.DictField()
    high_risk_positions = serializers.IntegerField()
    risk_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    recommendations = serializers.ListField()

class MarketPredictionSerializer(serializers.ModelSerializer):
    """
    Serializer for market predictions and AI-generated insights.
    """
    class Meta:
        model = MarketPrediction
        fields = '__all__'
        read_only_fields = ['timestamp']

    def validate(self, data):
        """
        Validate that confidence score is between 0 and 1.
        """
        if not 0 <= data['confidence_score'] <= 1:
            raise serializers.ValidationError("Confidence score must be between 0 and 1")
        return data

class SentimentAnalysisSerializer(serializers.ModelSerializer):
    """
    Serializer for market sentiment analysis data.
    """
    class Meta:
        model = SentimentAnalysis
        fields = '__all__'
        read_only_fields = ['timestamp']

    def validate(self, data):
        """
        Validate sentiment and confidence scores.
        """
        if not -1 <= data['sentiment_score'] <= 1:
            raise serializers.ValidationError("Sentiment score must be between -1 and 1")
        if not 0 <= data['confidence_score'] <= 1:
            raise serializers.ValidationError("Confidence score must be between 0 and 1")
        return data

class SystemHealthSerializer(serializers.ModelSerializer):
    """
    Serializer for system health monitoring data.
    """
    class Meta:
        model = SystemHealth
        fields = '__all__'
        read_only_fields = ['timestamp']

    def validate_metric_value(self, value):
        """
        Validate that metric value is non-negative.
        """
        if value < 0:
            raise serializers.ValidationError("Metric value cannot be negative")
        return value

class MarketInsightsSerializer(serializers.Serializer):
    """
    Serializer for aggregated market insights combining predictions and sentiment.
    """
    asset = serializers.CharField()
    predictions = MarketPredictionSerializer(many=True)
    sentiment = SentimentAnalysisSerializer(many=True)
    system_status = serializers.DictField()
    timestamp = serializers.DateTimeField()
    
    def validate(self, data):
        """
        Validate that predictions and sentiment analyses are for the same asset.
        """
        asset = data['asset']
        for pred in data['predictions']:
            if pred['asset'] != asset:
                raise serializers.ValidationError("All predictions must be for the same asset")
        for sent in data['sentiment']:
            if sent['asset'] != asset:
                raise serializers.ValidationError("All sentiment analyses must be for the same asset")
        return data

class AITradeSuggestionSerializer(serializers.Serializer):
    """
    Serializer for AI-generated trade suggestions.
    """
    asset = serializers.CharField()
    suggestion = serializers.ChoiceField(choices=['BUY', 'SELL', 'HOLD'])
    confidence_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    supporting_data = serializers.DictField()
    generated_at = serializers.DateTimeField()
    expiry_time = serializers.DateTimeField()
    risk_level = serializers.ChoiceField(choices=['LOW', 'MEDIUM', 'HIGH'])
    
    def validate(self, data):
        """
        Validate suggestion data.
        """
        if data['generated_at'] >= data['expiry_time']:
            raise serializers.ValidationError("Expiry time must be after generation time")
        if not 0 <= data['confidence_score'] <= 1:
            raise serializers.ValidationError("Confidence score must be between 0 and 1")
        return data
