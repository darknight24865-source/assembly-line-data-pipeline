"""Beginner-friendly, auto-refreshing Streamlit view of the API metrics."""
from datetime import date
import os

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Assembly Line", layout="wide")
st.title("🚗 Assembly Line Performance")
st.caption("Simulated production data · refreshes every 15 seconds")
api_url = os.getenv("API_URL", "http://localhost:8000")

try:
    dimensions_response = requests.get(f"{api_url}/dimensions", timeout=5)
    dimensions_response.raise_for_status()
    dimensions = dimensions_response.json()
except requests.RequestException as exc:
    st.error(f"Could not reach the metrics API: {exc}")
    st.stop()

st.sidebar.header("Filters")
station_options = ["All stations", *dimensions["stations"]]
shift_options = ["All shifts", *dimensions["shifts"]]
selected_station = st.sidebar.selectbox("Station", station_options)
selected_shift = st.sidebar.selectbox("Shift", shift_options)
use_dates = st.sidebar.checkbox("Filter by date")
filters = {}
if selected_station != "All stations":
    filters["station_id"] = selected_station
if selected_shift != "All shifts":
    filters["shift_name"] = selected_shift
if use_dates:
    start_date = st.sidebar.date_input("From", value=date(2026, 1, 1))
    end_date = st.sidebar.date_input("Through", value=date.today())
    if start_date > end_date:
        st.sidebar.error("The start date must be on or before the end date.")
        st.stop()
    filters["start_date"] = start_date.isoformat()
    filters["end_date"] = end_date.isoformat()


@st.fragment(run_every="15s")
def show_metrics(query_filters: dict):
    """A fragment refreshes metrics without resetting the user's filters."""
    try:
        summary_response = requests.get(f"{api_url}/metrics/summary", params=query_filters, timeout=5)
        summary_response.raise_for_status()
        stations_response = requests.get(f"{api_url}/metrics/stations", params=query_filters, timeout=5)
        stations_response.raise_for_status()
    except requests.RequestException as exc:
        st.error(f"Could not load current metrics: {exc}")
        return

    summary = summary_response.json()
    stations = stations_response.json()
    cols = st.columns(4)
    values = [
        ("Vehicles", summary.get("vehicles_processed", 0)),
        ("Station events", summary.get("station_events", 0)),
        ("Average cycle", f"{summary.get('avg_cycle_minutes') or 0} min"),
        ("First-pass yield", f"{summary.get('first_pass_yield_pct') or 0}%"),
    ]
    for col, (label, value) in zip(cols, values):
        col.metric(label, value)

    st.subheader("Station bottleneck view")
    station_frame = pd.DataFrame(stations)
    if station_frame.empty:
        st.info("No events match these filters. Generate, clean, and load a dataset to populate this view.")
    else:
        st.bar_chart(station_frame.set_index("station_id")["avg_cycle_minutes"])
        st.dataframe(station_frame, use_container_width=True, hide_index=True)
        st.caption("A longer average cycle is a bottleneck candidate. Check shift mix and downtime before drawing conclusions.")


show_metrics(filters)
