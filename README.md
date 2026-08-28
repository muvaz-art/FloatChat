# 🌊 FloatChat – AI Ocean Intelligence Platform

FloatChat is an advanced conversational interface for exploring ARGO oceanographic data, combining real-time hydrographic visuals with natural language query capabilities.

---

## 🚀 Quickstart Guide (Windows + VS Code)

### 1. Create Python Virtual Environment
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Configure Environment
```powershell
Copy-Item .env.example .env
# Edit .env with your OpenAI API key and database connection values
```

### 4. Run the App
```powershell
streamlit run app.py
```

### One-click launch on Windows
Double-click **Run_FloatChat.bat** in the project folder. It starts the app and opens the dashboard automatically. The first launch creates the virtual environment and installs dependencies if required.

### 5. Optional Database Setup
```powershell
psql -U floatchat_user -d floatchat_db -f database/init.sql
```

## 🧩 Project Layout
- app/ – Streamlit interface and chart logic
- ingestion/ – demo and NetCDF ingest utilities
- database/ – SQL schema and connection helpers
- rag/ – retrieval and planner scaffolding
- mcp_server/ – Model Context Protocol endpoint
- tests/ – smoke tests for query parsing and safety checks

## ✅ Features
- Global ARGO float map
- Natural language query planner
- Depth-profile visualizations for temperature, salinity, oxygen, and chlorophyll
- NetCDF upload workflow for ARGO data
- PostgreSQL + PostGIS-ready schema
- Operational command center with fleet readiness, regional coverage, and low-oxygen alerts
- AI chat with natural-language, guided query-builder, and query-explanation modes
- Beginner field guide covering ARGO floats, variables, charts, and demo/live boundaries
- Team and project principles section for science, engineering, AI, and product contributors
- Guided Demo Walkthrough with presentation steps, snapshot export, and ocean-observing references

## Team
FloatChat is developed by **HEXAHACK**: Muvazulla Shaik, Sanjitha Rokkam, Pallavi, Jai Vardhan, Subramayanam, and Sai Kumar.

## Current Runtime Status
- **Working now:** reproducible ARGO-like demo data, maps, depth profiles, float explorer, query planner, filtered CSV export, and NetCDF upload parsing.
- **Ready for integration:** PostgreSQL/PostGIS schema, RAG modules, and MCP tools.
- **Demo limitation:** the default dashboard uses synthetic data until a live ARGO or database connector is configured.
