# Decarbonization Platform — One-Pager

**AI-native carbon accounting for the sustainability analyst, built on the Climatiq API.**

---

## The problem

Sustainability analysts at multinational companies are drowning in messy activity data. Utility bills,
ERP exports, travel logs, and supplier invoices arrive in dozens of formats, in different units and
currencies, from every region the company operates in. Turning that into an auditable, GHG-Protocol
inventory is still largely **manual line-by-line mapping** — the analyst decides the scope, finds the
right emission factor, converts the units, and documents it for the auditor. Enterprise suites
(Salesforce Net Zero Cloud, Persefoni, Watershed) are built for large-cap budgets and still push most of
that mapping work back onto the analyst.

## What we built

A platform that ingests raw activity data and produces a scope-classified, factor-backed emissions
inventory — automatically — then lets the analyst interrogate it in plain language.

| Capability | What it does | Why the analyst cares |
|---|---|---|
| **AI-native ingestion** | Upload CSV, XLSX, PDF, or a photo of an invoice. An LLM classifies each row into GHG Scope 1/2/3 + Scope-3 category, picks the right Climatiq endpoint, and builds the emission-factor query. | Drop in messy data, get an inventory. No pre-mapping. |
| **Climatiq calculation engine** | Every number is backed by a scientifically-vetted Climatiq emission factor with full audit trail (source, dataset, year, region). | Audit-ready, no greenwashing risk. |
| **Carbon Copilot** | Ask questions in natural language ("which sites drove my Scope 2 spike?"). Generates safe, read-only queries over the org's own data, with per-org rate governance. | Answers in seconds, not spreadsheet hours. |
| **Anomaly & gap auditing** | Automatically flags implausible values, zero-emission rows, and missing data before the audit. | Catches errors the analyst would otherwise find manually. |
| **Reduction targets & trajectory** | Set science-based baselines and targets; deterministic trajectory forecasting shows whether you're on track. | Turns reporting into planning. |
| **Multi-tenant, multi-region** | Organization isolation, JWT auth; handles DE/IN/US/GB activity in one inventory. | Fits an MNC's real footprint. |

## Built on Climatiq

The platform runs entirely on the **Climatiq API** — 200,000+ GHG-Protocol-compliant emission factors
across global territories and sectors — for search and estimate calculations across electricity, fuel,
travel, freight, spend-based procurement, and waste. Climatiq is the trusted data layer; this platform is
the AI workflow and analyst experience on top.

## Proof point

A synthetic 18-line annual inventory for a fictional MNC (Germany, India, US, UK — electricity, gas,
fuel, flights, rail, freight, cloud/IT/consulting spend, waste, water) was ingested end-to-end: **every
line auto-classified and calculated against live Climatiq factors**, producing a full Scope 1/2/3
breakdown with per-activity audit trails, in a single upload.

## Technology

Next.js 15 / React 19 frontend · FastAPI / Python backend · Vertex AI (Gemini) classification ·
Climatiq API calculation engine · PostgreSQL · multi-tenant architecture.

## Target customer

Sustainability and ESG analysts at multinational enterprises facing CSRD, supplier disclosure, and
regional reporting mandates — the mid-market and enterprise teams that need Climatiq-grade data without
enterprise-suite overhead.

---

*Contact: dasajitava@gmail.com · Built on [Climatiq](https://www.climatiq.io/)*
