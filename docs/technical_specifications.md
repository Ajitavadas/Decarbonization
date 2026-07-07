# Decarbonization Platform - Technical Specifications

## System Overview

The Decarbonization Platform is built on a modern web architecture with React/Next.js frontend and FastAPI backend, providing a comprehensive solution for carbon footprint management.

## Data Import System

### CSV Upload Format Requirements

#### Required Columns:
- `description`: Activity description (text)
- `amount`: Numerical value (number)
- `unit`: Measurement unit (text)
- `category`: Emission category (text)
- `supplier_name`: Provider name (text)
- `region`: Geographic region (text)
- `activity_date`: Date in YYYY-MM-DD format (date)
- `year`: Reporting year (number)

#### Data Validation:
1. All required columns must be present
2. Amount must be numeric and positive
3. Date format must be valid (YYYY-MM-DD)
4. Unit must be a recognized measurement type
5. Category must match predefined emission categories

### File Processing Pipeline:
1. **Upload**: CSV file received via HTTP POST
2. **Validation**: Schema and data integrity checks
3. **Transformation**: Data mapping to internal format
4. **Storage**: Database insertion with metadata
5. **Processing**: Emission calculations and categorization
6. **Notification**: Success/failure feedback to user

## Architecture Components

### Frontend (React/Next.js)
- **DashboardShell**: Main application layout with sidebar, header, and copilot
- **ArchetypeOnboarding**: User onboarding modal for industry role selection
- **CarbonCopilot**: AI assistant panel
- **Data Upload Interface**: CSV upload component
- **Visualization Components**: Charts, graphs, and dashboards

### Backend (FastAPI)
- **Data Management API**: Endpoints for data import and retrieval
- **User Management**: Authentication and user preference handling
- **Emission Calculation Engine**: Core logic for carbon footprint calculations
- **Reporting Service**: Dashboard and report generation
- **Database Layer**: PostgreSQL storage with proper indexing

## Onboarding System Architecture

### ArchetypeOnboarding Component
- **Role Selection**: Industry archetype picker (Energy, Manufacturing, etc.)
- **Preference Setup**: Dashboard customization options
- **Completion Flow**: Progress tracking and final confirmation
- **State Management**: React hooks for modal state handling

### Integration Points:
1. **DashboardShell Prop**: `showArchetypeOnboarding` boolean flag
2. **Event Handlers**: Completion callbacks for seamless transition
3. **User Context**: Persists user preferences for future sessions

## API Endpoints

### Data Import Endpoints:
- `POST /api/data/upload` - Upload CSV file
- `GET /api/data/status/{upload_id}` - Check upload status
- `GET /api/data/list` - List uploaded data sets

### User Management:
- `POST /api/users/onboard` - Complete onboarding process
- `GET /api/users/preferences` - Get user preferences
- `PUT /api/users/preferences` - Update user preferences

## Data Flow Diagram

```
User → Upload CSV File → API Validation → Data Processing → Database Storage → Dashboard Visualization
     ↑                                                    ↓
   Onboarding System ← Role Selection → Preference Setup ← User Context
```

## Performance Metrics

### Typical Response Times:
- CSV Upload: < 5 seconds for 20-row file
- Data Processing: < 2 seconds per row
- Dashboard Load: < 3 seconds
- API Endpoints: < 1 second

### Scalability:
- Supports files up to 10,000 rows
- Handles concurrent users
- Optimized database queries
- Caching for frequently accessed data

## Security Considerations

### Data Protection:
- HTTPS encryption for all communications
- Secure file upload handling
- User authentication and authorization
- Data anonymization options

### Access Control:
- Role-based permissions
- Data isolation between organizations
- Audit logging for all activities
- GDPR compliance measures

## Testing Framework

### Unit Tests:
- Component testing with React Testing Library
- API endpoint validation
- Data processing logic verification

### Integration Tests:
- End-to-end data upload flow
- Onboarding system functionality
- Database interaction validation

### Performance Tests:
- Load testing for concurrent users
- CSV processing speed benchmarks
- Memory usage monitoring

## Deployment Requirements

### Infrastructure:
- Node.js 18+ (frontend)
- Python 3.9+ (backend)
- PostgreSQL 13+
- Redis (for caching)

### Environment Variables:
- DATABASE_URL: PostgreSQL connection string
- SECRET_KEY: Application secret for authentication
- UPLOAD_PATH: Local storage path for uploaded files
- API_BASE_URL: Backend API endpoint

## Future Enhancements

1. **Multi-language Support**: Internationalization capabilities
2. **Advanced Analytics**: Machine learning-based insights
3. **Integration APIs**: Direct integration with accounting systems
4. **Mobile App**: Native mobile application
5. **Carbon Credit Marketplace**: Integration with carbon credit platforms

## Support & Maintenance

### Documentation:
- Complete API documentation (Swagger UI)
- User guides and tutorials
- Developer documentation
- Troubleshooting guides

### Monitoring:
- Application performance monitoring
- Error tracking and reporting
- User activity analytics
- System health checks

This technical specification provides a comprehensive overview of the Decarbonization Platform's architecture, functionality, and implementation details for ClimateIQ GTM team evaluation.