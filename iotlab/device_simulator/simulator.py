"""
IoT Device Simulator.

This module provides the core functionality for simulating IoT devices 
that generate telemetry data and publish it to an MQTT broker.
"""

import time
import json
import uuid
import logging
import threading
import random
from datetime import datetime
import paho.mqtt.client as mqtt

from .device_types import DEVICE_TYPES


logger = logging.getLogger(__name__)


class DeviceRegistry:
    """Registry for keeping track of all simulated devices."""
    
    def __init__(self):
        self.devices = {}
        self.lock = threading.Lock()
    
    def add_device(self, device):
        """Add a device to the registry."""
        with self.lock:
            self.devices[device.device_id] = device
        return device
    
    def get_device(self, device_id):
        """Get a device from the registry."""
        with self.lock:
            return self.devices.get(device_id)
    
    def remove_device(self, device_id):
        """Remove a device from the registry."""
        with self.lock:
            if device_id in self.devices:
                del self.devices[device_id]
                return True
        return False
    
    def get_all_devices(self):
        """Get all devices in the registry."""
        with self.lock:
            return list(self.devices.values())
    
    def get_device_count(self):
        """Get the number of devices in the registry."""
        with self.lock:
            return len(self.devices)


class DeviceSimulator:
    """
    Simulator for IoT devices that publishes telemetry data to an MQTT broker.
    """
    
    def __init__(self, broker_host="localhost", broker_port=1883, client_id=None):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id or f"device_simulator_{uuid.uuid4().hex[:8]}"
        
        # Set up MQTT client
        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        
        # Set up device registry
        self.registry = DeviceRegistry()
        
        # Set up thread management
        self.running = False
        self.threads = {}
        self.main_thread = None
        
        # Configure logger
        self.logger = logging.getLogger(__name__)
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to the MQTT broker."""
        if rc == 0:
            self.logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
        else:
            self.logger.error(f"Failed to connect to MQTT broker with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from the MQTT broker."""
        if rc != 0:
            self.logger.warning(f"Unexpected disconnection from MQTT broker: {rc}")
            # Try to reconnect in a separate thread
            threading.Thread(target=self._reconnect).start()
    
    def _reconnect(self, max_retries=5):
        """Attempt to reconnect to the MQTT broker."""
        retries = 0
        while retries < max_retries:
            try:
                self.logger.info(f"Attempting to reconnect to MQTT broker (attempt {retries+1}/{max_retries})...")
                self.client.reconnect()
                self.logger.info("Successfully reconnected to MQTT broker")
                return True
            except Exception as e:
                self.logger.error(f"Failed to reconnect: {e}")
                retries += 1
                time.sleep(2 ** retries)  # Exponential backoff
        
        self.logger.error(f"Failed to reconnect after {max_retries} attempts")
        return False
    
    def connect(self):
        """Connect to the MQTT broker."""
        try:
            self.client.connect(self.broker_host, self.broker_port)
            self.client.loop_start()
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()
        self.logger.info("Disconnected from MQTT broker")
    
    def add_device(self, device_type, **kwargs):
        """
        Add a device to the simulator.
        
        Args:
            device_type: Type of device (must be in DEVICE_TYPES)
            **kwargs: Additional parameters for the device
        
        Returns:
            The created device instance
        """
        if device_type not in DEVICE_TYPES:
            raise ValueError(f"Unknown device type: {device_type}. Available types: {', '.join(DEVICE_TYPES.keys())}")
        
        device_class = DEVICE_TYPES[device_type]
        device = device_class(**kwargs)
        self.registry.add_device(device)
        self.logger.info(f"Added {device_type} device: {device.name} ({device.device_id})")
        return device
    
    def remove_device(self, device_id):
        """Remove a device from the simulator."""
        if self.registry.remove_device(device_id):
            # Stop the device thread if it's running
            if device_id in self.threads:
                self.threads[device_id].running = False
                del self.threads[device_id]
            self.logger.info(f"Removed device: {device_id}")
            return True
        return False
    
    def publish_telemetry(self, device_id, telemetry):
        """Publish telemetry data to the MQTT broker."""
        device = self.registry.get_device(device_id)
        if not device:
            self.logger.warning(f"Device not found: {device_id}")
            return False
        
        topic = f"telemetry/{device_id}"
        payload = json.dumps(telemetry)
        
        try:
            result = self.client.publish(topic, payload)
            if result.rc != 0:
                self.logger.error(f"Failed to publish telemetry: {result}")
                return False
            
            self.logger.debug(f"Published telemetry for device {device_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error publishing telemetry: {e}")
            return False
    
    def _device_thread(self, device_id, interval):
        """Thread function for each device."""
        thread_local = threading.local()
        thread_local.running = True
        
        device = self.registry.get_device(device_id)
        if not device:
            self.logger.error(f"Device not found for thread: {device_id}")
            return
        
        self.logger.info(f"Started device thread for {device.name} ({device_id})")
        
        # Store thread reference
        self.threads[device_id] = thread_local
        
        while thread_local.running and self.running:
            try:
                # Generate telemetry
                telemetry = device.generate_telemetry()
                
                # Publish to MQTT
                self.publish_telemetry(device_id, telemetry)
                
            except Exception as e:
                self.logger.error(f"Error in device thread {device_id}: {e}")
            
            # Wait for next interval
            time.sleep(interval)
        
        self.logger.info(f"Stopped device thread for {device.name} ({device_id})")
    
    def start_device(self, device_id, interval=60):
        """Start a device publishing telemetry data."""
        device = self.registry.get_device(device_id)
        if not device:
            self.logger.warning(f"Device not found: {device_id}")
            return False
        
        if device_id in self.threads:
            self.logger.warning(f"Device already running: {device_id}")
            return True
        
        # Create and start the device thread
        device_thread = threading.Thread(
            target=self._device_thread,
            args=(device_id, interval)
        )
        device_thread.daemon = True
        device_thread.start()
        
        return True
    
    def stop_device(self, device_id):
        """Stop a device from publishing telemetry data."""
        if device_id in self.threads:
            self.threads[device_id].running = False
            del self.threads[device_id]
            self.logger.info(f"Stopped device: {device_id}")
            return True
        return False
    
    def start(self):
        """Start the simulator."""
        if self.running:
            self.logger.warning("Simulator is already running")
            return False
        
        # Connect to MQTT broker
        if not self.connect():
            return False
        
        self.running = True
        self.logger.info("Started device simulator")
        return True
    
    def stop(self):
        """Stop the simulator."""
        if not self.running:
            self.logger.warning("Simulator is not running")
            return False
        
        self.running = False
        
        # Stop all device threads
        for device_id in list(self.threads.keys()):
            self.stop_device(device_id)
        
        # Disconnect from MQTT broker
        self.disconnect()
        
        self.logger.info("Stopped device simulator")
        return True
    
    def get_device_info(self, device_id):
        """Get information about a device."""
        device = self.registry.get_device(device_id)
        if not device:
            return None
        
        info = device.to_dict()
        info["is_running"] = device_id in self.threads
        return info
    
    def get_all_devices_info(self):
        """Get information about all devices."""
        devices = []
        for device in self.registry.get_all_devices():
            info = device.to_dict()
            info["is_running"] = device.device_id in self.threads
            devices.append(info)
        return devices 