# Live Demo Script — Decarbonization Platform

A ~4–5 minute walkthrough for demonstrating the platform live (to Climatiq or any prospect). Everything
below is verified working against live Climatiq factors and the Vertex AI classifier.

---

## Demo credentials & data

| Item | Value |
|---|---|
| **App URL** | http://localhost:3000 |
| **Login email** | `demo@acmeglobal.io` |
| **Password** | `Demo2025!` |
| **User** | Priya Sharma (Sustainability Analyst, ACME Global) |
| **Project** | FY2025 Corporate Carbon Inventory |
| **Dataset** | `docs/demo/demo_carbon_data.csv` (18 rows, DE/IN/US/GB) |

The account already has the 18-row inventory loaded, so you can demo immediately. To re-upload live (a
strong beat), delete/recreate a project or use a second CSV.

### Verified numbers (what the dashboard shows)

- **Total: 591,939 kg CO₂e** (~592 tonnes) across 18 activities, **0 calculation errors**
- **Scope 1: 33,837 kg** (natural gas, diesel generators, fleet gasoline)
- **Scope 2: 283,731 kg** (grid electricity — DE/IN/US)
- **Scope 3: 274,372 kg** (flights, rail commute, freight, cloud/IT/consulting spend, waste, water)
- Top 3 sources: Bangalore electricity (119,228), Austin data center (83,221), Laptops & IT (80,520)

---

## Pre-demo checklist (2 min before you start)

1. Backend running: `http://localhost:8000/docs` returns 200. (From `backend/`: `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000`)
2. Frontend running: `http://localhost:3000` loads. (From `frontend/`: `npm run dev`)
3. Confirm ADC is active so Vertex AI works: `gcloud auth application-default print-access-token` succeeds, project `project-504e3feb-474e-4db6-9a0`.
4. **Do a dry run of the login once** — the first login shows a "Carbon Copilot" onboarding modal
   (org personalization). Either complete it once beforehand, or use it as your opening beat (Scene 1).
5. Have `docs/demo/demo_carbon_data.csv` handy if you want to show a live upload.

---

## Scene-by-scene

### Scene 1 — The hook (30s)
**Say:** "Sustainability analysts at multinationals spend weeks turning messy activity data — utility
bills, ERP exports, travel logs, supplier invoices in different units and currencies — into an auditable
carbon inventory. This platform does it in one upload, on top of Climatiq's emission-factor database."

Log in as Priya. If the **Carbon Copilot onboarding modal** appears, use it: "On first login the copilot
learns the organization's profile to tailor insights and anomaly detection." Click **Let's Get Started**,
pick an archetype, finish.

### Scene 2 — The upload magic (60s) *(optional live, or narrate the loaded data)*
Go to **Activity Data Upload**. Drop in `demo_carbon_data.csv`.

**Say:** "This is raw activity data — no emission factors, no scope labels. Watch what happens." Behind
the scenes, each row is sent to an AI classifier (Vertex AI Gemini) that assigns GHG Scope 1/2/3, picks
the right Climatiq endpoint, and builds the factor query; then Climatiq returns a scientifically-vetted
CO₂e value with a full audit trail.

**Key line:** "No pre-mapping. The analyst didn't tell it that 'Bangalore delivery center electricity' is
Scope 2 grid power in India — the AI did, and Climatiq priced it with the Indian grid factor."

### Scene 3 — The dashboard (45s)
Land on the **Dashboard**.

**Point to:** Total **591,939 kg CO₂e**, the **Scope 1/2/3 cards**, the **Emissions Over Time** chart,
and the **Scope Breakdown** donut.

**Say:** "A complete, GHG-Protocol inventory across four countries — Scope 2 electricity dominates at
284 tonnes, with Scope 3 value-chain right behind at 274. Every number traces back to a named Climatiq
factor."

### Scene 4 — Scope analysis & audit trail (30s)
Open **Scope Analysis**, then **Emissions** (or a project's activity list). Click into a row — show the
stored emission factor, source dataset, region, and year.

**Say:** "This is what makes it audit-ready. Each line carries its Climatiq source, so there's no
greenwashing exposure — an auditor can trace every kilogram."

### Scene 5 — The Carbon Copilot (60s) — *the standout*
Open **Carbon Copilot**. Type these (all verified to return real answers):

1. **"What are my top 3 emission sources?"**
   → Lists Bangalore electricity 119,228 kg, Austin data center 83,221 kg, Laptops & IT 80,520 kg.
2. **"What are my total Scope 2 emissions?"**
   → 283,731 kg CO₂e.
3. **"Which activities have the highest emissions?"** or **"Show my Scope 3 breakdown."**

**Say:** "The copilot turns a plain-language question into a safe, read-only query over the analyst's own
data — no dashboards to configure, no SQL. This is the daily driver: 'where's my footprint concentrated,
and what changed?'"

### Scene 6 — Anomalies & targets (30s)
Open **Anomalies** (the platform auto-flags implausible values and missing factors) and **Reduction
Targets** (set a baseline, see the trajectory forecast).

**Say:** "It also does the QA the analyst dreads — flagging anomalies and data gaps before the audit — and
turns the inventory into a reduction plan with on-track/off-track forecasting."

### Scene 7 — Close (20s)
**Say:** "So: messy data in, audit-ready inventory out, with a copilot on top — built entirely on
Climatiq's API. Exactly the analyst-facing workflow layer that turns Climatiq's data into a daily tool."

---

## If something breaks mid-demo

- **Copilot returns only a total / "error" intent:** Vertex AI (ADC) isn't reachable — run
  `gcloud auth application-default login` and restart the backend. Groq is the fallback but its key may be
  unset.
- **Upload rows show 0 kg:** free-tier Climatiq premium endpoint was hit — already handled by
  search+estimate fallbacks; re-run the upload. See `docs/technical_specifications.md`.
- **Onboarding modal blocks the view:** complete it once ("Let's Get Started") — it won't reappear after
  onboarding is finished for that org.

---

## Talking points if asked "how is this different from Salesforce / Persefoni / Watershed?"

- **AI-native ingestion** vs. template-based mapping — drop in messy data, no pre-mapping.
- **Natural-language Copilot** over the analyst's own data — not just static dashboards.
- **Automated anomaly + gap auditing** before the audit.
- **Priced for the analyst/mid-market**, not just enterprise budgets — the segment the big suites price out.
