# 🌍 Decarbonization Platform

**AI-Powered Carbon Accounting and Decarbonization Platform**

A full-stack enterprise platform for tracking, analyzing, and reducing organizational carbon emissions. Built with FastAPI, Next.js, and PostgreSQL, featuring intelligent AI classification, real-time anomaly detection, and comprehensive PDF reporting.

---

## 🚀 Key Features

### 📊 **Carbon Emissions Management**
- **CSV Upload & Processing**: Bulk import activity data with automatic AI classification
- **Multi-Scope Tracking**: Complete GHG Protocol Scope 1, 2, and 3 emissions tracking
- **Real-time Calculations**: Climatiq API integration for accurate CO2e calculations
- **Interactive Dashboard**: Visual analytics with charts, trends, and scope breakdowns

### 🤖 **AI-Powered Intelligence**
- **Smart Classification**: Groq/Gemini AI for automatic scope and category assignment
- **Carbon Copilot**: Conversational AI assistant for emissions queries
- **Anomaly Detection**: AI-driven identification of data gaps and outliers
- **Strategy Generation**: AI-suggested reduction strategies based on your emissions profile

### 📈 **Reduction Targets & Tracking**
- **Target Setting**: Absolute and percentage-based reduction targets
- **Progress Monitoring**: Real-time tracking against milestones
- **Trajectory Analysis**: Predictive modeling for target achievement

### 📋 **Professional Reporting**
- **PDF Reports**: Beautifully formatted carbon footprint reports
- **Custom Reports**: Configurable tables and columns
- **Executive Summaries**: High-level insights for stakeholders

### 🔒 **Enterprise Security**
- **Multi-Organization Support**: Complete data isolation between organizations
- **Role-Based Access**: Secure authentication with JWT tokens
- **Project-Level Permissions**: Fine-grained access control

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                       │
│  Dashboard │ Projects │ Emissions │ Targets │ Anomalies │ Reports│
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend API (FastAPI)                       │
│  Auth │ Upload │ Activities │ Audit │ Targets │ Copilot │ Reports│
└─────────────────────────────────────────────────────────────────┘
         │                    │                         │
         ▼                    ▼                         ▼
┌─────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│  PostgreSQL │    │  Climatiq API    │    │  AI Services        │
│  Database   │    │  (Emissions)     │    │  (Groq/Gemini)      │
└─────────────┘    └──────────────────┘    └─────────────────────┘
         │
         ▼
┌─────────────┐
│   Redis     │
│   (Cache)   │
└─────────────┘
```

---

## 📦 Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS, Recharts |
| **Backend** | FastAPI, SQLAlchemy, Pydantic |
| **Database** | PostgreSQL 16 |
| **Cache** | Redis 7 |
| **AI Services** | Groq (Llama-3.3-70b), Google Gemini |
| **Emissions API** | Climatiq |
| **PDF Generation** | ReportLab, Matplotlib |
| **Containerization** | Docker, Docker Compose |

---

## 🛠️ Quick Start

### Prerequisites

- Docker & Docker Compose
- API Keys: Climatiq, Groq (or Gemini)

### 1. Clone the Repository

```bash
git clone https://github.com/Ajitavadas/Decarbonization.git
cd Decarbonization
```

### 2. Configure Environment

```bash
# Backend configuration
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your API keys:

```env
# Required
CLIMATIQ_API_KEY=your_climatiq_api_key
GROQ_API_KEY=your_groq_api_key

# Optional (fallback AI)
GEMINI_API_KEY=your_gemini_api_key

# Security
SECRET_KEY=your_secret_key_here
```

### 3. Start the Platform

```bash
docker compose up -d
```

### 4. Access the Application

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **Backend API** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |

---

## 📚 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get JWT token |
| GET | `/api/v1/auth/me` | Get current user info |

### Projects
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/projects/` | List all projects |
| POST | `/api/v1/projects/` | Create new project |
| GET | `/api/v1/projects/{id}` | Get project details |

### Activities & Emissions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/upload/csv` | Upload CSV for processing |
| GET | `/api/v1/activities/?project_id={id}` | List activities |
| GET | `/api/v1/activities/project/{id}/summary` | Get emissions summary |

### Carbon Auditor
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/audit/run` | Run audit analysis |
| GET | `/api/v1/audit/findings` | Get audit findings |
| PATCH | `/api/v1/audit/findings/{id}/resolve` | Resolve finding |

### Reduction Targets
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/targets/` | List reduction targets |
| POST | `/api/v1/targets/` | Create new target |
| POST | `/api/v1/targets/{id}/strategies/generate` | Generate AI strategies |

### Carbon Copilot
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/copilot/chat` | Chat with AI assistant |
| GET | `/api/v1/copilot/quick-stats` | Get quick statistics |

### Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/projects/{id}/report` | Generate PDF report |
| GET | `/api/v1/projects/{id}/report-summary` | Get report data |
| GET | `/api/v1/projects/{id}/report/available-columns` | Get custom report options |

---

## 📊 CSV Upload Format

Upload CSV files with the following columns:

| Column | Required | Description | Example |
|--------|----------|-------------|---------|
| `description` | ✅ | Activity description | "Office electricity usage" |
| `amount` | ✅ | Quantity value | 2500 |
| `unit` | ✅ | Unit of measure | "kWh", "km", "USD" |
| `category` | ❌ | Activity category | "Energy", "Travel" |
| `region` | ❌ | Geographic region | "US", "EU", "IN" |
| `activity_date` | ❌ | Date of activity | "2026-01-15" |

### Example CSV

```csv
description,amount,unit,category,region,activity_date
Office electricity usage,2500,kWh,Energy,US,2026-01-15
Business flight NYC to LA,5000,km,Travel,US,2026-01-10
Natural gas heating,150,therms,Energy,US,2026-01-20
Office supplies purchase,2500,USD,Procurement,US,2026-01-12
```

---

## 🧠 AI Classification

The platform uses a multi-tier AI classification strategy:

1. **Groq (Primary)**: Llama-3.3-70b for fast, structured classification
2. **Gemini (Fallback)**: Google's Gemini as reliable backup
3. **Heuristics (Final)**: Rule-based classification for edge cases

### Scope Assignment

| Scope | Description | Examples |
|-------|-------------|----------|
| **Scope 1** | Direct emissions | Fuel combustion, company vehicles |
| **Scope 2** | Purchased energy | Electricity, heating |
| **Scope 3** | Value chain | Business travel, procurement, waste |

---

## 🔧 Development

### Running Locally (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
docker compose exec backend pytest

# Report generation tests
docker compose exec backend pytest tests/test_report_generation.py -v
```

### Database Migrations

```bash
# Create migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker compose exec backend alembic upgrade head
```

---

## 📁 Project Structure

```
Decarbonization/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # API routes
│   │   ├── core/                # Config, security, auth
│   │   ├── crud/                # Database operations
│   │   ├── db/                  # Database session
│   │   ├── integration/         # Climatiq API client
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic
│   │   └── main.py              # FastAPI app
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js pages
│   │   ├── components/          # React components
│   │   ├── lib/                 # API client, utilities
│   │   └── types/               # TypeScript types
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🎯 Frontend Pages

| Page | Path | Description |
|------|------|-------------|
| Dashboard | `/` | Overview with metrics and charts |
| Projects | `/projects` | Manage projects |
| Upload | `/upload` | CSV file upload |
| Emissions | `/emissions` | View all emissions data |
| Scope Analysis | `/scope-analysis` | Detailed scope breakdown |
| Targets | `/targets` | Reduction targets & strategies |
| Anomalies | `/anomalies` | Audit findings & data quality |
| Reports | `/reports` | Generate PDF reports |

---

## 🔐 Environment Variables

### Backend (`backend/.env`)

```env
# Application
APP_NAME=Decarbonization Platform
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://carbon_user:carbon_password@postgres:5432/decarbonization_db

# Redis
REDIS_URL=redis://redis:6379/0

# Climatiq API
CLIMATIQ_API_KEY=your_climatiq_api_key

# AI Services (at least one required)
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key

# CORS
ALLOWED_ORIGINS=["http://localhost:3000"]
```

### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 📄 License

This project is licensed under the MIT License.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📬 Support

For questions and support, please open an issue on GitHub.
