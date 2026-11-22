# Architecture and data flow

```mermaid
flowchart LR
  A[Python generator] -->|raw CSV exports| B[data/raw]
  B --> C[Extract and clean with Pandas]
  C -->|clean CSV and metrics JSON| D[data/processed]
  D -->|transactional demo load| E[(PostgreSQL star schema)]
  E --> F[FastAPI read-only metrics endpoints]
  F --> G[Streamlit dashboard]
```

## Why these components?

- **Generator:** creates repeatable fake machine exports without external data access.
- **Pandas transform:** exposes the cleaning rules in a familiar table-oriented style.
- **PostgreSQL:** stores facts separately from descriptive dimensions and runs analytical SQL.
- **FastAPI:** keeps database access out of the dashboard and gives the UI a small API contract.
- **Streamlit:** provides a quick visual layer without needing a separate JavaScript frontend.

The current run is batch-oriented: generate, clean, load, then refresh the dashboard. The data is not streaming. `docker compose up` starts the database, API, and dashboard; the ETL is run from the host so the learner can inspect the raw and processed CSVs.
