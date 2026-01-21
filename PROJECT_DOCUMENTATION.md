# TelemetryPulse - Project Master Documentation

## 1. Project Overview & Explanation

**TelemetryPulse** is a production-grade, real-time IoT (Internet of Things) Event Streaming Pipeline. It simulates a Smart Building management system where thousands of sensors (CO2, Temperature, Humidity, Occupancy) continuously stream data.

### The Problem
Traditional databases cannot handle the sheer velocity of "firehose" data from thousands of devices. Processing this data in batch (e.g., once a night) is too slow for critical alerts (e.g., "CO2 levels are toxic").

### The Solution: Event-Driven Architecture
TelemetryPulse treats every sensor reading as an "Event". These events are streamed instantly through a broker (Kafka), processed in real-time (Stream Processor), and made available for analytics (API) within milliseconds of generation.

---

## 2. Dataset Description (Synthesized)

Since real IoT hardware is expensive, this project includes a **Producer Simulator** that mathematically generates realistic synthetic data.

### Data Model
*   **Sites**: 3 Physical locations (e.g., `Site-01`, `Site-02`).
*   **Zones**: 5 Zones per site (e.g., `Zone-01`... `Zone-05`).
*   **Devices**: 3 Devices per Zone (Total: ~45 simulating devices).

### Sensor Types
| Sensor Type | Unit | Normal Range | Anomaly Threshold | Description |
| :--- | :--- | :--- | :--- | :--- |
| **CO2** | ppm | 400 - 800 | > 1000 | Carbon Dioxide. High levels indicate poor ventilation. |
| **Temperature** | Celsius | 18 - 26 | > 30 | Room temperature. High means AC failure or fire risk. |
| **Humidity** | % | 30 - 60 | > 80 | Relative Humidity. High means mold risk. |
| **Occupancy** | Count | 0 - 20 | N/A | Number of people in the room. |

**Volume**: Configurable. Defaults to **5 events/second** (continuous).

---

## 3. Functionalities

1.  **Real-Time Ingestion**: Capable of ingesting thousands of events/sec via Kafka.
2.  **Windowed Aggregation**: Automatically calculates "Average Temperature per 5 Minutes" or "Max CO2 per 15 Minutes" using tumbling windows.
3.  **Anomaly Detection**: Instantly detects value violations (e.g., Temp > 30°C) and generates a separate "Alert" event.
4.  **Idempotency**: Guarantees "Exactly-Once" processing. If the system crashes and restarts, it won't duplicate data in the database.
5.  **Analytics API**: Provides REST endpoints for frontend dashboards to query live status, historical trends, and heatmaps.
6.  **Self-Healing**: The cloud deployment includes logic to automatically create missing topics and handle connection drops.

---

## 4. How is this different from other projects?

| Feature | Standard "CRUD" App | TelemetryPulse (Event-Driven) |
| :--- | :--- | :--- |
| **Data Flow** | User clicks "Save" -> Database | Devices stream continuously -> Broker -> Processor -> Database |
| **Processing** | On-Demand (when requested) | Always-On (background processing) |
| **Scalability** | Limited by DB Connection Pool | Decoupled by Kafka (can buffer millions of messages) |
| **Complexity** | Low (Monolith) | High (Microservices: Producer, Broker, Consumer, API) |
| **Fault Tolerance**| If DB is down, App fails | If DB is down, Kafka buffers data until it's back |

---

## 5. Technology Stack

| Technology | Role | Usage in Project |
| :--- | :--- | :--- |
| **Python 3.11** | Language | Core logic for Producer, Processor, and API. |
| **Apache Kafka** | Message Broker | Decouples the Producer from the Consumer. Buffers data. |
| **Redpanda** | Broker (Local) | A clearer, faster, single-binary replacement for Kafka used for local dev. |
| **PostgreSQL** | Database | Stores raw events (partitioned), aggregated KPIs, and alerts. |
| **FastAPI** | REST API | Exposes data to the outside world with auto-generated Swagger docs. |
| **SQLAlchemy** | ORM | Manages database connections and SQL generation. |
| **Pandas** | Data Processing | Used in the simulator for logic (and extensible for heavier analytics). |
| **Docker** | Containerization | Packages the app for consistent local execution. |
| **Render** | Cloud Compute | Hosts the Python services (Serverless). |
| **Aiven** | Cloud Kafka | Managed Kafka service for the cloud deployment. |
| **Neon** | Cloud DB | Serverless Postgres for the cloud deployment. |

---

## 6. Architecture Diagram

```mermaid
graph TD
    subgraph "Edge Layer"
        P[Producer Simulator] -->|Raw JSON Events| K(Kafka Topic: telemetry.events)
    end

    subgraph "Processing Layer"
        K --> C[Stream Processor]
        C -->|Raw Insert| DB[(PostgreSQL)]
        C -->|Aggregate (5m/15m)| DB
        C -->|Alert Trigger| DB
    end

    subgraph "Consumption Layer"
        API[FastAPI Service] -- Read --> DB
        User[Dashboard / Swagger UI] -- HTTP GET --> API
    end

    style K fill:#ff9900,stroke:#333,stroke-width:2px
    style DB fill:#336791,stroke:#fff,stroke-width:2px
```

---

## 7. Commands & Operations

### A. Local Development (Docker)

**1. Clone the Repository**
```bash
git clone https://github.com/ashiksharonm/TelemetryPulse.git
cd TelemetryPulse
```

**2. Start the Stack (Using Makefile or Docker Compose)**
```bash
make up
# OR
docker-compose up -d --build
```
*Creates: Redpanda, Console, Postgres, API, Stream Processor, Producer.*

**3. Access Interfaces**
*   **Redpanda Console**: [http://localhost:8080](http://localhost:8080) (View Topics/Messages)
*   **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Database**: `localhost:5432` (User: `admin`, Pass: `password`, DB: `telemetry`)

**4. Stop the Stack**
```bash
make down
```

### B. Cloud Deployment (Render + Aiven + Neon)

**1. Prerequisites**
*   **Neon**: Create Project -> Get Connection String. Run `src/db/migrations.sql` in SQL Editor.
*   **Aiven**: Create Kafka Service -> Get Service URI. Download `ca.pem`, `service.cert`, `service.key`.
*   **Render**: Link GitHub Repo.

**2. Environment Variables (Render)**
Set these in your Render Dashboard for each service:
*   `DATABASE_URL`: `postgresql://user:pass@neon.tech/neondb?sslmode=require` (No 'psql' prefix!)
*   `KAFKA_BOOTSTRAP_SERVERS`: `kafka-xyz.aivencloud.com:port`
*   `KAFKA_SECURITY_PROTOCOL`: `SASL_SSL`
*   `KAFKA_SSL_CA`, `KAFKA_SSL_CERT`, `KAFKA_SSL_KEY`: (Paste file contents)

**3. Manual Deploy**
In Render Dashboard -> Select Service -> **Manual Deploy** -> **Deploy latest commit**.

### C. GitHub Commands

**Check Status** (See what files changed)
```bash
git status
```

**Stage Changes** (Prepare files for commit)
```bash
git add .
```

**Commit Changes** (Save version)
```bash
git commit -m "Description of changes"
```

**Push to Cloud** (Send to GitHub)
```bash
git push origin main
```

**Pull Updates** (Get changes from Cloud)
```bash
git pull origin main
```
