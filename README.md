# Decarbonization Platform - Implementation & Architecture

## 🌍 Overview

This platform provides comprehensive carbon emissions calculation and management using the Climatiq API with intelligent AI-powered classification. The system automatically processes CSV uploads, classifies activities into GHG Protocol scopes, calculates CO2e emissions using optimal Climatiq endpoints, and stores results for frontend integration.

## 🏗️ Architecture

### **Core Components**

1. **Backend API** (FastAPI + SQLAlchemy)
   - RESTful endpoints for authentication, projects, activities, batch jobs
   - Async processing with Celery for background tasks
   - PostgreSQL database with comprehensive activity tracking

2. **AI Classification Service** (Groq + Gemini + Heuristics)
   - Multi-provider AI classification with fallbacks
   - GHG Protocol scope assignment (Scope 1, 2, 3)
   - 15+ Scope 3 subcategories with confidence scoring

3. **Climatiq Integration** (Multi-Endpoint Strategy)
   - Intelligent endpoint selection based on activity type
   - 3-tier fallback strategy for maximum coverage
   - Response structure handling for different API formats

4. **Unit Normalization**
   - Comprehensive unit type detection (energy, weight, volume, money, distance)
   - Automatic conversion for API compatibility
   - Case-insensitive matching with fallbacks

## 🧠 AI Classification System

### **Classification Strategy**

```python
# Multi-tier classification approach
1. Groq (Llama-3.3-70b) - Primary: Fast, structured output
2. Gemini - Secondary: Reliable backup  
3. Heuristics - Tertiary: Rule-based fallback
```

### **Scope Assignment Logic**

- **Scope 1**: Direct emissions from owned assets
  - Fuel combustion (natural gas, diesel, petrol)
  - Company vehicles
  - On-site heating/cooling

- **Scope 2**: Indirect emissions from purchased energy
  - Electricity consumption
  - Purchased heating/steam
  - Grid-connected energy

- **Scope 3**: All other value chain emissions
  - Business travel (air, car, rail)
  - Procurement and purchased goods
  - Waste disposal
  - Employee commuting
  - Investments

### **Classification Output Format**

```python
# Returns tuple: (scope_number, confidence, needs_review)
classification = await ai_classifier.classify_transaction(
    description="Office electricity usage",
    category="Energy", 
    supplier_name=None
)
# Example: (2, 0.95, False) = Scope 2, 95% confidence
```

## ⚡ Climatiq Integration

### **Smart Endpoint Selection**

The system uses a 3-tier strategy for optimal CO2e calculation:

#### **Strategy 1: Autopilot (AI-powered)**
```json
POST https://api.climatiq.io/estimate/v1/autopilot
{
  "text": "Office electricity usage",
  "parameters": {
    "energy": 2500.0,
    "energy_unit": "kWh"
  }
}
```

#### **Strategy 2: Specific Endpoints**

**Energy Endpoint** (Electricity)
```json
POST https://api.climatiq.io/energy/v1/electricity
{
  "year": 2026,
  "region": "US", 
  "amount": {
    "energy": 2500.0,
    "energy_unit": "kWh"
  }
}
```

**Fuel Endpoint** (Natural Gas)
```json
POST https://api.climatiq.io/energy/v1/fuel
{
  "fuel_type": "natural_gas",
  "amount": {
    "volume": 12436.05,
    "volume_unit": "l"
  },
  "region": "US",
  "year": 2026
}
```

**Travel Endpoint** (Distance-based)
```json
POST https://preview.api.climatiq.io/travel/v1-preview1/distance
{
  "origin": {"query": "US"},
  "destination": {"query": "US"},
  "travel_mode": "air"
}
```

**Procurement Endpoint** (Spend-based)
```json
POST https://api.climatiq.io/procurement/v1/spend/batch
{
  "activity": {
    "classification_code": "25",
    "classification_type": "isic4"
  },
  "spend_year": 2026,
  "spend_region": "US",
  "money": 2500.0,
  "money_unit": "usd"
}
```

#### **Strategy 3: Direct Estimate** (Fallback)
```json
POST https://api.climatiq.io/data/v1/estimate
{
  "emission_factor": {
    "id": "electricity-supply_grid-source_production_mix",
    "data_version": "20.20"
  },
  "parameters": {
    "energy": 2500.0,
    "energy_unit": "kWh"
  }
}
```

### **Response Structure Handling**

Different endpoints return different JSON structures:

```python
def extract_co2e_from_response(result, endpoint_type):
    if endpoint_type == "energy":
        # Direct response: {"co2e": 91.62, "co2e_unit": "kg"}
        return result["co2e"]
    
    elif endpoint_type == "fuel":
        # Nested response: {"combustion": {"co2e": 837.55}}
        return result["combustion"]["co2e"]
    
    elif endpoint_type == "procurement":
        # Wrapped response: {"estimate": {"co2e": 631.17}}
        return result["estimate"]["co2e"]
    
    elif endpoint_type == "travel":
        # Direct response: {"co2e": 1397.05}
        return result["co2e"]
```

## 📊 Unit Normalization

### **Supported Unit Types**

```python
ENERGY_UNITS = ['kwh', 'mwh', 'gwh', 'wh', 'mj', 'gj', 'btu', 'therm', 'therms', 'mmbtu']
WEIGHT_UNITS = ['kg', 't', 'ton', 'tonne', 'lb', 'lbs', 'g', 'gram', 'grams']
VOLUME_UNITS = ['l', 'liter', 'liters', 'm3', 'm³', 'cubic meter', 'gal', 'gallon', 'gallons', 'ml', 'milliliter']
MONEY_UNITS = ['eur', 'usd', 'gbp', 'chf', 'cad', 'aud', 'jpy', 'cny', 'inr', 'aed', 'sar', 'sek', 'nok', 'dkk']
DISTANCE_UNITS = ['km', 'kilometer', 'kilometre', 'mile', 'miles', 'm', 'meter', 'metre']
```

### **Automatic Conversions**

- **Natural Gas**: Therms → Liters (1 therm = 2.83L)
- **MMBtu**: MMBtu → Liters (1 MMBtu = 28.3L)
- **Currency**: Case normalization (USD → usd)

## 🔄 Processing Workflow

### **CSV Upload Process**

1. **File Validation**
   - CSV format verification
   - Required columns: description, amount, unit, category, region, year, activity_date

2. **Row Processing Loop**
   ```python
   for each row in CSV:
       # Extract data
       description = row["description"]
       amount = float(row["amount"])
       unit = normalize_unit(row["unit"])
       
       # AI Classification
       scope, confidence, needs_review = await classify_transaction(description, category, supplier_name)
       
       # CO2e Calculation
       co2e = await calculate_with_ai_suggestion(description, amount, unit, unit_type, region, year)
       
       # Database Storage
       save_activity(description, co2e, scope, metadata)
   ```

3. **Batch Job Tracking**
   - Real-time progress updates
   - Success/failure counting
   - Error logging with detailed messages

## 📈 Real Calculation Examples

### **Office Electricity (2500 kWh)**
- **Classification**: Scope 2 (95% confidence)
- **Endpoint**: Energy endpoint
- **Payload**: `{"year": 2026, "region": "US", "amount": {"energy": 2500, "energy_unit": "kWh"}}`
- **Response**: `{"co2e": 91.62, "co2e_unit": "kg"}`
- **Result**: **91.62 kg CO2e**

### **Business Travel (5000 km air)**
- **Classification**: Scope 3 (98% confidence)
- **Endpoint**: Travel endpoint  
- **Payload**: `{"origin": {"query": "US"}, "destination": {"query": "US"}, "travel_mode": "air"}`
- **Response**: `{"co2e": 1397.05, "co2e_unit": "kg"}`
- **Result**: **1397.05 kg CO2e**

### **Office Supplies ($2500)**
- **Classification**: Scope 3 (90% confidence)
- **Endpoint**: Procurement endpoint
- **Payload**: `{"activity": {"classification_code": "25"}, "spend_year": 2026, "spend_region": "US", "money": 2500, "money_unit": "usd"}`
- **Response**: `{"estimate": {"co2e": 631.17, "co2e_unit": "kg"}}`
- **Result**: **631.17 kg CO2e**

## 🗄️ Database Schema

### **Core Tables**

```sql
-- Projects
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    name VARCHAR,
    description TEXT,
    start_date DATE,
    end_date DATE,
    reporting_year INTEGER,
    created_at TIMESTAMP
);

-- Emission Activities  
CREATE TABLE emission_activities (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    activity_type VARCHAR,
    sub_type VARCHAR,
    scope VARCHAR,
    activity_date DATE,
    co2e_kg NUMERIC(20, 6),
    co2e_unit VARCHAR,
    calculation_method VARCHAR,
    input_data JSONB,
    region VARCHAR,
    year VARCHAR,
    description TEXT,
    created_at TIMESTAMP
);

-- Batch Jobs
CREATE TABLE batch_jobs (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    status VARCHAR,
    total_records INTEGER,
    processed_records INTEGER,
    successful_records INTEGER,
    failed_records INTEGER,
    error_log JSONB,
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

## 🚀 API Endpoints

### **Authentication**
```
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
```

### **Projects**
```
POST /api/v1/projects
GET  /api/v1/projects/{project_id}
PUT  /api/v1/projects/{project_id}
DELETE /api/v1/projects/{project_id}
```

### **Activities**
```
GET /api/v1/activities/?project_id={id}
POST /api/v1/activities
GET /api/v1/activities/{activity_id}
PUT /api/v1/activities/{activity_id}
DELETE /api/v1/activities/{activity_id}
```

### **Batch Processing**
```
POST /api/v1/upload/csv
GET /api/v1/batch/jobs
GET /api/v1/batch/jobs/{job_id}
```

### **Climatiq Integration**
```
POST /api/v1/energy/electricity
POST /api/v1/energy/fuel
POST /api/v1/travel/distance
POST /api/v1/travel/spend
POST /api/v1/procurement/calculate
POST /api/v1/climatiq/autopilot
```

## ⚠️ Current Concerns & Considerations

### **Known Issues**

1. **Activity Description Handling**
   - Some activities show `None` descriptions in database
   - Affects frontend display and test script execution
   - **Root Cause**: CSV parsing or data type conversion issues

2. **API Rate Limiting**
   - Climatiq API has rate limits (varies by plan)
   - Current implementation lacks rate limit handling
   - **Risk**: Failed calculations during high volume uploads

3. **Error Recovery**
   - Limited retry logic for failed API calls
   - No exponential backoff for transient failures
   - **Impact**: Reduced reliability for large datasets

4. **Data Validation**
   - Minimal input validation for edge cases
   - No schema validation for Climatiq responses
   - **Risk**: Data corruption or unexpected errors

### **Performance Considerations**

1. **Batch Processing**
   - Current implementation processes rows sequentially
   - Could benefit from parallel processing for large files
   - **Optimization**: Async batch processing

2. **Caching**
   - No caching of emission factors or classifications
   - Repeated calculations for similar activities
   - **Opportunity**: Redis cache for common patterns

3. **Database Optimization**
   - Missing indexes on frequently queried fields
   - JSONB queries could be optimized
   - **Improvement**: Add GIN indexes on JSONB columns

### **Security Considerations**

1. **API Key Management**
   - Climatiq API key stored in environment variables
   - No key rotation mechanism
   - **Best Practice**: Key vault integration

2. **Input Sanitization**
   - Limited validation of user inputs
   - Potential SQL injection in complex queries
   - **Recommendation**: Input validation middleware

## 🔧 Configuration

### **Environment Variables**

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/decarbonization

# Climatiq API  
CLIMATIQ_API_KEY=your_api_key_here
CLIMATIQ_BASE_URL=https://api.climatiq.io

# AI Services
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key

# Application
SECRET_KEY=your_secret_key
AI_MIN_CONFIDENCE_THRESHOLD=0.7
```

### **Docker Setup**

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/decarbonization
    depends_on:
      - db
      - redis
      
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: decarbonization
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      
  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
```

## 🧪 Testing

### **End-to-End Test Script**

```python
# test_end_to_end.py
1. Health check
2. Authentication
3. CSV upload
4. Batch job monitoring
5. Activity verification
6. CO2e calculation validation
```

### **Test Results Summary**

✅ **Working Features:**
- AI classification (Scope 1, 2, 3)
- CO2e calculation (18,904.90 kg total)
- Multi-endpoint Climatiq integration
- Database storage and retrieval

⚠️ **Areas for Improvement:**
- Activity description handling
- Error recovery mechanisms
- Performance optimization
- Enhanced validation

## 🚀 Deployment

### **Production Checklist**

- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] SSL certificates installed
- [ ] Rate limiting configured
- [ ] Monitoring and logging setup
- [ ] Backup procedures documented
- [ ] API keys secured in vault
- [ ] Load balancer configured
- [ ] Health checks implemented

## 📚 API Documentation

### **Authentication Headers**
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### **Response Format**
```json
{
  "success": true,
  "data": {...},
  "message": "Operation completed",
  "total_records": 5
}
```

### **Error Format**
```json
{
  "success": false,
  "error": "Validation failed",
  "details": {
    "field": "amount",
    "message": "Must be positive number"
  }
}
```

---

## 🎯 Next Steps

1. **Fix Activity Descriptions**: Resolve `None` description issue
2. **Add Rate Limiting**: Implement Climatiq API rate limit handling
3. **Enhance Error Recovery**: Add retry logic with exponential backoff
4. **Performance Optimization**: Implement batch processing and caching
5. **Security Hardening**: Add input validation and API key rotation
6. **Monitoring**: Add comprehensive logging and alerting
7. **Frontend Integration**: Prepare API documentation for Next.js integration

This platform provides a robust foundation for carbon emissions management with intelligent classification and accurate CO2e calculations using industry-standard Climatiq API integration.
