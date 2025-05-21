from django.urls import re_path
from telemetrix_lab.ingest_api.api.v1.consumers import TelemetryConsumer

websocket_urlpatterns = [
    re_path(r'ws/telemetry/(?P<device_id>[^/]+)/$', TelemetryConsumer.as_asgi()),
    re_path(r'ws/telemetry/$', TelemetryConsumer.as_asgi()),
] 