# Disk Reliability Lab v6

A full-featured disk validation and reliability analytics platform inspired by
large-scale storage operators.

## Burn-in Testing Primer

**Why Burn-in Disks?**

Enterprise storage operators know that new disks are the most unreliable component in any storage system. Factory defects show up early, and deploying untested disks is a recipe for data loss and expensive RAID rebuilds.

**What This Tool Does:**

- **Sequential Surface Scan** - Writes and verifies every sector to catch surface defects
- **SMART Attribute Tracking** - Monitors reallocated sectors, pending sectors, and error counts
- **Latency Testing** - Identifies disks with abnormal latency spikes under load
- **Thermal Stress Testing** - Ensures disks operate within safe temperature ranges
- **Reliability Scoring** - Calculates a 0-100 score based on multiple health indicators

**When to Use:**
- New disk arrivals (before putting into production)
- Pre-deployment certification for ZFS pools
- RMA warranty validation (prove defects to manufacturers)
- Suspected disk failure verification
- Periodic health checks on critical storage

**The Testing Philosophy:**

> "A disk that survives 24 hours of burn-in testing is exponentially more likely to survive its warranty period than one that hasn't been tested."

This tool implements that philosophy at scale, tracking hundreds of disks through their testing lifecycle.

## Key Capabilities

- HDD / SSD / NVMe burn-in testing
- Sequential surface initialization
- Random stress workloads
- SMART + NVMe health ingestion
- Reliability scoring engine
- SMART heuristic failure prediction
- Latency anomaly detection
- Thermal monitoring hooks
- Batch / vendor reliability statistics
- ZFS pre-deployment certification tests
- Artifact storage and audit logs
- SQLite (default) or PostgreSQL backend
- FastAPI REST API
- **New:** Full-featured Web Dashboard with HTMX
- Prometheus metrics exporter
- Grafana dashboards
- Docker deployment
- Kubernetes-ready structure

## Typical Architecture

```
burn nodes
   |
artifacts + metrics
   |
API ingestion
   |
database
   |
Prometheus
   |
Grafana dashboards
   |
Web Dashboard
```

## Quick Start

### Option A: Manual Start

```bash
chmod +x *.sh

# Initialize database:
./diskdb.sh init

# Install dependencies (for dashboard):
pip3 install -r requirements.txt

# Run burn-in on disk:
sudo ./burnin.sh /dev/sdX

# Batch testing:
sudo ./batch_burnin.sh

# Start API server:
python3 api_server.py

# Start web dashboard:
python3 web_dashboard.py

# Start Prometheus exporter:
python3 prometheus_exporter.py
```

### Option B: Docker Compose (Recommended)

```bash
# Initialize database first:
./diskdb.sh init

# Start all services:
docker compose up -d

# View logs:
docker compose logs -f

# Stop services:
docker compose down
```

Services will be available at:
- Dashboard: http://localhost:8080
- API: http://localhost:8181
- API Docs: http://localhost:8181/docs

## Web Dashboard

The new web dashboard provides a comprehensive interface for monitoring disk reliability:

### Features

- **Main Dashboard:** Overview with stats cards, charts, and recent activity
- **Disks View:** Searchable/filterable list of all disks with detailed information
- **Disk Detail:** Individual disk views with SMART data, temperature history, test results
- **Analytics:** Charts for reliability trends, vendor/model comparisons, batch performance
- **Alerts:** Centralized alert management for low scores, high temperatures, latency issues
- **Tests:** Test queue management and history tracking

### Access

- Dashboard: http://localhost:8080
- API Docs: http://localhost:8000/docs

### Configuration

Dashboard settings in `config.env`:

```
DASHBOARD_PORT=8080              # Dashboard HTTP port
DASHBOARD_REFRESH_INTERVAL=30    # Auto-refresh interval (seconds)
ALERT_RELIABILITY_THRESHOLD=70   # Score threshold for alerts
ALERT_TEMPERATURE_THRESHOLD=45   # Temperature threshold for alerts
```

### Technology Stack

- **Backend:** FastAPI (async Python web framework)
- **Frontend:** HTMX (dynamic UI without complex JavaScript)
- **Styling:** Tailwind CSS (responsive, modern UI)
- **Charts:** Chart.js (interactive visualizations)
- **Database:** SQLite (direct connection)
