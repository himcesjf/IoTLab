#!/usr/bin/env python3
"""
Command-line interface for the IoT device simulator.
"""

import os
import sys
import time
import json
import random
import signal
import logging
import argparse
from pathlib import Path
from datetime import datetime

from .simulator import DeviceSimulator
from .device_types import DEVICE_TYPES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# Global simulator instance
simulator = None


def setup_args():
    """Set up command line arguments."""
    parser = argparse.ArgumentParser(description="IoT Device Simulator")
    
    # MQTT connection settings
    parser.add_argument('--mqtt-host', default='localhost',
                        help='MQTT broker host (default: localhost)')
    parser.add_argument('--mqtt-port', type=int, default=1883,
                        help='MQTT broker port (default: 1883)')
    
    # Device settings
    parser.add_argument('--device-type', default='temperature',
                        choices=list(DEVICE_TYPES.keys()),
                        help='Type of device to simulate')
    parser.add_argument('--count', type=int, default=10,
                        help='Number of devices to simulate (default: 10)')
    parser.add_argument('--frequency', type=float, default=5.0,
                        help='Publishing frequency in seconds (default: 5.0)')
    parser.add_argument('--failure-rate', type=float, default=0.01,
                        help='Device failure rate (0.0-1.0, default: 0.01)')
    parser.add_argument('--noise-factor', type=float, default=0.05,
                        help='Sensor noise factor (0.0-1.0, default: 0.05)')
    
    # Location settings
    parser.add_argument('--locations', nargs='+', default=['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'],
                        help='List of location names for the devices')
    
    # Runtime settings
    parser.add_argument('--runtime', type=int, default=0,
                        help='Run for specified seconds then exit (default: 0 = run indefinitely)')
    parser.add_argument('--output-file', type=str, default=None,
                        help='Save device information to the specified JSON file')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')
    
    return parser.parse_args()


def signal_handler(signal, frame):
    """Handle Ctrl+C gracefully."""
    logger.info("Shutting down simulator...")
    if simulator:
        simulator.stop()
    sys.exit(0)


def main():
    """Main entry point for the simulator CLI."""
    global simulator
    
    # Parse command line arguments
    args = setup_args()
    
    # Set up logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create the simulator
    simulator = DeviceSimulator(
        broker_host=args.mqtt_host,
        broker_port=args.mqtt_port
    )
    
    # Start the simulator
    if not simulator.start():
        logger.error("Failed to start simulator. Exiting.")
        return 1
    
    # Create the specified number of devices
    logger.info(f"Creating {args.count} {args.device_type} devices...")
    
    devices = []
    for i in range(args.count):
        # Set up device configuration
        config = {
            "failure_rate": args.failure_rate,
            "noise_factor": args.noise_factor
        }
        
        # Pick a random location
        location = random.choice(args.locations)
        
        # Create device name
        name = f"{args.device_type.capitalize()}-{i+1:03d}"
        
        # Create the device
        device = simulator.add_device(
            args.device_type,
            name=name,
            location=location,
            config=config
        )
        
        # Start the device
        simulator.start_device(device.device_id, interval=args.frequency)
        
        devices.append(device.device_id)
    
    logger.info(f"Started {len(devices)} {args.device_type} devices")
    
    # Save device information to file if requested
    if args.output_file:
        try:
            device_info = simulator.get_all_devices_info()
            with open(args.output_file, 'w') as f:
                json.dump(device_info, f, indent=2)
            logger.info(f"Saved device information to {args.output_file}")
        except Exception as e:
            logger.error(f"Failed to save device information: {e}")
    
    # Run for the specified time or indefinitely
    if args.runtime > 0:
        logger.info(f"Running simulator for {args.runtime} seconds")
        time.sleep(args.runtime)
        simulator.stop()
        return 0
    else:
        logger.info("Simulator running. Press Ctrl+C to stop.")
        # Keep the main thread alive
        while True:
            time.sleep(1)


if __name__ == "__main__":
    sys.exit(main()) 