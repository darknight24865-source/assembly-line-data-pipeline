# Dashboard guide

Open <http://localhost:8501> after the services are running and after loading data. The top cards show unique vehicles, station-event count, average cycle time, and first-pass yield. The bar chart orders average cycle time by station; the table also shows event and rework counts.

The dashboard calls `/metrics/summary` and `/metrics/stations` on the FastAPI service. If there are no database rows yet, load a dataset. If the API is unavailable, confirm the Compose services are healthy and check <http://localhost:8000/health>.

The chart flags candidates, not root causes. A useful next improvement is a date and shift filter so comparisons use the same production mix.
