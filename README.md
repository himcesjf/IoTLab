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

## Quick Start

```bash
# 1. Clone + install deps
git clone https://github.com/himcesjf/IoTLab.git
cd IoTLab
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Start supporting services (TimescaleDB, Redis, Mosquitto)
docker-compose up -d

# 3. Configure + migrate
cp env.example .env
python manage.py migrate

# 4. Seed and backfill sample data
python manage.py seed_devices
python manage.py generate_telemetry --days 1 --readings-per-day 24

# 5. Run the app
python manage.py run_mqtt_client   # optional: live ingestion
python manage.py runserver         # dashboard/API at http://127.0.0.1:8000
```

## Project Structure

```
IoTLab/
├─ manage.py                  # Django entry point (uses iotlab.ingest_api.core.settings)
├─ docker-compose.yml         # TimescaleDB, Redis, Mosquitto services
├─ iotlab/
│  ├─ ingest_api/core/        # Django project (settings/urls/asgi/wsgi)
│  ├─ ingest_api/devices/     # Device registry models + seed command
│  ├─ ingest_api/telemetry/   # Telemetry/anomaly models + MQTT client
│  ├─ ingest_api/api/         # API configuration (v1 router lives in /v1)
│  ├─ dashboard/              # Views, templates, static assets for UI
│  └─ device_simulator/       # Simulator CLI + device type definitions
├─ v1/                        # DRF viewsets + routers
└─ static/, etc.
```

## Accessing Services

After starting all services, you can access them at:

- **Dashboard**: http://127.0.0.1:8000/
- **Devices List**: http://127.0.0.1:8000/devices/
- **Anomalies**: http://127.0.0.1:8000/anomalies/
- **Metrics**: http://127.0.0.1:8000/metrics/
- **API v1**: http://127.0.0.1:8000/api/v1/
- **API Documentation**: http://127.0.0.1:8000/api/docs/
- **Django Admin**: http://127.0.0.1:8000/admin/

Other services:
- **PostgreSQL/TimescaleDB**: Port 5432
- **Redis**: Port 6379
- **MQTT (Mosquitto)**: Port 1883

## Data Generation

### Real-time simulator (MQTT)

```bash
python -m iotlab.device_simulator.cli \
  --device-type temperature \
  --count 10 \
  --frequency 5 \
  --failure-rate 0.02 \
  --noise-factor 0.1
```

Flags: `--device-type` (`temperature|vibration|flow`), `--count`, `--frequency` (others available via `python -m iotlab.device_simulator.cli --help`).

 (Simulator implementation lives under `iotlab/device_simulator/` — device types, MQTT engine, and CLI.)

### Historical backfill

```bash
python manage.py seed_devices
python manage.py generate_telemetry --days 7 --readings-per-day 96 --anomaly-probability 0.1
```

### Command help

```bash
python manage.py help
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