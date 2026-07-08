# Decarbonization Platform - User Guide

## Getting Started

### 1. Accessing the Platform
- Navigate to the platform URL
- Login with your credentials (or use demo account)
- Complete the onboarding process if this is your first visit

### 2. Onboarding Process
Upon first login, you'll see the ArchetypeOnboarding modal:

**Step 1: Role Selection**
- Choose your industry archetype from the dropdown:
  - Energy & Utilities
  - Manufacturing & Industrial
  - Transportation & Logistics
  - Services & Retail
  - Technology & IT
  - Agriculture & Food Production
  - Other

**Step 2: Dashboard Preferences**
- Customize your dashboard view
- Select which metrics are most important to you
- Set default time periods for analysis

**Step 3: Completion**
- Review your selections
- Click "Complete Onboarding" to proceed

## Data Upload Process

### 1. Navigate to Data Import
- Click on the "Data Upload" section in the main menu
- Select "Upload CSV File"

### 2. Prepare Your CSV File
Your file should contain these columns:
- description: Activity description (e.g., "Office electricity consumption")
- amount: Numerical value (e.g., 15200)
- unit: Measurement unit (e.g., "kWh")
- category: Emission category (e.g., "Electricity")
- supplier_name: Provider name (e.g., "Metro Power")
- region: Geographic region (e.g., "US")
- activity_date: Date in YYYY-MM-DD format (e.g., "2025-01-15")
- year: Reporting year (e.g., 2025)

### 3. Upload and Process
- Select your CSV file from local system
- Platform validates the file structure
- Data is processed and stored automatically
- View results in dashboard

## Using CarbonCopilot

The CarbonCopilot is available as a side panel:

### Features:
- **AI Assistance**: Get help with platform navigation
- **Insight Generation**: Automatic carbon footprint analysis
- **Recommendations**: Actionable suggestions for reduction
- **Quick Help**: Context-sensitive guidance

### How to Use:
1. Click the copilot icon in the sidebar
2. Type your question or request
3. Receive AI-generated responses and suggestions
4. Follow up with additional queries as needed

## Dashboard Navigation

### Main Sections:
- **Overview**: High-level carbon footprint summary
- **By Category**: Breakdown by emission categories
- **By Time**: Trend analysis over time
- **By Region**: Geographic distribution of emissions
- **Data Management**: View and manage uploaded data

### Customization Options:
- Change time periods for analysis
- Filter by category or region
- Export charts and reports
- Set up alerts for emission thresholds

## Sample Data Verification

The platform includes sample data in `tests/data/test_data_20_rows.csv` demonstrating:

### Data Structure:
- 20 rows of diverse emission activities
- Multiple categories (Electricity, Heating Fuel, Transportation)
- Various units (kWh, therms, gallons, miles)
- Geographic distribution (US, UK)
- Time-based activities across multiple months

### Testing Steps:
1. Upload the sample CSV file
2. Verify data appears in dashboard
3. Check that calculations are correct
4. Confirm onboarding system works properly

## Troubleshooting

### Common Issues:
1. **Upload Failures**: 
   - Ensure CSV format matches requirements
   - Check for special characters in column names
   - Verify all required columns are present

2. **Data Display Issues**:
   - Refresh the dashboard
   - Check date formats (YYYY-MM-DD)
   - Verify units are recognized by the system

3. **Onboarding Problems**:
   - Clear browser cache and cookies
   - Try incognito mode
   - Contact support if issues persist

## Support Resources

### Documentation:
- Full technical specifications in docs/technical_specifications.md
- Platform overview in docs/platform_overview.md

### Help Resources:
- CarbonCopilot for AI assistance
- Support team available via help desk
- Community forum for user questions

This guide provides all the information needed to start using the Decarbonization Platform effectively.