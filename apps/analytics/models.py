from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()

class TradeAnalytics(models.Model):
    """
    Model for storing real-time trade analytics data.
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    active_traders = models.IntegerField(default=0)
    trading_volume = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    number_of_trades = models.IntegerField(default=0)
    average_trade_size = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    most_traded_asset = models.CharField(max_length=50, blank=True)
    
    class Meta:
        verbose_name = _('Trade Analytics')
        verbose_name_plural = _('Trade Analytics')
        ordering = ['-timestamp']

    def __str__(self):
        return f"Trade Analytics - {self.timestamp}"

class RevenueReport(models.Model):
    """
    Model for tracking platform revenue from various sources.
    """
    class ReportPeriod(models.TextChoices):
        HOURLY = 'HOURLY', _('Hourly')
        DAILY = 'DAILY', _('Daily')
        WEEKLY = 'WEEKLY', _('Weekly')
        MONTHLY = 'MONTHLY', _('Monthly')

    period = models.CharField(max_length=10, choices=ReportPeriod.choices)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    commission_earnings = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    spread_revenue = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    withdrawal_fees = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    other_fees = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    total_revenue = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    
    class Meta:
        verbose_name = _('Revenue Report')
        verbose_name_plural = _('Revenue Reports')
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['period', 'start_time']),
        ]

    def __str__(self):
        return f"{self.period} Revenue Report - {self.start_time}"

    def save(self, *args, **kwargs):
        # Calculate total revenue before saving
        self.total_revenue = (
            self.commission_earnings +
            self.spread_revenue +
            self.withdrawal_fees +
            self.other_fees
        )
        super().save(*args, **kwargs)

class RiskExposure(models.Model):
    """
    Model for tracking platform's risk exposure.
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    total_leveraged_positions = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    max_leverage_ratio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_margin_used = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    available_margin = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    risk_level = models.CharField(max_length=20, default='NORMAL')
    exposure_by_asset = models.JSONField(default=dict)
    
    class Meta:
        verbose_name = _('Risk Exposure')
        verbose_name_plural = _('Risk Exposures')
        ordering = ['-timestamp']

    def __str__(self):
        return f"Risk Exposure - {self.timestamp}"

class ProfitLoss(models.Model):
    """
    Model for tracking platform's profit and loss.
    """
    date = models.DateField()
    gross_profit = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    gross_loss = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    net_profit = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    trading_volume = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    market_conditions = models.JSONField(default=dict)
    
    class Meta:
        verbose_name = _('Profit & Loss')
        verbose_name_plural = _('Profit & Loss')
        ordering = ['-date']

    def __str__(self):
        return f"P&L Report - {self.date}"

    def save(self, *args, **kwargs):
        # Calculate net profit before saving
        self.net_profit = self.gross_profit - self.gross_loss
        super().save(*args, **kwargs)

class CustomReport(models.Model):
    """
    Model for storing custom generated reports.
    """
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    report_type = models.CharField(max_length=50)
    parameters = models.JSONField(default=dict)
    result_data = models.JSONField(default=dict)
    file_format = models.CharField(max_length=10)  # CSV, PDF, etc.
    file_url = models.URLField(blank=True)
    
    class Meta:
        verbose_name = _('Custom Report')
        verbose_name_plural = _('Custom Reports')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.created_at}"

class AnalyticsSnapshot(models.Model):
    """
    Model for storing periodic snapshots of key analytics metrics.
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    metrics = models.JSONField()
    snapshot_type = models.CharField(max_length=50)
    
    class Meta:
        verbose_name = _('Analytics Snapshot')
        verbose_name_plural = _('Analytics Snapshots')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.snapshot_type} Snapshot - {self.timestamp}"

class MarketPrediction(models.Model):
    """
    Model for storing AI-generated market predictions and insights.
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    asset = models.CharField(max_length=50)
    prediction_type = models.CharField(max_length=20, choices=[
        ('PRICE', 'Price Movement'),
        ('VOLUME', 'Volume Trend'),
        ('VOLATILITY', 'Volatility Forecast')
    ])
    prediction_value = models.DecimalField(max_digits=20, decimal_places=8)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2)
    time_horizon = models.CharField(max_length=20, choices=[
        ('SHORT', 'Short Term'),
        ('MEDIUM', 'Medium Term'),
        ('LONG', 'Long Term')
    ])
    features_used = models.JSONField(help_text="Features used in prediction")
    model_version = models.CharField(max_length=50)
    
    class Meta:
        verbose_name = _('Market Prediction')
        verbose_name_plural = _('Market Predictions')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['asset', 'prediction_type', 'time_horizon']),
        ]

    def __str__(self):
        return f"{self.asset} {self.prediction_type} Prediction - {self.timestamp}"

class SentimentAnalysis(models.Model):
    """
    Model for tracking market sentiment from various sources.
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    asset = models.CharField(max_length=50)
    source_type = models.CharField(max_length=20, choices=[
        ('NEWS', 'News Articles'),
        ('SOCIAL', 'Social Media'),
        ('TRADING', 'Trading Activity')
    ])
    sentiment_score = models.DecimalField(max_digits=5, decimal_places=2)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2)
    source_data = models.JSONField(help_text="Raw data used for sentiment analysis")
    analysis_version = models.CharField(max_length=50)
    
    class Meta:
        verbose_name = _('Sentiment Analysis')
        verbose_name_plural = _('Sentiment Analyses')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['asset', 'source_type']),
        ]

    def __str__(self):
        return f"{self.asset} Sentiment from {self.source_type} - {self.timestamp}"

class SystemHealth(models.Model):
    """
    Model for monitoring platform performance and system health.
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    component = models.CharField(max_length=50)
    metric_type = models.CharField(max_length=20, choices=[
        ('LATENCY', 'API Latency'),
        ('ERROR_RATE', 'Error Rate'),
        ('LOAD', 'System Load'),
        ('MEMORY', 'Memory Usage'),
        ('CPU', 'CPU Usage')
    ])
    metric_value = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('HEALTHY', 'Healthy'),
        ('WARNING', 'Warning'),
        ('CRITICAL', 'Critical')
    ])
    details = models.JSONField(help_text="Additional monitoring details")
    
    class Meta:
        verbose_name = _('System Health')
        verbose_name_plural = _('System Health Records')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['component', 'metric_type', 'status']),
        ]

    def __str__(self):
        return f"{self.component} {self.metric_type} Status: {self.status} - {self.timestamp}"
