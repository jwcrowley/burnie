# Disk Reliability Lab v6

A full-featured disk validation and reliability analytics platform inspired by
large-scale storage operators.

Key Capabilities
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
- Prometheus metrics exporter
- Grafana dashboards
- Simple web dashboard
- Docker deployment
- Kubernetes-ready structure

Typical Architecture

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

Quick Start

chmod +x *.sh

Initialize database:

./diskdb.sh init

Run burn-in on disk:

sudo ./burnin.sh /dev/sdX

Batch testing:

sudo ./batch_burnin.sh

Start API:

python3 api_server.py

Start dashboard:

python3 dashboard.py

Start Prometheus exporter:

python3 prometheus_exporter.py
