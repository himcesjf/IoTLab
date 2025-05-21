# IoTLab

IoT telemetry simulator and observability stack.


## Overview

Telemetrix Lab is a comprehensive IoT telemetry platform that includes:

1. **Device Simulator** - A CLI tool that spawns hundreds of virtual edge devices, each publishing configurable data schemas over MQTT/WebSockets with tunable noise & failure modes.

2. **Ingest & API Layer** - Django + Django-Channels service that subscribes, persists to PostgreSQL/TimescaleDB, exposes a versioned REST/GraphQL API, and pushes live updates via Server-Sent Events.

3. **Realtime Dashboard** - Lightweight HTMX/Alpine.js frontend with live charts, anomaly flags, and per-device drill-downs.

## Tech Stack

- **Backend**: Django + Django Channels
- **Database**: PostgreSQL with TimescaleDB extension
- **Real-time Communication**: MQTT, WebSockets
- **Frontend**: HTMX, Alpine.js
- **Message Broker**: Mosquitto (MQTT)
- **Containerization**: Docker & Docker Compose

## Architecture

![Architecture Diagram](ToDO)

## Getting Started

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- MQTT Broker (Mosquitto is included in Docker setup)

### Installation

1. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Start the required services using Docker:
   ```
   docker-compose up -d
   ```

3. Configure environment variables:
   ```
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Run database migrations:
   ```
   python manage.py migrate
   ```

5. Start the Django development server:
   ```
   python manage.py runserver
   ```

### Running the Device Simulator

```
# Spawn 10 simulated temperature sensors
python -m telemetrix_lab.device_simulator.cli --device-type temperature --count 10

# Generate high-frequency data with customized failure rate
python -m telemetrix_lab.device_simulator.cli --device-type vibration --count 5 --frequency 10 --failure-rate 0.05
```

## API Reference

(ToDo) The API documentation will be available at `/api/docs/` when the server is running.