import type {
    User,
    Project,
    CreateProjectData,
    Activity,
    BatchJob,
    ProjectSummary,
    AuthResponse,
    RegisterData,
    UploadResponse,
} from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

class ApiClient {
    private token: string | null = null;

    setToken(token: string) {
        this.token = token;
        if (typeof window !== "undefined") {
            localStorage.setItem("token", token);
        }
    }

    getToken(): string | null {
        if (this.token) return this.token;
        if (typeof window !== "undefined") {
            return localStorage.getItem("token");
        }
        return null;
    }

    clearToken() {
        this.token = null;
        if (typeof window !== "undefined") {
            localStorage.removeItem("token");
        }
    }

    isAuthenticated(): boolean {
        return !!this.getToken();
    }

    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const token = this.getToken();
        const headers: HeadersInit = {
            "Content-Type": "application/json",
            ...options.headers,
        };

        if (token) {
            (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_URL}${endpoint}`, {
            ...options,
            headers,
        });

        if (response.status === 401) {
            this.clearToken();
            if (typeof window !== "undefined") {
                window.location.href = "/login";
            }
            throw new Error("Unauthorized");
        }

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: "API Error" }));
            throw new Error(error.detail || "API Error");
        }

        // Handle empty responses (like DELETE)
        const text = await response.text();
        if (!text) {
            return {} as T;
        }
        return JSON.parse(text);
    }

    // Auth endpoints
    async register(data: RegisterData): Promise<User> {
        return this.request<User>("/auth/register", {
            method: "POST",
            body: JSON.stringify(data),
        });
    }

    async login(email: string, password: string): Promise<AuthResponse> {
        const response = await this.request<AuthResponse>("/auth/login", {
            method: "POST",
            body: JSON.stringify({ email, password }),
        });
        this.setToken(response.access_token);
        return response;
    }

    async getMe(): Promise<User> {
        return this.request<User>("/auth/me");
    }

    logout() {
        this.clearToken();
        if (typeof window !== "undefined") {
            window.location.href = "/login";
        }
    }

    // Project endpoints
    async getProjects(): Promise<Project[]> {
        return this.request<Project[]>("/projects/");
    }

    async createProject(data: CreateProjectData): Promise<Project> {
        return this.request<Project>("/projects/", {
            method: "POST",
            body: JSON.stringify(data),
        });
    }

    async getProject(id: string): Promise<Project> {
        return this.request<Project>(`/projects/${id}`);
    }

    // Upload endpoints
    async uploadCSV(projectId: string, file: File): Promise<UploadResponse> {
        const token = this.getToken();
        const formData = new FormData();
        formData.append("file", file);
        formData.append("project_id", projectId);

        const response = await fetch(`${API_URL}/upload/csv`, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${token}`,
            },
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: "Upload failed" }));
            throw new Error(error.detail || "Upload failed");
        }

        return response.json();
    }

    // Batch Job endpoints
    async getBatchJobs(): Promise<BatchJob[]> {
        return this.request<BatchJob[]>("/batch/jobs");
    }

    async getBatchJob(id: string): Promise<BatchJob> {
        return this.request<BatchJob>(`/batch/jobs/${id}`);
    }

    // Activity endpoints
    async getActivities(projectId: string): Promise<Activity[]> {
        return this.request<Activity[]>(`/activities/?project_id=${projectId}`);
    }

    async getProjectSummary(projectId: string): Promise<ProjectSummary> {
        return this.request<ProjectSummary>(`/activities/project/${projectId}/summary`);
    }

    async deleteActivity(id: string): Promise<void> {
        await this.request(`/activities/${id}`, { method: "DELETE" });
    }

    // Report endpoints
    async downloadReport(projectId: string, config?: any): Promise<Blob> {
        // Backend now expects POST with optional configuration
        const token = this.getToken();
        const response = await fetch(`${API_URL}/projects/${projectId}/report`, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
            },
            body: JSON.stringify(config || { format_type: "standard" }),
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: "Report generation failed" }));
            throw new Error(error.detail || "Report generation failed");
        }

        return response.blob();
    }

    async getReportSummary(projectId: string): Promise<any> {
        return this.request<any>(`/projects/${projectId}/report-summary`);
    }

    async getAvailableReportColumns(projectId: string): Promise<any> {
        return this.request<any>(`/projects/${projectId}/report/available-columns`);
    }
}

export const api = new ApiClient();
