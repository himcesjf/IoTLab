from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('v1/', include('telemetrix_lab.ingest_api.api.v1.urls')),
    path('docs/', include_docs_urls(title='Telemetrix API Documentation')),
    path('', views.index, name='index'),
    path('devices/', views.device_list, name='device_list'),
    path('devices/<uuid:device_id>/', views.device_detail, name='device_detail'),
    path('anomalies/', views.anomaly_list, name='anomaly_list'),
    path('metrics/', views.metrics_dashboard, name='metrics'),
    path('telemetry-stream/', views.telemetry_stream, name='telemetry_stream'),
] 