from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response
from starlette.responses import StreamingResponse
from typing import Optional, List
import sqlite3
import os
from datetime import datetime, timedelta
import json

app = FastAPI(title="Disk Reliability Lab API")

DB_PATH = os.getenv("DB", "./disks.db")


def get_db():
    """Get database connection with row factory for dict access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def format_datetime(dt_str: Optional[str]) -> Optional[str]:
    """Format datetime string for display."""
    if not dt_str:
        return None
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return dt_str


# ============================================================================
# Disk Endpoints
# ============================================================================

@app.get("/disks")
def get_disks(
    limit: Optional[int] = None,
    offset: int = 0,
    sort_by: str = "serial",
    sort_order: str = "asc"
):
    """
    Get list of all disks with pagination and sorting.

    Query params:
    - limit: Max number of results (default: all)
    - offset: Offset for pagination (default: 0)
    - sort_by: Column to sort by (default: serial)
    - sort_order: asc or desc (default: asc)
    """
    conn = get_db()

    # Validate sort column
    valid_columns = ["serial", "model", "vendor", "batch", "size_bytes", "interface", "first_seen", "last_test", "status", "reliability_score"]
    if sort_by not in valid_columns:
        sort_by = "serial"

    sort_order = "ASC" if sort_order.lower() == "asc" else "DESC"

    query = f"SELECT * FROM disks ORDER BY {sort_by} {sort_order}"
    if limit:
        query += f" LIMIT {limit} OFFSET {offset}"

    rows = conn.execute(query).fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.get("/disks/{serial}")
def get_disk(serial: str):
    """Get detailed information about a specific disk including all history."""
    conn = get_db()

    disk = conn.execute("SELECT * FROM disks WHERE serial = ?", (serial,)).fetchone()
    if not disk:
        conn.close()
        raise HTTPException(status_code=404, detail="Disk not found")

    disk_data = dict(disk)

    # Get recent SMART history (last 10 entries per attribute)
    smart_query = """
        SELECT attribute, value, timestamp
        FROM smart_history
        WHERE serial = ?
        ORDER BY timestamp DESC
        LIMIT 100
    """
    smart_rows = conn.execute(smart_query, (serial,)).fetchall()
    disk_data["smart_history"] = [dict(row) for row in smart_rows]

    # Get temperature history
    temp_query = """
        SELECT temperature, timestamp
        FROM temperature_history
        WHERE serial = ?
        ORDER BY timestamp DESC
        LIMIT 1000
    """
    temp_rows = conn.execute(temp_query, (serial,)).fetchall()
    disk_data["temperature_history"] = [dict(row) for row in temp_rows]

    # Get test history
    test_query = """
        SELECT * FROM tests
        WHERE serial = ?
        ORDER BY started DESC
        LIMIT 50
    """
    test_rows = conn.execute(test_query, (serial,)).fetchall()
    disk_data["test_history"] = [dict(row) for row in test_rows]

    # Get latency anomalies
    latency_query = """
        SELECT * FROM latency_anomalies
        WHERE serial = ?
        ORDER BY timestamp DESC
        LIMIT 100
    """
    latency_rows = conn.execute(latency_query, (serial,)).fetchall()
    disk_data["latency_anomalies"] = [dict(row) for row in latency_rows]

    conn.close()
    return disk_data


@app.get("/disks/{serial}/smart")
def get_disk_smart(serial: str, limit: int = 100):
    """Get SMART attribute history for a disk."""
    conn = get_db()

    query = """
        SELECT attribute, value, timestamp
        FROM smart_history
        WHERE serial = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """
    rows = conn.execute(query, (serial, limit)).fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.get("/disks/{serial}/temperature")
def get_disk_temperature(serial: str, hours: int = 24):
    """Get temperature history for a disk within the last N hours."""
    conn = get_db()

    cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

    query = """
        SELECT temperature, timestamp
        FROM temperature_history
        WHERE serial = ? AND timestamp >= ?
        ORDER BY timestamp ASC
    """
    rows = conn.execute(query, (serial, cutoff)).fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.get("/disks/{serial}/tests")
def get_disk_tests(serial: str, limit: int = 50):
    """Get test history for a disk."""
    conn = get_db()

    query = """
        SELECT * FROM tests
        WHERE serial = ?
        ORDER BY started DESC
        LIMIT ?
    """
    rows = conn.execute(query, (serial, limit)).fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.get("/disks/{serial}/latency")
def get_disk_latency(serial: str, limit: int = 100):
    """Get latency anomalies for a disk."""
    conn = get_db()

    query = """
        SELECT * FROM latency_anomalies
        WHERE serial = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """
    rows = conn.execute(query, (serial, limit)).fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.get("/disks/export/csv")
def export_disks_csv():
    """Export all disks as CSV."""
    conn = get_db()
    conn.row_factory = None  # Use tuple factory for CSV
    rows = conn.execute("SELECT * FROM disks").fetchall()

    # Get column names
    columns = [desc[0] for desc in conn.execute("SELECT * FROM disks LIMIT 1").description]
    conn.close()

    def iter_rows():
        yield ",".join(columns) + "\n"
        for row in rows:
            yield ",".join(str(v) if v is not None else "" for v in row) + "\n"

    return StreamingResponse(
        iter_rows(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=disks_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


# ============================================================================
# Statistics Endpoints
# ============================================================================

@app.get("/stats/overview")
def get_stats_overview():
    """Get dashboard overview statistics."""
    conn = get_db()

    # Total disks
    total_disks = conn.execute("SELECT COUNT(*) FROM disks").fetchone()[0]

    # Average reliability score
    avg_score = conn.execute("SELECT AVG(reliability_score) FROM disks WHERE reliability_score IS NOT NULL").fetchone()[0] or 0

    # Count by status
    status_counts = conn.execute("""
        SELECT status, COUNT(*) as count
        FROM disks
        GROUP BY status
    """).fetchall()
    status_breakdown = {row[0]: row[1] for row in status_counts}

    # Low reliability disks (< 70)
    low_reliability = conn.execute("""
        SELECT COUNT(*) FROM disks
        WHERE reliability_score < 70 AND reliability_score IS NOT NULL
    """).fetchone()[0]

    # Currently running tests
    running_tests = conn.execute("""
        SELECT COUNT(*) FROM tests
        WHERE finished IS NULL
    """).fetchone()[0]

    # Recent tests (last 24 hours)
    recent_tests = conn.execute("""
        SELECT COUNT(*) FROM tests
        WHERE started >= datetime('now', '-1 day')
    """).fetchone()[0]

    # Temperature stats
    temp_stats = conn.execute("""
        SELECT AVG(temperature), MAX(temperature)
        FROM temperature_history
        WHERE timestamp >= datetime('now', '-1 hour')
    """).fetchone()

    # High temperature count (disks with temp > 45°C in last hour)
    high_temp_count = conn.execute("""
        SELECT COUNT(DISTINCT disk_serial)
        FROM temperature_history
        WHERE timestamp >= datetime('now', '-1 hour')
        AND temperature > 45
    """).fetchone()[0]

    # Reliability score distribution
    score_dist = conn.execute("""
        SELECT
            CASE
                WHEN reliability_score >= 90 THEN '90-100'
                WHEN reliability_score >= 70 THEN '70-89'
                WHEN reliability_score >= 50 THEN '50-69'
                WHEN reliability_score >= 30 THEN '30-49'
                ELSE '0-29'
            END as range,
            COUNT(*) as count
        FROM disks
        WHERE reliability_score IS NOT NULL
        GROUP BY range
        ORDER BY range DESC
    """).fetchall()

    conn.close()

    return {
        "total_disks": total_disks,
        "average_score": round(avg_score, 1),
        "status_breakdown": status_breakdown,
        "low_reliability_count": low_reliability,
        "running_tests": running_tests,
        "recent_tests_24h": recent_tests,
        "avg_temperature": round(temp_stats[0], 1) if temp_stats[0] else None,
        "max_temperature": temp_stats[1],
        "high_temp_count": high_temp_count,
        "score_distribution": {row[0]: row[1] for row in score_dist}
    }


@app.get("/stats/vendor")
def get_stats_vendor():
    """Get reliability statistics grouped by vendor."""
    conn = get_db()

    query = """
        SELECT
            vendor,
            COUNT(*) as disk_count,
            AVG(reliability_score) as avg_score,
            MIN(reliability_score) as min_score,
            MAX(reliability_score) as max_score
        FROM disks
        WHERE vendor IS NOT NULL AND reliability_score IS NOT NULL
        GROUP BY vendor
        ORDER BY avg_score DESC
    """
    rows = conn.execute(query).fetchall()
    conn.close()

    return [
        {
            "vendor": row[0],
            "disk_count": row[1],
            "avg_score": round(row[2], 1) if row[2] else None,
            "min_score": row[3],
            "max_score": row[4]
        }
        for row in rows
    ]


@app.get("/stats/model")
def get_stats_model():
    """Get reliability statistics grouped by model."""
    conn = get_db()

    query = """
        SELECT
            model,
            vendor,
            COUNT(*) as disk_count,
            AVG(reliability_score) as avg_score,
            MIN(reliability_score) as min_score,
            MAX(reliability_score) as max_score
        FROM disks
        WHERE model IS NOT NULL AND reliability_score IS NOT NULL
        GROUP BY model, vendor
        ORDER BY avg_score DESC
    """
    rows = conn.execute(query).fetchall()
    conn.close()

    return [
        {
            "model": row[0],
            "vendor": row[1],
            "disk_count": row[2],
            "avg_score": round(row[3], 1) if row[3] else None,
            "min_score": row[4],
            "max_score": row[5]
        }
        for row in rows
    ]


@app.get("/stats/batch")
def get_stats_batch():
    """Get reliability statistics grouped by batch."""
    conn = get_db()

    query = """
        SELECT
            batch,
            COUNT(*) as disk_count,
            AVG(reliability_score) as avg_score,
            COUNT(CASE WHEN reliability_score < 70 THEN 1 END) as failed_count
        FROM disks
        WHERE batch IS NOT NULL AND reliability_score IS NOT NULL
        GROUP BY batch
        ORDER BY batch DESC
    """
    rows = conn.execute(query).fetchall()
    conn.close()

    return [
        {
            "batch": row[0],
            "disk_count": row[1],
            "avg_score": round(row[2], 1) if row[2] else None,
            "failed_count": row[3],
            "failure_rate": round((row[3] / row[1] * 100), 1) if row[1] > 0 else 0
        }
        for row in rows
    ]


@app.get("/stats/interface")
def get_stats_interface():
    """Get reliability statistics grouped by interface type."""
    conn = get_db()

    query = """
        SELECT
            interface_type,
            COUNT(*) as disk_count,
            AVG(reliability_score) as avg_score
        FROM disks
        WHERE interface_type IS NOT NULL AND reliability_score IS NOT NULL
        GROUP BY interface_type
        ORDER BY avg_score DESC
    """
    rows = conn.execute(query).fetchall()
    conn.close()

    return [
        {
            "interface_type": row[0],
            "disk_count": row[1],
            "avg_score": round(row[2], 1) if row[2] else None
        }
        for row in rows
    ]


@app.get("/stats/timeline")
def get_stats_timeline(days: int = 30):
    """Get reliability score trends over time."""
    conn = get_db()

    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    query = """
        SELECT
            DATE(last_test) as test_date,
            COUNT(*) as test_count,
            AVG(reliability_score) as avg_score
        FROM disks
        WHERE last_test >= ?
            AND reliability_score IS NOT NULL
        GROUP BY DATE(last_test)
        ORDER BY test_date ASC
    """
    rows = conn.execute(query, (cutoff,)).fetchall()
    conn.close()

    return [
        {
            "date": row[0],
            "test_count": row[1],
            "avg_score": round(row[2], 1) if row[2] else None
        }
        for row in rows
    ]


@app.get("/temperature/summary")
def get_temperature_summary():
    """Get temperature summary statistics."""
    conn = get_db()

    # Get recent temperature stats
    temp_stats = conn.execute("""
        SELECT AVG(temperature) as avg_temp,
               MAX(temperature) as max_temp,
               COUNT(*) as reading_count
        FROM temperature_history
        WHERE timestamp >= datetime('now', '-1 hour')
    """).fetchone()

    # Get disks with high temperatures
    high_temp_disks = conn.execute("""
        SELECT DISTINCT dh.serial, d.model, dh.temperature
        FROM temperature_history dh
        JOIN disks d ON d.serial = dh.serial
        WHERE dh.timestamp >= datetime('now', '-1 hour')
            AND dh.temperature > 45
        ORDER BY dh.temperature DESC
        LIMIT 10
    """).fetchall()

    conn.close()

    return {
        "avg_temperature": round(temp_stats[0], 1) if temp_stats and temp_stats[0] else None,
        "max_temperature": temp_stats[1] if temp_stats else None,
        "reading_count": temp_stats[2] if temp_stats else 0,
        "high_temp_disks": [
            {"serial": row[0], "model": row[1], "temperature": row[2]}
            for row in high_temp_disks
        ]
    }


# ============================================================================
# Alerts Endpoints
# ============================================================================

@app.get("/alerts")
def get_alerts(
    alert_type: Optional[str] = None,
    limit: int = 100
):
    """
    Get active alerts.

    Query params:
    - alert_type: Filter by type (reliability, temperature, latency)
    - limit: Max number of alerts (default: 100)
    """
    conn = get_db()
    alerts = []

    reliability_threshold = int(os.getenv("ALERT_RELIABILITY_THRESHOLD", "70"))
    temperature_threshold = int(os.getenv("ALERT_TEMPERATURE_THRESHOLD", "45"))

    if alert_type in [None, "reliability"]:
        # Low reliability alerts
        query = """
            SELECT serial, model, reliability_score, 'reliability' as type
            FROM disks
            WHERE reliability_score < ?
            ORDER BY reliability_score ASC
        """
        rows = conn.execute(query, (reliability_threshold,)).fetchall()
        for row in rows:
            alerts.append({
                "serial": row[0],
                "model": row[1],
                "type": "reliability",
                "severity": "critical" if row[2] < 50 else "warning",
                "message": f"Reliability score {row[2]} is below threshold {reliability_threshold}",
                "value": row[2],
                "threshold": reliability_threshold
            })

    if alert_type in [None, "temperature"]:
        # High temperature alerts (last hour)
        query = """
            SELECT DISTINCT dh.serial, d.model, dh.temperature
            FROM temperature_history dh
            JOIN disks d ON d.serial = dh.serial
            WHERE dh.timestamp >= datetime('now', '-1 hour')
                AND dh.temperature > ?
            ORDER BY dh.temperature DESC
        """
        rows = conn.execute(query, (temperature_threshold,)).fetchall()
        for row in rows:
            alerts.append({
                "serial": row[0],
                "model": row[1],
                "type": "temperature",
                "severity": "critical" if row[2] > 55 else "warning",
                "message": f"Temperature {row[2]}°C exceeds threshold {temperature_threshold}°C",
                "value": row[2],
                "threshold": temperature_threshold
            })

    if alert_type in [None, "latency"]:
        # Latency anomaly alerts (last 24 hours)
        query = """
            SELECT la.serial, d.model, la.latency_ms, la.timestamp
            FROM latency_anomalies la
            JOIN disks d ON d.serial = la.serial
            WHERE la.timestamp >= datetime('now', '-1 day')
            ORDER BY la.latency_ms DESC
        """
        rows = conn.execute(query,()).fetchall()
        for row in rows:
            alerts.append({
                "serial": row[0],
                "model": row[1],
                "type": "latency",
                "severity": "warning",
                "message": f"Latency anomaly detected: {row[2]}ms",
                "value": row[2],
                "timestamp": row[3]
            })

    if alert_type in [None, "test"]:
        # Failed test alerts (last 7 days)
        query = """
            SELECT t.serial, d.model, t.result, t.finished
            FROM tests t
            JOIN disks d ON d.serial = t.serial
            WHERE t.result = 'failed'
                AND t.finished >= datetime('now', '-7 days')
            ORDER BY t.finished DESC
        """
        rows = conn.execute(query,()).fetchall()
        for row in rows:
            alerts.append({
                "serial": row[0],
                "model": row[1],
                "type": "test",
                "severity": "error",
                "message": f"Test failed",
                "timestamp": row[3]
            })

    conn.close()

    # Sort by severity and limit
    severity_order = {"critical": 0, "error": 1, "warning": 2}
    alerts.sort(key=lambda x: (severity_order.get(x["severity"], 99), x.get("timestamp", "")))

    return alerts[:limit]


# ============================================================================
# Test Endpoints
# ============================================================================

@app.get("/tests/running")
def get_running_tests():
    """Get currently running tests."""
    conn = get_db()

    query = """
        SELECT t.*, d.model, d.vendor
        FROM tests t
        JOIN disks d ON d.serial = t.serial
        WHERE t.finished IS NULL
        ORDER BY t.started ASC
    """
    rows = conn.execute(query,()).fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.get("/tests/history")
def get_test_history(
    serial: Optional[str] = None,
    result: Optional[str] = None,
    limit: int = 100
):
    """Get test history with optional filtering."""
    conn = get_db()

    query = """
        SELECT t.*, d.model, d.vendor
        FROM tests t
        JOIN disks d ON d.serial = t.serial
        WHERE 1=1
    """
    params = []

    if serial:
        query += " AND t.serial = ?"
        params.append(serial)

    if result:
        query += " AND t.result = ?"
        params.append(result)

    query += " ORDER BY t.started DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.get("/tests/summary")
def get_tests_summary():
    """Get test statistics summary."""
    conn = get_db()

    # Total tests
    total_tests = conn.execute("SELECT COUNT(*) FROM tests").fetchone()[0]

    # Tests by result
    result_counts = conn.execute("""
        SELECT result, COUNT(*) as count
        FROM tests
        WHERE result IS NOT NULL
        GROUP BY result
    """).fetchall()

    # Tests in last 24 hours
    recent_tests = conn.execute("""
        SELECT COUNT(*) FROM tests
        WHERE started >= datetime('now', '-1 day')
    """).fetchone()[0]

    # Currently running
    running = conn.execute("""
        SELECT COUNT(*) FROM tests
        WHERE finished IS NULL
    """).fetchone()[0]

    # Average test duration (for completed tests)
    avg_duration = conn.execute("""
        SELECT AVG(JULIANDAY(finished) - JULIANDAY(started)) * 86400
        FROM tests
        WHERE finished IS NOT NULL AND started IS NOT NULL
    """).fetchone()[0]

    conn.close()

    return {
        "total_tests": total_tests,
        "running_tests": running,
        "recent_tests_24h": recent_tests,
        "avg_duration_seconds": round(avg_duration, 1) if avg_duration else None,
        "result_breakdown": {row[0]: row[1] for row in result_counts}
    }


# ============================================================================
# Search/Filter Endpoints
# ============================================================================

@app.get("/search/disks")
def search_disks(
    q: str,
    limit: int = 50
):
    """
    Search disks by serial, model, or vendor.

    Query params:
    - q: Search query string
    - limit: Max results (default: 50)
    """
    conn = get_db()

    pattern = f"%{q}%"
    query = """
        SELECT * FROM disks
        WHERE serial LIKE ?
           OR model LIKE ?
           OR vendor LIKE ?
           OR batch LIKE ?
        LIMIT ?
    """
    rows = conn.execute(query, (pattern, pattern, pattern, pattern, limit)).fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.get("/filter/disks")
def filter_disks(
    vendor: Optional[str] = None,
    model: Optional[str] = None,
    status: Optional[str] = None,
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    interface: Optional[str] = None
):
    """Filter disks by various criteria."""
    conn = get_db()

    query = "SELECT * FROM disks WHERE 1=1"
    params = []

    if vendor:
        query += " AND vendor = ?"
        params.append(vendor)

    if model:
        query += " AND model = ?"
        params.append(model)

    if status:
        query += " AND status = ?"
        params.append(status)

    if min_score is not None:
        query += " AND reliability_score >= ?"
        params.append(min_score)

    if max_score is not None:
        query += " AND reliability_score <= ?"
        params.append(max_score)

    if interface:
        query += " AND interface = ?"
        params.append(interface)

    query += " ORDER BY serial ASC"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    return [dict(row) for row in rows]


# ============================================================================
# Metadata/Utility Endpoints
# ============================================================================

@app.get("/metadata/vendors")
def get_vendors():
    """Get list of all unique vendors."""
    conn = get_db()
    rows = conn.execute("SELECT DISTINCT vendor FROM disks WHERE vendor IS NOT NULL ORDER BY vendor").fetchall()
    conn.close()
    return [row[0] for row in rows]


@app.get("/metadata/models")
def get_models():
    """Get list of all unique models."""
    conn = get_db()
    rows = conn.execute("SELECT DISTINCT model FROM disks WHERE model IS NOT NULL ORDER BY model").fetchall()
    conn.close()
    return [row[0] for row in rows]


@app.get("/metadata/interfaces")
def get_interfaces():
    """Get list of all unique interfaces."""
    conn = get_db()
    rows = conn.execute("SELECT DISTINCT interface FROM disks WHERE interface IS NOT NULL ORDER BY interface").fetchall()
    conn.close()
    return [row[0] for row in rows]


@app.get("/metadata/batches")
def get_batches():
    """Get list of all unique batches."""
    conn = get_db()
    rows = conn.execute("SELECT DISTINCT batch FROM disks WHERE batch IS NOT NULL ORDER BY batch DESC").fetchall()
    conn.close()
    return [row[0] for row in rows]


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "disk-reliability-lab-api"}


@app.get("/system/available-disks")
def get_available_disks():
    """Get list of available disk devices for testing."""
    import subprocess
    import os
    import re

    try:
        # Get list of block devices
        result = subprocess.run(
            ['lsblk', '-d', '-n', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT'],
            capture_output=True,
            text=True
        )

        disks = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue

            parts = line.split()
            if len(parts) < 3:
                continue

            name = parts[0]
            size = parts[1] if len(parts) > 1 else ''
            dtype = parts[2] if len(parts) > 2 else ''
            mountpoint = parts[3] if len(parts) > 3 else ''

            # Skip loopback, raid, etc. - only physical disks
            if dtype not in ['disk']:
                continue

            # Skip if mounted (likely in use)
            if mountpoint:
                continue

            # Check if device exists
            device_path = f"/dev/{name}"
            if not os.path.exists(device_path):
                continue

            disks.append({
                "name": name,
                "device": device_path,
                "size": size,
                "type": dtype
            })

        return {"disks": disks}
    except Exception as e:
        return {"disks": [], "error": str(e)}


@app.post("/tests/start")
def start_test(request):
    """Start a burn-in test on a device."""
    import subprocess
    import json

    try:
        # Parse request body
        body = json.loads(request.body.decode())
        device = body.get('device')

        if not device:
            raise HTTPException(status_code=400, detail="Device is required")

        # Validate device exists
        import os
        if not os.path.exists(device):
            raise HTTPException(status_code=404, detail=f"Device not found: {device}")

        # Get device info for serial
        try:
            serial_result = subprocess.run(
                ['smartctl', '-i', device],
                capture_output=True,
                text=True,
                timeout=30
            )
            serial = None
            for line in serial_result.stdout.split('\n'):
                if 'Serial Number:' in line or 'Serial number:' in line:
                    serial = line.split(':', 1)[1].strip()
                    break
        except:
            serial = os.path.basename(device)

        # Create test record
        conn = get_db()
        conn.execute("""
            INSERT INTO tests (serial, device, started, result)
            VALUES (?, ?, datetime('now'), 'running')
        """, (serial, device))
        conn.commit()
        conn.close()

        return {
            "status": "started",
            "device": device,
            "serial": serial,
            "message": f"Test started. Run: sudo ./burnin.sh {device}"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
