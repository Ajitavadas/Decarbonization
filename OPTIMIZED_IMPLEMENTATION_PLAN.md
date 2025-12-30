# 🎯 OPTIMIZED IMPLEMENTATION APPROACH - Decarbonization Platform

## Executive Summary

Based on your deep research and the comprehensive Climatiq API documentation, here is the **optimized, phased implementation strategy** that bridges your research findings with production-ready code.

**Key Optimization Insights:**
- Modular monolith architecture > Microservices (for carbon accounting domain)
- Climatiq's 4 primary endpoint groups (Estimate, Batch, Travel, Freight) + Autopilot
- JSONB polymorphic activity storage in PostgreSQL
- Redis caching with 24-hour TTL for emission factors
- Celery async workers for batch processing (100-record chunks)

---

## PHASE 1: Core Foundation (Weeks 1-2)

### Goal
Establish the base infrastructure and primary estimation endpoints.

### Implementation Priority

#### 1.1 Database Schema Setup
**Files to create:**
```
backend/app/db/models/
├── base.py              # SQLAlchemy declarative base
├── organization.py      # Tenant model
├── project.py           # Reporting project
├── activity.py          # Central polymorphic activity table (JSONB)
└── batch_job.py         # Async job tracking
```

**Critical Tables:**
```sql
-- emission_activities (Core ledger)
CREATE TABLE emission_activities (
    id UUID PRIMARY KEY,
    project_id UUID FK,
    activity_type VARCHAR(50),    -- travel, freight, energy, procurement
    scope VARCHAR(10),             -- Scope 1/2/3 (auto-classified)
    input_data JSONB,              -- Raw Climatiq request payload
    co2e_kg NUMERIC(20,6),         -- Result
    calculation_method VARCHAR(20) -- ar4, ar5, ar6
);

-- custom_mappings (Organizational memory)
CREATE TABLE custom_mappings (
    id UUID PRIMARY KEY,
    organization_id UUID FK,
    internal_label VARCHAR(255),      -- ERP code
    climatiq_activity_id VARCHAR(255),
    confidence_score FLOAT
);

-- batch_jobs (Async tracking)
CREATE TABLE batch_jobs (
    id UUID PRIMARY KEY,
    status VARCHAR(20),        -- queued, processing, completed, failed
    processed_records INT,
    error_log JSONB            -- Array of failure objects
);
```

**GIN Index on JSONB:**
```sql
CREATE INDEX idx_activity_input_data ON emission_activities USING gin(input_data);
```

#### 1.2 Climatiq Integration Base Layer
**Files:**
```
backend/app/integration/climatiq/
├── client.py           # HTTP client with retry logic (httpx async)
├── schemas.py          # Pydantic models for Climatiq payloads
├── service.py          # Business logic facade
└── endpoints/
    ├── estimate.py     # Single & batch estimation
    ├── travel.py       # Distance & spend-based
    ├── energy.py       # Electricity & fuel
    └── freight.py      # Intermodal routing
```

**Critical Implementation - Climatiq Client:**
```python
# backend/app/integration/climatiq/client.py
import httpx
from tenacity import retry, wait_exponential, stop_after_attempt

class ClimatiqClient:
    def __init__(self, api_key: str):
        self.base_url = "https://api.climatiq.io"
        self.preview_url = "https://preview.api.climatiq.io"
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3)
    )
    async def estimate(self, payload: dict) -> dict:
        """Single estimate: POST /data/v1/estimate"""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/data/v1/estimate",
                json=payload,
                headers=self.headers
            )
            return response.json()
    
    @retry(wait=wait_exponential(multiplier=1, min=2, max=10))
    async def estimate_batch(self, payloads: list) -> dict:
        """Batch: POST /data/v1/estimate/batch (100 max items)"""
        # Chunk into max 100 items
        chunked = [payloads[i:i+100] for i in range(0, len(payloads), 100)]
        results = []
        
        for chunk in chunked:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.base_url}/data/v1/estimate/batch",
                    json={"estimates": chunk},
                    headers=self.headers
                )
                results.extend(response.json()["results"])
        
        return {"results": results}
```

#### 1.3 Core Services Layer
**Files:**
```
backend/app/services/
├── calculation_engine.py    # Orchestration logic
├── scope_classifier.py      # Auto-classification (Scope 1/2/3)
└── cache_manager.py         # Redis caching
```

**Scope Classification Logic:**
```python
# Pseudo-code structure
class ScopeClassifier:
    def classify(self, activity_type: str, sub_type: str = None) -> str:
        """
        SCOPE 1: Owned direct emissions (fuel combustion)
        SCOPE 2: Purchased energy (electricity, heat, steam)
        SCOPE 3: Value chain (travel, freight, procurement)
        """
        if activity_type == "energy":
            return "Scope 1" if sub_type == "fuel" else "Scope 2"
        elif activity_type in ["travel", "freight", "procurement"]:
            return "Scope 3"
        return "Unclassified"
```

---

## PHASE 2: Domain-Specific Endpoints (Weeks 2-3)

### Goal
Implement the 4 primary Climatiq feature groups with full API coverage.

#### 2.1 Estimate & Batch Endpoints
**Endpoint Structure:**
```python
# backend/app/api/v1/endpoints/estimate.py

@router.post("/estimate")
async def single_estimate(
    req: EstimateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Single activity calculation"""
    # 1. Validate input
    # 2. Construct Climatiq payload
    # 3. Call climatiq_service.estimate()
    # 4. Store result in emission_activities
    # 5. Return with scope classification
    pass

@router.post("/estimate/batch")
async def batch_estimate(
    file: UploadFile,
    db: Session = Depends(get_db)
):
    """
    Async batch processing:
    1. Save file to S3
    2. Create batch_job record (status: queued)
    3. Push Celery task
    4. Return job_id for polling
    """
    job = BatchJob(status="queued", file_url=s3_path)
    db.add(job)
    db.commit()
    
    # Push to Redis queue
    process_batch_task.delay(job.id)
    
    return {"job_id": job.id, "status": "queued"}
```

**Celery Task:**
```python
# backend/app/tasks/batch_processor.py
@celery_app.task
def process_batch_task(job_id: str):
    """
    Worker processes CSV:
    1. Download from S3
    2. Parse with Pandas
    3. Chunk into 100-record batches
    4. Call Climatiq batch endpoint
    5. Update db with results
    6. Handle errors gracefully
    """
    df = pandas.read_csv(s3_path)
    
    for chunk in chunked_df:
        payloads = [
            {
                "emission_factor": {"activity_id": row["type"]},
                "parameters": {"energy": row["amount"], "energy_unit": row["unit"]}
            }
            for _, row in chunk.iterrows()
        ]
        
        results = climatiq_service.estimate_batch(payloads)
        
        for i, result in enumerate(results):
            if "error" in result:
                job.error_log.append({"row": i, "error": result["error"]})
            else:
                create_activity(result["co2e"]["kg"], result)
```

#### 2.2 Travel Endpoints (Distance & Spend)

**Key API Differences:**
```python
# Distance-based: /travel/v1-preview1/distance
{
    "origin": {"iata": "LHR"},        # Airport codes
    "destination": {"iata": "JFK"},
    "travel_mode": "air",
    "air_details": {"class": "economy"}  # economy, business, first
}

# Spend-based: /travel/v1-preview1/spend
{
    "spend_type": "hotel",
    "money": 1000,
    "money_unit": "usd",
    "spend_location": {"query": "New York"},
    "spend_year": 2023  # CRITICAL: Inflation adjustment
}
```

**Implementation:**
```python
# backend/app/api/v1/endpoints/travel.py

@router.post("/travel/distance")
async def calculate_travel_distance(req: TravelDistanceRequest):
    """
    Auto-routes based on origin/destination
    - IATA codes for airports
    - UN/LOCODE for ports
    - Coordinates as fallback
    """
    payload = {
        "origin": {"iata": req.origin_airport},
        "destination": {"iata": req.destination_airport},
        "travel_mode": req.mode,  # air, car, rail
        "year": 2024
    }
    
    if req.mode == "air":
        payload["air_details"] = {"class": req.cabin_class}
    
    result = await climatiq.calculate_travel_distance(payload)
    # Store in activities with Scope 3, Category 6 classification
    return result

@router.post("/travel/spend")
async def calculate_travel_spend(req: TravelSpendRequest):
    """
    Spend-based (credit card ledger entries, etc.)
    CRITICAL: Must include spend_year for inflation adjustment
    """
    payload = {
        "spend_type": req.type,  # air, hotel, rail, road, sea
        "money": req.amount,
        "money_unit": req.currency,
        "spend_location": {"query": req.location},
        "spend_year": req.year  # DON'T OMIT THIS
    }
    
    result = await climatiq.calculate_travel_spend(payload)
    return result
```

#### 2.3 Energy Endpoints (Electricity, Heat, Fuel)

**Electricity Specifics:**
```python
{
    "region": "US-CA",             # MANDATORY: grid region matters
    "year": 2023,
    "amount": {"energy": 5000, "energy_unit": "kWh"},
    "connection_type": "grid",     # or "direct" for dedicated line
    "source_set": "core",          # "iea" for premium
    "recs": {                      # Renewable Energy Certificates
        "energy": 1000,            # 1000 kWh covered by green certs
        "energy_unit": "kWh"
    }
}
```

**Implementation:**
```python
# backend/app/api/v1/endpoints/energy.py

@router.post("/energy/electricity")
async def calculate_electricity(req: ElectricityRequest):
    """
    Scope 2: Purchased electricity
    Must handle:
    - Location-based (grid intensity)
    - Market-based (with RECs)
    """
    payload = {
        "region": req.grid_region,
        "amount": {"energy": req.kwh, "energy_unit": "kWh"},
        "connection_type": "grid"
    }
    
    if req.renewable_certificates_kwh:
        payload["recs"] = {
            "energy": req.renewable_certificates_kwh,
            "energy_unit": "kWh"
        }
    
    result = await climatiq.estimate_electricity(payload)
    # Market-based: portion covered by RECs zeroed out
    # Location-based: full grid intensity applied
    return result

@router.post("/energy/fuel")
async def calculate_fuel(req: FuelRequest):
    """
    Scope 1: Direct combustion
    Fuel types: natural_gas, diesel, biodiesel_b100
    """
    payload = {
        "fuel_type": req.fuel_type,
        "amount": req.amount,
        "unit": req.unit  # kg, liters, etc.
    }
    
    result = await climatiq.estimate_fuel(payload)
    # Store separately: biogenic_emissions vs fossil CO2e
    return result
```

#### 2.4 Freight (Intermodal) & Procurement

**Freight Route Structure:**
```python
{
    "route": [
        {"location": {"query": "Port of Shanghai"}},
        {"leg_details": {"transport_mode": "sea", "transit_type": "auto"}},
        {"location": {"query": "Port of Rotterdam"}},
        {"leg_details": {"transport_mode": "road", "vehicle_type": "rigid_truck"}},
        {"location": {"query": "Final Destination, Berlin"}}
    ],
    "cargo": {"weight": 10, "weight_unit": "t"}
}
```

**Procurement/Classification:**
```python
{
    "activity": {
        "classification_code": "25",
        "classification_type": "isic4"  # isic4, nace2, naics2017, mcc
    },
    "money": 5000,
    "money_unit": "eur",
    "spend_year": 2022,
    "spend_region": "DE"
}
```

---

## PHASE 3: Autopilot & Custom Mappings (Week 3)

### 3.1 Autopilot Implementation

**Two-Step Process:**
1. **Suggest**: User types → API returns candidates with confidence
2. **Estimate**: Confirmed match → Direct calculation + storage

```python
# backend/app/api/v1/endpoints/autopilot.py

@router.post("/autopilot/suggest")
async def suggest_factors(req: AutopilotSuggestRequest):
    """
    LLM-powered matching
    Input: "500 Dell Latitude Laptops for employee purchase"
    Output: [
        {"id": "...", "name": "Computing Equipment", "confidence": 0.92},
        {"id": "...", "name": "Electronics", "confidence": 0.85}
    ]
    """
    result = await climatiq.autopilot_suggest(
        text=req.description,
        domain=req.domain  # "general" or "manufacturing"
    )
    return result["suggestions"]

@router.post("/autopilot/estimate")
async def autopilot_estimate(req: AutopilotEstimateRequest):
    """
    Combined: Match + Calculate in one call
    Returns: co2e + factor details + confidence
    
    CRITICAL: Store matched pair in custom_mappings for future reuse
    """
    result = await climatiq.autopilot_estimate(req.text, req.amount, req.unit)
    
    # Auto-save mapping for future reference
    mapping = CustomMapping(
        organization_id=user.org_id,
        internal_label=req.text[:255],  # Truncate
        climatiq_activity_id=result["activity_id"],
        confidence_score=result["confidence"]
    )
    db.add(mapping)
    
    return result
```

### 3.2 Custom Mappings API

```python
# backend/app/api/v1/endpoints/mappings.py

@router.post("/mappings")
async def create_mapping(req: CreateMappingRequest):
    """
    Manual mapping creation
    Example: "GL-TRAVEL-001" → "flight_emissions"
    """
    mapping = CustomMapping(
        organization_id=user.org_id,
        internal_label=req.internal_label,
        climatiq_activity_id=req.climatiq_activity_id,
        source=req.source_preference,
        year=req.year_preference
    )
    db.add(mapping)
    db.commit()
    return mapping

@router.post("/estimate/with-mapping")
async def estimate_with_mapping(req: EstimateWithMappingRequest):
    """
    Use pre-defined mappings for ERP integration
    Instead of searching for factors, use the stored mapping
    """
    mapping = db.query(CustomMapping).filter(
        CustomMapping.internal_label == req.internal_label
    ).first()
    
    if not mapping:
        raise ValueError(f"No mapping found for {req.internal_label}")
    
    # Direct calculation using mapped factor
    result = await climatiq.estimate({
        "emission_factor": {"activity_id": mapping.climatiq_activity_id},
        "parameters": req.parameters
    })
    return result
```

---

## PHASE 4: Caching & Performance (Week 4)

### 4.1 Redis Caching Strategy

```python
# backend/app/core/cache.py

import redis
import json
from datetime import timedelta

class CacheManager:
    def __init__(self):
        self.redis = redis.Redis(host="redis", port=6379, decode_responses=True)
    
    def _make_key(self, activity_id: str, region: str, year: int, version: str):
        return f"climatiq:factor:{activity_id}:{region}:{year}:{version}"
    
    async def get_or_fetch(self, activity_id, region, year, version):
        """Cache-aside pattern"""
        key = self._make_key(activity_id, region, year, version)
        
        # Check cache
        cached = self.redis.get(key)
        if cached:
            return json.loads(cached)
        
        # Cache miss: fetch from API
        factor = await climatiq_client.search_factors(activity_id, region, year)
        
        # Store with 24-hour TTL
        self.redis.setex(key, timedelta(hours=24), json.dumps(factor))
        
        return factor
    
    def invalidate_pattern(self, pattern: str):
        """Bulk invalidate (e.g., all 2023 factors)"""
        for key in self.redis.scan_iter(match=pattern):
            self.redis.delete(key)
```

### 4.2 API Response Caching

```python
from functools import wraps

def cache_response(ttl_seconds=3600):
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            cache_key = f"response:{f.__name__}:{hash(str(args) + str(kwargs))}"
            
            cached = redis.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = await f(*args, **kwargs)
            redis.setex(cache_key, ttl_seconds, json.dumps(result))
            
            return result
        return wrapper
    return decorator

@router.get("/dashboard/summary")
@cache_response(ttl_seconds=3600)
async def get_summary(user_id: str):
    # Heavy aggregation query
    # Results cached for 1 hour
    pass
```

---

## PHASE 5: Frontend & Dashboard (Week 4-5)

### 5.1 Key React Components

```tsx
// components/travel/TravelCalculator.tsx
export function TravelCalculator() {
  const [origin, setOrigin] = useState("LHR");
  const [destination, setDestination] = useState("JFK");
  const [cabinClass, setCabinClass] = useState("economy");
  
  const mutation = useMutation({
    mutationFn: (data) => 
      fetch("/api/v1/travel/distance", { method: "POST", body: JSON.stringify(data) })
  });
  
  return (
    <div>
      <input value={origin} onChange={(e) => setOrigin(e.target.value)} />
      <input value={destination} onChange={(e) => setDestination(e.target.value)} />
      <select value={cabinClass} onChange={(e) => setCabinClass(e.target.value)}>
        <option>economy</option>
        <option>business</option>
      </select>
      
      <button onClick={() => mutation.mutate({origin, destination, cabinClass})}>
        Calculate
      </button>
      
      {mutation.data && <p>{mutation.data.co2e_kg} kg CO2e</p>}
    </div>
  );
}

// components/autopilot/SmartClassifier.tsx
export function SmartClassifier() {
  const [input, setInput] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  
  const debouncedSuggest = useDebouncedCallback(async (text) => {
    const result = await fetch("/api/v1/autopilot/suggest", {
      method: "POST",
      body: JSON.stringify({ description: text })
    });
    setSuggestions(await result.json());
  }, 300);
  
  return (
    <div>
      <input 
        value={input} 
        onChange={(e) => {
          setInput(e.target.value);
          debouncedSuggest(e.target.value);
        }}
        placeholder="E.g., '500 Dell Latitude Laptops'"
      />
      
      <ul>
        {suggestions.map(s => (
          <li key={s.id}>
            {s.name} - {Math.round(s.confidence * 100)}% match
          </li>
        ))}
      </ul>
    </div>
  );
}

// components/dashboard/EmissionsBreakdown.tsx
export function EmissionsBreakdown({ activities }) {
  const groupedByScope = useMemo(() => {
    const grouped = {};
    activities.forEach(a => {
      if (!grouped[a.scope]) grouped[a.scope] = [];
      grouped[a.scope].push(a);
    });
    return grouped;
  }, [activities]);
  
  return (
    <div>
      {Object.entries(groupedByScope).map(([scope, items]) => (
        <ScopeCard
          scope={scope}
          totalCo2e={items.reduce((sum, a) => sum + a.co2e_kg, 0)}
          count={items.length}
        />
      ))}
    </div>
  );
}
```

---

## IMPLEMENTATION CHECKLIST

### Phase 1 Deliverables
- [ ] PostgreSQL schema with JSONB activities table
- [ ] Climatiq HTTP client with retry logic
- [ ] EstimateRequest/EstimateResponse Pydantic schemas
- [ ] Single estimate endpoint working
- [ ] Scope classifier logic implemented
- [ ] Redis caching layer operational

### Phase 2 Deliverables
- [ ] Batch endpoint + Celery worker
- [ ] Travel distance & spend endpoints
- [ ] Energy (electricity & fuel) endpoints
- [ ] Freight intermodal endpoint
- [ ] Procurement/classification endpoint
- [ ] All endpoints tested with sample Climatiq requests

### Phase 3 Deliverables
- [ ] Autopilot suggest endpoint
- [ ] Autopilot estimate endpoint
- [ ] Custom mappings table & CRUD
- [ ] Estimate with mapping endpoint
- [ ] Auto-saving of Autopilot matches

### Phase 4 Deliverables
- [ ] Cache-aside pattern implemented
- [ ] 24-hour TTL on emission factors
- [ ] API response caching
- [ ] Cache invalidation triggers

### Phase 5 Deliverables
- [ ] Travel calculator UI component
- [ ] Autopilot classifier UI component
- [ ] Dashboard with emissions breakdown
- [ ] Batch upload progress tracking
- [ ] Error reporting interface

---

## Key Implementation Principles

1. **Atomic Independence**: Batch API failures on item 50 don't affect items 51-100
2. **Inflation Adjustment**: Always include `spend_year` for spend-based calculations
3. **Region Specificity**: Don't use global averages; specify region for accuracy
4. **Polymorphic Storage**: Use JSONB for flexible activity attributes
5. **Scope Auto-Classification**: Automatically assign Scope 1/2/3 based on activity type
6. **Cache Everything**: Emission factors rarely change; cache for 24 hours
7. **Audit Trail**: Store raw inputs in activity table for reproducibility
8. **Error Gracefully**: Batch errors shouldn't cascade; log individually

---

## Critical Climatiq API Nuances

| Feature | Critical Parameter | Why It Matters |
|---------|-------------------|----------------|
| **Travel** | `spend_year` | Inflation adjustment (2020 ≠ 2023) |
| **Travel** | Cabin `class` | Business = 2-3x economy emissions |
| **Electricity** | `region` | Grid carbon intensity varies 10x globally |
| **Electricity** | `recs` object | Market-based vs location-based reporting |
| **Freight** | `vehicle_type` | Empty vs full truck = different intensity |
| **Freight** | `radiative_forcing_index` | RFI=2.0 accounts for cirrus clouds |
| **All** | `data_version` | "^28" = latest 28.x; "28" = exact version |
| **Procurement** | `spend_region` | Same product, different emissions by region |

---

## Ready for Implementation?

All 5 phases are now structured for immediate development. Each phase builds on the previous, with clear dependencies and deliverables.

**Total estimated effort:** 5-6 weeks for a production-ready platform.

Next step: Begin Phase 1 with database schema and Climatiq client implementation.

