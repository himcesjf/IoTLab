"""
Device type definitions for the IoT simulator.
Each device type has a specific schema and behavior for generating telemetry data.
"""

import random
import time
import uuid
import math
from datetime import datetime
import numpy as np


class DeviceType:
    """Base class for all device types."""
    
    def __init__(self, device_id=None, name=None, location=None, config=None):
        self.device_id = device_id or str(uuid.uuid4())
        self.name = name or f"{self.__class__.__name__}-{self.device_id[:8]}"
        self.location = location or "Unknown"
        self.config = config or {}
        self.created_at = datetime.utcnow().isoformat()
        self.failure_rate = float(self.config.get("failure_rate", 0.01))
        self.noise_factor = float(self.config.get("noise_factor", 0.05))
        
        # State management
        self.last_reading = None
        self.anomaly_counter = 0
        self.failure_state = False
        self.failure_duration = 0
        
    def get_schema(self):
        """Get the data schema for this device type."""
        raise NotImplementedError
    
    def generate_telemetry(self):
        """Generate telemetry data based on device type."""
        raise NotImplementedError
    
    def simulate_failure(self):
        """Simulate a device failure."""
        if not self.failure_state and random.random() < self.failure_rate:
            self.failure_state = True
            self.failure_duration = random.randint(5, 20)  # Failure lasts 5-20 iterations
            return True
        
        if self.failure_state:
            self.failure_duration -= 1
            if self.failure_duration <= 0:
                self.failure_state = False
            return True
            
        return False
    
    def add_noise(self, value, factor=None):
        """Add random noise to a value."""
        if factor is None:
            factor = self.noise_factor
        noise = (random.random() * 2 - 1) * factor * value
        return value + noise
    
    def detect_anomalies(self, data):
        """Detect anomalies in the telemetry data."""
        return []
    
    def to_dict(self):
        """Convert device to dictionary representation."""
        return {
            "id": self.device_id,
            "name": self.name,
            "type": self.__class__.__name__,
            "location": self.location,
            "config": self.config,
            "created_at": self.created_at
        }


class TemperatureSensor(DeviceType):
    """Temperature sensor device type."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_temperature = random.uniform(19.0, 22.0)  # Base temperature in Celsius
        self.daily_variation = random.uniform(2.0, 5.0)     # Daily temperature variation
        self.hourly_noise = random.uniform(0.1, 0.5)        # Hourly noise factor
        
    def get_schema(self):
        return {
            "temperature": "number",  # Celsius
            "humidity": "number",     # Percentage
            "battery": "number",      # Percentage
            "status": "string"
        }
    
    def generate_telemetry(self):
        # Simulate failure
        if self.simulate_failure():
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "status": "error",
                    "error_code": f"E{random.randint(1, 9)}{random.randint(0, 9)}{random.randint(0, 9)}"
                }
            }
        
        # Get time-based variations
        current_time = time.time()
        day_factor = math.sin(current_time / 86400 * 2 * math.pi)  # Daily cycle
        hour_factor = math.sin(current_time / 3600 * 2 * math.pi)  # hourly cycle
        
        # Calculate temperature with variations
        temperature = self.base_temperature + (day_factor * self.daily_variation) + (hour_factor * self.hourly_noise)
        temperature = self.add_noise(temperature)
        
        # Calculate related humidity (inverse relationship with temperature)
        humidity = 100 - (temperature - 10) * 2
        humidity = max(30, min(95, humidity))  # Keep humidity between 30%-95%
        humidity = self.add_noise(humidity)
        
        # Battery level slowly decreases over time
        battery_level = 100 - (((current_time % 2592000) / 2592000) * 20)  # 20% drain over 30 days
        
        data = {
            "temperature": round(temperature, 2),
            "humidity": round(humidity, 2),
            "battery": round(battery_level, 2),
            "status": "normal"
        }
        
        # Detect anomalies
        anomalies = self.detect_anomalies(data)
        
        telemetry = {
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        if anomalies:
            telemetry["anomalies"] = anomalies
            
        self.last_reading = data
        return telemetry
    
    def detect_anomalies(self, data):
        anomalies = []
        
        # Temperature anomalies
        if data["temperature"] > 30:
            anomalies.append({
                "severity": "critical",
                "description": "High temperature detected",
                "value": data["temperature"],
                "threshold": 30
            })
        elif data["temperature"] > 28:
            anomalies.append({
                "severity": "high",
                "description": "Elevated temperature",
                "value": data["temperature"],
                "threshold": 28
            })
        elif data["temperature"] < 10:
            anomalies.append({
                "severity": "high",
                "description": "Low temperature detected",
                "value": data["temperature"],
                "threshold": 10
            })
            
        # Humidity anomalies
        if data["humidity"] > 90:
            anomalies.append({
                "severity": "medium",
                "description": "High humidity detected",
                "value": data["humidity"],
                "threshold": 90
            })
        elif data["humidity"] < 35:
            anomalies.append({
                "severity": "medium",
                "description": "Low humidity detected",
                "value": data["humidity"],
                "threshold": 35
            })
            
        # Battery anomalies
        if data["battery"] < 20:
            anomalies.append({
                "severity": "low",
                "description": "Low battery",
                "value": data["battery"],
                "threshold": 20
            })
            
        return anomalies


class VibrationSensor(DeviceType):
    """Vibration and acceleration sensor device type."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.machine_type = random.choice(["pump", "motor", "compressor", "fan"])
        self.base_frequency = random.uniform(20, 60)  # Base frequency in Hz
        self.base_amplitude = random.uniform(0.5, 2.0)  # Base amplitude in mm/s
        
    def get_schema(self):
        return {
            "acceleration_x": "number",  # m^s2
            "acceleration_y": "number",  # m^s2
            "acceleration_z": "number",  # m^s2
            "velocity_rms": "number",    # mm^s
            "frequency": "number",       # Hz
            "temperature": "number",     # Celsius
            "machine_state": "string"    # on/off/starting/stopping
        }
    
    def generate_telemetry(self):
        # Simulate failure
        if self.simulate_failure():
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "machine_state": "fault",
                    "error_code": f"F{random.randint(1, 9)}{random.randint(0, 9)}{random.randint(0, 9)}"
                }
            }
        
        # Determine machine state
        states = ["on", "on", "on", "on", "on", "off", "starting", "stopping"]
        weights = [0.7, 0.7, 0.7, 0.7, 0.7, 0.1, 0.1, 0.1]
        
        if self.last_reading and self.last_reading.get("machine_state") == "starting":
            states = ["on", "starting"]
            weights = [0.7, 0.3]
        elif self.last_reading and self.last_reading.get("machine_state") == "stopping":
            states = ["off", "stopping"]
            weights = [0.7, 0.3]
            
        machine_state = random.choices(states, weights=weights)[0]
        
        # Generate vibration characteristics based on machine state
        if machine_state == "on":
            # Normal operational vibration
            frequency = self.base_frequency
            frequency = self.add_noise(frequency, 0.1)
            
            amplitude = self.base_amplitude
            amplitude = self.add_noise(amplitude, 0.15)
            
            # Generate 3-axis acceleration
            accel_x = amplitude * math.sin(time.time() * frequency * 0.1)
            accel_y = amplitude * math.cos(time.time() * frequency * 0.1)
            accel_z = self.add_noise(amplitude * 0.5, 0.2)
            
            # RMS velocity
            velocity_rms = amplitude * 0.85
            velocity_rms = self.add_noise(velocity_rms, 0.1)
            
            # Motor temperature rises during operation
            temperature = 40 + (amplitude * 5)
            temperature = self.add_noise(temperature, 0.05)
            
        elif machine_state == "starting":
            # Startup vibration (higher, changing frequency)
            frequency = self.base_frequency * random.uniform(0.5, 1.5)
            amplitude = self.base_amplitude * random.uniform(1.5, 2.5)
            
            accel_x = amplitude * math.sin(time.time() * frequency * 0.2)
            accel_y = amplitude * math.cos(time.time() * frequency * 0.2)
            accel_z = self.add_noise(amplitude * 0.7, 0.3)
            
            velocity_rms = amplitude * random.uniform(0.9, 1.3)
            temperature = 25 + (10 * random.random())
            
        elif machine_state == "stopping":
            # Slowdown vibration (decreasing frequency and amplitude)
            frequency = self.base_frequency * random.uniform(0.3, 0.8)
            amplitude = self.base_amplitude * random.uniform(0.7, 1.5)
            
            accel_x = amplitude * math.sin(time.time() * frequency * 0.05)
            accel_y = amplitude * math.cos(time.time() * frequency * 0.05)
            accel_z = self.add_noise(amplitude * 0.4, 0.15)
            
            velocity_rms = amplitude * 0.6
            temperature = 35 + (5 * random.random())
            
        else:  # off
            # Minimal vibration
            frequency = self.add_noise(0.5, 1.0)
            amplitude = self.add_noise(0.1, 1.0)
            
            accel_x = self.add_noise(0.05, 1.0)
            accel_y = self.add_noise(0.05, 1.0)
            accel_z = self.add_noise(0.05, 1.0)
            
            velocity_rms = self.add_noise(0.1, 0.5)
            temperature = self.add_noise(22, 0.1)
        
        # Add harmonics or sub-harmonics to simulate mechanical issues
        if machine_state == "on" and random.random() < 0.05:
            harmonic_factor = random.choice([0.5, 2.0, 3.0])
            harmonic_amplitude = amplitude * random.uniform(0.2, 0.5)
            accel_x += harmonic_amplitude * math.sin(time.time() * frequency * harmonic_factor)
            accel_y += harmonic_amplitude * math.cos(time.time() * frequency * harmonic_factor)
            
            self.anomaly_counter += 1
        else:
            self.anomaly_counter = max(0, self.anomaly_counter - 0.2)  # Decrease counter over time
            
        data = {
            "acceleration_x": round(accel_x, 3),
            "acceleration_y": round(accel_y, 3),
            "acceleration_z": round(accel_z, 3),
            "velocity_rms": round(velocity_rms, 3),
            "frequency": round(frequency, 2),
            "temperature": round(temperature, 2),
            "machine_state": machine_state,
            "machine_type": self.machine_type
        }
        
        # Detect anomalies
        anomalies = self.detect_anomalies(data)
        
        telemetry = {
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        if anomalies:
            telemetry["anomalies"] = anomalies
            
        self.last_reading = data
        return telemetry
    
    def detect_anomalies(self, data):
        anomalies = []
        
        if data["machine_state"] not in ["on", "starting"]:
            return anomalies
            
        # Velocity RMS thresholds based on ISO 10816 standards
        if data["velocity_rms"] > 11.0:
            anomalies.append({
                "severity": "critical",
                "description": f"Extreme vibration detected in {self.machine_type}",
                "value": data["velocity_rms"],
                "threshold": 11.0
            })
        elif data["velocity_rms"] > 7.1:
            anomalies.append({
                "severity": "high",
                "description": f"High vibration detected in {self.machine_type}",
                "value": data["velocity_rms"],
                "threshold": 7.1
            })
        elif data["velocity_rms"] > 4.5 and self.anomaly_counter > 5:
            anomalies.append({
                "severity": "medium",
                "description": f"Elevated vibration with harmonic pattern in {self.machine_type}",
                "value": data["velocity_rms"],
                "harmonic_detected": True,
                "threshold": 4.5
            })
            
        # Temperature anomalies
        if data["temperature"] > 80:
            anomalies.append({
                "severity": "critical",
                "description": f"Critical temperature in {self.machine_type}",
                "value": data["temperature"],
                "threshold": 80
            })
        elif data["temperature"] > 70:
            anomalies.append({
                "severity": "high",
                "description": f"High temperature in {self.machine_type}",
                "value": data["temperature"],
                "threshold": 70
            })
            
        return anomalies


class FlowMeter(DeviceType):
    """Flow meter device type."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fluid_type = random.choice(["water", "oil", "gas", "coolant"])
        self.pipe_diameter = random.uniform(50, 200)  # mm
        self.target_flow_rate = random.uniform(10, 100)  # L/min
        self.base_pressure = random.uniform(2, 10)  # bar
        
    def get_schema(self):
        return {
            "flow_rate": "number",     # L/min
            "pressure": "number",      # bar
            "temperature": "number",   # Celsius
            "total_flow": "number",    # Cumulative L
            "fluid_type": "string",
            "status": "string"
        }
    
    def generate_telemetry(self):
        # Simulate failure
        if self.simulate_failure():
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "status": "error",
                    "error_code": f"E{random.randint(1, 9)}{random.randint(0, 9)}{random.randint(0, 9)}",
                    "fluid_type": self.fluid_type
                }
            }
        
        # Time-based flow variations (simulating system demand)
        current_time = time.time()
        hour_of_day = (current_time % 86400) / 3600  # 0-24 hour of day
        
        # Flow pattern based on time of day (lower at night, peaks in morning and evening)
        if hour_of_day < 6:  # Midnight to 6 AM
            flow_factor = 0.6
        elif hour_of_day < 9:  # 6 AM to 9 AM (morning peak)
            flow_factor = 1.2
        elif hour_of_day < 17:  # 9 AM to 5 PM
            flow_factor = 1.0
        elif hour_of_day < 22:  # 5 PM to 10 PM (evening peak)
            flow_factor = 1.1
        else:  # 10 PM to midnight
            flow_factor = 0.8
            
        # Add some random variations to the flow
        flow_factor += random.uniform(-0.1, 0.1)
        
        # Calculate the flow rate
        flow_rate = self.target_flow_rate * flow_factor
        flow_rate = self.add_noise(flow_rate)
        
        # Calculate related parameters
        # Pressure is inversely related to flow (higher flow, lower pressure)
        pressure = self.base_pressure - (0.05 * flow_rate)
        pressure = max(0.5, pressure)  # Ensure pressure doesn't go too low
        pressure = self.add_noise(pressure)
        
        # Temperature varies based on flow (higher flow, slightly lower temp)
        if self.fluid_type == "water":
            base_temp = 15
        elif self.fluid_type == "oil":
            base_temp = 45
        elif self.fluid_type == "coolant":
            base_temp = 30
        else:  # gas
            base_temp = 25
            
        temperature = base_temp - (0.02 * flow_rate) + (math.sin(hour_of_day / 24 * 2 * math.pi) * 2)
        temperature = self.add_noise(temperature)
        
        # Calculate cumulative flow
        if self.last_reading:
            last_total = self.last_reading.get("total_flow", 0)
            # Assume this reading is taken 1 minute after the last one
            total_flow = last_total + (flow_rate / 60)
        else:
            # First reading, initialize with a random value
            total_flow = random.uniform(10000, 50000)
            
        # Determine flow status
        if flow_rate < (self.target_flow_rate * 0.3):
            status = "low_flow"
        elif flow_rate > (self.target_flow_rate * 1.5):
            status = "high_flow"
        else:
            status = "normal"
            
        data = {
            "flow_rate": round(flow_rate, 2),
            "pressure": round(pressure, 2),
            "temperature": round(temperature, 2),
            "total_flow": round(total_flow, 2),
            "fluid_type": self.fluid_type,
            "status": status
        }
        
        # Detect anomalies
        anomalies = self.detect_anomalies(data)
        
        telemetry = {
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        if anomalies:
            telemetry["anomalies"] = anomalies
            
        self.last_reading = data
        return telemetry
    
    def detect_anomalies(self, data):
        anomalies = []
        
        # Flow rate anomalies
        if data["flow_rate"] < (self.target_flow_rate * 0.2):
            anomalies.append({
                "severity": "high",
                "description": f"Very low flow rate detected in {self.fluid_type} line",
                "value": data["flow_rate"],
                "threshold": self.target_flow_rate * 0.2
            })
        elif data["flow_rate"] > (self.target_flow_rate * 1.8):
            anomalies.append({
                "severity": "high",
                "description": f"Very high flow rate detected in {self.fluid_type} line",
                "value": data["flow_rate"],
                "threshold": self.target_flow_rate * 1.8
            })
            
        # Pressure anomalies
        if data["pressure"] < 1.0:
            anomalies.append({
                "severity": "critical",
                "description": f"Critical low pressure in {self.fluid_type} line",
                "value": data["pressure"],
                "threshold": 1.0
            })
        elif data["pressure"] > (self.base_pressure * 1.5):
            anomalies.append({
                "severity": "high",
                "description": f"High pressure in {self.fluid_type} line",
                "value": data["pressure"],
                "threshold": self.base_pressure * 1.5
            })
            
        # Temperature anomalies
        if self.fluid_type == "water" and data["temperature"] > 40:
            anomalies.append({
                "severity": "medium",
                "description": "High water temperature",
                "value": data["temperature"],
                "threshold": 40
            })
        elif self.fluid_type == "oil" and data["temperature"] > 80:
            anomalies.append({
                "severity": "high",
                "description": "High oil temperature",
                "value": data["temperature"],
                "threshold": 80
            })
        elif self.fluid_type == "coolant" and data["temperature"] > 60:
            anomalies.append({
                "severity": "high",
                "description": "High coolant temperature",
                "value": data["temperature"],
                "threshold": 60
            })
            
        return anomalies


# Dictionary of available device types
DEVICE_TYPES = {
    "temperature": TemperatureSensor,
    "vibration": VibrationSensor,
    "flow": FlowMeter
} 