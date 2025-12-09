// Configuration
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000',
    API_VERSION: 'v1',
    ENDPOINTS: {
        AUTH: {
            LOGIN: '/auth/token',
            REGISTER: '/auth/register',
            ME: '/auth/me'
        },
        DASHBOARD: '/api/v1/dashboard',
        EMISSIONS: '/api/v1/emissions',
        TARGETS: '/api/v1/targets',
        COPILOT: '/api/v1/copilot/query',
        REPORTS: '/api/v1/reports/pdf',
        ANOMALIES: '/api/v1/anomalies',
        FORECAST: '/api/v1/forecast'
    },
    STORAGE_KEYS: {
        ACCESS_TOKEN: 'decarb_access_token',
        USER_DATA: 'decarb_user_data'
    }
};

// Helper to build full URL
function buildUrl(endpoint) {
    return CONFIG.API_BASE_URL + endpoint;
}
