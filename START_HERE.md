# 🚀 Quick Start - Decarbonization Platform

## One-Time Setup (Only First Time)

No external installations needed! Everything runs inside the uv environment.

### 1. Install Frontend Dependencies

```bash
cd backend
uv run frontend
```

This will:
- Download and install Node.js 20.11.0 in `.nodeenv/` (2-3 minutes)
- Install all frontend npm packages (2-3 minutes)

Press `Ctrl+C` once it says "Ready" and you see the frontend running.

---

## Running the Platform

Open **TWO terminals** in the project root:

### Terminal 1 - Backend

```bash
cd backend
uv run backend
```

✅ Backend will start at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Terminal 2 - Frontend

```bash
cd backend
uv run frontend
```

✅ Frontend will start at:
- **App**: http://localhost:3000

---

## That's It!

Both commands run entirely within the uv environment. No Docker, no external Node.js installation needed!

### Quick Test

Once both are running:

1. Visit http://localhost:8000/docs - See the API documentation
2. Visit http://localhost:3000 - Access the web app
3. Register a new account
4. Start tracking emissions!

---

## API Keys Already Configured ✅

- Climatiq API
- Mistral AI
- Gemini AI

All set in `backend/.env`

---

## Database

SQLite database at `backend/decarbonization.db` (created automatically)

---

## Stop Services

Press `Ctrl+C` in each terminal window.

---

## Troubleshooting

**Port already in use?**
```bash
# Kill existing processes
pkill -f uvicorn
pkill -f "npm run dev"
```

**Backend won't start?**
```bash
cd backend
uv sync
```

**Frontend won't start?**
```bash
# Delete and reinstall
rm -rf ../.nodeenv
rm -rf ../frontend/node_modules
uv run frontend
```
