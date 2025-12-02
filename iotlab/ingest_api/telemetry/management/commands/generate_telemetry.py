from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
import logging

from iotlab.ingest_api.devices.models import Device
from iotlab.ingest_api.telemetry.models import Telemetry, AnomalyDetection

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generates historical telemetry (and anomalies) for existing online devices'

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
            default=288,  # Every 5 minutes
            help='Number of readings per day per device'
        )
        parser.add_argument(
            '--device-id',
            type=str,
            help='Generate data for specific device ID (optional)'
        )
        parser.add_argument(
            '--anomaly-probability',
            type=float,
            default=0.05,
            help='Probability of generating an anomaly for each reading (default: 0.05)'
        )

    def handle(self, *args, **options):
        days = options['days']
        readings_per_day = options['readings_per_day']
        device_id = options.get('device_id')
        anomaly_probability = options['anomaly_probability']

        # Get devices to generate data for
        if device_id:
            devices = Device.objects.filter(id=device_id, status='online')
            if not devices.exists():
                self.stderr.write(f"Online device with ID {device_id} not found")
                return
        else:
            devices = Device.objects.filter(status='online')

        if not devices.exists():
            self.stderr.write(
                self.style.ERROR('No online devices found. Please run seed_devices first.')
            )
            return

        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        interval = timedelta(days=1) / readings_per_day

        self.stdout.write(f"Generating {days} days of data for {devices.count()} devices...")

        total_readings = 0
        total_anomalies = 0

        for device in devices:
            current_time = start_date
            readings_count = 0
            anomalies_count = 0

            # Set base values for the device
            if device.device_type.name == 'Temperature Sensor':
                base_value = random.uniform(19.0, 22.0) # Base temperature
            elif device.device_type.name == 'Vibration Sensor':
                base_value = random.uniform(20.0, 60.0) # Base frequency
            elif device.device_type.name == 'Flow Meter':
                base_value = random.uniform(40.0, 60.0) # Base flow rate / pressure
            else:
                continue

            while current_time <= end_date:
                # Generate telemetry data based on device type
                if device.device_type.name == 'Temperature Sensor':
                    data = self.generate_temperature_data(base_value, current_time)
                elif device.device_type.name == 'Vibration Sensor':
                    data = self.generate_vibration_data(base_value, current_time)
                elif device.device_type.name == 'Flow Meter':
                    data = self.generate_flow_data(base_value, current_time)
                else:
                    continue
                # Create telemetry record
                telemetry = Telemetry.objects.create(
                    device=device,
                    timestamp=current_time,
                    data=data
                )
                readings_count += 1

                # Generate anomaly if probability is met
                if random.random() < anomaly_probability:
                    anomaly = self.generate_anomaly(device, telemetry, data)
                    if anomaly:
                        anomalies_count += 1

                current_time += interval

            total_readings += readings_count
            total_anomalies += anomalies_count
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Generated {readings_count} readings and {anomalies_count} anomalies for {device.name}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTotal: {total_readings} readings and {total_anomalies} anomalies across {devices.count()} devices"
            )
        )

    def generate_temperature_data(self, base_temp, timestamp):
        # Generate temperature data based on time of day
        hour = timestamp.hour
        # Time factor is 0 at 14:00 and 1 at 00:00 and 24:00
        time_factor = abs(hour - 14) / 14.0
        daily_temp = base_temp - (time_factor * 5) # Daily temperature variation of 5C
        # Add random noise to the temperature
        temp = daily_temp + random.uniform(-0.5, 0.5)

        humidity = 100 - (temp - 10) * 2
        humidity = max(30, min(95, humidity))
    
        battery = 100 - (timestamp.day % 30) * 3
        return {
            "temperature": round(temp, 2),
            "humidity": round(humidity, 2),
            "battery": round(battery, 2),
            "status": "normal"
        }

    def generate_vibration_data(self, base_freq, timestamp):
        # Generate vibration data based on time of day
        hour = timestamp.hour
        if 8 <= hour <= 18:
            freq_factor = 1.0
            velocity_factor = 1.0
        else:
            freq_factor = 0.7
            velocity_factor = 0.6
        frequency = base_freq * freq_factor + random.uniform(-2, 2)
        velocity = 2.5 * velocity_factor + random.uniform(-0.2, 0.2)
        temp = 35 + (velocity * 2) + random.uniform(-0.5, 0.5)
        return {
            "velocity_rms": round(velocity, 3),
            "frequency": round(frequency, 2),
            "temperature": round(temp, 2),
            "machine_state": "on"
        }

    def generate_flow_data(self, base_flow, timestamp):
        # Generate flow data based on time of day
        hour = timestamp.hour
        # Flow factor is 0.6 at 00:00-06:00, 1.2 at 06:00-09:00, 1.0 at 09:00-17:00, 1.1 at 17:00-22:00, 0.8 at 22:00-00:00
        if hour < 6:
            flow_factor = 0.6
        elif hour < 9:
            flow_factor = 1.2
        elif hour < 17:
            flow_factor = 1.0
        elif hour < 22:
            flow_factor = 1.1
        else:
            flow_factor = 0.8
        flow_rate = base_flow * flow_factor + random.uniform(-2, 2)
        pressure = 5.0 - (0.05 * flow_rate) + random.uniform(-0.1, 0.1)
        temp = 25 + (flow_rate * 0.1) + random.uniform(-0.5, 0.5)
        return {
            "flow_rate": round(flow_rate, 2),
            "pressure": round(pressure, 2),
            "temperature": round(temp, 2),
            "status": "normal"
        }

    def generate_anomaly(self, device, telemetry, data):
        # Generate anomaly based on device type and data
        severity_choices = ['low', 'medium', 'high', 'critical']
        severity_weights = [0.4, 0.3, 0.2, 0.1]
        severity = random.choices(severity_choices, weights=severity_weights)[0]
        anomaly_data = {}
        description = ""

        if device.device_type.name == 'Temperature Sensor':
            # Generate anomaly for temperature if probability is met
            if random.random() < 0.7: 
                # Threshold is 30C for high and critical severity, 28C for medium severity
                threshold = 30 if severity in ['high', 'critical'] else 28
                if data['temperature'] < threshold:
                    data['temperature'] += random.uniform(5, 15)
                description = "High temperature detected"
                anomaly_data = {"threshold": threshold, "value": data['temperature']}
            else:
                # Threshold is 85C for high and critical severity, 80C for medium severity
                threshold = 85 if severity in ['high', 'critical'] else 80
                if data['humidity'] < threshold:
                    data['humidity'] += random.uniform(10, 20)
                description = "High humidity detected"
                anomaly_data = {"threshold": threshold, "value": data['humidity']}

        elif device.device_type.name == 'Vibration Sensor':
            # Threshold is 7 for high and critical severity, 5 for medium severity
            threshold = 7 if severity in ['high', 'critical'] else 5
            if data['velocity_rms'] < threshold:
                data['velocity_rms'] *= random.uniform(2.0, 3.0)
            description = "High vibration detected"
            anomaly_data = {"threshold": threshold, "value": data['velocity_rms']}

        elif device.device_type.name == 'Flow Meter':
            
            if random.random() < 0.6:
                threshold = 8 if severity in ['high', 'critical'] else 6
                if data['pressure'] < threshold:
                    data['pressure'] *= random.uniform(1.5, 2.0)
                description = "High pressure detected"
                anomaly_data = {"threshold": threshold, "value": data['pressure']}
            else:
                threshold = data['flow_rate'] * 1.5
                data['flow_rate'] *= random.uniform(1.5, 2.0)
                description = "Abnormal flow rate detected"
                anomaly_data = {"threshold": threshold, "value": data['flow_rate']}

        if description and anomaly_data:
            telemetry.data = data
            telemetry.save()
            return AnomalyDetection.objects.create(
                device=device,
                severity=severity,
                description=description,
                data=anomaly_data,
                timestamp=telemetry.timestamp
            )
        return None

