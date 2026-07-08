# Decarbonization Platform

AI-Powered Carbon Accounting and Decarbonization Platform built on the [Climatiq API](https://www.climatiq.io/).

## Features

- **Climatiq-powered emission estimates** — CSV upload → AI classification → batch Climatiq API calls
- **AI Copilot** — natural-language queries over your emission data (Groq/Mistral/Gemini)
- **Dashboard** — scope 1/2/3 breakdowns, trend charts, category analysis
- **Anomaly detection** — automatic flagging of unusual emission spikes
- **Reporting** — export to PDF, Word, Excel
- **Reduction targets** — set baselines, track progress against goals
- **Multi-tenant architecture** — organization isolation with JWT auth

## Architecture

```
frontend/          Next.js 15 · React 19 · Tailwind 4 · shadcn/ui · Recharts
backend/           FastAPI · SQLAlchemy · Pydantic · Climatiq SDK
  app/api/         12 REST endpoints (auth, upload, activities, reports, copilot, ...)
  app/services/    AI classifier, copilot, anomaly detector, report generator, ...
  app/integration/ Climatiq client, schemas, batch processor
  app/models/      14 SQLAlchemy models
tests/             E2E and integration tests
docs/              Platform docs, tech specs, user guide
```

## Quick Start

### Prerequisites
- Python 3.11+ with [`uv`](https://docs.astral.sh/uv/)
- Node.js 18+

### Setup

```bash
# Backend
cd backend
cp .env.example .env      # Add your API keys
uv sync                   # Install dependencies
uv run alembic upgrade head
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Or use the one-command launcher: `./start.sh`

### Access Points
- **App**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

> See [docs/quickstart.md](docs/quickstart.md) for full setup details.

## Configuration

Copy `backend/.env.example` → `backend/.env` and set:

| Variable | Description |
|----------|-------------|
| `CLIMATIQ_API_KEY` | [Climatiq](https://www.climatiq.io/) API key |
| `MISTRAL_API_KEY` | [Mistral](https://console.mistral.ai/) AI key |
| `GEMINI_API_KEY` | [Google AI](https://aistudio.google.com/) key (optional) |
| `GROQ_API_KEY` | [Groq](https://console.groq.com/) key (Copilot) |
| `DATABASE_URL` | PostgreSQL or SQLite connection string |
| `SECRET_KEY` | JWT secret (min 32 chars) |

## Documentation

| Document | Description |
|----------|-------------|
| [Quick Start](docs/quickstart.md) | Setup and running instructions |
| [Platform Overview](docs/platform_overview.md) | Features and GTM summary |
| [Technical Specs](docs/technical_specifications.md) | Architecture deep-dive |
| [User Guide](docs/user_guide.md) | End-user instructions |
| [Test Guide](docs/test_guide.md) | E2E testing walkthrough |

## Testing

```bash
# Test data is in tests/data/test_data_20_rows.csv
# See docs/test_guide.md for the full E2E walkthrough
```

## License

MIT License