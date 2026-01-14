"""
AI Prompt Templates for Enhanced Context-Aware Analysis

Contains:
- System instruction for all AI calls
- General anomaly analysis prompt template
- Archetype-specific strategy prompts (7 archetypes)
- Helper methods for prompt formatting
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


# ============================================================================
# SYSTEM INSTRUCTION (Used for all prompts)
# ============================================================================

SYSTEM_INSTRUCTION = """You are a technical sustainability copilot for a decarbonization platform.
Your job: (1) explain anomalies precisely and actionably; (2) produce ranked, regionally-aware reduction strategies tied to measurable metrics and timelines.

Always:
1) Reference available evidence (benchmarks, Climatiq EF metadata, regional context) where present
2) Provide estimated CO2 impact and confidence band (High/Medium/Low) for each suggestion
3) Provide next-best action (what to ask user, what to check in the system) and required data to improve confidence
4) Be specific to the organization's archetype, region, and actual emission data - avoid generic advice
5) For anomalies, classify as: (A) data quality issue, (B) operational anomaly, (C) seasonal variation, or (D) high-emission pattern needing mitigation"""


# ============================================================================
# ANOMALY ANALYSIS PROMPT TEMPLATE
# ============================================================================

ANOMALY_ANALYSIS_TEMPLATE = """ANOMALY ANALYSIS REQUEST
Organization: {org_name} (ID: {org_id})
Country / Region: {country} — Grid EF: {grid_ef} kgCO2e/kWh
Archetype: {archetype_display_name}
Industry: {industry}

Reporting period: {period_start} to {period_end}

AGGREGATES:
{aggregates_text}

TOP 10 CONTRIBUTORS:
{top_contributors_text}

SAMPLE ACTIVITIES (stratified selection: top emitters, recent, previously flagged):
{activities_text}

ACTIVE REDUCTION TARGETS:
{targets_text}

RECENT FLAG HISTORY (last 6):
{flags_text}

REGIONAL CONTEXT:
{regional_context_text}

ARCHETYPE EXPECTATIONS:
{archetype_context_text}

TASK:
1) For each SAMPLE ACTIVITY, classify as:
   (A) data quality problem - missing data, unit errors, calculation issues
   (B) operational efficiency anomaly - unusual patterns indicating inefficiency
   (C) expected seasonal variation - normal fluctuation for this archetype/region
   (D) high-emission pattern needing mitigation - correct data but actionable

2) For each positive finding (A/B/C/D), provide:
   - Concise explanation (2-3 sentences)
   - Required evidence to confirm (exact fields/invoices/sensor checks)
   - Probable CO2 impact if unresolved for 90 days (numeric estimate in kg)
   - Confidence level (H/M/L)
   - Recommended immediate action (one liner)
   - Recommended next action (3-6 week timeframe)

3) Provide a ranked list of top 3 actions that will move the organization's active reduction targets the most (tie to specific metrics)

OUTPUT FORMAT:
Return ONLY valid JSON with this structure:
{{
    "findings": [
        {{
            "activity_id": "uuid",
            "verdict": "A|B|C|D",
            "explanation": "string",
            "required_evidence": ["check item 1", "check item 2"],
            "co2e_90d_est_kg": number,
            "confidence": "H|M|L",
            "immediate_action": "string",
            "next_action": "string"
        }}
    ],
    "top_actions": [
        {{
            "action": "string",
            "estimated_annual_co2e_reduction_kg": number,
            "confidence": "H|M|L",
            "effort_estimate": "low|medium|high",
            "target_impacted": "target name or null"
        }}
    ],
    "overall_assessment": "Brief 2-3 sentence overall data quality and efficiency assessment"
}}"""


# ============================================================================
# ARCHETYPE-SPECIFIC STRATEGY PROMPTS
# ============================================================================

@dataclass
class ArchetypePromptConfig:
    """Configuration for archetype-specific prompts"""
    name: str
    display_name: str
    context_specific_fields: str
    key_kpis: str
    anomaly_detection_rules: str
    quick_audit_checklist: str


ARCHETYPE_STRATEGY_CONFIGS: Dict[str, ArchetypePromptConfig] = {
    "digital_service": ArchetypePromptConfig(
        name="digital_service",
        display_name="Digital Service (Tech / Finance / SaaS)",
        context_specific_fields="""
- Cloud infrastructure: data center locations, estimated cloud spend and vCPU usage
- Office footprint: area sqm, headcount, remote work percentage
- Business travel: annual travel km by mode (air, rail, road)
- Equipment: laptop/device count, refresh cycles""",
        key_kpis="""
- PUE (Power Usage Effectiveness) for data centers
- kWh per employee per year
- CO2e per active user or transaction
- Business travel CO2e per employee""",
        anomaly_detection_rules="""
- Sudden jump in kWh per active user (>15% vs baseline)
- Abnormal change in cloud vCPU-hours vs revenue
- Spike in business travel not correlated with revenue/headcount
- Data center electricity increasing while compute workload decreasing""",
        quick_audit_checklist="""
1. Verify cloud provider sustainability reports and renewable energy claims
2. Check for unused/idle cloud instances and storage
3. Validate Scope 3 employee commute estimation methodology
4. Confirm business travel policy compliance
5. Review hardware procurement sustainability criteria"""
    ),
    
    "material_transformer": ArchetypePromptConfig(
        name="material_transformer",
        display_name="Material Transformer (Manufacturing / Pharma / Textiles)",
        context_specific_fields="""
- Production metrics: units produced per period, uptime percentage
- Fuel consumption: natural gas (m³), diesel (liters), LPG/other fuels
- Electricity: kWh for production vs auxiliary systems
- Raw materials: key inputs (steel tonnes, chemicals kg, etc.)
- SCADA/sensor integration: available or not""",
        key_kpis="""
- CO2e per unit produced (carbon intensity)
- Energy per unit produced (kWh/unit)
- Fuel per unit produced (GJ/unit)
- Scope 3 raw material intensity (kgCO2e/kg input)""",
        anomaly_detection_rules="""
- Energy per unit produced drift >10% for 3 consecutive periods
- Fuel consumption not correlating with production volume
- Electricity spike during non-production hours
- Process heat consumption inconsistent with output quality
- Scope 3 material procurement spikes not matching production schedules""",
        quick_audit_checklist="""
1. Verify production volume data matches energy consumption trends
2. Check boiler/furnace efficiency ratings and maintenance logs
3. Review waste heat recovery potential
4. Validate supplier EPDs (Environmental Product Declarations)
5. Confirm SCADA data quality and completeness"""
    ),
    
    "structure_builder": ArchetypePromptConfig(
        name="structure_builder",
        display_name="Structure Builder (Construction / Real Estate)",
        context_specific_fields="""
- Active projects: project IDs, area m², construction phase
- Embodied carbon: baseline A1-A3 estimates if available
- Bill of Quantities: major materials (concrete m³, steel tonnes, timber m³)
- On-site energy: diesel for machinery (liters), site electricity (kWh)
- Logistics: material transport distances (km)""",
        key_kpis="""
- kgCO2e per m² built (operational + embodied)
- Diesel per machine-hour
- Material waste percentage
- Recycled/low-carbon material substitution rate""",
        anomaly_detection_rules="""
- Diesel consumption per machine-hour >20% above benchmark
- Concrete/steel usage exceeding BoQ estimates by >15%
- Site electricity spikes not correlated with construction activity
- Transport distances increasing for same material type
- Waste tonnage ratio increasing without project scope change""",
        quick_audit_checklist="""
1. Compare actual material quantities vs BoQ estimates
2. Review concrete mix specification for low-carbon alternatives
3. Check machinery idle time and fuel efficiency
4. Validate EPDs for key materials (concrete, steel)
5. Assess on-site renewable energy opportunities"""
    ),
    
    "mover": ArchetypePromptConfig(
        name="mover",
        display_name="The Mover (Logistics / Shipping / Airlines / Fleet)",
        context_specific_fields="""
- Fleet composition: vehicle types and counts, fuel types
- Route data: average distances, load factors, empty mile percentage
- Fuel consumption: liters or kWh by vehicle segment
- Modal split: road vs rail vs sea vs air percentage
- Telematics availability: yes/no, data quality""",
        key_kpis="""
- Fuel per km per vehicle type
- CO2e per tonne-km
- Load factor percentage
- Empty miles/backhaul percentage
- Modal shift progress (road to rail/sea)""",
        anomaly_detection_rules="""
- Fuel per km per vehicle >15% above baseline for specific routes
- Sudden increase in empty miles percentage
- Load factor dropping below 60% consistently
- Idle time spikes indicating route inefficiency
- Fuel consumption not correlating with distance traveled""",
        quick_audit_checklist="""
1. Verify telematics data completeness and accuracy
2. Review route optimization system effectiveness
3. Check driver behavior metrics (harsh braking, idling)
4. Validate fuel receipt reconciliation with telematics
5. Assess fleet electrification/alternative fuel roadmap"""
    ),
    
    "land_steward": ArchetypePromptConfig(
        name="land_steward",
        display_name="Land Steward (Agriculture / Forestry / Food & Bev)",
        context_specific_fields="""
- Land use: crop types, area (hectares), livestock headcount
- Inputs: fertilizer N application (kg), pesticides (kg)
- Outputs: yield (tonnes), products
- Energy: irrigation (kWh), cold chain (kWh), processing (kWh)
- Land use change: deforestation, peatland conversion history""",
        key_kpis="""
- CH4 per livestock head
- N2O per kg fertilizer applied
- CO2e per tonne of product
- Cold chain energy intensity (kWh per tonne stored)
- Soil organic carbon change""",
        anomaly_detection_rules="""
- Fertilizer N application >20% above regional best practice
- CH4 per head increasing without feed change
- Cold-chain temperature excursions indicating equipment issues
- Yield/input ratio declining (more inputs, less output)
- Irrigation energy spiking without drought conditions""",
        quick_audit_checklist="""
1. Review fertilizer application rates vs soil testing recommendations
2. Check livestock feed composition and methane reduction additives
3. Validate cold-chain equipment efficiency and maintenance
4. Review land use change documentation and carbon stock changes
5. Assess precision agriculture adoption (variable rate application)"""
    ),
    
    "energy_producer": ArchetypePromptConfig(
        name="energy_producer",
        display_name="Energy Producer (Utilities / Oil & Gas / Mining)",
        context_specific_fields="""
- Generation mix: capacity by fuel type (MW), output (MWh)
- CEMS data: continuous emissions monitoring availability
- Fugitive emissions: methane monitoring program status
- Fuel consumption: per generation unit
- Own-use electricity: percentage of generation
- Outage/maintenance schedule""",
        key_kpis="""
- CO2e per MWh generated (grid intensity)
- Methane leak rate (percentage of throughput)
- Capacity factor by unit
- Own-use electricity percentage
- Combustion efficiency percentage""",
        anomaly_detection_rules="""
- Combustion efficiency dropping below design specifications
- Fugitive methane emissions spiking (LDAR trigger)
- Own-use electricity increasing without capacity addition
- Capacity factor declining outside maintenance windows
- CO2e/MWh increasing for same fuel type""",
        quick_audit_checklist="""
1. Verify CEMS calibration and data quality
2. Review LDAR (Leak Detection and Repair) program compliance
3. Check combustion optimization and tuning records
4. Validate methane venting and flaring data
5. Assess grid storage and renewable integration opportunities"""
    ),
    
    "retailer": ArchetypePromptConfig(
        name="retailer",
        display_name="Retailer (Retail / E-commerce / Hospitality)",
        context_specific_fields="""
- Store footprint: count, total area sqm, refrigeration presence
- Logistics: delivery fleet, last-mile partners, warehouse locations
- Energy: store electricity (HVAC, lighting, refrigeration), warehouse electricity
- Supply chain: key product categories, supplier sustainability scores
- Packaging: materials used, recycled content percentage""",
        key_kpis="""
- CO2e per sqm of retail space
- Refrigeration energy per sqm
- Last-mile delivery CO2e per order
- Supply chain CO2e per $ revenue
- Packaging CO2e per product""",
        anomaly_detection_rules="""
- Store-level energy per sqm spike >25% vs baseline
- Refrigeration temperature excursions indicating equipment failure
- Last-mile delivery emissions increasing per order
- Supplier emissions intensity diverging from category average
- Packaging weight per unit increasing without product change""",
        quick_audit_checklist="""
1. Review refrigerant leak detection and GWP of refrigerants
2. Check store HVAC schedules vs occupancy
3. Validate last-mile delivery partner sustainability data
4. Review supplier sustainability scorecards and engagement
5. Assess packaging reduction and recycled content opportunities"""
    ),
}


def build_strategy_prompt(
    archetype: str,
    org_context: Dict[str, Any],
    max_strategies: int = 5
) -> str:
    """
    Build archetype-specific strategy generation prompt
    
    Args:
        archetype: Organization archetype key
        org_context: Full organization context from OrgContextBuilder
        max_strategies: Number of strategies to request
        
    Returns:
        Formatted prompt string
    """
    config = ARCHETYPE_STRATEGY_CONFIGS.get(archetype)
    
    if not config:
        # Fallback for unknown archetype
        config = ArchetypePromptConfig(
            name="generic",
            display_name="General Organization",
            context_specific_fields="- Standard emission data available",
            key_kpis="- CO2e per revenue unit\n- Energy intensity",
            anomaly_detection_rules="- Significant deviations from baseline",
            quick_audit_checklist="1. Review data completeness\n2. Validate emission factors"
        )
    
    # Format organization context
    aggregates = org_context.get("aggregates", {})
    targets_list = org_context.get("reduction_targets", [])
    regional = org_context.get("regional_context", {}) or {}
    
    targets_text = "\n".join([
        f"- {t['name']}: {t['baseline']} → {t['target']} (Progress: {t['progress']}, Status: {t['status']})"
        for t in targets_list
    ]) if targets_list else "No active reduction targets"
    
    regional_text = ""
    if regional:
        regs = regional.get("regulations", [])
        incentives = regional.get("incentives", [])
        regional_text = f"""
Grid EF: {regional.get('grid_ef_kwh', 'N/A')} kgCO2e/kWh (Source: {regional.get('grid_ef_source', 'Unknown')})
Carbon Price: ${regional.get('carbon_price_usd', 'N/A')}/tonne ({regional.get('carbon_pricing_scheme', 'No scheme')})
Regulations: {', '.join([r.get('name', '') for r in regs[:3]]) if regs else 'None specified'}
Incentives: {', '.join([i.get('name', '') for i in incentives[:3]]) if incentives else 'None specified'}"""
    
    top_types = org_context.get("type_breakdown", {})
    top_types_text = "\n".join([
        f"- {atype}: {pct:.1f}%"
        for atype, pct in sorted(top_types.items(), key=lambda x: x[1], reverse=True)[:5]
    ]) if top_types else "No type breakdown available"
    
    return f"""REDUCTION STRATEGY REQUEST
Organization: {org_context.get('org_name', 'Unknown')} ({org_context.get('org_id', 'N/A')})
Country: {org_context.get('country', 'N/A')}
Industry: {org_context.get('industry', 'N/A')}
Archetype: {config.display_name}

CURRENT EMISSIONS SUMMARY:
- Total: {aggregates.get('total_kg', 0):,.0f} kgCO2e
- Scope 1: {aggregates.get('scope1_kg', 0):,.0f} kgCO2e ({aggregates.get('scope1_pct', 0):.1f}%)
- Scope 2: {aggregates.get('scope2_kg', 0):,.0f} kgCO2e ({aggregates.get('scope2_pct', 0):.1f}%)
- Scope 3: {aggregates.get('scope3_kg', 0):,.0f} kgCO2e ({aggregates.get('scope3_pct', 0):.1f}%)

TOP EMISSION CATEGORIES:
{top_types_text}

ACTIVE REDUCTION TARGETS:
{targets_text}

REGIONAL CONTEXT:
{regional_text}

ARCHETYPE-SPECIFIC CONTEXT:
{config.context_specific_fields}

KEY KPIs TO TRACK:
{config.key_kpis}

TASK:
Produce {max_strategies} prioritized reduction strategies tailored to this {config.display_name} organization. For each strategy:

1. Short title and detailed description
2. Category: energy|travel|procurement|operations|facility|fleet|process
3. Target scope: Scope 1|Scope 2|Scope 3
4. Estimated annual CO2e reduction (kg) with confidence (H/M/L)
5. Implementation difficulty: easy|medium|hard
6. Implementation timeframe: immediate|short-term (0-6mo)|medium-term (6-18mo)|long-term (18mo+)
7. Regional factor: How regulations/incentives in {org_context.get('country', 'the region')} affect this strategy
8. Required data/sensors to verify success
9. Priority ranking (1 = highest)

Also provide:
- Suggested anomaly detection rules for this archetype:
{config.anomaly_detection_rules}

- Quick audit checklist:
{config.quick_audit_checklist}

OUTPUT FORMAT:
Return ONLY valid JSON:
{{
    "strategies": [
        {{
            "title": "string",
            "description": "detailed implementation guidance",
            "category": "string",
            "scope": "Scope 1|Scope 2|Scope 3",
            "estimated_reduction_kg": number,
            "confidence": "H|M|L",
            "difficulty": "easy|medium|hard",
            "implementation_timeframe": "string",
            "regional_factor": "string",
            "verification_data": ["data point 1", "data point 2"],
            "priority": number
        }}
    ],
    "recommended_kpis": [
        {{
            "name": "string",
            "formula": "string",
            "target_value": "string",
            "monitoring_frequency": "string"
        }}
    ],
    "quick_wins": ["immediate action 1", "immediate action 2", "immediate action 3"]
}}"""


def format_anomaly_prompt(org_context: Dict[str, Any]) -> str:
    """
    Format the anomaly analysis prompt with organization context
    
    Args:
        org_context: Full organization context from OrgContextBuilder.to_ai_payload()
        
    Returns:
        Formatted prompt string ready for AI
    """
    aggregates = org_context.get("aggregates", {})
    regional = org_context.get("regional_context", {}) or {}
    archetype_ctx = org_context.get("archetype_context", {}) or {}
    
    # Format aggregates
    aggregates_text = f"""Total Emissions: {aggregates.get('total_kg', 0):,.0f} kgCO2e
- Scope 1: {aggregates.get('scope1_kg', 0):,.0f} kgCO2e ({aggregates.get('scope1_pct', 0):.1f}%)
- Scope 2: {aggregates.get('scope2_kg', 0):,.0f} kgCO2e ({aggregates.get('scope2_pct', 0):.1f}%)
- Scope 3: {aggregates.get('scope3_kg', 0):,.0f} kgCO2e ({aggregates.get('scope3_pct', 0):.1f}%)"""
    
    # Format top contributors
    contributors = org_context.get("top_contributors", [])
    contributors_text = "\n".join([
        f"{c['rank']}. {c['activity_type']} | {c['co2e_kg']:,.0f} kgCO2e | {c['pct_of_total']:.1f}% | {c['description']}"
        for c in contributors[:10]
    ]) if contributors else "No top contributors data"
    
    # Format sample activities
    samples = org_context.get("sample_activities", [])
    activities_text = "\n".join([
        f"- {a['date']} | {a['type']} | {a['amount'] or 'N/A'} {a['unit'] or ''} | "
        f"{a['co2e_kg']:,.0f} kgCO2e | {a['pct_of_total']:.1f}% | [{a['category']}] | "
        f"region: {a['region'] or 'N/A'} | id: {a['id'][:8]}..."
        for a in samples
    ]) if samples else "No sample activities"
    
    # Format targets
    targets = org_context.get("reduction_targets", [])
    targets_text = "\n".join([
        f"- {t['name']}: {t['baseline']} → {t['target']} | Progress: {t['progress']} | Status: {t['status']}"
        for t in targets
    ]) if targets else "No active reduction targets"
    
    # Format flags
    flags = org_context.get("recent_flags", [])
    flags_text = "\n".join([
        f"- {f['id'][:8]}... | {f['type']} | {f['severity']} | {f['title'][:50]} | {f['status']} | verdict: {f['verdict'] or 'N/A'}"
        for f in flags
    ]) if flags else "No recent flags"
    
    # Format regional context
    regional_text = "No regional context available"
    if regional:
        regs = regional.get("regulations", [])
        regional_text = f"""Country: {regional.get('country_code', 'Unknown')} ({regional.get('region_name', '')})
Grid EF: {regional.get('grid_ef_kwh', 'N/A')} kgCO2e/kWh
Carbon Price: ${regional.get('carbon_price_usd', 'N/A')}/tonne
Regulations: {', '.join([r.get('name', '') for r in regs[:3]]) if regs else 'None'}"""
    
    # Format archetype context
    archetype_text = "No archetype context"
    if archetype_ctx:
        exp_dist = archetype_ctx.get("expected_scope_distribution", {})
        archetype_text = f"""Archetype: {archetype_ctx.get('display_name', 'Unknown')}
Expected Scope Distribution: Scope 1 {exp_dist.get('Scope 1', 0)*100:.0f}%, Scope 2 {exp_dist.get('Scope 2', 0)*100:.0f}%, Scope 3 {exp_dist.get('Scope 3', 0)*100:.0f}%
Expected Activity Types: {', '.join(archetype_ctx.get('expected_activity_types', [])[:5])}
Key Signals: {', '.join(archetype_ctx.get('key_emission_signals', [])[:5])}"""
    
    return ANOMALY_ANALYSIS_TEMPLATE.format(
        org_name=org_context.get("org_name", "Unknown"),
        org_id=org_context.get("org_id", "N/A"),
        country=org_context.get("country", "N/A"),
        grid_ef=regional.get("grid_ef_kwh", "N/A"),
        archetype_display_name=org_context.get("archetype_display_name", "Unknown"),
        industry=org_context.get("industry", "N/A"),
        period_start=org_context.get("period_start", "N/A"),
        period_end=org_context.get("period_end", "N/A"),
        aggregates_text=aggregates_text,
        top_contributors_text=contributors_text,
        activities_text=activities_text,
        targets_text=targets_text,
        flags_text=flags_text,
        regional_context_text=regional_text,
        archetype_context_text=archetype_text,
    )
