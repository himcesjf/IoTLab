import time
import logging
from django.core.management.base import BaseCommand
from iotlab.ingest_api.telemetry.mqtt_client import mqtt_client

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Start the MQTT client to receive telemetry data'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting MQTT client...'))
        
        try:
            # Connect to the MQTT broker
            mqtt_client.connect()
            
            self.stdout.write(self.style.SUCCESS('MQTT client started successfully'))
            
            # Keep the command running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('Stopping MQTT client...'))
                mqtt_client.disconnect()
                self.stdout.write(self.style.SUCCESS('MQTT client stopped'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error starting MQTT client: {e}'))
            logger.error(f'Error in MQTT client command: {e}', exc_info=True) 