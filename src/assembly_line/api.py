"""Read-only metrics API backed by PostgreSQL."""
from datetime import date

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


def _filters(start_date: date | None, end_date: date | None, station_id: str | None, shift_name: str | None):
    clauses, params = [], []
    if start_date:
        clauses.append("f.start_ts >= %s::date")
        params.append(start_date)
    if end_date:
        clauses.append("f.start_ts < (%s::date + INTERVAL '1 day')")
        params.append(end_date)
    if station_id:
        clauses.append("f.station_id = %s")
        params.append(station_id)
    if shift_name:
        clauses.append("sh.shift_name = %s")
        params.append(shift_name)
    return (" WHERE " + " AND ".join(clauses) if clauses else ""), params


@app.get("/metrics/summary")
def summary(start_date: date | None = None, end_date: date | None = None,
            station_id: str | None = None, shift_name: str | None = None):
    where, params = _filters(start_date, end_date, station_id, shift_name)
    with connect() as conn, conn.cursor() as cur:
        cur.execute("""WITH filtered AS (
              SELECT f.vehicle_id, f.status, f.cycle_time_minutes
              FROM fact_station_event f JOIN dim_shift sh USING(shift_id)""" + where + """),
            per_vehicle AS (
              SELECT vehicle_id, bool_and(status='complete') AS first_pass
              FROM filtered GROUP BY vehicle_id
            ), totals AS (
              SELECT count(*) AS station_events, round(avg(cycle_time_minutes)::numeric, 2) AS avg_cycle_minutes
              FROM filtered
            )
            SELECT totals.station_events, (SELECT count(*) FROM per_vehicle) AS vehicles_processed,
              totals.avg_cycle_minutes,
              round(100.0 * (SELECT count(*) FROM per_vehicle WHERE first_pass) /
                    NULLIF((SELECT count(*) FROM per_vehicle),0), 2) AS first_pass_yield_pct
            FROM totals""", params)
        result = cur.fetchone()
    return dict(result)


@app.get("/metrics/stations")
def stations(start_date: date | None = None, end_date: date | None = None,
             station_id: str | None = None, shift_name: str | None = None):
    where, params = _filters(start_date, end_date, station_id, shift_name)
    with connect() as conn, conn.cursor() as cur:
        cur.execute("""SELECT f.station_id, count(*) AS events,
            round(avg(f.cycle_time_minutes)::numeric,2) AS avg_cycle_minutes,
            count(*) FILTER (WHERE f.status='rework') AS rework_events
            FROM fact_station_event f JOIN dim_station s USING(station_id)
            JOIN dim_shift sh USING(shift_id)""" + where +
            " GROUP BY f.station_id ORDER BY avg(f.cycle_time_minutes) DESC", params)
        return [dict(row) for row in cur.fetchall()]


@app.get("/dimensions")
def dimensions():
    """Return distinct filter choices for the dashboard."""
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT station_id FROM dim_station ORDER BY station_id")
        station_ids = [row["station_id"] for row in cur.fetchall()]
        cur.execute("SELECT shift_name FROM dim_shift ORDER BY shift_name")
        shifts = [row["shift_name"] for row in cur.fetchall()]
    return {"stations": station_ids, "shifts": shifts}
