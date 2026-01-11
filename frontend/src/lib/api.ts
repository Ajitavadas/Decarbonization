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

    // Reduction Target endpoints
    async getTargets(activeOnly: boolean = true): Promise<ReductionTarget[]> {
        return this.request<ReductionTarget[]>(`/targets/?active_only=${activeOnly}`);
    }

    async getTarget(id: string): Promise<ReductionTarget> {
        return this.request<ReductionTarget>(`/targets/${id}`);
    }

    async createTarget(data: CreateTargetData): Promise<ReductionTarget> {
        return this.request<ReductionTarget>("/targets/", {
            method: "POST",
            body: JSON.stringify(data),
        });
    }

    async updateTarget(id: string, data: Partial<CreateTargetData>): Promise<ReductionTarget> {
        return this.request<ReductionTarget>(`/targets/${id}`, {
            method: "PUT",
            body: JSON.stringify(data),
        });
    }

    async deleteTarget(id: string): Promise<void> {
        await this.request(`/targets/${id}`, { method: "DELETE" });
    }

    async calculateTargetProgress(id: string): Promise<ReductionTarget> {
        return this.request<ReductionTarget>(`/targets/${id}/calculate-progress`, {
            method: "POST",
        });
    }

    // Strategy endpoints
    async getStrategies(targetId: string): Promise<ReductionStrategy[]> {
        return this.request<ReductionStrategy[]>(`/targets/${targetId}/strategies`);
    }

    async generateStrategies(targetId: string, forceRefresh: boolean = false): Promise<ReductionStrategy[]> {
        return this.request<ReductionStrategy[]>(`/targets/${targetId}/strategies/generate`, {
            method: "POST",
            body: JSON.stringify({ force_refresh: forceRefresh, max_strategies: 5 }),
        });
    }

    async updateStrategyStatus(strategyId: string, status: string): Promise<ReductionStrategy> {
        return this.request<ReductionStrategy>(`/targets/strategies/${strategyId}/status`, {
            method: "PATCH",
            body: JSON.stringify({ status }),
        });
    }

    // Copilot endpoints
    async chatWithCopilot(message: string, history: { role: string; content: string; source?: string }[] = [], includeLlm: boolean = true): Promise<CopilotChatResponse> {
        return this.request<CopilotChatResponse>("/copilot/chat", {
            method: "POST",
            body: JSON.stringify({
                message,
                history,
                include_llm: includeLlm
            }),
        });
    }

    async getCopilotQuickStats(): Promise<CopilotQuickStat[]> {
        return this.request<CopilotQuickStat[]>("/copilot/quick-stats");
    }

    async getTargetTrajectory(targetId: string): Promise<Record<string, unknown>> {
        return this.request<Record<string, unknown>>(`/targets/${targetId}/trajectory`);
    }

    async getSuggestedBaseline(year?: number, scope?: string): Promise<{ suggested_baseline: number; confidence: string; data_completeness: number }> {
        const params = new URLSearchParams();
        if (year) params.append("year", year.toString());
        if (scope) params.append("scope", scope);
        return this.request(`/targets/suggest-baseline?${params.toString()}`);
    }
}

// Type definitions for Reduction Targets
export interface ReductionTarget {
    id: string;
    name: string;
    description: string | null;
    target_type: "absolute" | "percentage";
    scope: string | null;
    baseline_year: string;
    baseline_value: number;
    target_year: string;
    target_value: number;
    milestones: Milestone[];
    current_year: string | null;
    current_value: number | null;
    current_reduction_pct: number | null;
    progress_percentage: number | null;
    status: "on_track" | "at_risk" | "off_track" | "achieved";
    is_active: boolean;
    created_at: string;
    last_calculated_at: string | null;
}

export interface Milestone {
    year: string;
    value: number;
    achieved: boolean;
    achieved_at?: string;
}

export interface CreateTargetData {
    name: string;
    description?: string;
    target_type: "absolute" | "percentage";
    scope?: string;
    baseline_year: string;
    baseline_value: number;
    target_year: string;
    target_value: number;
    milestones?: Milestone[];
    project_id?: string;
}

export interface ReductionStrategy {
    id: string;
    title: string;
    description: string;
    category: string;
    scope: string | null;
    difficulty: "easy" | "medium" | "hard" | null;
    priority: number;
    implementation_timeframe: string | null;
    estimated_reduction_pct: number | null;
    estimated_cost: number | null;
    estimated_savings: number | null;
    payback_period_months: number | null;
    source: "ai" | "manual";
    status: string;
    is_ai_generated: boolean;
    created_at: string;
}

// Copilot types
export interface CopilotChatRequest {
    message: string;
    history?: { role: string; content: string; source?: string }[];
    include_llm?: boolean;
}

export interface CopilotChatResponse {
    text: string;
    intent: string;
    data: Record<string, unknown>;
    source: "deterministic" | "llm" | "cache" | "error";
    model: string | null;
    suggestions: string[];
}

export interface CopilotQuickStat {
    label: string;
    value: string;
    change: string | null;
    trend: "positive" | "negative" | null;
}

export const api = new ApiClient();

