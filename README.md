# IoTLab

A comprehensive IoT telemetry simulation and monitoring platform with real-time data processing and visualization capabilities.

## Overview

IoTLab is a robust IoT telemetry platform that includes:

1. **Device Simulator** - A CLI tool that spawns hundreds of virtual edge devices, each publishing configurable data schemas over MQTT/WebSockets with tunable noise & failure modes.

2. **Ingest & API Layer** - Django + Django-Channels service that subscribes, persists to PostgreSQL/TimescaleDB, exposes a versioned REST/GraphQL API, and pushes live updates via Server-Sent Events.

3. **Realtime Dashboard** - Lightweight HTMX/Alpine.js frontend with live charts, anomaly flags, and per-device drill-downs. Features include:
   - Real-time device status monitoring
   - Live telemetry data visualization
   - Anomaly detection and alerts
   - Historical data analysis
   - System-wide metrics and statistics

## Tech Stack

- **Backend**: Django + Django Channels
- **Database**: PostgreSQL with TimescaleDB extension
- **Real-time Communication**: MQTT, WebSockets
- **Frontend**: HTMX, Alpine.js
- **Message Broker**: Eclipse Mosquitto (MQTT)
- **Cache**: Redis
- **Containerization**: Docker & Docker Compose

## Prerequisites

- Python 3.10 or higher (Project not compatible with Python 3.9 or lower)
- Docker Desktop
- Git

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/himcesjf/IoTLab.git
cd IoTLab
```

### 2. Python Environment Setup

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Docker Setup

1. Ensure Docker Desktop is running
2. Check for port conflicts:
   - Mosquitto: 1883
   - PostgreSQL/TimescaleDB: 5432
   - Redis: 6379

3. Start the services:
```bash
docker-compose up -d
```

To verify all services are running:
```bash
docker-compose ps
```

### 4. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 5. Database Setup

```bash
python manage.py migrate
```

### 6. Run Development Server

```bash
python manage.py runserver
```

## Accessing Services

After starting all services, you can access them at:

- **Django Development Server**: http://127.0.0.1:8000
- **Django Admin Interface**: http://127.0.0.1:8000/admin
- **API Documentation**: http://127.0.0.1:8000/api/docs
- **Real-time Dashboard**: http://127.0.0.1:8000/dashboard
- **Device Monitoring**: http://127.0.0.1:8000/devices
- **Anomaly Detection**: http://127.0.0.1:8000/anomalies
- **System Metrics**: http://127.0.0.1:8000/metrics

Other services:
- **PostgreSQL/TimescaleDB**: Port 5432
- **Redis**: Port 6379
- **MQTT (Mosquitto)**: Port 1883

## Running Device Simulators

There are two ways to generate device data:

### 1. Real-time Device Simulator

This simulator creates live devices that publish data continuously over MQTT:

```bash
# Spawn 10 simulated temperature sensors
python -m telemetrix_lab.device_simulator.cli --device-type temperature --count 10 --frequency 5

# Generate high-frequency vibration data with customized failure rate
python -m telemetrix_lab.device_simulator.cli --device-type vibration --count 5 --frequency 10 --failure-rate 0.05

# Create flow meters with specific noise factor
python -m telemetrix_lab.device_simulator.cli --device-type flow --count 3 --frequency 30 --noise-factor 0.1
```

Available options:
- `--device-type`: temperature, vibration, or flow
- `--count`: Number of devices to simulate
- `--frequency`: Publishing frequency in seconds
- `--failure-rate`: Device failure probability (0.0-1.0)
- `--noise-factor`: Sensor noise factor (0.0-1.0)
- `--mqtt-host`: MQTT broker host (default: localhost)
- `--mqtt-port`: MQTT broker port (default: 1883)

### 2. Sample Data Generation

For testing purposes, you can also generate historical sample data using Django management commands:

```bash
# First, seed sample devices
python manage.py seed_devices

# Then generate historical telemetry data
python manage.py generate_telemetry --days 7 --readings-per-day 96 --anomaly-probability 0.1
```

Sample data options:
- `--days`: Number of days of historical data to generate
- `--readings-per-day`: Number of readings per day per device
- `--anomaly-probability`: Probability of generating anomalies

### Management command help

Use Django's built-in help to discover available commands and options:

```bash
# List all commands
python manage.py help

# Command-specific help and options
python manage.py seed_devices --help
python manage.py generate_telemetry --help
python manage.py run_mqtt_client --help
```

## API Reference

The API documentation is available at `/api/docs/` when the server is running.

## Troubleshooting

1. **Port Conflicts**
   - If Mosquitto fails to start, check if a local Mosquitto service is running:
     ```bash
     sudo lsof -i :1883  # Check what's using MQTT port
     sudo service mosquitto stop  # Stop local Mosquitto if needed
     ```

2. **Python Version**
   - Ensure you're using Python 3.10 or higher:
     ```bash
     python --version
     ```
   - If using an older version, consider using pyenv or conda to install a compatible version

3. **Docker Issues**
   - Ensure Docker Desktop is running
   - Try restarting Docker Desktop if containers fail to start
   - Check container logs: `docker-compose logs [service_name]`