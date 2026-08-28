# FloatChat Project Brief

## Project
FloatChat is an ocean intelligence dashboard created by Team HEXAHACK. It helps users explore ARGO-style ocean observations through interactive maps, depth profiles, natural-language queries, guided filters, and beginner explanations.

## Team
- Muvazulla Shaik
- Sanjitha Rokkam
- Pallavi
- Jai Vardhan
- Subramayanam
- Sai Kumar

## Technology
- Python
- Streamlit
- Pandas
- NumPy
- Plotly
- Xarray
- NetCDF support
- Optional PostgreSQL/PostGIS
- Optional OpenAI query planning
- RAG and MCP extension scaffolding

## Main Files
- `app.py`: application entry point.
- `app/streamlit_app.py`: Streamlit UI, navigation, pages, chat, field guide, team page, demo walkthrough, responsive styling, saved queries, and exports.
- `app/query_engine.py`: converts natural-language questions into structured plans and filters data.
- `app/visualization.py`: creates maps, depth profiles, comparative profiles, and float trajectories.
- `ingestion/demo_data.py`: generates reproducible synthetic ARGO-style data.
- `ingestion/netcdf_ingest.py`: parses uploaded ARGO NetCDF files.
- `database/init.sql`: PostgreSQL/PostGIS schema prepared for future integration.
- `rag/`: RAG scaffolding.
- `mcp_server/`: MCP server scaffolding.
- `Run_FloatChat.bat`: Windows one-click launcher.

## Working Features
- Ocean Command Center with fleet metrics, regional coverage, readiness, and oxygen alerts.
- AI Ocean Chat with natural-language mode, guided query builder, query plans, recent history, saved queries, and CSV results.
- Interactive ARGO map with region, status, depth, date, and parameter-color filters.
- Float Explorer with metadata, profiles, oxygen data, salinity, and trajectory.
- Ocean Profile Lab with parameter and region comparisons.
- Data Explorer with sorting, filtering, and CSV export.
- NetCDF upload and parser warnings.
- Beginner Field Guide explaining ARGO, ocean variables, charts, alerts, terminology, and limitations.
- Team HEXAHACK section and Demo Walkthrough section.

## Current Limitations
The default application uses reproducible synthetic data. The database, RAG, MCP, authentication, and live ARGO API connections are prepared extension points but are not connected to production services yet.

## Run Locally
Double-click `Run_FloatChat.bat`, or run:

```powershell
cd e:\FloatChat
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Then open `http://127.0.0.1:8502`.

## Prompt for ChatGPT
Explain this FloatChat project as a software mentor. Cover the architecture, data flow, Streamlit navigation, AI query engine, Plotly visualizations, synthetic ARGO data, NetCDF ingestion, current limitations, and a roadmap to production. Explain difficult concepts for a beginner and include likely viva/interview questions with answers.
