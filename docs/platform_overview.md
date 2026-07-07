# Decarbonization Platform - ClimateIQ GTM Team Documentation

## Executive Summary

The Decarbonization Platform is a comprehensive solution for organizations to measure, track, and reduce their carbon footprint. This platform provides:

- **Carbon Footprint Calculation**: Accurate measurement of emissions across multiple scopes
- **Data Management**: Centralized storage and management of emission data
- **Reporting & Analytics**: Comprehensive dashboards and reports for stakeholders
- **Onboarding System**: Guided user experience for new platform adoption

## Platform Features

### 1. Core Functionality
- **Emission Data Upload**: Support for CSV file uploads with standardized formats
- **Multi-Category Tracking**: Electricity, fuel, transportation, manufacturing, etc.
- **Geographic Scope**: Regional and global emissions tracking
- **Time-based Analysis**: Year-over-year comparisons and trend analysis

### 2. User Experience Features
- **Archetype Onboarding**: Role-based onboarding system for different industry types
- **CarbonCopilot**: AI assistant for platform navigation and guidance
- **Dashboard Customization**: Personalized views based on user roles
- **Interactive Visualizations**: Charts, graphs, and heatmaps for data interpretation

### 3. Data Management
- **CSV Import System**: Robust CSV upload with validation
- **Data Validation**: Automated checks for data consistency
- **Historical Tracking**: Multi-year emission trend analysis
- **Export Capabilities**: Data export in multiple formats

## Test Data Structure

The platform accepts CSV files with the following columns:

| Column Name | Description | Example |
|-------------|-------------|---------|
| `description` | Activity description | "Office electricity consumption - January" |
| `amount` | Quantity of activity | 15200 |
| `unit` | Measurement unit | "kWh" |
| `category` | Emission category | "Electricity" |
| `supplier_name` | Provider/organization name | "Metro Power" |
| `region` | Geographic region | "US" |
| `activity_date` | Date of activity | "2025-01-15" |
| `year` | Reporting year | 2025 |

## Implementation Details

### Data Upload Process
1. Users navigate to the data upload section
2. Select CSV file from local system
3. Platform validates file format and structure
4. Data is processed and stored in database
5. Users can view results in dashboard

### Onboarding System
- **Archetype Selection**: Users choose their industry role (Energy, Manufacturing, etc.)
- **Preferences Setup**: Dashboard customization options
- **Guided Tour**: Interactive walkthrough of platform features
- **Completion Confirmation**: Smooth transition to main dashboard

## Technical Architecture

### Frontend Components
- React/Next.js based interface
- Tailwind CSS for styling
- Responsive design for all devices
- Component-based architecture

### Backend Integration
- FastAPI/Python backend
- PostgreSQL database
- RESTful API endpoints
- Data processing pipelines

## ClimateIQ Integration Value

This platform provides significant value to ClimateIQ's GTM team by:

1. **Data Standardization**: Clean, structured data format for analysis
2. **Industry-Specific Insights**: Role-based categorization of emission sources
3. **Scalable Solution**: Handles both small and large enterprise data sets
4. **User Adoption**: Intuitive onboarding system reduces friction
5. **Comprehensive Reporting**: Multi-dimensional analytics capabilities

## Test Data Verification

The test file `test_upload_fresh.csv` contains 20 rows of sample emission data demonstrating:

- Multiple categories (Electricity, Heating Fuel, Transportation, etc.)
- Various units (kWh, therms, gallons, miles)
- Geographic distribution (US, UK)
- Time-based activities across multiple months
- Different activity types and suppliers

## Next Steps for ClimateIQ GTM Team

1. **Data Validation**: Verify test data structure against your standards
2. **Integration Testing**: Test CSV upload functionality with real data
3. **User Experience Review**: Evaluate onboarding system effectiveness
4. **Scalability Assessment**: Confirm platform handles enterprise-scale data
5. **Feature Discussion**: Explore customization options for specific use cases

## Support & Documentation

For technical support or questions about the platform, please contact:
- Platform Developer: [Your Name]
- Technical Documentation: docs/platform_overview.md
- API Endpoints: /api/docs (Swagger UI)