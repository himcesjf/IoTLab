from django.contrib import admin
from .models import Telemetry, AnomalyDetection, Notification





@admin.register(Telemetry)
class TelemetryAdmin(admin.ModelAdmin):
    list_display = ('device', 'timestamp', 'id')
    list_filter = ('device', 'timestamp')
    search_fields = ('device__name', 'device__id')
    readonly_fields = ('id', 'device', 'timestamp', 'data')
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AnomalyDetection)
class AnomalyDetectionAdmin(admin.ModelAdmin):
    list_display = ('device', 'severity', 'timestamp', 'acknowledged')
    list_filter = ('device', 'severity', 'acknowledged', 'timestamp')
    search_fields = ('device__name', 'description')
    readonly_fields = ('telemetry', 'device', 'timestamp', 'anomaly_data')
    date_hierarchy = 'timestamp'
    actions = ['mark_acknowledged']
    
    def mark_acknowledged(self, request, queryset):
        updated = queryset.update(acknowledged=True)
        self.message_user(
            request, 
            f"{updated} anomalies marked as acknowledged."
        )
    mark_acknowledged.short_description = "Mark selected anomalies as acknowledged"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('device', 'notification_type', 'status', 'created_at', 'sent_at')
    list_filter = ('notification_type', 'status', 'created_at')
    search_fields = ('device__name', 'recipient', 'subject')
    readonly_fields = ('anomaly', 'device', 'created_at', 'sent_at')
    date_hierarchy = 'created_at'
    fieldsets = (
        (None, {
            'fields': ('anomaly', 'device', 'notification_type', 'status')
        }),
        ('Notification Content', {
            'fields': ('recipient', 'subject', 'message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'sent_at'),
            'classes': ('collapse',)
        }),
    ) 