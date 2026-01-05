// User & Organization
export interface User {
    id: string;
    email: string;
    full_name: string;
    organization_id: string;
    organization?: Organization;
    created_at: string;
}

export interface Organization {
    id: string;
    name: string;
}

// Project
export interface Project {
    id: string;
    name: string;
    description?: string;
    start_date?: string;
    end_date?: string;
    reporting_year: number;
    organization_id: string;
    created_at: string;
}

export interface CreateProjectData {
    name: string;
    description?: string;
    start_date: string;
    end_date: string;
    reporting_year: string;
}

// Activity
export interface Activity {
    id: string;
    activity_type: ActivityType;
    scope: Scope;
    co2e_kg: number;
    co2e_unit: string;
    region: string;
    activity_date?: string;
    input_data: {
        description: string;
        amount: number;
        unit: string;
        unit_type?: string;
    };
    created_at: string;
}

export type Scope = "Scope 1" | "Scope 2" | "Scope 3";

export type ActivityType =
    | "electricity"
    | "stationary_combustion"
    | "mobile_combustion"
    | "business_travel"
    | "employee_commuting"
    | "purchased_goods"
    | "waste";

// Batch Job
export interface BatchJob {
    id: string;
    status: "pending" | "processing" | "completed" | "failed";
    file_name: string;
    total_records: number;
    processed_records: number;
    successful_records: number;
    failed_records: number;
    error_message?: string;
    created_at: string;
    completed_at?: string;
}

// Project Summary
export interface ProjectSummary {
    project_id: string;
    total_activities: number;
    total_co2e_kg: number;
    scope_breakdown: Record<Scope, number>;
    activity_type_breakdown: Record<string, number>;
}

// Auth
export interface AuthResponse {
    access_token: string;
    token_type: string;
}

export interface RegisterData {
    email: string;
    password: string;
    full_name: string;
    organization_name: string;
}

export interface LoginData {
    email: string;
    password: string;
}

// Upload
export interface UploadResponse {
    message: string;
    job_id: string;
    total_records: number;
    file_name: string;
}
