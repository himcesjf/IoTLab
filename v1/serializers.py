from rest_framework import serializers
from iotlab.ingest_api.devices.models import DeviceType, Device, DeviceConfig
from iotlab.ingest_api.telemetry.models import Telemetry, AnomalyDetection


class DeviceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceType
        fields = ['id', 'name', 'description', 'schema', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class DeviceConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceConfig
        fields = ['id', 'config', 'publishing_interval', 'failure_rate', 
                  'noise_factor', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class DeviceSerializer(serializers.ModelSerializer):
    device_type = DeviceTypeSerializer(read_only=True)
    device_type_id = serializers.PrimaryKeyRelatedField(
        write_only=True, 
        queryset=DeviceType.objects.all(),
        source='device_type'
    )
    config = DeviceConfigSerializer(read_only=True)
    
    class Meta:
        model = Device
        fields = ['id', 'name', 'device_type', 'device_type_id', 'status', 
                  'location', 'metadata', 'last_seen', 'config', 
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'last_seen', 'created_at', 'updated_at']


class TelemetrySerializer(serializers.ModelSerializer):
    device_id = serializers.UUIDField(source='device.id', read_only=True)
    device_name = serializers.CharField(source='device.name', read_only=True)
    
    class Meta:
        model = Telemetry
        fields = ['id', 'device', 'device_id', 'device_name', 'timestamp', 'data']
        read_only_fields = ['id']
        

class AnomalyDetectionSerializer(serializers.ModelSerializer):
    device_id = serializers.UUIDField(source='device.id', read_only=True)
    device_name = serializers.CharField(source='device.name', read_only=True)
    
    class Meta:
        model = AnomalyDetection
        fields = ['id', 'telemetry', 'device', 'device_id', 'device_name',
                  'timestamp', 'severity', 'description', 'anomaly_data', 
                  'acknowledged']
        read_only_fields = ['id', 'telemetry', 'device', 'timestamp']

