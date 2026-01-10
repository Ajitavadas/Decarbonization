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

// Activity - matches backend EmissionActivityResponse
export interface ClimatiqEmissionFactor {
    id: string;
    name: string;
    activity_id: string;
    source: string;
    source_dataset: string;
    region: string;
    year: number;
    category?: string;
}

export interface ClimatiqActivityData {
    activity_value: number;
    activity_unit: string;
}

export interface ClimatiqEstimate {
    co2e: number;
    co2e_unit: string;
    emission_factor?: ClimatiqEmissionFactor;
    activity_data?: ClimatiqActivityData;
}

export interface ClimatiqAutopilotResponse {
    estimate?: ClimatiqEstimate;
}

export interface ActivityInputData {
    unit?: string;
    amount?: number;
    unit_type?: string;
    description?: string;
    autopilot_response?: ClimatiqAutopilotResponse;
}

export interface Activity {
    id: string;
    project_id: string;
    activity_type: ActivityType;
    sub_type?: string;
    scope: Scope;
    co2e_kg: number | string;  // Backend returns as string
    co2e_unit: string;
    calculation_method?: string;
    emission_factor_id?: string;
    source_dataset?: string;
    region?: string;
    year?: string;
    activity_date?: string;
    description?: string;  // At top level, not in input_data
    input_data?: ActivityInputData;  // Full Climatiq response with emission factor info
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

// Audit / Anomalies
export type FlagType = "gap" | "anomaly" | "archetype_mismatch";
export type Severity = "info" | "warning" | "critical";
export type FindingStatus = "open" | "acknowledged" | "resolved" | "false_positive";

export interface AuditFinding {
    id: string;
    flag_type: FlagType;
    severity: Severity;
    rule_id: string;
    title: string;
    description?: string;
    recommendation?: string;
    evidence?: Record<string, unknown>;
    status: FindingStatus;
    project_id?: string;
    activity_id?: string;
    created_at?: string;
    resolved_at?: string;
    resolution_notes?: string;
}

export interface AuditSummary {
    total_findings: number;
    by_status: Record<string, number>;
    by_severity: Record<string, number>;
    by_type: Record<string, number>;
    open_critical: number;
}

export interface AuditRunRequest {
    project_id?: string;
    include_ai_analysis?: boolean;
}

export interface AuditRunResponse {
    audit_run_id: string;
    organization_id: string;
    project_id?: string;
    archetype?: string;
    started_at: string;
    completed_at: string;
    duration_seconds: number;
    summary: {
        total_findings: number;
        gap_findings: number;
        anomaly_findings: number;
        ai_findings: number;
        critical_count: number;
        warning_count: number;
        info_count: number;
    };
    findings: AuditFinding[];
    persisted_count: number;
}

export interface FindingsResponse {
    findings: AuditFinding[];
    total: number;
    limit: number;
    offset: number;
}

