"""Read-only metrics API backed by PostgreSQL."""
from fastapi import FastAPI, HTTPException

from assembly_line.db import connect

app = FastAPI(title="Assembly Line Metrics API", version="0.1.0")


@app.get("/health")
def health():
    try:
        with connect() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable") from exc


@app.get("/metrics/summary")
def summary():
    with connect() as conn, conn.cursor() as cur:
        cur.execute("""SELECT count(*) AS station_events,
            count(DISTINCT vehicle_id) AS vehicles_processed,
            round(avg(cycle_time_minutes)::numeric, 2) AS avg_cycle_minutes,
            round(100.0 * count(*) FILTER (WHERE status='complete') / NULLIF(count(*),0), 2) AS first_pass_yield_pct
            FROM fact_station_event""")
        result = cur.fetchone()
    return dict(result)


@app.get("/metrics/stations")
def stations():
    with connect() as conn, conn.cursor() as cur:
        cur.execute("""SELECT s.station_id, count(*) AS events,
            round(avg(f.cycle_time_minutes)::numeric,2) AS avg_cycle_minutes,
            count(*) FILTER (WHERE f.status='rework') AS rework_events
            FROM fact_station_event f JOIN dim_station s USING(station_id)
            GROUP BY s.station_id ORDER BY avg(f.cycle_time_minutes) DESC""")
        return [dict(row) for row in cur.fetchall()]
