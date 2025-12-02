import json
import uuid
import logging
import paho.mqtt.client as mqtt
from django.conf import settings
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.serializers.json import DjangoJSONEncoder

from iotlab.ingest_api.devices.models import Device
from iotlab.ingest_api.telemetry.models import Telemetry, AnomalyDetection

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


class MQTTClient:
    """MQTT Client for receiving telemetry data from IoT devices."""
    
    def __init__(self):
        self.client = mqtt.Client(client_id=settings.MQTT_CLIENT_ID)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        # Configure logger
        self.logger = logging.getLogger(__name__)
    
    def connect(self):
        """Connect to the MQTT broker."""
        try:
            self.client.connect(
                settings.MQTT_BROKER_HOST,
                settings.MQTT_BROKER_PORT,
                settings.MQTT_KEEPALIVE
            )
            self.client.loop_start()
            self.logger.info(f"Connected to MQTT broker at {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")
        except Exception as e:
            self.logger.error(f"Failed to connect to MQTT broker: {e}")
    
    def disconnect(self):
        """Disconnect from the MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()
        self.logger.info("Disconnected from MQTT broker")
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to the MQTT broker."""
        if rc == 0:
            self.logger.info("Successfully connected to MQTT broker")
            # Subscribe to all device telemetry topics
            client.subscribe("telemetry/#")
            self.logger.info("Subscribed to telemetry/# topic")
        else:
            self.logger.error(f"Failed to connect to MQTT broker with code {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from the MQTT broker."""
        if rc != 0:
            self.logger.warning(f"Unexpected disconnection from MQTT broker: {rc}")
            # Try to reconnect
            try:
                self.client.reconnect()
            except Exception as e:
                self.logger.error(f"Failed to reconnect to MQTT broker: {e}")
    
    def on_message(self, client, userdata, msg):
        """Callback when a message is received from the MQTT broker."""
        try:
            # Parse the topic to get device ID
            # Expected format: telemetry/{device_id}
            topic_parts = msg.topic.split('/')
            if len(topic_parts) < 2:
                self.logger.warning(f"Invalid topic format: {msg.topic}")
                return
            
            device_id = topic_parts[1]
            
            # Decode payload
            payload = json.loads(msg.payload.decode('utf-8'))
            
            # Process the telemetry data
            self.process_telemetry(device_id, payload)
            
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON payload: {msg.payload}")
        except Exception as e:
            self.logger.error(f"Error processing MQTT message: {e}")
    
    def process_telemetry(self, device_id, payload):
        """Process telemetry data from a device."""
        try:
            # Get the device from the database
            try:
                device = Device.objects.get(id=device_id)
            except Device.DoesNotExist:
                self.logger.warning(f"Device not found: {device_id}")
                return
            
            # Extract timestamp from payload or use current time
            timestamp = payload.get('timestamp', timezone.now().isoformat())
            if isinstance(timestamp, str):
                timestamp = timezone.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # Create telemetry entry
            telemetry = Telemetry.objects.create(
                device=device,
                timestamp=timestamp,
                data=payload.get('data', {})
            )
            
            # Update device last_seen
            device.last_seen = timezone.now()
            device.save(update_fields=['last_seen'])
            
            # Check for anomalies if data contains any
            if 'anomalies' in payload and payload['anomalies']:
                self.process_anomalies(device, telemetry, payload['anomalies'])
            
            # Broadcast to WebSocket
            self.broadcast_telemetry(device, telemetry)
            
            self.logger.debug(f"Processed telemetry from device {device_id}")
            
        except Exception as e:
            self.logger.error(f"Error saving telemetry data: {e}")
    
    def process_anomalies(self, device, telemetry, anomalies):
        """Process anomalies in telemetry data."""
        for anomaly_data in anomalies:
            severity = anomaly_data.get('severity', 'medium')
            description = anomaly_data.get('description', 'Anomaly detected')
            
            # Create anomaly record
            anomaly = AnomalyDetection.objects.create(
                device=device,
                severity=severity,
                description=description,
                data=anomaly_data,
                timestamp=telemetry.timestamp
            )
            
            # Broadcast anomaly to WebSocket
            self.broadcast_anomaly(device, anomaly)
            
            self.logger.info(f"Anomaly detected: {description} (severity: {severity}) for device {device.id}")
    
    def broadcast_telemetry(self, device, telemetry):
        """Broadcast telemetry data to WebSocket channels."""
        try:
            # Serialize telemetry for broadcasting
            telemetry_data = {
                'id': str(telemetry.id),
                'device_id': str(device.id),
                'device_name': device.name,
                'timestamp': telemetry.timestamp.isoformat(),
                'data': telemetry.data
            }
            
            # Broadcast to device-specific group
            async_to_sync(channel_layer.group_send)(
                f'telemetry_{device.id}',
                {
                    'type': 'telemetry_message',
                    'message': telemetry_data
                }
            )
            
            # Broadcast to all-telemetry group
            async_to_sync(channel_layer.group_send)(
                'telemetry_all',
                {
                    'type': 'telemetry_message',
                    'message': telemetry_data
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error broadcasting telemetry: {e}")
    
    def broadcast_anomaly(self, device, anomaly):
        """Broadcast anomaly data to WebSocket channels."""
        try:
            # Serialize anomaly for broadcasting
            anomaly_data = {
                'id': str(anomaly.id),
                'device_id': str(device.id),
                'device_name': device.name,
                'timestamp': anomaly.timestamp.isoformat(),
                'severity': anomaly.severity,
                'description': anomaly.description,
                'data': anomaly.data
            }
            
            # Broadcast to device-specific group
            async_to_sync(channel_layer.group_send)(
                f'telemetry_{device.id}',
                {
                    'type': 'anomaly_detected',
                    'message': anomaly_data
                }
            )
            
            # Broadcast to all-telemetry group
            async_to_sync(channel_layer.group_send)(
                'telemetry_all',
                {
                    'type': 'anomaly_detected',
                    'message': anomaly_data
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error broadcasting anomaly: {e}")


# Singleton MQTT client instance
mqtt_client = MQTTClient() 