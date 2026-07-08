# End-to-End Testing Guide - Decarbonization Platform

## Test Credentials
- **Email**: ajit@example.com
- **Password**: 12345678

## Test Data CSV File
**File**: `tests/data/test_data_20_rows.csv` (in tests/data directory)

This file contains 20 synthetic activity rows with diverse emission sources across different categories.

### CSV Format
```csv
description,amount,unit,category,supplier_name,region,activity_date,year
```

### Required Fields:
- `description` - Activity description
- `amount` - Numeric value
- `unit` - Unit of measurement (kWh, gallons, miles, therms, etc.)
- `category` - Category type (Electricity, Transportation, Heating Fuel, etc.)
- `region` - Region code (US, UK, etc.)
- `activity_date` - Date in YYYY-MM-DD format
- `year` - Year (YYYY)

### Optional Fields:
- `supplier_name` - Name of supplier/vendor

### Sample Data Included (20 rows):
1. **Electricity** - Office and facility consumption (15,200 - 45,000 kWh)
2. **Natural Gas** - Heating fuel (290 - 420 therms)
3. **Transportation** - Diesel, gasoline for vehicles (850 - 2,100 gallons)
4. **Business Travel** - Flights (1,850 - 6,845 miles), rental cars
5. **IT Services** - Data center and server electricity (18,900 - 22,500 kWh)
6. **Manufacturing** - Warehouse and production electricity (28,500 - 45,000 kWh)
7. **Stationary Combustion** - Backup generators, forklifts (320 - 850 gallons)
8. **Employee Commute** - Commute surveys (18,500 miles)

## End-to-End Test Flow

### 1. Login
1. Open http://localhost:3000
2. Click "Sign In" or go to http://localhost:3000/login
3. Enter credentials:
   - Email: ajit@example.com
   - Password: 12345678
4. Click "Sign In"

### 2. Dashboard Overview
After login, you'll see the main dashboard with:
- **Sidebar** - Navigation menu
- **Header** - Search, notifications, theme toggle, user menu
- **Main Content** - Dashboard widgets and stats
- **Carbon Copilot** - AI assistant (toggle from sidebar)

### 3. Create a Project (If needed)
1. Click "Projects" in sidebar
2. Click "New Project"
3. Fill in project details:
   - Name: "Q1 2025 Carbon Tracking"
   - Description: "Testing emission tracking"
4. Save project

### 4. Upload CSV Data
1. Click "Upload" in the sidebar
2. Select your project from the dropdown
3. Click "Choose File" or drag & drop
4. Select `test_data_20_rows.csv`
5. Click "Upload"

**What happens:**
- File is parsed and validated
- Activities are classified (scope 1/2/3)
- Emissions are calculated via Climatiq API
- Data is stored in the database
- Batch job status is shown (processing → completed)

### 5. View Emissions Data
1. Click "Emissions" in sidebar
2. You'll see all 20 uploaded activities with:
   - Description
   - Amount & Unit
   - CO2e emissions
   - Scope classification
   - Date
   - Supplier
3. Filter by:
   - Scope (1, 2, 3)
   - Date range
   - Category
   - Search by description

### 6. Analyze by Scope
1. Click "Scope Analysis" in sidebar
2. View emissions breakdown:
   - **Scope 1**: Direct emissions (natural gas, diesel, propane)
   - **Scope 2**: Indirect from electricity (office, warehouse, servers)
   - **Scope 3**: Other indirect (business travel, commute)
3. See visual charts:
   - Pie chart by scope
   - Bar chart by category
   - Trend over time

### 7. View Reports
1. Click "Reports" in sidebar
2. Generate reports:
   - **Summary Report**: Overall emissions
   - **Scope Breakdown**: Detailed by scope
   - **Category Analysis**: By emission type
   - **Supplier Report**: By vendor
3. Export options:
   - Download as PDF
   - Download as Word document
   - Export to Excel

### 8. Set Reduction Targets
1. Click "Targets" in sidebar
2. Click "New Target"
3. Set target:
   - Baseline year: 2024
   - Target year: 2030
   - Reduction percentage: 50%
   - Scope: All or specific
4. View progress tracking

### 9. Get AI Recommendations (Carbon Copilot)
1. Click the bot icon in sidebar to open Copilot
2. Ask questions like:
   - "What are my highest emission sources?"
   - "Suggest reduction strategies for electricity"
   - "How can I reduce Scope 3 emissions?"
3. Get AI-powered suggestions:
   - Specific reduction strategies
   - Cost-benefit analysis
   - Implementation roadmap

### 10. Anomaly Detection
1. Click "Anomalies" in sidebar
2. View flagged unusual activities:
   - Spikes in electricity
   - Unusual fuel consumption
   - Missing data
3. AI verdict for each anomaly
4. Required evidence to verify

### 11. Theme Toggle (NEW!)
1. Look for the sun/moon icon in the header (top right)
2. Click to open theme menu
3. Choose:
   - **Light** - Light mode
   - **Dark** - Dark mode (default)
   - **System** - Follow OS preference

## API Testing (Alternative via Swagger)

### Access API Docs
http://localhost:8000/docs

### Key Endpoints to Test:

1. **POST /api/v1/auth/login**
   - Test authentication
   - Get access token

2. **POST /api/v1/upload/upload**
   - Upload CSV file
   - Requires: project_id, file
   - Returns: batch job ID

3. **GET /api/v1/estimate/activities**
   - List all activities
   - Filter by project, scope, date

4. **POST /api/v1/estimate/single**
   - Calculate single emission
   - Requires: description, amount, unit, region

5. **GET /api/v1/reports/summary**
   - Get emission summary
   - Breakdown by scope

6. **POST /api/v1/copilot/suggest**
   - Get AI recommendations
   - Context-aware suggestions

## Expected Results

### After Uploading test_data_20_rows.csv:
- **Total Activities**: 20
- **Total CO2e**: ~500-800 tonnes (varies by Climatiq API calculations)
- **Scope 1**: ~8-10 activities (natural gas, diesel, propane)
- **Scope 2**: ~8-10 activities (electricity consumption)
- **Scope 3**: ~2-4 activities (business travel, employee commute)

### Categories Breakdown:
- Electricity: 7 activities
- Transportation: 3 activities
- Heating Fuel: 3 activities
- Business Travel: 4 activities
- IT Services: 2 activities
- Manufacturing: 3 activities
- Stationary Combustion: 2 activities
- Employee Commute: 1 activity

## Troubleshooting

### CSV Upload Fails
**Error**: "Missing required fields"
- Check CSV has all required columns
- Ensure column names match exactly (case-insensitive)
- Verify no empty required fields

### No Emissions Calculated
**Issue**: Activities upload but CO2e is 0
- Check Climatiq API key in backend/.env
- Verify CLIMATIQ_API_KEY is valid
- Check backend logs for API errors

### AI Copilot Not Responding
**Issue**: Suggestions not generating
- Verify MISTRAL_API_KEY in backend/.env
- Check if Gemini key is valid
- Backend falls back to Mistral if Gemini fails

### Theme Toggle Not Working
**Issue**: Light/dark mode doesn't switch
- Reload the page (hard refresh: Ctrl+Shift+R)
- Clear browser cache
- Check if browser has dark mode forced

## Platform Architecture

### Backend (Python + FastAPI)
- **Framework**: FastAPI + SQLAlchemy
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **APIs**: Climatiq (emissions), Mistral/Gemini (AI)
- **Port**: 8000

### Frontend (Next.js + React)
- **Framework**: Next.js 15 with App Router
- **UI**: Tailwind CSS + shadcn/ui
- **State**: React hooks
- **Port**: 3000

### Key Features:
1. **Multi-format Upload**: CSV, XLSX, PDF (with OCR)
2. **Automatic Scope Classification**: AI-powered
3. **Real-time Calculations**: Via Climatiq API
4. **AI Copilot**: Context-aware recommendations
5. **Anomaly Detection**: Automatic flagging
6. **Comprehensive Reports**: PDF, Word, Excel export
7. **Target Tracking**: Set and monitor reduction goals
8. **Theme Support**: Light/Dark mode

## Support

### Check Logs:
**Backend logs**:
```bash
cd backend
uv run backend
# Logs appear in terminal
```

**Frontend logs**:
```bash
cd frontend
export PATH="../.nodeenv/Scripts:$PATH"
npm run dev
# Logs appear in terminal and browser console (F12)
```

### API Health Check:
- Backend: http://localhost:8000/health
- Frontend: Should redirect to /login if not authenticated

### Database:
- Location: `backend/decarbonization.db`
- View with: DB Browser for SQLite or any SQL tool
- Tables: users, projects, activities, batch_jobs, etc.

---

**Happy Testing!** 🚀

For issues or questions, check the logs or API documentation at http://localhost:8000/docs
