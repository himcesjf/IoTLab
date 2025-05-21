from django.core.management.base import BaseCommand
from django.utils import timezone
from telemetrix_lab.ingest_api.devices.models import DeviceType, Device

class Command(BaseCommand):
    help = 'Creates sample device types and devices for testing'

    def handle(self, *args, **kwargs):
        # Create sample device types
        device_types = [
            {
                "name": "Temperature Sensor",
                "description": "Environmental temperature and humidity monitoring sensor",
                "schema": {
                    "type": "object",
                    "properties": {
                        "temperature": {"type": "number", "minimum": -40, "maximum": 85},
                        "humidity": {"type": "number", "minimum": 0, "maximum": 100},
                        "battery": {"type": "number", "minimum": 0, "maximum": 100}
                    }
                }
            },
            {
                "name": "Vibration Sensor",
                "description": "Industrial machinery vibration monitoring sensor",
                "schema": {
                    "type": "object",
                    "properties": {
                        "velocity_rms": {"type": "number", "minimum": 0, "maximum": 50},
                        "frequency": {"type": "number", "minimum": 0, "maximum": 1000},
                        "temperature": {"type": "number", "minimum": -10, "maximum": 100}
                    }
                }
            },
            {
                "name": "Flow Meter",
                "description": "Liquid flow rate and pressure monitoring sensor",
                "schema": {
                    "type": "object",
                    "properties": {
                        "flow_rate": {"type": "number", "minimum": 0, "maximum": 100},
                        "pressure": {"type": "number", "minimum": 0, "maximum": 200},
                        "temperature": {"type": "number", "minimum": 0, "maximum": 150}
                    }
                }
            }
        ]

        # Create device types
        created_types = []
        for dt in device_types:
            device_type, created = DeviceType.objects.get_or_create(
                name=dt["name"],
                defaults={
                    "description": dt["description"],
                    "schema": dt["schema"]
                }
            )
            created_types.append(device_type)
            self.stdout.write(
                self.style.SUCCESS(f"{'Created' if created else 'Found'} device type: {device_type.name}")
            )

        # Create sample devices for each type
        sample_devices = [
            # Temperature Sensors
            {"name": "Temp-001", "type": "Temperature Sensor", "status": "online"},
            {"name": "Temp-002", "type": "Temperature Sensor", "status": "offline"},
            {"name": "Temp-003", "type": "Temperature Sensor", "status": "maintenance"},
            # Vibration Sensors
            {"name": "Vib-001", "type": "Vibration Sensor", "status": "online"},
            {"name": "Vib-002", "type": "Vibration Sensor", "status": "error"},
            # Flow Meters
            {"name": "Flow-001", "type": "Flow Meter", "status": "online"},
            {"name": "Flow-002", "type": "Flow Meter", "status": "online"},
        ]

        # Create devices
        for dev in sample_devices:
            device_type = DeviceType.objects.get(name=dev["type"])
            device, created = Device.objects.get_or_create(
                name=dev["name"],
                defaults={
                    "device_type": device_type,
                    "status": dev["status"],
                    "last_seen": timezone.now() if dev["status"] == "online" else None,
                    "metadata": {
                        "location": "Factory Floor",
                        "installation_date": timezone.now().isoformat()
                    }
                }
            )
            self.stdout.write(
                self.style.SUCCESS(f"{'Created' if created else 'Found'} device: {device.name} ({device.status})")
            )

        # Print summary
        self.stdout.write("\nSummary:")
        self.stdout.write(f"Total Device Types: {DeviceType.objects.count()}")
        self.stdout.write(f"Total Devices: {Device.objects.count()}")
        self.stdout.write(
            f"Online Devices: {Device.objects.filter(status='online').count()}"
        ) 