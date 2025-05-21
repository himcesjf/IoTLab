from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
import json

from telemetrix_lab.ingest_api.devices.models import Device
from telemetrix_lab.ingest_api.telemetry.models import Telemetry, AnomalyDetection

class Command(BaseCommand):
    help = 'Generates sample telemetry and anomaly data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days of historical data to generate'
        )
        parser.add_argument(
            '--readings-per-day',
            type=int,
            default=96,  # Every 15 minutes
            help='Number of readings per day per device'
        )
        parser.add_argument(
            '--anomaly-probability',
            type=float,
            default=0.1,
            help='Probability of generating an anomaly for each reading'
        )

    def handle(self, *args, **options):
        days = options['days']
        readings_per_day = options['readings_per_day']
        anomaly_probability = options['anomaly_probability']

        # Get all active devices
        devices = Device.objects.filter(status='online')
        if not devices.exists():
            self.stdout.write(
                self.style.ERROR('No online devices found. Please run create_sample_data first.')
            )
            return

        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        interval = timedelta(days=1) / readings_per_day

        self.stdout.write(f"Generating {days} days of data for {devices.count()} devices...")

        for device in devices:
            current_time = start_date
            readings_count = 0
            anomalies_count = 0

            while current_time <= end_date:
                # Generate telemetry data based on device type
                if device.device_type.name == 'Temperature Sensor':
                    data = self.generate_temperature_data()
                elif device.device_type.name == 'Vibration Sensor':
                    data = self.generate_vibration_data()
                elif device.device_type.name == 'Flow Meter':
                    data = self.generate_flow_data()
                else:
                    continue

                # Create telemetry record
                telemetry = Telemetry.objects.create(
                    device=device,
                    timestamp=current_time,
                    data=data
                )
                readings_count += 1

                # Randomly generate anomalies
                if random.random() < anomaly_probability:
                    anomaly = self.generate_anomaly(device, telemetry, data)
                    if anomaly:
                        anomalies_count += 1

                current_time += interval

            self.stdout.write(
                self.style.SUCCESS(
                    f"Generated {readings_count} readings and {anomalies_count} "
                    f"anomalies for {device.name}"
                )
            )

    def generate_temperature_data(self):
        """Generate realistic temperature sensor data."""
        base_temp = random.uniform(20, 35)  # Base temperature
        humidity = random.uniform(30, 85)    # Base humidity
        battery = random.uniform(85, 100)    # Battery level

        # Add some noise
        temperature = base_temp + random.uniform(-2, 2)
        humidity = humidity + random.uniform(-5, 5)
        
        return {
            "temperature": round(temperature, 2),
            "humidity": round(humidity, 2),
            "battery": round(battery, 2),
            "status": "normal"
        }

    def generate_vibration_data(self):
        """Generate realistic vibration sensor data."""
        base_velocity = random.uniform(2, 7)     # Increased range to generate more anomalies
        base_freq = random.uniform(30, 50)       # Base frequency
        base_temp = random.uniform(35, 45)       # Base temperature

        # Add some noise
        velocity = base_velocity + random.uniform(-0.5, 0.5)
        frequency = base_freq + random.uniform(-5, 5)
        temperature = base_temp + random.uniform(-2, 2)

        return {
            "velocity_rms": round(velocity, 3),
            "frequency": round(frequency, 2),
            "temperature": round(temperature, 2),
            "machine_state": "on"
        }

    def generate_flow_data(self):
        """Generate realistic flow meter data."""
        base_flow = random.uniform(40, 60)       # Base flow rate
        base_pressure = random.uniform(2.5, 4.5)  # Increased range to generate more anomalies
        base_temp = random.uniform(25, 35)       # Base temperature

        # Add some noise
        flow_rate = base_flow + random.uniform(-5, 5)
        pressure = base_pressure + random.uniform(-0.2, 0.2)
        temperature = base_temp + random.uniform(-1, 1)

        return {
            "flow_rate": round(flow_rate, 2),
            "pressure": round(pressure, 2),
            "temperature": round(temperature, 2),
            "status": "normal"
        }

    def generate_anomaly(self, device, telemetry, data):
        """Generate an anomaly based on device type and telemetry data."""
        severity_choices = ['low', 'medium', 'high', 'critical']
        severity_weights = [0.4, 0.3, 0.2, 0.1]  # More low/medium than high/critical
        
        severity = random.choices(severity_choices, weights=severity_weights)[0]
        anomaly_data = {}
        description = ""

        if device.device_type.name == 'Temperature Sensor':
            if data['temperature'] > 30:
                description = "High temperature detected"
                anomaly_data = {
                    "threshold": 30,
                    "value": data['temperature']
                }
            elif data['humidity'] > 80:
                description = "High humidity detected"
                anomaly_data = {
                    "threshold": 80,
                    "value": data['humidity']
                }
        elif device.device_type.name == 'Vibration Sensor':
            if data['velocity_rms'] > 5:
                description = "High vibration detected"
                anomaly_data = {
                    "threshold": 5,
                    "value": data['velocity_rms']
                }
        elif device.device_type.name == 'Flow Meter':
            if data['pressure'] > 4:
                description = "High pressure detected"
                anomaly_data = {
                    "threshold": 4,
                    "value": data['pressure']
                }

        if description and anomaly_data:
            return AnomalyDetection.objects.create(
                device=device,
                severity=severity,
                description=description,
                data=anomaly_data,
                timestamp=telemetry.timestamp
            )
        return None 