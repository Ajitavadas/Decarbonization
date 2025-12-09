// API Service Layer
class API {
    static async request(endpoint, options = {}) {
        const token = authService.getToken();

        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const config = {
            ...options,
            headers
        };

        try {
            const response = await fetch(buildUrl(endpoint), config);

            if (response.status === 401) {
                // Token expired, redirect to login
                authService.logout();
                return null;
            }

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'API request failed');
            }

            // Check if response has content
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }

            return response;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    static async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    static async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    static async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    static async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
}

// Dashboard API
class DashboardAPI {
    static async getOverview() {
        return API.get(CONFIG.ENDPOINTS.DASHBOARD);
    }

    static async getEmissions(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return API.get(`${CONFIG.ENDPOINTS.EMISSIONS}?${queryString}`);
    }

    static async getAnomalies() {
        return API.get(CONFIG.ENDPOINTS.ANOMALIES);
    }

    static async getForecast(monthsAhead = 12) {
        return API.get(`${CONFIG.ENDPOINTS.FORECAST}?months_ahead=${monthsAhead}`);
    }

    static async exportReport() {
        const token = authService.getToken();
        const response = await fetch(buildUrl(CONFIG.ENDPOINTS.REPORTS), {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Export failed');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `carbon-report-${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }
}

// Copilot API
class CopilotAPI {
    static async query(question) {
        return API.post(CONFIG.ENDPOINTS.COPILOT, { query: question });
    }
}

// Targets API
class TargetsAPI {
    static async getProgress() {
        return API.get(`${CONFIG.ENDPOINTS.TARGETS}/progress`);
    }

    static async createTarget(targetData) {
        return API.post(CONFIG.ENDPOINTS.TARGETS, targetData);
    }
}
