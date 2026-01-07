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

    // Audit endpoints
    async runAudit(data?: { project_id?: string; include_ai_analysis?: boolean }): Promise<import("@/types").AuditRunResponse> {
        return this.request<import("@/types").AuditRunResponse>("/audit/run", {
            method: "POST",
            body: JSON.stringify(data || { include_ai_analysis: true }),
        });
    }

    async getAuditFindings(params?: {
        status?: string;
        flag_type?: string;
        severity?: string;
        limit?: number;
        offset?: number;
    }): Promise<import("@/types").FindingsResponse> {
        const searchParams = new URLSearchParams();
        if (params?.status) searchParams.append("status", params.status);
        if (params?.flag_type) searchParams.append("flag_type", params.flag_type);
        if (params?.severity) searchParams.append("severity", params.severity);
        if (params?.limit) searchParams.append("limit", params.limit.toString());
        if (params?.offset) searchParams.append("offset", params.offset.toString());

        const query = searchParams.toString();
        return this.request<import("@/types").FindingsResponse>(`/audit/findings${query ? `?${query}` : ""}`);
    }

    async getAuditSummary(): Promise<import("@/types").AuditSummary> {
        return this.request<import("@/types").AuditSummary>("/audit/summary");
    }

    async resolveFinding(id: string, status: string, notes?: string): Promise<{ id: string; status: string }> {
        return this.request<{ id: string; status: string }>(`/audit/findings/${id}/resolve`, {
            method: "PATCH",
            body: JSON.stringify({ status, notes }),
        });
    }

    // Organization endpoints
    async getMyOrganization(): Promise<{
        id: string;
        name: string;
        industry: string | null;
        country: string | null;
        emission_archetype: string | null;
        is_active: boolean;
    }> {
        return this.request("/organizations/me");
    }

    async getArchetypes(): Promise<{
        archetypes: Array<{
            id: string;
            name: string;
            icon: string;
            tagline: string;
            description: string;
            examples: string[];
            dominant_scope: string;
        }>;
    }> {
        return this.request("/organizations/archetypes");
    }

    async setOrganizationArchetype(archetype: string): Promise<{
        id: string;
        name: string;
        emission_archetype: string;
    }> {
        return this.request("/organizations/archetype", {
            method: "PATCH",
            body: JSON.stringify({ archetype }),
        });
    }
}

export const api = new ApiClient();

