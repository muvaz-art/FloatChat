# FloatChat

FloatChat is an AI-oriented conversational interface for exploring ARGO oceanographic observations. Team HEXAHACK built it as an Indian Ocean proof of concept with a reproducible demo mode and explicit extension points for live data and production storage.

## What It Contains

- Streamlit command center with fleet readiness, regional coverage, alerts, maps, profiles, and tables.
- AI Ocean Chat with natural-language parsing, guided query building, history, saved queries, explainability, RAG context, and CSV export.
- Interactive ARGO map with region, status, depth, date, and variable-color filters.
- Float Explorer with metadata, profiles, and trajectory.
- Profile Lab with multi-float comparison and depth-time heatmaps.
- Data Explorer with sorting, filtering, quality information, and downloads.
- NetCDF normalization for common ARGO core and optional BGC variables.
- Persistent dependency-light local semantic store for ARGO/schema documentation.
- Validated `QueryPlan` and parameterized read-only SQL builder.
- Controlled MCP tools that reuse the safe query service.

## Architecture

```text
ARGO NetCDF -> xarray/netCDF4 -> normalized DataFrames -> Parquet or PostgreSQL/PostGIS
                                                        |
Question -> local RAG documentation -> LLM or deterministic parser -> QueryPlan
                                                        |
                         Pandas demo executor or parameterized PostgreSQL executor
                                                        |
                         MCP read-only tools / Streamlit -> Plotly charts and tables
```

The LLM may interpret a question, but application code validates the plan and builds the query. Raw LLM SQL is never executed.

## Modes and Status

- **Complete locally:** demo data, Streamlit pages, Plotly maps/profiles/trajectories/depth-time charts, NetCDF normalization, Parquet helpers, local RAG retrieval, QueryPlan validation, SQL builder, and MCP tool boundaries.
- **Partially implemented:** PostgreSQL execution is available through `database/service.py` but requires a configured PostgreSQL/PostGIS instance and loaded tables.
- **Optional:** OpenAI planning. Without an API key, the deterministic parser works offline.
- **Future integration:** live ARGO API synchronization, full database ingestion command, authentication, production vector database, and deployment automation.

The default app uses synthetic ARGO-like data and labels the UI as demo mode. It does not claim synthetic observations are real measurements.

## Project Layout

- `app.py` - Streamlit entry point.
- `app/streamlit_app.py` - UI, navigation, workflows, and explanations.
- `app/query_plan.py` - validated Pydantic query contract.
- `app/query_engine.py` - deterministic parsing and demo Pandas execution.
- `app/visualization.py` - Plotly visualization functions.
- `database/queries.py` - allowlisted, parameterized SELECT builder.
- `database/service.py` - read-only PostgreSQL executor.
- `database/init.sql` - PostGIS-ready schema and indexes.
- `ingestion/netcdf_ingest.py` - common ARGO NetCDF normalization.
- `ingestion/parquet.py` - optional Parquet read/write helpers.
- `scripts/ingest_argo.py` - command-line NetCDF-to-PostgreSQL/PostGIS ingestion.
- `rag/` - documents, local vector store, retrieval, and RAG pipeline.
- `mcp_server/server.py` - controlled read-only MCP tools.
- `tests/` - parser, execution, SQL-safety, and RAG tests.
- `Run_FloatChat.bat` - Windows one-click launcher.

## Windows Setup

```powershell
cd e:\FloatChat
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py --server.port 8502
```

Or double-click `Run_FloatChat.bat`. It creates the environment and installs dependencies on first use.

## Configuration

Set these in `.env` as needed:

```text
DATA_MODE=demo
VECTOR_STORE_PATH=data/vector_store.json
EMBEDDING_MODEL=local-hash
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=floatchat_db
POSTGRES_USER=floatchat_user
POSTGRES_PASSWORD=
```

Demo mode works without PostgreSQL or an OpenAI key. Run `database/init.sql` in a PostgreSQL database with PostGIS enabled before using the database executor.

## Real ARGO Ingestion

Place one `.nc` file or a directory of `.nc` files outside Git, configure the PostgreSQL values in `.env`, initialize the schema, and run:

```powershell
psql -U floatchat_user -d floatchat_db -f database/init.sql
.\.venv\Scripts\python.exe scripts\ingest_argo.py path\to\argo-files
```

The command reports each file, warnings, float/profile/measurement totals, and failures. Missing optional BGC variables are preserved as empty columns rather than fabricated. Common ARGO QC fields are retained when present.

## Database Mode

Set `DATA_MODE=postgres` to make the Streamlit runtime attempt PostgreSQL/PostGIS. If the connection or tables are unavailable, the dashboard reports the error and uses the demo fallback rather than crashing. Set `DATA_MODE=demo` to force offline reproducible data.

## Remote ARGO Mode

FloatChat can load a remote ERDDAP CSV endpoint through the same normalized data model. Set `DATA_MODE=erddap` and provide `ERDDAP_URL` in `.env`. The endpoint must include float/platform ID, timestamp, latitude, longitude, depth or pressure, and at least one measured variable. Missing optional BGC fields remain absent; they are never fabricated.

### Fast local PostGIS setup

With Docker Desktop installed:

```powershell
docker compose up -d postgres
Copy-Item .env.example .env
# Keep the default POSTGRES_* values for the included container.
.\.venv\Scripts\python.exe scripts\init_database.py
.\.venv\Scripts\python.exe scripts\ingest_argo.py path\to\argo-files
```

Then set `DATA_MODE=postgres` in `.env` and restart Streamlit. Check the System / Data Sources page for connection and dataset status. Stop the database with `docker compose down`; keep the volume with `docker compose down` or remove it with `docker compose down -v`.

## Container Deployment

For a repeatable container deployment:

```powershell
docker compose up --build
```

Open `http://localhost:8501`. The compose app starts in demo mode and includes PostGIS for later database-mode use. The Streamlit health endpoint is `http://localhost:8501/_stcore/health`.

Run the local health check with:

```powershell
.\.venv\Scripts\python.exe scripts\healthcheck.py
```

## RAG and MCP

The local RAG pipeline persists documentation embeddings in `data/vector_store.json`; it stores schema and oceanographic documents, not raw measurement rows. When the optional `faiss-cpu` package is available, it uses a persisted FAISS inner-product index at `data/vector_store.faiss`; otherwise it uses the same stable local embeddings with a NumPy search fallback. MCP tools use the shared service factory and expose validated read-only operations. PostgreSQL-backed MCP execution follows the configured `DATA_MODE`; demo mode remains available offline.

Install FAISS where a compatible wheel is available:

```powershell
pip install faiss-cpu
```

## Example Questions

- Show me salinity profiles near the equator in March 2023.
- Compare BGC parameters in the Arabian Sea for the last 6 months.
- What are the nearest ARGO floats to 15 N, 72 E?
- Show oxygen profiles deeper than 500m.
- Find active floats near 15, 75.
- Show temperature profiles in the Bay of Bengal.
- Compare salinity profiles in the Arabian Sea.
- Show a depth-time heatmap for oxygen.
- Find inactive floats in the Global Ocean.
- Show chlorophyll observations near the equator.

## Testing

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The tests do not require paid APIs or a live database. They cover demo generation, parsing, required query patterns, validation, SQL safety, and local RAG retrieval.

## Team HEXAHACK

Muvazulla Shaik, Sanjitha Rokkam, Pallavi, Jai Vardhan, Subramayanam, and Sai Kumar.

## Limitations and Next Steps

A production release should add a live ARGO/Copernicus or ERDDAP connector, a controlled database ingestion job, quality flags from source files, a production embedding model/vector database, authentication, monitoring, and deployment configuration. These should be added without replacing the offline demo fallback.
