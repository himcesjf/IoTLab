from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from telemetrix_lab.ingest_api.devices.models import DeviceType, Device, DeviceConfig
from telemetrix_lab.ingest_api.telemetry.models import Telemetry, AnomalyDetection, Notification
from .serializers import (
    DeviceTypeSerializer, DeviceSerializer, DeviceConfigSerializer,
    TelemetrySerializer, AnomalyDetectionSerializer, NotificationSerializer
)


class DeviceTypeViewSet(viewsets.ModelViewSet):
    queryset = DeviceType.objects.all()
    serializer_class = DeviceTypeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['device_type', 'status', 'location']
    search_fields = ['name', 'location']
    ordering_fields = ['name', 'status', 'last_seen', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def update_config(self, request, pk=None):
        device = self.get_object()
        try:
            config = device.config
        except DeviceConfig.DoesNotExist:
            config = DeviceConfig(device=device)
        
        serializer = DeviceConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def telemetry(self, request, pk=None):
        device = self.get_object()
        
        # Get query parameters for time filtering
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        limit = request.query_params.get('limit', 100)
        
        # Build the queryset with filters
        queryset = device.telemetry.all()
        if start_time:
            queryset = queryset.filter(timestamp__gte=start_time)
        if end_time:
            queryset = queryset.filter(timestamp__lte=end_time)
            
        # Apply limit and order
        queryset = queryset.order_by('-timestamp')[:int(limit)]
        
        serializer = TelemetrySerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def anomalies(self, request, pk=None):
        device = self.get_object()
        
        # Get query parameters
        acknowledged = request.query_params.get('acknowledged')
        severity = request.query_params.get('severity')
        limit = request.query_params.get('limit', 50)
        
        # Build the queryset with filters
        queryset = device.anomalies.all()
        if acknowledged is not None:
            queryset = queryset.filter(acknowledged=(acknowledged.lower() == 'true'))
        if severity:
            queryset = queryset.filter(severity=severity)
            
        # Apply limit and order
        queryset = queryset.order_by('-timestamp')[:int(limit)]
        
        serializer = AnomalyDetectionSerializer(queryset, many=True)
        return Response(serializer.data)


class TelemetryViewSet(viewsets.ModelViewSet):
    queryset = Telemetry.objects.all()
    serializer_class = TelemetrySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['device']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def perform_create(self, serializer):
        # Update the device's last_seen timestamp
        device = serializer.validated_data.get('device')
        device.last_seen = timezone.now()
        device.save(update_fields=['last_seen'])
        
        # Save the telemetry data
        serializer.save()


class AnomalyDetectionViewSet(viewsets.ModelViewSet):
    queryset = AnomalyDetection.objects.all()
    serializer_class = AnomalyDetectionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['device', 'severity', 'acknowledged']
    search_fields = ['description']
    ordering_fields = ['timestamp', 'severity']
    ordering = ['-timestamp']
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        anomaly = self.get_object()
        anomaly.acknowledged = True
        anomaly.save()
        return Response({'status': 'acknowledged'})


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['device', 'notification_type', 'status']
    search_fields = ['subject', 'message', 'recipient']
    ordering_fields = ['created_at', 'sent_at']
    ordering = ['-created_at'] 