from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('devices/', views.device_list, name='device_list'),
    path('devices/<uuid:device_id>/', views.device_detail, name='device_detail'),
    path('anomalies/', views.anomaly_list, name='anomaly_list'),
path('anomalies/<int:anomaly_id>/acknowledge/', views.acknowledge_anomaly, name='acknowledge_anomaly'),
    path('metrics/', views.metrics_dashboard, name='metrics'),
    path('telemetry-stream/', views.telemetry_stream, name='telemetry_stream'),
]

