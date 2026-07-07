# Decarbonization Platform

AI-Powered Carbon Accounting and Decarbonization Platform for sustainable business practices.

## Features

- AI-powered carbon footprint calculation using Climatiq API
- Copilot functionality with LLMs (Mistral, Gemini, Groq)
- Dashboard with visualization of decarbonization metrics
- Activity tracking and reporting
- Anomaly detection for emissions data
- Multi-tenant architecture

## Architecture

### Backend (Python/FastAPI)
- RESTful API with FastAPI
- PostgreSQL database
- Redis caching
- Celery for background tasks
- AI/ML integration via Mistral, Gemini, Groq APIs

### Frontend (Next.js)
- React-based dashboard
- TypeScript and Tailwind CSS
- Real-time data visualization
- Responsive design for all devices

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker (optional for full deployment)

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

- `/api/v1/` - Main API endpoints
- `/docs` - Interactive API documentation (Swagger UI)
- `/redoc` - ReDoc documentation

## Configuration

Environment variables are used for configuration:

### Application Settings
- `APP_NAME` - Application name
- `DEBUG` - Debug mode flag
- `ENVIRONMENT` - Environment (development, staging, production)

### Climatiq API
- `CLIMATIQ_API_KEY` - Climatiq API authentication key
- `CLIMATIQ_BASE_URL` - Climatiq API base URL

### AI Services
- `MISTRAL_API_KEY` - Mistral AI API key
- `GEMINI_API_KEY` - Gemini AI API key
- `GROQ_API_KEY` - Groq AI API key

### Database
- `DATABASE_URL` - Database connection string (PostgreSQL or SQLite)

### Security
- `SECRET_KEY` - JWT secret key for authentication
- `ALGORITHM` - JWT algorithm
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time

## Development

The platform is structured as a monorepo with:
- `/backend` - Python FastAPI application
- `/frontend` - Next.js React application

## License

MIT License