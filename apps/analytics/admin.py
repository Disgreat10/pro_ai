from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Avg, Count
from .models import (
    TradeAnalytics, RevenueReport, RiskExposure,
    ProfitLoss, CustomReport, AnalyticsSnapshot,
    MarketPrediction, SentimentAnalysis, SystemHealth
)

@admin.register(TradeAnalytics)
class TradeAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'active_traders', 'trading_volume', 'number_of_trades', 'average_trade_size', 'most_traded_asset')
    list_filter = ('timestamp', 'most_traded_asset')
    search_fields = ('most_traded_asset',)
    ordering = ('-timestamp',)
    
    def get_readonly_fields(self, request, obj=None):
        return ('timestamp',) if obj else ()

@admin.register(RevenueReport)
class RevenueReportAdmin(admin.ModelAdmin):
    list_display = ('period', 'start_time', 'end_time', 'total_revenue', 'commission_earnings', 'spread_revenue')
    list_filter = ('period', 'start_time')
    search_fields = ('period',)
    ordering = ('-start_time',)
    
    def get_readonly_fields(self, request, obj=None):
        return ('total_revenue',) if obj else ()

@admin.register(RiskExposure)
class RiskExposureAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'total_leveraged_positions', 'max_leverage_ratio', 'risk_level', 'margin_status')
    list_filter = ('risk_level', 'timestamp')
    search_fields = ('risk_level',)
    ordering = ('-timestamp',)
    
    def margin_status(self, obj):
        margin_ratio = obj.total_margin_used / obj.available_margin if obj.available_margin else 0
        if margin_ratio > 0.8:
            return format_html('<span style="color: red;">High Usage ({}%)</span>', int(margin_ratio * 100))
        elif margin_ratio > 0.5:
            return format_html('<span style="color: orange;">Moderate ({}%)</span>', int(margin_ratio * 100))
        return format_html('<span style="color: green;">Healthy ({}%)</span>', int(margin_ratio * 100))
    
    margin_status.short_description = 'Margin Status'

@admin.register(ProfitLoss)
class ProfitLossAdmin(admin.ModelAdmin):
    list_display = ('date', 'net_profit', 'gross_profit', 'gross_loss', 'win_rate', 'trading_volume')
    list_filter = ('date',)
    search_fields = ('date',)
    ordering = ('-date',)
    
    def get_readonly_fields(self, request, obj=None):
        return ('net_profit',) if obj else ()

@admin.register(CustomReport)
class CustomReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'created_by', 'created_at', 'file_format', 'view_report')
    list_filter = ('report_type', 'created_at', 'file_format')
    search_fields = ('title', 'description', 'created_by__username')
    ordering = ('-created_at',)
    
    def view_report(self, obj):
        if obj.file_url:
            return format_html('<a href="{}" target="_blank">View Report</a>', obj.file_url)
        return "No file available"
    
    view_report.short_description = 'Report'

@admin.register(AnalyticsSnapshot)
class AnalyticsSnapshotAdmin(admin.ModelAdmin):
    list_display = ('snapshot_type', 'timestamp', 'display_metrics')
    list_filter = ('snapshot_type', 'timestamp')
    search_fields = ('snapshot_type',)
    ordering = ('-timestamp',)
    
    def display_metrics(self, obj):
        return format_html('<pre>{}</pre>', obj.metrics)
    
    display_metrics.short_description = 'Metrics'

@admin.register(MarketPrediction)
class MarketPredictionAdmin(admin.ModelAdmin):
    list_display = ('asset', 'prediction_type', 'prediction_value', 'confidence_score', 'time_horizon', 'timestamp')
    list_filter = ('asset', 'prediction_type', 'time_horizon', 'timestamp')
    search_fields = ('asset', 'prediction_type')
    ordering = ('-timestamp',)
    
    def get_readonly_fields(self, request, obj=None):
        return ('timestamp',) if obj else ()
    
    def changelist_view(self, request, extra_context=None):
        # Add summary statistics to the change list view
        response = super().changelist_view(request, extra_context)
        
        try:
            qs = self.get_queryset(request)
            extra_context = {
                'avg_confidence': qs.aggregate(Avg('confidence_score'))['confidence_score__avg'],
                'prediction_counts': qs.values('prediction_type').annotate(count=Count('id')),
            }
            response.context_data.update(extra_context)
        except (AttributeError, KeyError):
            pass
        
        return response

@admin.register(SentimentAnalysis)
class SentimentAnalysisAdmin(admin.ModelAdmin):
    list_display = ('asset', 'source_type', 'sentiment_score', 'confidence_score', 'timestamp', 'sentiment_indicator')
    list_filter = ('asset', 'source_type', 'timestamp')
    search_fields = ('asset', 'source_type')
    ordering = ('-timestamp',)
    
    def sentiment_indicator(self, obj):
        if obj.sentiment_score > 0.5:
            return format_html('<span style="color: green;">Very Bullish</span>')
        elif obj.sentiment_score > 0.1:
            return format_html('<span style="color: lightgreen;">Bullish</span>')
        elif obj.sentiment_score > -0.1:
            return format_html('<span style="color: gray;">Neutral</span>')
        elif obj.sentiment_score > -0.5:
            return format_html('<span style="color: orange;">Bearish</span>')
        return format_html('<span style="color: red;">Very Bearish</span>')
    
    sentiment_indicator.short_description = 'Market Sentiment'

@admin.register(SystemHealth)
class SystemHealthAdmin(admin.ModelAdmin):
    list_display = ('component', 'metric_type', 'metric_value', 'status', 'timestamp', 'health_indicator')
    list_filter = ('component', 'metric_type', 'status', 'timestamp')
    search_fields = ('component', 'metric_type')
    ordering = ('-timestamp',)
    
    def health_indicator(self, obj):
        if obj.status == 'HEALTHY':
            return format_html('<span style="color: green;">●</span> Healthy')
        elif obj.status == 'WARNING':
            return format_html('<span style="color: orange;">●</span> Warning')
        return format_html('<span style="color: red;">●</span> Critical')
    
    health_indicator.short_description = 'Health Status'
    
    def changelist_view(self, request, extra_context=None):
        # Add summary statistics to the change list view
        response = super().changelist_view(request, extra_context)
        
        try:
            qs = self.get_queryset(request)
            status_summary = qs.values('status').annotate(count=Count('id'))
            critical_components = qs.filter(status='CRITICAL').values_list('component', flat=True)
            
            extra_context = {
                'status_summary': status_summary,
                'critical_components': critical_components,
            }
            response.context_data.update(extra_context)
        except (AttributeError, KeyError):
            pass
        
        return response

# Register custom admin site header and title
admin.site.site_header = 'BlackBox Trader Analytics Admin'
admin.site.site_title = 'BlackBox Trader Analytics'
admin.site.index_title = 'Analytics Dashboard'
