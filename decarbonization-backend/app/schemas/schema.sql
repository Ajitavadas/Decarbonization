-- =============================================================================
-- MASTER DATABASE SCHEMA: AUTONOMOUS DECARBONIZATION PLATFORM
-- Carbon Emissions Accounting + Calculation System
-- 
-- Data Sources: EPA Hub 2025, IPCC EFDB, Open CEDA 2025, Climatiq API
-- Compliance: GHG Protocol, CSRD, SEC, SECR, NGER
-- Last Updated: December 17, 2025
-- =============================================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- MULTI-TENANT INFRASTRUCTURE
-- =============================================================================

CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_name VARCHAR(255) UNIQUE NOT NULL,
    industry VARCHAR(10), -- NAICS code
    countries TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    headcount INTEGER,
    annual_revenue DECIMAL(15, 2),
    is_public_company BOOLEAN DEFAULT FALSE,
    listing_status VARCHAR(50) CHECK (listing_status IN ('public', 'private', 'subsidiary')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT org_unique UNIQUE (organization_name)
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(512),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) CHECK (role IN ('admin', 'auditor', 'analyst', 'viewer')),
    permissions JSONB,
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_org_email UNIQUE (organization_id, email)
);

CREATE TABLE regulatory_requirements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    csrd_applicable BOOLEAN DEFAULT FALSE,
    sec_applicable BOOLEAN DEFAULT FALSE,
    secr_applicable BOOLEAN DEFAULT FALSE,
    nger_applicable BOOLEAN DEFAULT FALSE,
    ghg_protocol_applicable BOOLEAN DEFAULT TRUE,
    scope_1_mandatory BOOLEAN DEFAULT FALSE,
    scope_2_mandatory BOOLEAN DEFAULT FALSE,
    scope_3_mandatory BOOLEAN DEFAULT FALSE,
    scope_3_priority_categories TEXT[] DEFAULT ARRAY[]::TEXT[],
    materiality_threshold DECIMAL(10, 2),
    assurance_level VARCHAR(50) CHECK (assurance_level IN ('limited', 'reasonable')),
    first_reporting_year INTEGER,
    reporting_deadline DATE,
    assessed_at TIMESTAMP WITH TIME ZONE,
    assessed_by UUID REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- EMISSION FACTORS DATABASE (110k+ records merged from EPA, IPCC, Open CEDA)
-- =============================================================================

CREATE TABLE emission_factors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    activity_id VARCHAR(255) UNIQUE NOT NULL,
    name TEXT NOT NULL,
    region VARCHAR(20) NOT NULL,
    region_name VARCHAR(255),
    country_name VARCHAR(255),
    year INTEGER NOT NULL,
    scope VARCHAR(20) NOT NULL CHECK (scope IN ('Scope 1', 'Scope 2', 'Scope 3')),
    sector VARCHAR(100),
    category VARCHAR(255),
    industry_code VARCHAR(10),
    
    -- Factor values (separate components for granularity)
    factor_value NUMERIC(12, 8) NOT NULL,
    factor_value_co2 NUMERIC(12, 8),
    factor_value_ch4 NUMERIC(12, 8),
    factor_value_n2o NUMERIC(12, 8),
    
    -- Units
    activity_unit VARCHAR(50) NOT NULL,
    emissions_unit VARCHAR(50),
    emissions_type VARCHAR(100),
    
    -- Method
    calculation_method VARCHAR(100),
    ghg_protocol_method VARCHAR(100),
    gwp_version VARCHAR(50),
    
    -- Quality
    uncertainty NUMERIC(5, 2),
    data_quality_score NUMERIC(3, 2),
    confidence_score NUMERIC(3, 2),
    data_quality_flags TEXT[],
    
    -- Source traceability (CRITICAL for CSRD compliance)
    source VARCHAR(100) NOT NULL,
    source_dataset VARCHAR(255),
    source_link TEXT,
    source_document_reference VARCHAR(255),
    source_citation TEXT,
    
    -- Status
    notes TEXT,
    is_preferred BOOLEAN DEFAULT FALSE,
    replacement_factor_id UUID,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES users(id),
    data_source_version VARCHAR(50)
);

CREATE INDEX idx_ef_activity_id ON emission_factors(activity_id);
CREATE INDEX idx_ef_region_year ON emission_factors(region, year);
CREATE INDEX idx_ef_scope ON emission_factors(scope);
CREATE INDEX idx_ef_source ON emission_factors(source);

-- =============================================================================
-- BUSINESS DATA LAYER
-- =============================================================================

CREATE TABLE emission_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    source_name VARCHAR(255) NOT NULL,
    source_code VARCHAR(100) UNIQUE,
    scope VARCHAR(20) NOT NULL CHECK (scope IN ('Scope 1', 'Scope 2', 'Scope 3')),
    scope_3_category VARCHAR(20),
    category VARCHAR(255),
    sector VARCHAR(100),
    unit VARCHAR(50),
    frequency VARCHAR(50),
    expected_annual_volume DECIMAL(15, 2),
    owner_id UUID REFERENCES users(id),
    owner_department VARCHAR(100),
    is_mandatory BOOLEAN DEFAULT FALSE,
    mandatory_frameworks TEXT[] DEFAULT ARRAY[]::TEXT[],
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'deprecated')),
    data_completeness_pct NUMERIC(5, 2) DEFAULT 0,
    description TEXT,
    calculation_method VARCHAR(100),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES users(id),
    
    CONSTRAINT unique_org_source_code UNIQUE (organization_id, source_code)
);

CREATE INDEX idx_es_org_scope ON emission_sources(organization_id, scope);

CREATE TABLE required_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    emission_source_id UUID NOT NULL REFERENCES emission_sources(id) ON DELETE CASCADE,
    document_type VARCHAR(100),
    document_description TEXT,
    required_by_frameworks TEXT[] DEFAULT ARRAY[]::TEXT[],
    scope VARCHAR(20),
    frequency VARCHAR(50),
    expected_count INTEGER,
    documents_uploaded INTEGER DEFAULT 0,
    upload_deadline DATE,
    is_complete BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- =============================================================================
-- UNIT CONVERSIONS (Normalization to canonical units)
-- =============================================================================

CREATE TABLE unit_conversions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_unit VARCHAR(50) NOT NULL,
    source_category VARCHAR(100),
    target_unit VARCHAR(50) NOT NULL,
    conversion_factor NUMERIC(15, 8) NOT NULL,
    conversion_formula TEXT,
    reference_source VARCHAR(100),
    reference_year INTEGER,
    uncertainty NUMERIC(5, 2),
    data_quality_score NUMERIC(3, 2),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Insert common unit conversions
INSERT INTO unit_conversions (source_unit, source_category, target_unit, conversion_factor, reference_source, reference_year) VALUES
('gallon', 'volume', 'liter', 3.78541, 'SI Standard', 2025),
('pound', 'mass', 'kg', 0.453592, 'SI Standard', 2025),
('MWh', 'energy', 'kWh', 1000, 'SI Standard', 2025),
('BTU', 'energy', 'MJ', 0.001055, 'SI Standard', 2025),
('mile', 'distance', 'km', 1.60934, 'SI Standard', 2025),
('short ton', 'mass', 'kg', 907.185, 'SI Standard', 2025),
('metric ton', 'mass', 'kg', 1000, 'SI Standard', 2025);

-- =============================================================================
-- PHASE 1: ACTIVITY CLASSIFICATION
-- =============================================================================

CREATE TABLE emission_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    emission_source_id UUID NOT NULL REFERENCES emission_sources(id) ON DELETE RESTRICT,
    activity_date DATE NOT NULL,
    
    -- Raw activity data
    activity_value DECIMAL(15, 2) NOT NULL,
    activity_unit_raw VARCHAR(50),
    activity_unit_normalized VARCHAR(50) NOT NULL,
    activity_value_normalized DECIMAL(15, 2) NOT NULL,
    
    -- Data source
    source_type VARCHAR(50) CHECK (source_type IN ('primary_supplier', 'secondary_benchmark', 'estimated')),
    source_document_id UUID,
    source_document_reference VARCHAR(255),
    
    -- Classification
    scope VARCHAR(20) CHECK (scope IN ('Scope 1', 'Scope 2', 'Scope 3')),
    scope_3_category VARCHAR(20),
    
    -- Matching
    activity_id_matched VARCHAR(255) REFERENCES emission_factors(activity_id),
    activity_id_confidence NUMERIC(3, 2),
    
    -- Quality
    confidence_score NUMERIC(3, 2),
    flag_data_quality BOOLEAN DEFAULT FALSE,
    quality_notes TEXT,
    
    -- Audit
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by_user_id UUID REFERENCES users(id),
    data_collection_date DATE,
    data_entry_date DATE DEFAULT CURRENT_DATE,
    entered_by_user_id UUID REFERENCES users(id),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_ee_org_date ON emission_events(organization_id, activity_date);
CREATE INDEX idx_ee_source ON emission_events(emission_source_id);
CREATE INDEX idx_ee_scope ON emission_events(scope);

CREATE TABLE scope_classification_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_name VARCHAR(255),
    rule_priority INTEGER,
    condition_activity_type VARCHAR(100),
    condition_sector VARCHAR(100),
    condition_ownership VARCHAR(50),
    assigned_scope VARCHAR(20) NOT NULL,
    assigned_scope_3_category VARCHAR(20),
    framework_applicability TEXT[] DEFAULT ARRAY[]::TEXT[],
    reasoning TEXT,
    examples TEXT[],
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- =============================================================================
-- PHASE 2: EMISSION CALCULATION
-- =============================================================================

CREATE TABLE calculation_ledger (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    batch_id VARCHAR(100),
    calculation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Input
    emission_event_id UUID NOT NULL REFERENCES emission_events(id) ON DELETE RESTRICT,
    activity_value NUMERIC(15, 2),
    activity_unit_normalized VARCHAR(50),
    
    -- Factor used
    emission_factor_id UUID NOT NULL REFERENCES emission_factors(id),
    emission_factor_value NUMERIC(12, 8),
    emission_factor_source VARCHAR(100),
    emission_factor_dataset VARCHAR(255),
    emission_factor_region VARCHAR(10),
    emission_factor_year INTEGER,
    emission_factor_method VARCHAR(100),
    factor_uncertainty NUMERIC(5, 2),
    factor_data_quality NUMERIC(3, 2),
    
    -- Calculation
    calculation_method VARCHAR(100),
    calculation_formula TEXT,
    gwp_version VARCHAR(50) DEFAULT 'AR5',
    gwp_ch4 NUMERIC(5, 2) DEFAULT 28,
    gwp_n2o NUMERIC(5, 2) DEFAULT 265,
    
    -- RESULTS (kg CO2e)
    result_kg_co2e DECIMAL(15, 2),
    result_kg_co2 DECIMAL(15, 2),
    result_kg_ch4 DECIMAL(15, 2),
    result_kg_n2o DECIMAL(15, 2),
    result_kg_total DECIMAL(15, 2),
    
    -- Quality
    overall_confidence NUMERIC(3, 2),
    quality_flags TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- Fallback tracking
    fell_back_to_climatiq BOOLEAN DEFAULT FALSE,
    climatiq_request_id VARCHAR(255),
    climatiq_factor_source VARCHAR(255),
    
    -- Audit
    calculated_by_user_id UUID REFERENCES users(id),
    calculated_by_agent_name VARCHAR(100),
    calculation_notes TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by_user_id UUID REFERENCES users(id),
    was_corrected BOOLEAN DEFAULT FALSE,
    correction_reason TEXT,
    original_result_id UUID
);

CREATE INDEX idx_cl_org_timestamp ON calculation_ledger(organization_id, calculation_timestamp);
CREATE INDEX idx_cl_batch ON calculation_ledger(batch_id);

CREATE TABLE conversion_factors_gwp (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gas_name VARCHAR(100),
    chemical_formula VARCHAR(50),
    gwp_ar4_100yr NUMERIC(8, 2),
    gwp_ar5_100yr NUMERIC(8, 2),
    gwp_ar6_100yr NUMERIC(8, 2),
    ipcc_assessment_report VARCHAR(20),
    year_published INTEGER,
    notes TEXT
);

-- Insert GWP values (AR5 with 100-year horizon)
INSERT INTO conversion_factors_gwp (gas_name, chemical_formula, gwp_ar4_100yr, gwp_ar5_100yr, ipcc_assessment_report, year_published) VALUES
('Methane', 'CH4', 25, 28, 'AR5', 2013),
('Nitrous Oxide', 'N2O', 298, 265, 'AR5', 2013),
('Carbon Dioxide', 'CO2', 1, 1, 'AR5', 2013);

CREATE TABLE emission_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    reporting_period_start DATE NOT NULL,
    reporting_period_end DATE NOT NULL,
    aggregation_level VARCHAR(50),
    aggregation_id VARCHAR(255),
    
    -- Results by scope
    scope_1_total_kg_co2e DECIMAL(15, 2) DEFAULT 0,
    scope_2_total_kg_co2e DECIMAL(15, 2) DEFAULT 0,
    scope_3_total_kg_co2e DECIMAL(15, 2) DEFAULT 0,
    scope_3_by_category JSONB,
    
    -- Breakdown
    total_co2_kg DECIMAL(15, 2),
    total_ch4_kg DECIMAL(15, 2),
    total_n2o_kg DECIMAL(15, 2),
    total_co2e_kg DECIMAL(15, 2),
    
    -- Quality metrics
    data_completeness_pct NUMERIC(5, 2),
    estimated_pct NUMERIC(5, 2),
    weighted_confidence NUMERIC(3, 2),
    
    -- Metadata
    number_of_events INTEGER,
    calculation_method_used VARCHAR(100),
    gwp_version_used VARCHAR(50),
    frameworks_reported TEXT[],
    assurance_level VARCHAR(50),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    calculated_by_agent_name VARCHAR(100)
);

-- =============================================================================
-- PHASE 3: AUDIT & COMPLIANCE
-- =============================================================================

CREATE TABLE audit_trail (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    action_type VARCHAR(100),
    resource_type VARCHAR(100),
    resource_id UUID,
    actor_user_id UUID NOT NULL REFERENCES users(id),
    actor_role VARCHAR(50),
    old_values JSONB,
    new_values JSONB,
    change_reason TEXT,
    action_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_compliance_critical BOOLEAN DEFAULT FALSE,
    compliance_reference VARCHAR(255)
);

CREATE INDEX idx_audit_org_timestamp ON audit_trail(organization_id, action_timestamp);
CREATE INDEX idx_audit_resource ON audit_trail(resource_type, resource_id);

CREATE TABLE quality_flags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    flag_type VARCHAR(100),
    severity VARCHAR(50) CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    target_type VARCHAR(100),
    target_id UUID,
    flag_description TEXT,
    resolution_required BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT,
    flag_created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    flag_resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by_user_id UUID REFERENCES users(id),
    estimated_co2e_impact DECIMAL(15, 2),
    percentage_of_total NUMERIC(5, 2)
);

CREATE TABLE compliance_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    report_type VARCHAR(100),
    reporting_period_start DATE,
    reporting_period_end DATE,
    report_title TEXT,
    executive_summary TEXT,
    detailed_breakdown JSONB,
    includes_scope_1 BOOLEAN,
    includes_scope_2 BOOLEAN,
    includes_scope_3 BOOLEAN,
    scope_3_categories_included TEXT[],
    gwp_version_used VARCHAR(50),
    assurance_level VARCHAR(50),
    assurance_provider VARCHAR(255),
    prepared_by_user_id UUID REFERENCES users(id),
    prepared_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    reviewed_by_user_id UUID REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    export_formats TEXT[] DEFAULT ARRAY[]::TEXT[],
    export_file_paths JSONB,
    report_version INTEGER DEFAULT 1,
    is_final BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- =============================================================================
-- SUPPORTING TABLES
-- =============================================================================

CREATE TABLE uploaded_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    emission_source_id UUID REFERENCES emission_sources(id),
    file_name VARCHAR(255),
    file_type VARCHAR(50),
    file_size_bytes INTEGER,
    file_hash VARCHAR(256),
    storage_path TEXT,
    storage_provider VARCHAR(50),
    extracted_data JSONB,
    extraction_confidence NUMERIC(3, 2),
    uploaded_by_user_id UUID NOT NULL REFERENCES users(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(50) DEFAULT 'pending',
    processing_error_message TEXT
);

CREATE TABLE climatiq_api_fallback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    request_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    emission_event_id UUID REFERENCES emission_events(id),
    calculation_ledger_id UUID REFERENCES calculation_ledger(id),
    request_region VARCHAR(10),
    request_activity_type VARCHAR(255),
    request_unit VARCHAR(50),
    request_value DECIMAL(15, 2),
    response_factor DECIMAL(12, 8),
    response_uncertainty NUMERIC(5, 2),
    response_dataset VARCHAR(255),
    request_status VARCHAR(50),
    api_latency_ms INTEGER,
    fallback_reason VARCHAR(255),
    local_factor_attempted_id UUID REFERENCES emission_factors(id)
);

CREATE TABLE api_credentials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    api_provider VARCHAR(100),
    api_name VARCHAR(100),
    api_key_encrypted VARCHAR(512),
    api_secret_encrypted VARCHAR(512),
    monthly_calls_limit INTEGER,
    monthly_calls_used INTEGER DEFAULT 0,
    rate_limit_per_minute INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    last_tested_at TIMESTAMP WITH TIME ZONE,
    test_status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    rotated_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_by_user_id UUID REFERENCES users(id),
    managed_by_user_id UUID REFERENCES users(id)
);

-- =============================================================================
-- GRANT PERMISSIONS (for application user)
-- =============================================================================

-- Create application user (adjust as needed)
-- CREATE USER app_user WITH PASSWORD 'secure_password';
-- GRANT CONNECT ON DATABASE carbon_platform TO app_user;
-- GRANT USAGE ON SCHEMA public TO app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- =============================================================================
-- END OF SCHEMA
-- =============================================================================
