"""Beginner-friendly Streamlit view that reads from the FastAPI service."""
import os

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Assembly Line", layout="wide")
st.title("🚗 Assembly Line Performance")
st.caption("A simulated line: metrics update when the ETL loads a new export.")
api_url = os.getenv("API_URL", "http://localhost:8000")
try:
    summary = requests.get(f"{api_url}/metrics/summary", timeout=5).json()
    stations = requests.get(f"{api_url}/metrics/stations", timeout=5).json()
except requests.RequestException as exc:
    st.error(f"Could not reach the metrics API: {exc}")
    st.stop()

cols = st.columns(4)
labels = [("Vehicles", "vehicles_processed", ""), ("Station events", "station_events", ""),
          ("Average cycle", "avg_cycle_minutes", " min"), ("First-pass yield", "first_pass_yield_pct", "%")]
for col, (label, key, suffix) in zip(cols, labels):
    col.metric(label, f"{summary.get(key, 0)}{suffix}")

st.subheader("Station bottleneck view")
station_frame = pd.DataFrame(stations)
if station_frame.empty:
    st.info("No events yet. Generate, clean, and load a dataset to populate this view.")
else:
    st.bar_chart(station_frame.set_index("station_id")["avg_cycle_minutes"])
    st.dataframe(station_frame, use_container_width=True, hide_index=True)
    st.caption("A longer average cycle is a bottleneck candidate. Check shift mix and downtime before drawing conclusions.")
