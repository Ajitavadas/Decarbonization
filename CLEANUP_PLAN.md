# Codebase Cleanup Plan - Docker to UV Migration

## ✅ SAFE TO DELETE (No Impact)

### 1. Docker Files (6 files)
- ❌ `docker-compose.yml` - Root docker compose config
- ❌ `backend/Dockerfile` - Backend container image
- ❌ `frontend/Dockerfile` - Frontend container image
- ❌ `.dockerignore` - Root docker ignore
- ❌ `backend/.dockerignore` - Backend docker ignore (if exists)
- ❌ `frontend/.dockerignore` - Frontend docker ignore (if exists)

### 2. Old Dependency Files
- ❌ `backend/requirements.txt` - Replaced by pyproject.toml

### 3. Celery Files (No longer used)
- ❌ `backend/app/core/celery_app.py` - Celery configuration
- ✏️ `backend/app/tasks/batch_processing.py` - Convert tasks to regular functions
- ✏️ `backend/app/api/v1/endpoints/batch.py` - Remove Celery imports

### 4. Python Cache Files (~1551 items)
- ❌ All `__pycache__/` directories
- ❌ All `*.pyc` files

### 5. Old Migration Files (Already deleted but git tracked)
- ❌ `backend/alembic/versions/135bec871877_*.py`
- ❌ `backend/alembic/versions/bb59ec217272_*.py`

### 6. Temporary/Build Artifacts
- ❌ `frontend/.next/` - Next.js build cache (regenerated)
- ❌ `.nodeenv/src/` - Node source (keep Scripts)

## ⚠️ NEEDS REVIEW

### 1. Redundant Startup Scripts
Current scripts:
- ✅ `start.sh` - Bash script (KEEP - useful for Unix)
- ❓ `start.py` - Python script (REVIEW - redundant with uv run commands?)

Recommendation: Keep start.sh, delete start.py since we have simpler `uv run backend/frontend`

### 2. Documentation Files
- ✅ `QUICKSTART.md` - Quick setup guide
- ✅ `START_HERE.md` - Simplified startup
- ✅ `TEST_GUIDE.md` - Testing workflow
- ✅ `README.md` - Main readme

Recommendation: Merge into single comprehensive README

### 3. Redis Dependencies
- `backend/app/services/cache_manager.py` - Uses Redis
- Keep Redis dependency in pyproject.toml
- Make Redis truly optional (graceful fallback)

## 🔧 CODE CLEANUP NEEDED

### 1. Remove Celery References

**File**: `backend/app/tasks/batch_processing.py`
```python
# Remove:
from app.core.celery_app import celery_app

@celery_app.task(bind=True)
def process_batch_estimates(self, ...):
    # Change to regular function
```

**File**: `backend/app/api/v1/endpoints/batch.py`
```python
# Remove:
from app.core.celery_app import celery_app
```

### 2. Unused Imports After UUID Migration

Check all model files for:
- ❌ `from sqlalchemy.dialects.postgresql import UUID` (removed)
- ✅ `from app.db.types import UUID` (added)

### 3. Frontend Cleanup

**Removed conflicting directory**:
- ❌ `frontend/app/` (was conflicting with src/app/)

## 📋 CLEANUP EXECUTION PLAN

### Phase 1: Delete Docker & Old Files (Safe)
```bash
# Docker files
rm docker-compose.yml
rm backend/Dockerfile
rm frontend/Dockerfile  
rm .dockerignore
rm frontend/.dockerignore 2>/dev/null

# Old requirements
rm backend/requirements.txt

# Python cache
find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find backend -type f -name "*.pyc" -delete

# Old migrations (already deleted, remove from git)
git rm backend/alembic/versions/135bec871877_*.py
git rm backend/alembic/versions/bb59ec217272_*.py
```

### Phase 2: Remove Celery Code
```bash
# Delete celery_app
rm backend/app/core/celery_app.py

# Update batch_processing.py - convert @task to regular functions
# Update batch.py - remove celery imports
# Update estimate.py - call functions directly instead of .delay()
```

### Phase 3: Optional Cleanup
```bash
# Remove redundant startup script
rm start.py  # Keep start.sh

# Clean frontend build
rm -rf frontend/.next

# Consolidate docs (manual merge)
# Keep: README.md, TEST_GUIDE.md
# Merge: QUICKSTART.md, START_HERE.md → README.md
```

## 🎯 POST-CLEANUP VERIFICATION

### 1. Backend Tests
```bash
cd backend
uv run python -c "from app.main import app; print('✓ Backend imports OK')"
uv run backend  # Should start without errors
```

### 2. Frontend Tests  
```bash
cd frontend
npm run build  # Should build successfully
```

### 3. Database Migrations
```bash
cd backend
uv run alembic current  # Should show current migration
```

## 📊 ESTIMATED CLEANUP IMPACT

**Files to Delete**: ~1560 files
- 6 Docker files
- 1 requirements.txt
- 1 celery_app.py
- ~1551 Python cache files
- 2 old migration files

**Files to Modify**: 3 files
- batch_processing.py
- batch.py  
- estimate.py

**Space Saved**: ~50-100 MB (mostly cache files)

**Complexity Reduction**: 
- No Docker knowledge needed
- No Celery/Redis required for basic operation
- Simpler dependency management (uv only)
- Fewer files to maintain

## ⚡ QUICK CLEANUP COMMANDS

```bash
# Navigate to project root
cd /d/Climatiq-Decarbonization/Decarbonization

# Delete Docker files
rm docker-compose.yml backend/Dockerfile frontend/Dockerfile .dockerignore frontend/.dockerignore 2>/dev/null

# Delete old requirements
rm backend/requirements.txt

# Delete Celery
rm backend/app/core/celery_app.py

# Clean Python cache
find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find backend -type f -name "*.pyc" -delete 2>/dev/null

# Clean frontend build
rm -rf frontend/.next

# Delete redundant startup
rm start.py

echo "✅ Cleanup complete!"
```

---

**Ready to proceed with cleanup?**
