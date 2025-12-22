# Decarbonization Platform

An AI-powered carbon accounting and decarbonization strategy platform.

## Features
- **Universal Semantic Adapter**: Upload messy CSV/XLSX files; AI maps your headers and normalizes units.
- **AI Classification**: Automatic Scope 1, 2, 3 classification and Category assignment (using Groq/Gemini).
- **Hybrid Calculation Engine**: Precise CO2e calculations using local factors or Climatiq fallback.
- **Auditor Agent**: Automatic detection of data gaps and anomalies in your footprint.
- **Real-time Dashboard**: Interactive charts, recent activity feed, and facility-level breakdowns.

---

## 🚀 Quick Start (Docker)

Ensure you have [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed.

### 1. Configure Environment
Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

**Required Keys**:
- `GEMINI_API_KEY`: For AI Classification and Refinement.
- `GROQ_API_KEY`: (Optional) For high-speed fallback classification.
- `CLIMATIQ_API_KEY`: (Optional) For specialized emission factor lookups.

### 2. Launch Platform
```bash
docker-compose up --build
```
This starts:
- **Backend API** (FastAPI) on `http://localhost:8000`
- **Frontend** (Next.js) on `http://localhost:3000`
- **PostgreSQL** (TimescaleDB)
- **Redis** (Caching/Import state)

### 3. Initialize Database
Once the services are running, initialize the schema:
```bash
docker-compose exec backend python scripts/db_init.py
```

---

## 📊 Using the Platform

### CSV/XLSX Upload
1. Click the **Upload CSV** button in the dashboard header.
2. Select your activity data file (Energy bills, logistics logs, etc.).
3. The platform will:
   - Identify column headers semantically.
   - Refine data (Unit normalization, date parsing).
   - Classify Scope and Category via AI.
   - Calculate emissions (kgCO2e).
4. Results appear immediately in the **Metric Cards** and **Recent Activity** feed.

### Data Auditor
The dashboard's **Data Quality Gaps** section highlights missing submissions or inconsistent reporting detected by the built-in Auditor Agent.

---

## 🛠 Tech Stack
- **Frontend**: Next.js 15, React 19, TailwindCSS, Lucide Icons, Recharts.
- **Backend**: FastAPI, SQLAlchemy (PostgreSQL/TimescaleDB), Redis.
- **AI**: Google Gemini (1.5 Flash), Groq (Llama 3), Pydantic for schema validation.
- **Infrastructure**: Docker Compose, Healthchecks, Automated Migrations.
