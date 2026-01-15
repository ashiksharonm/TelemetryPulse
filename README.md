# TelemetryPulse

TelemetryPulse is a production-style, real-time IoT event pipeline simulating a smart building analytics system. It ingests sensor data (CO2, Temperature, Humidity, Occupancy), streams it through Redpanda (Kafka), processes it for aggregation and alerting, and exposes analytics via a REST API.

## Architecture

1.  **Producer Simulator**: 
    - Simulates IoT devices across multiple sites and zones.
    - Generates random but realistic telemetry.
    - Publishes JSON events to the `telemetry.events` Kafka topic.

2.  **Message Broker**:
    - **Redpanda**: Kafka-compatible streaming platform.
    - **Redpanda Console**: Web UI for inspecting topics and messages.

3.  **Stream Processor**:
    - Consumes raw events.
    - Validates schema and inserts raw data into PostgreSQL (idempotent).
    - Computes tumbling window aggregates (5m, 15m).
    - Detects anomalies (e.g., High CO2) and generates alerts.
    - Handles failures with retries and a Dead Letter Queue (DLQ).

4.  **Database**:
    - **PostgreSQL**: Stores raw events, aggregates, and alerts.

5.  **Analytics API**:
    - **FastAPI** service exposing endpoints for real-time dashboards and historical trends.

## Prerequisites

- Docker
- Docker Compose

## Quick Start (Local)

1.  **Start Infrastructure**:
    ```bash
    docker-compose up -d
    ```

2.  **Access Interfaces**:
    - **Redpanda Console**: [http://localhost:8080](http://localhost:8080)
    - **Postgres**: localhost:5432 (User: `admin`, Pass: `password`, DB: `telemetry`)

## Development

- **Language**: Python 3.10+
- **Tools**: `poetry` or `pip` (requirements.txt provided per service)

## Directory Structure
- `producer_simulator/`: Source for determining and sending events.
- `stream_processor/`: Consumer logic, aggregation, and DB interaction.
- `api_service/`: FastAPI application.
- `api_service/`: FastAPI application.
- `postgres/`: Database initialization scripts.

## Running Tests

Unit tests are included for the Stream Processor and API Service.

1.  **Stream Processor**:
    ```bash
    pip install -r stream_processor/requirements.txt
    export PYTHONPATH=$PYTHONPATH:$(pwd)/stream_processor
    pytest stream_processor/tests/
    ```

2.  **API Service**:
    ```bash
    pip install -r api_service/requirements.txt
    export PYTHONPATH=$PYTHONPATH:$(pwd)/api_service
    pytest api_service/tests/
    ```

## CI/CD

A GitHub Actions workflow (`.github/workflows/ci.yml`) is configured to:
- Run unit tests on every push/PR to `main`.
- Build Docker images to ensure validity.

## Cloud Deployment (Free Tier)

To deploy this project for free, we use a serverless stack:
- **Kafka**: [Upstash](https://upstash.com/) (Free Tier)
- **Database**: [Neon](https://neon.tech/) (Free Tier Postgres)
- **Compute**: [Render](https://render.com/) (Free Tier)

### 1. Setup Resources
1.  **Upstash**: Create a Kafka cluster. Get `Bootstrap Server`, `Username`, and `Password`.
2.  **Neon**: Create a Postgres project. Get the `Connection String` (e.g., `postgresql://user:pass@ep-xyz.aws.neon.tech/neondb?sslmode=require`). Run the contents of `postgres/init.sql` in the Neon SQL Editor.

### 2. Deploy on Render
1.  Push this repo to your GitHub.
2.  Sign up for Render and link your GitHub account.
3.  Go to **Blueprints** -> **New Blueprint Instance**.
4.  Select your repo. Render will detect `render.yaml`.
5.  Fill in the environment variables when prompted:
    - `DATABASE_URL`: Your Neon connection string.
    - `KAFKA_BOOTSTRAP_SERVERS`: Your Upstash URL.
    - `KAFKA_SASL_USERNAME`: Your Upstash Username.
    - `KAFKA_SASL_PASSWORD`: Your Upstash Password.
6.  Click **Apply**. Render will deploy the API, Processor, and Simulator.

### 3. Verify
Once deployed, access your API at the URL provided by Render (e.g., `https://telemetry-api-xyz.onrender.com/docs`).


