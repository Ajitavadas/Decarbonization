# Decarbonization Platform - Strategic Implementation Roadmap

Based on "Strategic Architecture and Implementation Guide: The Autonomous Decarbonization Platform".

## **Phase 1: The Foundation (Weeks 1-6)**
**Focus:** Ingestion Engine, Spatial Data, and Core Infrastructure.

### **1.1 Advanced Ingestion Engine ("Universal Semantic Adapter")**
- [ ] **Multi-Modal Ingestion Pipeline**:
    - [ ] Handle static assets (images, scanned PDFs) vs native assets (digital PDFs, XLSX, CSV).
    - [ ] **OCR/Layout Intelligence**: Implement LayoutLMv3 for invoice scanning (bounding boxes, spatial relationships).
    - [ ] **Heuristic Parsing**: Improve `CSVParsingService` with "Natural Language Mapping" (RoBERTa or Gemini) to map arbitrary headers to internal fields.
- [ ] **Unit Ontology Enforcement**:
    - [ ] `Analyst` agent must parse and normalize units (Therms, liters, gallons -> GJ, kWh).

### **1.2 Geospatial & Time-Series Infrastructure**
- [ ] **PostGIS Integration**:
    - [ ] Update PostgreSQL to support PostGIS.
    - [ ] Store Grid Region Polygons (eGRID, etc.).
    - [ ] Implement Point-in-Polygon location mapping for facilities.
- [ ] **TimescaleDB Integration**:
    - [ ] Enable time-series optimizations for emission events.

### **1.3 Dynamic Region-Specific Calculation Engine**
- [ ] **Location-Based vs Market-Based**:
    - [ ] Implement dual reporting logic.
    - [ ] Architect engine to select emission factors based on `(Location, Time)`.

---

## **Phase 2: The Agentic Core (Weeks 7-12)**
**Focus:** Orchestration, Auditor/Interrogator Agents, and User Interaction.

### **2.1 Agentic Orchestration (LangGraph)**
- [ ] **Migrate to LangGraph**:
    - [ ] Implement the DAG: *Detect Gap -> Ask User -> Validate -> Calculate -> Store*.
    - [ ] State Management: `Agent_State` table in Postgres + Redis session storage.

### **2.2 The Trinity of Agents**
- [ ] **The Auditor (Observer)**:
    - [ ] Passive monitoring of `Emission_Events`.
    - [ ] Gap Detection (e.g., missing Scope 1 heating data).
    - [ ] Anomaly Detection (>2 sigma deviation).
- [ ] **The Interrogator (Communicator)**:
    - [ ] User-facing LLM agent.
    - [ ] Transforms `Flag_Event` into conversational prompts.
    - [ ] Channel-agnostic 'Pings' (WebSocket/Slack).
- [ ] **The Analyst (Computer)**:
    - [ ] Deterministic calculation engine.
    - [ ] Execution of math and unit conversions.

### **2.3 Frontend Evolution**
- [ ] **Modern UI Framework**:
    - [ ] Migrate to **React** or **Next.js**.
    - [ ] Implement persistent "Carbon Copilot" side-panel.
    - [ ] WebSocket support for real-time agent "Pings".

---

## **Phase 3: Intelligence & Fallback (Weeks 13-20)**
**Focus:** RAG, Estimation, and Auto-Classification.

### **3.1 RAG-Driven Estimator Agent**
- [ ] **Vector Database**: Setup Pinecone or Weaviate.
- [ ] **Knowledge Indexing**: Index CBECS, IEA data, and benchmarks.
- [ ] **Fallback Logic**:
    - [ ] Context Vector Construction (Sector, Location, Time).
    - [ ] Intelligent Gap Filling (Regression/Weather normalization).

### **3.2 Emission Factor Fingerprinting**
- [ ] **Organization Classifier**:
    - [ ] Classify orgs into 7 Archetypes (The Digital Service, The Material Transformer, etc.) based on data stream.
    - [ ] Auto-activate specific modules (e.g., Construction Module for "Structure Builder").

---

## **Phase 4: Sector Expansion (Weeks 21+)**
**Focus:** Deep Integrations and Sector Modules.

### **4.1 Industry-Specific Modules**
- [ ] **Tech Startup**: AWS CCFT integration (Scope 2).
- [ ] **Manufacturing**: SCADA integration, Supplier Engagement Portal.
- [ ] **Construction**: BoQ (Bill of Quantities) Parser, Embodied Carbon Calculator.
