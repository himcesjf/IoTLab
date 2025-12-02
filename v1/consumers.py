import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.serializers.json import DjangoJSONEncoder

from iotlab.ingest_api.devices.models import Device


class TelemetryConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # Get the device_id from the URL rout
        self.device_id = self.scope['url_route']['kwargs'].get('device_id')
        
        # Join the appropriate group
        if self.device_id:
            # Check if the device exists
            device_exists = await self.device_exists(self.device_id)
            if not device_exists:
                await self.close()
                return
                
            # Join device-specific group
            self.groups = [f'telemetry_{self.device_id}']
        else:
            # Join the "all telemetry" group
            self.groups = ['telemetry_all']
        
        # Add this channel to all the groups
        for group in self.groups:
            await self.channel_layer.group_add(
                group,
                self.channel_name
            )
        
        await self.accept()
        await self.send_json({
            'type': 'connection_established',
            'message': 'Connected to telemetry stream'
        })
    
    async def disconnect(self, close_code):
        # Leave all the groups
        for group in self.groups:
            await self.channel_layer.group_discard(
                group,
                self.channel_name
            )
    
    async def receive_json(self, content):
        # Client can send commands to alter the subscription
        command = content.get('command')
        
        if command == 'subscribe_device':
            device_id = content.get('device_id')
            if device_id and await self.device_exists(device_id):
                group_name = f'telemetry_{device_id}'
                if group_name not in self.groups:
                    self.groups.append(group_name)
                    await self.channel_layer.group_add(
                        group_name,
                        self.channel_name
                    )
                    await self.send_json({
                        'type': 'subscription_update',
                        'message': f'Subscribed to device {device_id}'
                    })
        
        elif command == 'unsubscribe_device':
            device_id = content.get('device_id')
            group_name = f'telemetry_{device_id}'
            if group_name in self.groups:
                self.groups.remove(group_name)
                await self.channel_layer.group_discard(
                    group_name,
                    self.channel_name
                )
                await self.send_json({
                    'type': 'subscription_update',
                    'message': f'Unsubscribed from device {device_id}'
                })
    
    # Handler for messages sent to the group
    async def telemetry_message(self, event):
        # Forward the message to the WebSocket
        message = event['message']
        await self.send_json({
            'type': 'telemetry',
            'data': message
        })
    
    async def anomaly_detected(self, event):
        # Forward anomaly events to the WebSocket
        message = event['message']
        await self.send_json({
            'type': 'anomaly',
            'data': message
        })
    
    @database_sync_to_async
    def device_exists(self, device_id):
        return Device.objects.filter(id=device_id).exists() 