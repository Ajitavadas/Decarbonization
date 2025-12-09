# 🌍 Decarbonization Platform

A complete carbon accounting platform with AI-powered insights, real-time tracking, and professional reporting capabilities.

## 🚀 Quick Start with Docker

### Prerequisites
- Docker Desktop or Docker Engine with Docker Compose
- Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### Setup & Run

1. **Clone and configure**:
   ```bash
   cd Decarbonization
   cp .env.example .env
   ```

2. **Edit `.env` file** and add your Gemini API key:
   ```bash
   GEMINI_API_KEY=your-actual-api-key-here
   ```

3. **Start all services**:
   ```bash
   docker compose up -d
   ```

4. **Access the platform**:
   - **Dashboard**: http://localhost:3000
   - **Backend API**: http://localhost:8000
   - **API Docs**: http://localhost:8000/docs

### First Time Setup

1. Open http://localhost:3000
2. Click "Register" on the login screen
3. Create your account:
   - Email: your@email.com
   - Username: testuser
   - Password: (secure password)
   - Organization: Your Company Name
4. Login and start tracking emissions!

## 📦 Services

The platform runs 4 Docker containers:

| Service | Container | Port | Purpose |
|---------|-----------|------|---------|
| Frontend | `decarb_frontend` | 3000 | React dashboard UI |
| Backend API | `decarb_api` | 8000 | FastAPI application |
| Database | `decarb_postgres` | 5432 | TimescaleDB (PostgreSQL) |
| Cache | `decarb_redis` | 6379 | Redis for sessions |

## 🎯 Features

### Carbon Tracking
- ✅ Real-time emissions dashboard
- ✅ Scope 1, 2, 3 breakdown
- ✅ Historical trend analysis
- ✅ CSV bulk import
- ✅ Automated calculations

### AI-Powered
- ✅ Natural language copilot
- ✅ Automatic scope classification (80%+ accuracy)
- ✅ Anomaly detection (90%+ detection rate)
- ✅ Reduction recommendations
- ✅ Emissions forecasting

### Reporting
- ✅ PDF report generation
- ✅ GHG Protocol compliant
- ✅ Audit trail
- ✅ Multi-organization support

## 🔧 Management Commands

```bash
# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f api
docker compose logs -f frontend

# Check service status
docker compose ps

# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes all data)
docker compose down -v

# Rebuild after code changes
docker compose up -d --build

# Access database
docker compose exec postgres psql -U decarb_user -d decarb_db

# Access API shell
docker compose exec api python
```

## 📊 Project Structure

```
Decarbonization/
├── docker-compose.yml          # Main orchestration file
├── .env.example               # Environment template
├── decarbonization-backend/   # FastAPI backend
│   ├── app/                   # Application code
│   ├── Dockerfile            # Backend container
│   └── requirements.txt      # Python dependencies
└── decarbonization-frontend/  # Dashboard UI
    ├── index.html            # Main page
    ├── css/                  # Styles
    ├── js/                   # JavaScript
    ├── Dockerfile           # Frontend container
    └── nginx.conf           # Web server config
```

## 🔒 Security Notes

**Development**: The default configuration is suitable for development.

**Production**: Update these before deploying:
- Change `SECRET_KEY` to a strong random value
- Use strong database passwords
- Enable HTTPS
- Set proper CORS origins
- Use environment-specific `.env` files
- Don't commit `.env` to version control

## 🐛 Troubleshooting

### Services won't start
```bash
# Check if ports are in use
lsof -i :3000,8000,5432,6379

# View detailed logs
docker compose logs

# Restart services
docker compose restart
```

### Frontend can't connect to API
- Check that API is healthy: `curl http://localhost:8000/health`
- Verify CORS settings in backend
- Check browser console for errors

### Database errors
```bash
# Reset database (WARNING: deletes data)
docker compose down -v
docker compose up -d
```

### Missing API key
- Ensure `.env` file exists in Decarbonization directory
- Verify `GEMINI_API_KEY` is set correctly
- Don't use quotes around the key value

## 📚 Documentation

- **[Frontend Documentation](decarbonization-frontend/README.md)** - UI customization and development
- **[Backend Documentation](decarbonization-backend/README.md)** - API and services
- **[API Reference](http://localhost:8000/docs)** - Interactive API docs (when running)

## 🎓 Development

### Making Changes

1. **Frontend**: Edit files in `decarbonization-frontend/`, refresh browser
2. **Backend**: Edit files in `decarbonization-backend/`, API auto-reloads
3. **Rebuild**: Run `docker compose up -d --build` after major changes

### Adding Dependencies

**Backend**:
```bash
# Add to requirements.txt
docker compose up -d --build api
```

**Frontend**:
```bash
# Edit HTML to add new libraries from CDN
# Or modify Dockerfile to copy new files
docker compose up -d --build frontend
```

## 🌟 Next Steps

1. **Import Data**: Use CSV import to add emissions data
2. **Set Targets**: Create net-zero targets
3. **Generate Reports**: Export PDF reports
4. **Query AI Copilot**: Ask questions about your emissions
5. **Review Insights**: Check anomalies and recommendations


## 🤝 Support

For issues or questions:
1. Check logs: `docker compose logs`
2. Review API docs: http://localhost:8000/docs
3. Check frontend README for UI issues

