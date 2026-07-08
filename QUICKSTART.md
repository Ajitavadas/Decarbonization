# Decarbonization Platform - Quick Start

## Prerequisites

- **Python 3.11+** with `uv` package manager
- **Node.js 18+** with `npm`
- **Git Bash** or any Unix-like shell (on Windows)

## Setup (First Time Only)

### 1. Backend Setup

The backend is already configured with:
- Python 3.11 virtual environment (via uv)
- SQLite database (no PostgreSQL needed for development)
- All dependencies installed
- Database migrations applied
- API keys configured

### 2. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

## Running the Platform

### Option 1: One-Command Start (Recommended)

```bash
./start.sh
```

This will start both backend and frontend automatically.

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## API Keys (Already Configured)

The following API keys are already set in `backend/.env`:

- **Climatiq API**: ``
- **Mistral API**: ``
- **Gemini API**: ``

## Database

- **Type**: SQLite (file-based, no installation needed)
- **Location**: `backend/decarbonization.db`
- **Reset Database**: Delete the file and run `uv run alembic upgrade head` from the backend directory

## Troubleshooting

### Port Already in Use

If you get "port already in use" errors:

```bash
# On Windows (Git Bash)
netstat -ano | findstr :8000
netstat -ano | findstr :3000
# Kill the process using the PID from above
taskkill //PID <PID> //F
```

### Backend Won't Start

```bash
cd backend
uv sync  # Reinstall dependencies
uv run alembic upgrade head  # Reapply migrations
```

### Frontend Won't Start

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Development

### Running Migrations

```bash
cd backend
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

### Adding Dependencies

**Backend:**
```bash
cd backend
# Edit pyproject.toml, then:
uv sync
```

**Frontend:**
```bash
cd frontend
npm install <package-name>
```

## Next Steps

1. Visit http://localhost:3000 to access the frontend
2. Register a new user account
3. Start entering emission activities
4. Explore the reports and reduction recommendations

## Support

For issues or questions, refer to the main README.md or create an issue in the repository.
