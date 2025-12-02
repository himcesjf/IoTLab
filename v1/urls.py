from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'device-types', views.DeviceTypeViewSet)
router.register(r'devices', views.DeviceViewSet)
router.register(r'telemetry', views.TelemetryViewSet)
router.register(r'anomalies', views.AnomalyDetectionViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 