const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

async function authenticatedFetch(endpoint: string, options: RequestInit = {}) {
    const token = localStorage.getItem('token');

    const headers = new Headers(options.headers || {});
    if (token) {
        headers.append('Authorization', `Bearer ${token}`);
    }

    const config = {
        ...options,
        headers: headers
    };

    const response = await fetch(`${API_URL}${endpoint}`, config);

    if (response.status === 401) {
        // Clear session and redirect to login
        localStorage.removeItem('token');
        if (typeof window !== 'undefined') {
            window.location.href = '/login';
        }
        throw new Error('Session expired');
    }

    return response;
}

export async function fetchDashboardData() {
    const response = await authenticatedFetch('/dashboard');
    if (!response.ok) throw new Error('Failed to fetch dashboard data');
    return response.json();
}

export async function fetchRecentActivity() {
    const response = await authenticatedFetch('/dashboard/activity');
    if (!response.ok) throw new Error("Failed to fetch activity");
    return response.json();
}

export async function fetchGaps() {
    const response = await authenticatedFetch('/dashboard/gaps');
    if (!response.ok) throw new Error("Failed to fetch gaps");
    return response.json();
}

export async function uploadCSV(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    // Note: Content-Type header for FormData is set automatically by fetch
    const response = await authenticatedFetch('/import/csv', {
        method: 'POST',
        body: formData
    });

    if (!response.ok) throw new Error('Failed to upload CSV');
    return response.json();
}

export async function getImportStatus(importId: string) {
    const response = await authenticatedFetch(`/import/csv/${importId}`);
    if (!response.ok) throw new Error('Failed to fetch import status');
    return response.json();
}

export async function sendCopilotQuery(query: string, sessionId: string = 'default') {
    const response = await authenticatedFetch('/copilot/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query, session_id: sessionId })
    });

    if (!response.ok) throw new Error('Failed to send copilot query');
    return response.json();
}

export async function login(credentials: any) {
    const response = await fetch(`${API_URL}/auth/token`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            email: credentials.email,
            password: credentials.password
        })
    });
    if (!response.ok) {
        const error = await response.json();
        const detail = typeof error.detail === 'string'
            ? error.detail
            : JSON.stringify(error.detail);
        throw new Error(detail || 'Operation failed');
    }
    return response.json();
}

export async function register(userData: any) {
    const response = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(userData)
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Registration failed');
    }
    return response.json();
}
