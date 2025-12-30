# 🚀 COMPLETE IMPLEMENTATION ROADMAP - Ready for Labs Development

This is your final, actionable guide. You now have:
1. ✅ Deep research on Climatiq API + your platform requirements
2. ✅ Optimized phased implementation plan (5 phases, 5-6 weeks)
3. ✅ Comprehensive schema references for all endpoints
4. ✅ Critical implementation principles and gotchas

---

## QUICK REFERENCE: What You Have

### Documents Created

| Document | Purpose | Use It For |
|----------|---------|-----------|
| **OPTIMIZED_IMPLEMENTATION_PLAN.md** | 5-phase implementation roadmap | Architecture decisions, project planning |
| **SCHEMAS_REFERENCE.md** | Exact Pydantic schemas for all endpoints | Copy-paste code for FastAPI endpoints |
| **This Document** | Orchestration & next steps | How to start coding in Labs |

### Your Research Documents
| Document | Focus |
|----------|-------|
| **Researched.md** (your upload) | Deep architecture blueprint (modular monolith, containerization) |
| **Climatiq Technical Reference** | Complete API documentation (all 9 endpoint groups) |

---

## IMPLEMENTATION STARTING POINT: Phase 1

### What to Build First (Days 1-3)

#### Step 1: Database Foundation
```
Create: backend/app/db/models/
├── __init__.py
├── activity.py          # From SCHEMAS_REFERENCE.md Part 8
├── organization.py
├── project.py
├── batch_job.py
└── custom_mapping.py
```

**Copy from SCHEMAS_REFERENCE.md → Part 8: Database Models**

#### Step 2: Climatiq Client
```
Create: backend/app/integration/climatiq/
├── __init__.py
├── client.py            # HTTP client with retry logic
├── schemas.py           # All Pydantic schemas (Parts 1-7)
└── service.py           # Facade for business logic
```

**Copy from SCHEMAS_REFERENCE.md → All Parts 1-7**
**Implement client.py pattern from OPTIMIZED_IMPLEMENTATION_PLAN.md → Phase 1.3**

#### Step 3: Estimate Endpoint
```
Create: backend/app/api/v1/endpoints/
├── __init__.py
└── estimate.py          # Single + batch endpoints
```

**Pattern from OPTIMIZED_IMPLEMENTATION_PLAN.md → Phase 2.1**

---

## CRITICAL DECISIONS ALREADY MADE

### Architecture
- ✅ **Modular Monolith**: Single FastAPI backend, domain-separated code
- ✅ **Async Workers**: Celery for batch processing (100-item chunks)
- ✅ **Caching**: Redis with 24-hour TTL on emission factors
- ✅ **Database**: PostgreSQL with JSONB for polymorphic activities

### API Integration
- ✅ **Primary Endpoints**: Estimate, Batch, Travel, Energy, Freight, Procurement, Autopilot
- ✅ **Data Versioning**: `"^28"` (latest 28.x) for all requests
- ✅ **Error Handling**: Batch failures non-cascading (200 OK with individual errors)
- ✅ **Region Specificity**: Always required for energy; grid intensity varies 10x

### Data Model
- ✅ **Scope Classification**: Auto-assigned based on activity_type
- ✅ **Input Storage**: Raw `input_data` JSONB for auditability
- ✅ **Batch Tracking**: `batch_jobs` table with error_log for failed rows
- ✅ **Custom Mappings**: ERP code → Climatiq factor mapping for reusability

---

## KEY IMPLEMENTATION PRINCIPLES (Recap)

### 1. Climatiq Specifics
| Feature | Critical Detail | Implementation |
|---------|-----------------|-----------------|
| **Spend Year** | Controls inflation adjustment | NEVER omit in spend-based calculations |
| **Region Code** | 10x variance in grid carbon | Required for energy; optional but recommended for others |
| **Cabin Class** | 2-3x multiplier for business | Air travel: economy vs business dramatically different |
| **RFI (Radiative Forcing Index)** | Accounts for cirrus warming | Default 2.0 for air freight; can override to 1.0 |
| **Batch Limit** | Max 100 items per request | Chunk larger files before sending |
| **JSONB Storage** | Stores raw request payload | Enables perfect auditability & reproducibility |

### 2. Scope Classification Logic
```python
if activity_type == "energy":
    scope = "Scope 1" if sub_type == "fuel" else "Scope 2"
elif activity_type in ["travel", "freight", "procurement"]:
    scope = "Scope 3"
```

### 3. Caching Strategy
```
Key: climatiq:factor:{activity_id}:{region}:{year}:{version}
TTL: 24 hours
Pattern: Check Redis → Cache miss → Call API → Store → Return
```

### 4. Batch Error Handling
```python
results = [
    {"co2e": 500},                    # Item 1: Success
    {"error": "Invalid region: XY"},  # Item 2: Failure
    {"co2e": 750}                     # Item 3: Success
]
# Client must iterate through results and handle individually
```

---

## IMPLEMENTATION CHECKLIST FOR LABS

### Phase 1: Foundation (Week 1-2)

**Database**
- [ ] Create `emission_activities` table with JSONB input_data
- [ ] Create `custom_mappings` table for ERP integration
- [ ] Create `batch_jobs` table for async tracking
- [ ] Add GIN index on `input_data` JSONB column
- [ ] Initialize `organizations` and `projects` tables

**Climatiq Integration**
- [ ] Create `ClimatiqClient` class with async httpx
- [ ] Implement retry logic (exponential backoff for 429s)
- [ ] Create Pydantic schemas for all 7 endpoint groups
- [ ] Create `ClimatiqService` facade layer
- [ ] Store API key in environment (Bearer token header)

**Core Endpoints**
- [ ] POST `/api/v1/estimate` (single)
- [ ] POST `/api/v1/estimate/batch` (bulk)
- [ ] Scope auto-classification logic
- [ ] Activity storage in PostgreSQL
- [ ] Health check endpoint

**Testing**
- [ ] Test single estimate with real Climatiq API
- [ ] Test batch with 50-100 items
- [ ] Verify batch error handling (non-cascading failures)
- [ ] Verify JSONB storage of input_data

### Phase 2: Domain Endpoints (Week 2-3)

**Travel**
- [ ] Distance-based endpoint (IATA codes, auto-routing)
- [ ] Spend-based endpoint (with spend_year inflation)
- [ ] Cabin class support (economy, business, first)

**Energy**
- [ ] Electricity endpoint (region, RECs, custom mix)
- [ ] Fuel endpoint (combustion, biogenic tracking)
- [ ] Heat/steam endpoint (with loss_factor)

**Freight**
- [ ] Intermodal route builder (location → leg → location)
- [ ] Multi-modal support (road, sea, air, rail)
- [ ] Cargo weight normalization

**Procurement**
- [ ] Classification code support (ISIC4, NACE2, NAICS, MCC)
- [ ] Spend-based with region specificity
- [ ] Currency conversion + inflation

### Phase 3: Advanced Features (Week 3)

**Autopilot (NLP)**
- [ ] Suggest endpoint (candidates with confidence)
- [ ] Estimate endpoint (suggest + calculate)
- [ ] Auto-save mappings on confirmation

**Custom Mappings**
- [ ] CRUD for custom mappings table
- [ ] Estimate with mapping (ERP code → factor)
- [ ] Mapping reuse in batch processing

### Phase 4: Performance (Week 4)

**Caching**
- [ ] Redis cache manager with cache-aside pattern
- [ ] 24-hour TTL on emission factors
- [ ] Cache key construction (activity_id:region:year:version)

**Async Processing**
- [ ] Celery task for batch processing
- [ ] Chunk into 100-item batches
- [ ] Error logging per failed row
- [ ] Job status tracking

### Phase 5: Frontend (Week 4-5)

**React Components**
- [ ] Travel calculator (origin/destination/class)
- [ ] Autopilot classifier (debounced suggestions)
- [ ] Batch uploader (file select, progress tracking)
- [ ] Dashboard (scope breakdown, total CO2e)

**API Integration**
- [ ] React Query for polling batch job status
- [ ] Error boundary for graceful failure
- [ ] Loading states for async operations

---

## CRITICAL GOTCHAS (Don't Miss These!)

### 1. Spend Year Omission ⚠️
```python
# ❌ WRONG
{"spend_type": "hotel", "money": 1000}

# ✅ RIGHT
{"spend_type": "hotel", "money": 1000, "spend_year": 2023}
```
Without spend_year, you'll artificially reduce emissions (inflation adjustment breaks).

### 2. Region Specificity ⚠️
```python
# Grid carbon intensity:
# - US (coal-heavy): 400+ g CO2/kWh
# - Germany (50% renewable): 200 g CO2/kWh
# - France (nuclear): 50 g CO2/kWh

# ALWAYS specify region for energy
```

### 3. Batch Failures Don't Cascade ⚠️
```python
# Item 50 fails → Items 51-100 STILL PROCESS
# You MUST check individual results for errors

for i, result in enumerate(batch_results):
    if "error" in result:
        log_error(i, result["error"])
    else:
        save_to_db(result)
```

### 4. JSONB Auditability ⚠️
```python
# Store the EXACT request sent to Climatiq
activity.input_data = {
    "emission_factor": {...},
    "parameters": {...}
}
# This allows perfect reproducibility in audits
```

### 5. Batch Endpoint Limit ⚠️
```python
# Max 100 items per /estimate/batch request
# For 50,000 rows, chunk into 500 requests
chunk_size = 100
for i in range(0, len(payloads), chunk_size):
    chunk = payloads[i:i+chunk_size]
    results = climatiq.batch(chunk)
```

---

## CODE ORGANIZATION REFERENCE

```
decarbonization-platform/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── endpoints/
│   │   │       │   ├── estimate.py       (Phase 1)
│   │   │       │   ├── travel.py         (Phase 2)
│   │   │       │   ├── energy.py         (Phase 2)
│   │   │       │   ├── freight.py        (Phase 2)
│   │   │       │   ├── procurement.py    (Phase 2)
│   │   │       │   ├── autopilot.py      (Phase 3)
│   │   │       │   └── mappings.py       (Phase 3)
│   │   │       └── router.py
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   └── models/
│   │   │       ├── __init__.py
│   │   │       ├── activity.py          (Phase 1)
│   │   │       ├── organization.py
│   │   │       ├── project.py
│   │   │       ├── batch_job.py         (Phase 1)
│   │   │       └── custom_mapping.py    (Phase 3)
│   │   │
│   │   ├── integration/
│   │   │   └── climatiq/
│   │   │       ├── __init__.py
│   │   │       ├── client.py            (Phase 1)
│   │   │       ├── service.py           (Phase 1)
│   │   │       ├── schemas.py           (Phase 1-2)
│   │   │       └── endpoints/
│   │   │           ├── estimate.py
│   │   │           ├── travel.py
│   │   │           └── ...
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── scope_classifier.py      (Phase 1)
│   │   │   ├── cache_manager.py         (Phase 4)
│   │   │   └── calculation_engine.py
│   │   │
│   │   ├── tasks/
│   │   │   ├── __init__.py
│   │   │   └── batch_processor.py       (Phase 4)
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── celery_app.py            (Phase 4)
│   │   │
│   │   ├── main.py                      (FastAPI app entry)
│   │   └── crud/
│   │       └── base.py
│   │
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                            (Phase 5)
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## START CODING: Next 24 Hours

### Hour 1: Project Setup
```bash
mkdir decarbonization-platform
cd decarbonization-platform
git init

# Create virtualenv
python -m venv venv
source venv/bin/activate

# Create directory structure
mkdir -p backend/app/{api/v1/endpoints,db/models,integration/climatiq,services,tasks,core,crud}
touch backend/app/__init__.py
touch backend/app/db/__init__.py
touch backend/app/integration/__init__.py
touch backend/app/integration/climatiq/__init__.py
```

### Hour 2-3: Schemas & Database Models
1. Copy ALL schemas from **SCHEMAS_REFERENCE.md** → Parts 1-8
2. Create `backend/app/db/models/activity.py` from SCHEMAS_REFERENCE.md Part 8
3. Create Pydantic schemas in `backend/app/integration/climatiq/schemas.py`

### Hour 4-6: Climatiq Client
1. Create `backend/app/integration/climatiq/client.py` with httpx async client
2. Implement retry logic (tenacity for exponential backoff)
3. Implement authenticate with Bearer token

### Hour 7-8: First Endpoint
1. Create `backend/app/api/v1/endpoints/estimate.py`
2. Implement POST `/estimate` endpoint
3. Connect to Climatiq client
4. Test with real API

### Hour 9-24: Polish & Testing
1. Add error handling
2. Test batch endpoint
3. Verify JSONB storage
4. Add scope classification logic
5. Implement Redis caching
6. Create health check endpoint

---

## QUESTIONS TO ANSWER BEFORE CODING

1. **Climatiq API Key**: Do you have a valid key from https://app.climatiq.io?
2. **PostgreSQL**: Running locally or managed service?
3. **Redis**: For caching + Celery broker?
4. **Frontend Stack**: Next.js or React?
5. **Deployment Target**: Docker Compose local, Docker Hub push, or cloud deployment?

---

## YOU'RE READY

You have:
- ✅ Complete architecture blueprint
- ✅ 5-phase implementation roadmap
- ✅ Exact Pydantic schemas for copy-paste
- ✅ Critical gotchas identified
- ✅ Code organization defined
- ✅ Checklis for each phase

**Time to build.** Start with Phase 1 in Labs. You've got this. 🚀

---

## Support References

When stuck:
1. **Architecture questions**: OPTIMIZED_IMPLEMENTATION_PLAN.md
2. **Schema/code questions**: SCHEMAS_REFERENCE.md
3. **Research-driven decisions**: Researched.md (your upload)
4. **Climatiq API details**: Comprehensive Climatiq documentation (provided)

All the knowledge you need is in these documents. Happy coding! 🌍

