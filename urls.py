from django.contrib import admin
from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from views import (
    index, device_list, device_detail, anomaly_list, 
    metrics_dashboard, telemetry_stream, acknowledge_anomaly
)

# Dashboard URL patterns
dashboard_patterns = [
    path('', index, name='index'),
    path('devices/', device_list, name='device_list'),
    path('devices/<uuid:device_id>/', device_detail, name='device_detail'),
    path('anomalies/', anomaly_list, name='anomaly_list'),
    path('anomalies/<int:anomaly_id>/acknowledge/', acknowledge_anomaly, name='acknowledge_anomaly'),
    path('metrics/', metrics_dashboard, name='metrics'),
    path('telemetry-stream/', telemetry_stream, name='telemetry_stream'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('telemetrix_lab.ingest_api.api.urls')),
    path('api/devices/', include('telemetrix_lab.ingest_api.devices.urls')),
    path('api/telemetry/', include('telemetrix_lab.ingest_api.telemetry.urls')),
    path('api/docs/', include_docs_urls(title='IoT Lab API Documentation')),
    path('', include((dashboard_patterns, 'dashboard'), namespace='dashboard')),
] 