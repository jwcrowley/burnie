# Disk Reliability Lab - Architecture Documentation

## System Architecture Overview

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Browser]
    end

    subgraph "Presentation Layer"
        DASH[Dashboard Server<br/>FastAPI + HTMX]
        STATIC[Static Assets<br/>CSS/JS]
        TEMPLATES[Jinja2 Templates]
    end

    subgraph "API Layer"
        API[API Server<br/>FastAPI]
        SWAGGER[Swagger UI]
    end

    subgraph "Service Layer"
        TEST_MGR[Test Manager]
        SMART_MGR[SMART Manager]
        RELIABILITY[Reliability Scoring]
        ALERT_MGR[Alert Manager]
    end

    subgraph "Data Layer"
        SQLITE[(SQLite Database)]
        FILES[Test Artifacts<br/>Logs/Outputs]
    end

    subgraph "Hardware Layer"
        DISKS[Physical Disks<br/>/dev/sd*]
        SMARTCTL[smartctl]
        BADBLOCKS[badblocks]
        FIO[fio]
    end

    subgraph "Monitoring Layer"
        PROM_EXP[Prometheus Exporter<br/>port 9105<br/>External Prometheus scrapes this]
    end

    WEB -->|HTTP| DASH
    WEB -->|HTTP| API
    DASH -->|Proxy| API
    DASH -->|Serve| STATIC
    DASH -->|Render| TEMPLATES
    API -->|Use| TEST_MGR
    API -->|Use| SMART_MGR
    API -->|Use| RELIABILITY
    API -->|Use| ALERT_MGR
    TEST_MGR -->|Execute| BADBLOCKS
    TEST_MGR -->|Execute| FIO
    SMART_MGR -->|Query| SMARTCTL
    BADBLOCKS -->|Access| DISKS
    SMARTCTL -->|Access| DISKS
    FIO -->|Access| DISKS
    API -->|SQL| SQLITE
    TEST_MGR -->|Write| FILES
    PROM_EXP -->|Read| SQLITE
```

## Component Details

### Dashboard Server (`web_dashboard.py`)

```mermaid
classDiagram
    class DashboardServer {
        +FastAPI app
        +Jinja2Templates templates
        +fetch_api(endpoint)
        +proxy_request(method, path)
    }

    class RouteHandlers {
        +GET_dashboard()
        +GET_disks()
        +GET_disks_serial()
        +GET_analytics()
        +GET_alerts()
        +GET_tests()
        +GET_attached()
    }

    class HTMXPartials {
        +GET_stats_overview()
        +GET_alerts_summary()
        +GET_disks_table()
        +GET_tests_running()
    }

    class SSEStream {
        +GET_events()
        -event_generator()
    }

    DashboardServer --> RouteHandlers
    DashboardServer --> HTMXPartials
    DashboardServer --> SSEStream
```

**Responsibilities:**
- Serve HTML templates with Jinja2
- Proxy API requests to backend
- Handle HTMX partial updates
- Provide SSE for real-time updates
- Serve static assets

### API Server (`api_server.py`)

```mermaid
classDiagram
    class APIServer {
        +FastAPI app
        +sqlite3 connection
        +test_manager
        +smart_manager
    }

    class DiskEndpoints {
        +GET_disks()
        +GET_disks_serial()
        +GET_attached()
        +POST_disk_register()
        +PUT_disk_update()
    }

    class TestEndpoints {
        +POST_test_start()
        +GET_tests_running()
        +POST_test_kill()
        +GET_tests_history()
        +POST_tests_cleanup()
    }

    class AnalyticsEndpoints {
        +GET_stats_overview()
        +GET_stats_vendor()
        +GET_stats_batch()
        +GET_batch_comparison()
    }

    class SmartEndpoints {
        +GET_smart_device()
        +GET_smart_errors()
        +GET_temp_summary()
    }

    class TestRunner {
        +run_burnin_test()
        +run_quick_test()
        +run_short_test()
        +run_long_test()
        +run_seq_speed_test()
        +run_iops_test()
        +run_sustained_write_test()
    }

    APIServer --> DiskEndpoints
    APIServer --> TestEndpoints
    APIServer --> AnalyticsEndpoints
    APIServer --> SmartEndpoints
    TestEndpoints --> TestRunner
```

## Test Execution Flow

```mermaid
sequenceDiagram
    actor User
    participant UI as Web Dashboard
    participant API as API Server
    participant DB as Database
    participant BG as Background Thread
    participant TST as Test Process
    participant HW as Hardware

    User->>UI: Start Test (device, type)
    UI->>API: POST /test/start
    API->>DB: Create test record (status=running)
    API->>BG: Spawn test thread
    API-->>UI: Test started (test_id)

    BG->>HW: Execute test (badblocks/smartctl)
    HW-->>BG: Progress updates

    loop Poll for completion
        BG->>HW: Check test status
        HW-->>BG: Status (running/complete)
        BG->>DB: Update progress
    end

    HW-->>BG: Test complete
    BG->>HW: Get final results
    BG->>HW: Collect SMART data
    BG->>DB: Update test (result, finished)
    BG->>DB: Store SMART history
    BG->>API: Trigger reliability recalc
    API->>DB: Update reliability_score
```

## Reliability Scoring Algorithm

```mermaid
graph TD
    A[SMART Data] --> B{Critical Issues?}
    B -->|Yes| C[Score: 0-20]
    B -->|No| D[Base Score: 100]

    D --> E[Subtract: Reallocated Sectors × 2]
    D --> F[Subtract: Pending Sectors × 5]
    D --> G[Subtract: Reallocation Events × 3]

    E --> H[Test History Score]
    F --> H
    G --> H

    H --> I{Recent Tests}
    I -->|All Pass| J[+0]
    I -->|Some Fail| K[-20]
    I -->|No Tests| L[-10]

    J --> M[Temperature Adjustment]
    K --> M
    L --> M

    M --> N{Max Temp}
    N -->|< 40°C| O[+0]
    N -->|40-50°C| P[-5]
    N -->|> 50°C| Q[-15]

    O --> R[Final Score]
    P --> R
    Q --> R
    C --> R

    R --> S{Score Range}
    S -->|90-100| T[Excellent]
    S -->|70-89| U[Good]
    S -->|50-69| V[Fair]
    S -->|< 50| W[Poor]
```

### Score Formula

```
Base Score = 100

SMART Penalties:
- Reallocated Sector Count: -2 per sector
- Pending Sector Count: -5 per sector
- Reallocation Events: -3 per event
- Critical Warnings: -80

Test History:
- All tests passed: +0
- Any test failed: -20
- No tests recorded: -10

Temperature:
- Max temp < 40°C: +0
- Max temp 40-50°C: -5
- Max temp > 50°C: -15

Latency Anomalies:
- 0-2 anomalies: +0
- 3-5 anomalies: -5
- 6+ anomalies: -10

Final Score = max(0, min(100, Base + Adjustments))
```

## Database Schema Relationships

```mermaid
erDiagram
    DISKS ||--o{ TESTS : "has many"
    DISKS ||--o{ SMART_HISTORY : "tracks"
    DISKS ||--o{ LATENCY_ANOMALIES : "records"
    DISKS ||--o{ TEMPERATURE_HISTORY : "monitors"

    DISKS {
        string serial PK "Disk serial number"
        string model "Device model"
        string vendor "Manufacturer"
        string batch "Purchase batch"
        int size_bytes "Capacity in bytes"
        string interface "SATA/SAS/NVMe"
        datetime first_seen "Initial detection"
        datetime last_test "Last test timestamp"
        string status "new/testing/failed/passed"
        int reliability_score "0-100 health score"
    }

    TESTS {
        int id PK
        string serial FK
        string device "/dev/sdX"
        datetime started "Test start"
        datetime finished "Test end"
        string result "running/passed/failed/aborted"
        string test_type "burnin/smart_short/etc"
        int pid "Process ID for cancellation"
    }

    SMART_HISTORY {
        int id PK
        string serial FK
        string attribute "Attribute name"
        int value "Raw/normalized value"
        datetime timestamp "Recorded at"
    }

    LATENCY_ANOMALIES {
        int id PK
        string serial FK
        float latency_ms "Latency in ms"
        datetime timestamp "Detected at"
    }

    TEMPERATURE_HISTORY {
        int id PK
        string serial FK
        int temperature "Celsius"
        datetime timestamp "Recorded at"
    }
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Docker Host"
        subgraph "Docker Network"
            API_CONT[burnie-api<br/>port 8181]
            DASH_CONT[burnie-dashboard<br/>port 8080]
            PROM_EXP[Prometheus Exporter<br/>port 9105]
        end

        subgraph "Volume Mounts"
            DB_VOL[(disks.db)]
            ART_VOL[artifacts/]
        end

        subgraph "Device Pass-through"
            DEV1[dev-sda]
            DEV2[dev-sdb]
            DEV3[dev-sdc]
        end
    end

    subgraph "External Monitoring"
        PROM[Prometheus<br/>scrapes port 9105]
        GRAF[Grafana<br/>queries Prometheus]
    end

    USER[User Browser] -->|HTTP 8080| DASH_CONT
    DASH_CONT -->|Internal API| API_CONT
    API_CONT -->|DB| DB_VOL
    API_CONT -->|Logs| ART_VOL
    API_CONT -->|Direct Access| DEV1
    API_CONT -->|Direct Access| DEV2
    API_CONT -->|Direct Access| DEV3
    PROM -->|Scrape| PROM_EXP
    GRAF -->|Query| PROM
```

## Security Considerations

**Current State:** No authentication or authorization. The API and dashboard are open to anyone who can reach them.

**Privilege Requirements:**

| Operation | Privilege | Reason |
|-----------|-----------|--------|
| badblocks (destructive) | root / SYS_RAWIO | Direct disk access |
| smartctl | root / SYS_RAWIO | SMART data access |
| fio | root / SYS_RAWIO | Direct disk I/O |
| hdparm (secure erase) | root / SYS_ADMIN | ATA commands |
| Database read/write | user level | SQLite file access |

**Deployment Recommendations:**

- Run behind a reverse proxy (nginx, traefik) with authentication
- Use network policies / firewall rules to restrict access
- Consider adding API key authentication for remote access
- Docker privileged mode is required for disk access - isolate appropriately

## Error Handling Strategy

```mermaid
graph TD
    A[Operation Start] --> B{Device Access?}
    B -->|Failed| C[Device Error]
    B -->|Success| D{Test Start?}

    C --> E[Mark disk: unavailable]
    E --> F[Alert: Device Error]

    D -->|Failed| G[Test Error]
    D -->|Success| H[Monitoring Loop]

    G --> I[Mark test: failed]
    I --> J[Alert: Test Failed]

    H --> K{Check Progress}
    K -->|Timeout| L[Mark test: aborted]
    K -->|Process Died| M[Mark test: failed]
    K -->|Success| N[Mark test: passed]

    L --> O[Alert: Test Timeout]
    M --> P[Alert: Process Died]
    N --> Q[Update SMART History]
    Q --> R[Recalculate Score]
```

## Performance Considerations

### Concurrency Model

```mermaid
graph LR
    subgraph "FastAPI Async"
        MAIN[Main Event Loop]
    end

    subgraph "Background Threads"
        T1[Test Thread 1]
        T2[Test Thread 2]
        T3[Test Thread N]
    end

    subgraph "Process Pool"
        P1[badblocks proc]
        P2[fio proc]
        P3[smartctl proc]
    end

    MAIN --> T1
    MAIN --> T2
    MAIN --> T3
    T1 --> P1
    T2 --> P2
    T3 --> P3
```

### Database Connection Management

```mermaid
sequenceDiagram
    participant API
    participant ConnPool
    participant DB

    API->>ConnPool: Request connection
    ConnPool->>DB: Open connection
    DB-->>ConnPool: Connection handle
    ConnPool-->>API: Connection

    API->>DB: Execute query
    DB-->>API: Results

    API->>ConnPool: Return connection
    ConnPool->>DB: Close connection
```

## Monitoring and Observability

### Metrics Collected

```mermaid
mindmap
  root((Metrics))
    Disk Health
      Reliability Score
      SMART Attributes
      Temperature
      Power On Hours
    Test Status
      Running Tests
      Pass Fail Rate
      Test Duration
      Last Test Time
    System
      Active Tests
      Queue Depth
      Database Size
      API Response Time
    Alerts
      Low Score Count
      High Temp Count
      Latency Anomalies
```

### Prometheus Metrics Exported

The `prometheus_exporter.py` exposes metrics on port 9105:

```prometheus
# Disk reliability score
disk_reliability_score{serial="XXXX"}
```

External Prometheus server scrapes this endpoint. Grafana dashboards can then query Prometheus to visualize the data.

## Extension Points

### Adding New Test Types

1. Implement test function in `api_server.py`
2. Add to `TestRequest.test_type` enum
3. Register in test router
4. Add UI option in `templates/tests.html`

### Adding New Analytics

1. Create query in `api_server.py`
2. Add endpoint `/stats/my_analytics`
3. Create chart in `templates/analytics.html`
4. Add to navigation

### Adding New Alerts

1. Define alert condition in `alert_manager.py`
2. Add to `/alerts` endpoint response
3. Create UI display in `templates/alerts.html`
4. Add notification handler
