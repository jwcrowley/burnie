#!/usr/bin/env python3
"""
Disk Reliability Lab - Web Dashboard
FastAPI + HTMX web interface for monitoring disk reliability testing
"""

import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import httpx

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8080"))
REFRESH_INTERVAL = int(os.getenv("DASHBOARD_REFRESH_INTERVAL", "30"))
SECRET_KEY = os.getenv("SECRET_KEY", "disk-reliability-lab-secret-key-change-in-production")

app = FastAPI(title="Disk Reliability Lab Dashboard")

# Add session middleware for potential future auth
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")


async def fetch_api(endpoint: str):
    """Fetch data from the API server."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}{endpoint}")
        return response.json()


def get_refresh_interval():
    """Get the configured refresh interval in seconds."""
    return REFRESH_INTERVAL


# ============================================================================
# Template Routes
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Redirect to main dashboard."""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "refresh_interval": get_refresh_interval(),
            "current_year": datetime.now().year
        }
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard overview."""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "refresh_interval": get_refresh_interval(),
            "current_year": datetime.now().year
        }
    )


@app.get("/disks", response_class=HTMLResponse)
async def disks(request: Request):
    """Disk list view."""
    return templates.TemplateResponse(
        "disks.html",
        {
            "request": request,
            "refresh_interval": get_refresh_interval(),
            "current_year": datetime.now().year
        }
    )


@app.get("/disks/{serial}", response_class=HTMLResponse)
async def disk_detail(request: Request, serial: str):
    """Individual disk detail view."""
    # Fetch disk data
    disk_data = await fetch_api(f"/disks/{serial}")

    return templates.TemplateResponse(
        "disk_detail.html",
        {
            "request": request,
            "serial": serial,
            "disk": disk_data,
            "refresh_interval": get_refresh_interval(),
            "current_year": datetime.now().year
        }
    )


@app.get("/analytics", response_class=HTMLResponse)
async def analytics(request: Request):
    """Analytics and charts view."""
    return templates.TemplateResponse(
        "analytics.html",
        {
            "request": request,
            "refresh_interval": get_refresh_interval(),
            "current_year": datetime.now().year
        }
    )


@app.get("/alerts", response_class=HTMLResponse)
async def alerts(request: Request):
    """Alerts center view."""
    return templates.TemplateResponse(
        "alerts.html",
        {
            "request": request,
            "refresh_interval": get_refresh_interval(),
            "current_year": datetime.now().year
        }
    )


@app.get("/tests", response_class=HTMLResponse)
async def tests(request: Request):
    """Test queue and history view."""
    return templates.TemplateResponse(
        "tests.html",
        {
            "request": request,
            "refresh_interval": get_refresh_interval(),
            "current_year": datetime.now().year
        }
    )


# ============================================================================
# HTMX Data Endpoints (for partial page updates)
# ============================================================================

@app.get("/partials/stats/overview", response_class=HTMLResponse)
async def partial_stats_overview(request: Request):
    """Partial update for dashboard stats cards."""
    stats = await fetch_api("/stats/overview")
    return templates.TemplateResponse(
        "partials/stats_cards.html",
        {"request": request, "stats": stats}
    )


@app.get("/partials/alerts/summary", response_class=HTMLResponse)
async def partial_alerts_summary(request: Request, limit: int = 5):
    """Partial update for alerts summary."""
    alerts = await fetch_api(f"/alerts?limit={limit}")
    return templates.TemplateResponse(
        "partials/alerts_table.html",
        {"request": request, "alerts": alerts, "show_all": False}
    )


@app.get("/partials/disks/low-reliability", response_class=HTMLResponse)
async def partial_low_reliability(request: Request, threshold: int = 70, limit: int = 10):
    """Partial update for low reliability disks table."""
    disks = await fetch_api(f"/filter/disks?max_score={threshold}&limit={limit}")
    return templates.TemplateResponse(
        "partials/low_reliability_table.html",
        {"request": request, "disks": disks, "threshold": threshold}
    )


@app.get("/partials/tests/running", response_class=HTMLResponse)
async def partial_running_tests(request: Request):
    """Partial update for running tests."""
    tests = await fetch_api("/tests/running")
    return templates.TemplateResponse(
        "partials/running_tests.html",
        {"request": request, "tests": tests}
    )


@app.get("/partials/disks/table", response_class=HTMLResponse)
async def partial_disks_table(
    request: Request,
    limit: Optional[int] = None,
    offset: int = 0,
    sort_by: str = "serial",
    sort_order: str = "asc"
):
    """Partial update for disks table."""
    params = []
    if limit:
        params.append(f"limit={limit}")
    params.append(f"offset={offset}")
    params.append(f"sort_by={sort_by}")
    params.append(f"sort_order={sort_order}")

    query_string = "&".join(params)
    disks = await fetch_api(f"/disks?{query_string}")

    return templates.TemplateResponse(
        "partials/disks_table.html",
        {
            "request": request,
            "disks": disks,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
    )


@app.get("/partials/alerts/table", response_class=HTMLResponse)
async def partial_alerts_table(
    request: Request,
    alert_type: Optional[str] = None,
    limit: int = 100
):
    """Partial update for alerts table."""
    query_params = f"alert_type={alert_type}&limit={limit}" if alert_type else f"limit={limit}"
    alerts = await fetch_api(f"/alerts?{query_params}")

    return templates.TemplateResponse(
        "partials/alerts_table.html",
        {"request": request, "alerts": alerts, "show_all": True}
    )


@app.get("/partials/tests/history", response_class=HTMLResponse)
async def partial_tests_history(
    request: Request,
    serial: Optional[str] = None,
    result: Optional[str] = None,
    limit: int = 50
):
    """Partial update for test history table."""
    params = []
    if serial:
        params.append(f"serial={serial}")
    if result:
        params.append(f"result={result}")
    params.append(f"limit={limit}")

    query_string = "&".join(params)
    tests = await fetch_api(f"/tests/history?{query_string}")

    return templates.TemplateResponse(
        "partials/tests_history.html",
        {"request": request, "tests": tests}
    )


# ============================================================================
# SSE for Real-time Updates
# ============================================================================

from fastapi.responses import StreamingResponse
import asyncio
import json


@app.get("/events")
async def event_stream(request: Request):
    """Server-Sent Events endpoint for real-time updates."""

    async def event_generator():
        """Generate SSE events."""
        while True:
            try:
                # Get latest stats
                stats = await fetch_api("/stats/overview")
                data = f"data: {json.dumps({'type': 'stats', 'data': stats})}\n\n"
                yield data

                # Check for new alerts
                alerts = await fetch_api("/alerts?limit=5")
                data = f"data: {json.dumps({'type': 'alerts', 'data': alerts})}\n\n"
                yield data

                await asyncio.sleep(REFRESH_INTERVAL)
            except Exception as e:
                # Send error and continue
                error_data = json.dumps({'type': 'error', 'message': str(e)})
                yield f"data: {error_data}\n\n"
                await asyncio.sleep(5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "disk-reliability-lab-dashboard"}


if __name__ == "__main__":
    print(f"Starting Disk Reliability Lab Dashboard on port {DASHBOARD_PORT}")
    print(f"API server at: {API_BASE_URL}")
    print(f"Dashboard: http://localhost:{DASHBOARD_PORT}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DASHBOARD_PORT,
        log_level="info"
    )
