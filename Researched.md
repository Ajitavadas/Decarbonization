# **Comprehensive Architectural Blueprint for an AI-Powered Decarbonization Platform**

## **Executive Summary**

The escalating urgency of the climate crisis has transitioned carbon accounting from a voluntary corporate social responsibility initiative to a rigorous financial and regulatory requirement. As organizations face mounting pressure to disclose their environmental impact under frameworks such as the Corporate Sustainability Reporting Directive (CSRD) and the SEC’s climate disclosure rules, the need for precise, auditable, and automated decarbonization infrastructure has never been greater. This report delineates the technical architecture, implementation guidelines, and data strategy for a state-of-the-art decarbonization platform designed to navigate this complexity.

The proposed system leverages the **Climatiq API** as its core intelligence engine, utilizing its sophisticated capabilities for emission calculation, scope classification, and predictive modeling. By integrating advanced features such as **Intermodal Freight** logistics, **Autopilot** for natural language processing (NLP) based classification, and **Batch Estimation** for high-volume data throughput, the platform addresses the critical pain points of data fragmentation and manual processing that currently plague the industry.1

Technologically, the platform adopts a modern, cloud-native stack: **FastAPI** provides a high-performance, asynchronous backend capable of handling complex I/O-bound operations; **Next.js** delivers a responsive, server-side rendered frontend; **PostgreSQL** ensures robust relational data integrity with JSONB flexibility for polymorphic activity data; and **Redis** powers high-speed caching and asynchronous task queue management. Encapsulated entirely within a **Dockerized** environment, this architecture ensures consistency across development, testing, and production lifecycles.2

This document serves as a definitive implementation guide. It moves beyond high-level abstractions to provide concrete database schemas, project directory structures, and API integration logic. It synthesizes technical specifications with sustainability reporting standards, ensuring that every architectural decision—from the choice of a modular monolith design to the specific indexing of emission factors—directly supports the goal of delivering accurate, actionable, and compliant carbon insights.4

---

## **Part 1: System Architecture and Containerization Strategy**

### **1.1 The Case for a Modular Monolith**

In designing complex enterprise systems, the initial impulse is often to adopt a microservices architecture. However, the domain of carbon accounting is characterized by tightly coupled entities—Emission Factors, Organization Settings, and Reporting Projects—that cross-cut through various functional modules like Freight, Travel, and Procurement. A distributed microservices architecture in this context introduces unnecessary latency, network complexity, and data consistency challenges.

Therefore, this platform utilizes a **Modular Monolith** architectural pattern. This approach maintains the code within a single deployable unit (the FastAPI backend) but enforces strict logical separation between domains. The Freight module, for example, encapsulates all logic, validation schemas, and Climatiq integrations specific to logistics, interacting with the Core or Users modules only through well-defined internal interfaces. This design enables the distinct separation of concerns while preserving the simplicity of a single database transaction scope and unified deployment pipeline. Should specific domains, such as the compute-intensive Freight calculation engine, require independent scaling in the future, the modular structure facilitates extraction into separate services with minimal refactoring.4

### **1.2 Container Orchestration with Docker**

To ensure scalability, reproducibility, and isolation, the application is fully containerized. The architecture distinguishes between the web serving layer, background processing, data persistence, and caching layers. This separation is critical for scaling individual components based on load; for instance, increasing the number of Celery workers to handle a surge in batch file uploads without replicating the entire database instance.3

The Docker Compose configuration orchestrates the following services:

1\. Backend API (FastAPI Service):

This container hosts the Uvicorn ASGI server. It is responsible for handling synchronous HTTP requests, performing authentication via JWT (JSON Web Tokens), and orchestrating business logic. The Dockerfile utilizes a multi-stage build process to minimize the final image size, separating the build dependencies (compilers, headers) from the runtime environment.3

2\. Frontend Application (Next.js Service):

Hosted in a separate container, the Next.js application serves the user interface. It communicates with the backend via RESTful HTTP calls. In a production environment, this container can be optimized to serve static assets directly or via a CDN, while dynamic routes rely on server-side rendering (SSR) to ensure SEO compatibility and fast initial page loads.

3\. Asynchronous Worker (Celery Service):

Carbon accounting frequently involves processing massive datasets, such as annual procurement ledgers containing tens of thousands of rows. Processing these synchronously would inevitably lead to HTTP timeouts and a poor user experience. A dedicated Python container runs the Celery worker process. It listens to the Redis queue for tasks such as process\_batch\_upload or generate\_compliance\_report, executing them in the background. This ensures the main API remains responsive to user interactions.2

4\. Task Scheduler (Celery Beat Service):

A lightweight container dedicated to the Celery Beat scheduler. This service triggers periodic tasks, such as the nightly synchronization of emission factors from Climatiq to ensure local caches are up-to-date, or the automated generation of monthly emission alerts for users exceeding their carbon budgets.

5\. Database (PostgreSQL Service):

The primary persistent store. It is configured with persistent volumes to ensure data survival across container restarts. The configuration includes optimizations for JSONB query performance, critical for querying the variable structures of API responses from Climatiq.

6\. Cache & Broker (Redis Service):

Redis serves a dual purpose. First, it acts as the message broker for Celery, managing the distribution of tasks to workers. Second, it functions as a high-speed cache for Climatiq API responses. Given that emission factors for a specific year and region change infrequently, caching these responses reduces external API calls, lowers costs, and significantly improves system latency.8

### **1.3 High-Level Interaction Flow**

The interaction between these components follows a strictly defined flow to maintain data integrity and system stability.

When a user initiates a complex calculation—for example, uploading a CSV for Batch Estimation of Scope 3 Procurement emissions—the request hits the **Next.js** frontend. The frontend validates the file format and streams it to the **FastAPI** backend.

The backend performs a preliminary validation of the schema. Instead of processing the file immediately, it creates a Job record in the **PostgreSQL** database with a status of PENDING. It then pushes the Job ID and file location to the **Redis** queue and immediately returns a 202 Accepted response to the frontend.

A **Celery Worker**, detecting the new message in Redis, picks up the task. It retrieves the file, parses the data, and orchestrates the calls to the **Climatiq Batch API**. As results are returned, the worker updates the database record with the calculated emissions and status. Throughout this process, the frontend polls a status endpoint (or listens to a WebSocket) to provide real-time progress updates to the user.7

---

## **Part 2: Backend Implementation and Project Structure**

The maintainability of the platform hinges on a robust, predictable project structure. We adopt a layout that separates configuration, data models, schemas (Pydantic), and business logic (Services).

### **2.1 Directory Structure**

The proposed structure adheres to Python and FastAPI best practices, emphasizing modularity and circular dependency avoidance.

Plaintext  
decarbonization-platform/  
├──.github/                        \# CI/CD workflows for testing and deployment  
├── backend/  
│   ├── app/  
│   │   ├── api/  
│   │   │   ├── v1/                 \# API Versioning for backwards compatibility   
│   │   │   │   ├── endpoints/      \# Route handlers  
│   │   │   │   │   ├── auth.py  
│   │   │   │   │   ├── autopilot.py      \# Autopilot/NLP mapping endpoints   
│   │   │   │   │   ├── energy.py         \# Electricity/Fuel calculation endpoints \[1, 1\]  
│   │   │   │   │   ├── freight.py        \# Intermodal freight logic   
│   │   │   │   │   ├── procurement.py    \# Spend-based procurement logic   
│   │   │   │   │   ├── travel.py         \# Activity and Spend-based travel \[1, 1\]  
│   │   │   │   │   ├── mappings.py       \# Custom mapping management   
│   │   │   │   │   └── tasks.py          \# Job status checking endpoints  
│   │   │   │   └── router.py             \# Main router aggregating all endpoints  
│   │   ├── core/  
│   │   │   ├── config.py                 \# Environment variables (CLIMATIQ\_KEY, DB\_URL)  
│   │   │   ├── security.py               \# JWT token generation and validation  
│   │   │   ├── celery\_app.py             \# Celery app configuration and initialization \[2\]  
│   │   │   └── errors.py                 \# Global exception handlers  
│   │   ├── crud/                         \# Database Create/Read/Update/Delete operations  
│   │   │   ├── base.py                   \# Generic CRUD repository pattern  
│   │   │   ├── crud\_activity.py  
│   │   │   └── crud\_mapping.py  
│   │   ├── db/  
│   │   │   ├── base.py                   \# SQLModel/SQLAlchemy declarative base  
│   │   │   ├── session.py                \# Database session factory  
│   │   │   └── init\_db.py                \# Initial seed data script  
│   │   ├── integration/                  \# External API Clients  
│   │   │   ├── climatiq/  
│   │   │   │   ├── client.py             \# Base HTTP Client with retry logic  
│   │   │   │   ├── service.py            \# Business logic wrapper for API interactions  
│   │   │   │   └── schemas.py            \# Pydantic models mirroring Climatiq JSON payloads  
│   │   ├── models/                       \# Database table definitions  
│   │   │   ├── activity.py               \# Polymorphic activity storage  
│   │   │   ├── user.py  
│   │   │   └── job.py                    \# Async task tracking  
│   │   ├── schemas/                      \# Pydantic response/request models for the API  
│   │   ├── services/                     \# Complex domain logic (Calculation Engines)  
│   │   │   ├── calculation\_engine.py     \# Orchestrates scope classification  
│   │   │   └── reporting\_service.py  
│   │   └── main.py                       \# Application entry point  
│   ├── tests/                            \# Pytest suite  
│   ├── Dockerfile                        \# Backend container definition  
│   ├── alembic.ini                       \# Alembic migration configuration  
│   └── requirements.txt                  \# Python dependencies  
├── frontend/                             \# Next.js Application Source  
├── docker-compose.yml                    \# Container orchestration  
└── README.md

### **2.2 FastAPI Dependency Injection and Middleware**

FastAPI's dependency injection system is utilized to manage database sessions and authentication contexts efficiently. A get\_db dependency ensures that a database session is created for each request and closed afterwards, preventing connection leaks. Similarly, a get\_current\_user dependency validates the JWT token in the Authorization header, injecting the authenticated user object into route handlers.

Middleware is configured in main.py to handle cross-cutting concerns:

* **CORS (Cross-Origin Resource Sharing):** Configured to allow requests solely from the frontend container's domain, preventing unauthorized browser access.  
* **Request Logging:** Captures request latency, status codes, and endpoints for monitoring system performance.  
* **Exception Handling:** A global exception handler catches specific errors (e.g., ClimatiqAPIError, ValidationException) and returns standardized JSON error responses to the client, preventing stack trace exposure.11

### **2.3 The Integration Layer**

The integration/climatiq directory is the bridge between the internal domain and the external Climatiq API.

* **client.py:** This module encapsulates the raw HTTP calls using an asynchronous library like httpx. It handles the injection of the Authorization: Bearer header and implements exponential backoff retry logic for 429 Too Many Requests errors, ensuring system resilience under load.11  
* **schemas.py:** This file defines Pydantic models that strictly mirror the Climatiq API's expected JSON payloads. For instance, an IntermodalFreightRequest model would rigorously validate that the route list contains valid location objects and that the transport\_mode matches allowed enums (sea, road, air, rail).1  
* **service.py:** This layer acts as an abstraction facade. It exposes high-level methods like estimate\_flight\_emissions(origin, destination, class) that internally construct the complex JSON payloads required by the raw client. This decouples the core business logic from the specific JSON structure of the Climatiq API, facilitating easier updates if the API signature changes.9

---

## **Part 3: Database Schema Design (PostgreSQL)**

Designing a database for carbon accounting presents a unique challenge: the data is inherently polymorphic. A flight has attributes like "flight class" and "IATA codes," while an electricity record has "grid region" and "consumption in kWh." Storing these in rigid separate tables creates massive schema bloat. Instead, we utilize PostgreSQL's robust **JSONB** column type to store the variable attributes of an activity while maintaining structured relational columns for common fields like date, organization, and calculated emissions.

### **3.1 Entity Relationship Diagram (ERD) Overview**

The schema centers around the organizations table (tenancy) and the emission\_activities table (the ledger of carbon events).

### **3.2 Detailed Table Definitions**

#### **1\. organizations**

Represents the tenant company.

| Column | Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| id | UUID | PK, Default: uuid\_generate\_v4() | Unique identifier |
| name | VARCHAR(255) | NOT NULL | Company legal name |
| default\_currency | VARCHAR(3) | NOT NULL, Default: 'USD' | ISO 4217 code for reporting |
| industry\_sector | VARCHAR(100) | NULLable | For benchmarking (e.g., "Tech") |
| settings | JSONB | Default: {} | Custom configs (e.g., default region) |
| created\_at | TIMESTAMPTZ | Default: NOW() | Record creation timestamp |

#### **2\. projects**

Logical groupings for reporting (e.g., "2024 Corporate Footprint").

| Column | Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| id | UUID | PK | Unique identifier |
| organization\_id | UUID | FK \-\> organizations.id | Tenant ownership |
| name | VARCHAR(255) | NOT NULL | Project name |
| description | TEXT | NULLable | Context for the project |
| start\_date | DATE | NOT NULL | Reporting period start |
| end\_date | DATE | NOT NULL | Reporting period end |
| status | VARCHAR(20) | Enum: active, archived | Project lifecycle status |

#### **3\. emission\_activities**

The central ledger. This table uses a hybrid relational/document model.

| Column | Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| id | UUID | PK | Unique identifier |
| project\_id | UUID | FK \-\> projects.id | Link to reporting project |
| activity\_type | VARCHAR(50) | NOT NULL | Enum: travel, freight, energy, procurement |
| scope | VARCHAR(10) | NOT NULL | Enum: Scope 1, Scope 2, Scope 3 |
| description | TEXT | NOT NULL | Human-readable label (e.g., "Flight to NY") |
| activity\_date | DATE | NOT NULL | Date usage occurred |
| region\_code | VARCHAR(10) | NULLable | UN/LOCODE or Country Code (e.g., "US", "DE") 1 |
| input\_data | JSONB | NOT NULL | **Critical:** Stores the exact payload sent to Climatiq |
| co2e\_kg | NUMERIC(20, 6\) | NOT NULL | The calculated CO2 equivalent |
| co2e\_unit | VARCHAR(10) | Default: 'kg' | Unit of the result |
| calculation\_method | VARCHAR(20) | NULLable | ar4, ar5, ar6 12 |
| source\_dataset | VARCHAR(100) | NULLable | E.g., "EPA", "EXIOBASE", "BEIS" |
| is\_estimate | BOOLEAN | Default: FALSE | True if derived via Autopilot estimation |
| batch\_job\_id | UUID | FK \-\> batch\_jobs.id | Link if created via batch upload |

**Data Integrity Note:** The input\_data JSONB column stores the raw inputs. For a flight, it might contain {"origin": "LHR", "destination": "JFK", "class": "business"}. For electricity, {"energy": 1000, "unit": "kWh", "connection": "grid"}. Storing this allows for auditability—you can always reconstruct *why* a specific CO2e figure was generated.

#### **4\. custom\_mappings**

Stores the "Organizational Memory" linking internal ERP codes to Climatiq IDs.10

| Column | Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| id | UUID | PK | Unique identifier |
| organization\_id | UUID | FK \-\> organizations.id | Tenant ownership |
| internal\_label | VARCHAR(255) | NOT NULL | The ERP code (e.g., "GL-TRAVEL-001") |
| climatiq\_activity\_id | VARCHAR(255) | NOT NULL | The mapped Climatiq Activity ID |
| source | VARCHAR(100) | NULLable | Preferred source (e.g., "BEIS") |
| year | INT | NULLable | Preferred vintage year |
| confidence\_score | FLOAT | NULLable | If mapped by Autopilot, the confidence level |

#### **5\. batch\_jobs**

Tracks the state of asynchronous processing.13

| Column | Type | Constraints | Description |
| :---- | :---- | :---- | :---- |
| id | UUID | PK | Unique identifier |
| organization\_id | UUID | FK \-\> organizations.id | Tenant ownership |
| status | VARCHAR(20) | Enum: queued, processing, completed, failed | Current state |
| file\_url | TEXT | NOT NULL | Path to the source CSV in object storage |
| total\_records | INT | Default: 0 | Total rows in file |
| processed\_records | INT | Default: 0 | Rows successfully calculated |
| error\_log | JSONB | Default: \`\` | Array of error objects for failed rows |

### **3.3 Indexing Strategy for Performance**

Efficient indexing is paramount for the reporting dashboard performance.

* **B-Tree Indexes:** On project\_id, activity\_date, and activity\_type to speed up standard filtering queries.  
* **GIN Index:** On emission\_activities.input\_data. This allows for powerful queries into the unstructured data. For example, a query could efficiently find "All activities where input\_data-\>\>'class' equals 'business'" across the entire database, enabling analytics on travel policy compliance without strict schema constraints.

---

## **Part 4: Deep Dive \- Climatiq Feature Implementation**

This section details the specific logic required to implement the requested Climatiq features, mapping business requirements to technical execution.

### **4.1 Feature: Intermodal Freight**

Freight emissions are highly sensitive to the mode of transport and the specific route taken. The platform must support complex, multi-leg journeys.

Operational Logic:

The API endpoint https://api.climatiq.io/freight/v2/intermodal expects a route array and a cargo object. The implementation must abstract this complexity from the user via a "Route Builder" interface.1

Implementation Detail:

The FreightService in the backend must construct a payload that supports alternating locations and transport modes.

* **Location Validation:** Locations can be defined by generic text (query), IATA codes (iata), UN/LOCODEs (un\_locode), or coordinates (latitude/longitude). The service should prioritize UN/LOCODEs for sea freight accuracy.  
* **Transport Modes:** The service must enforce valid enums: road, rail, sea, air.  
* **Weight Handling:** The cargo object requires a weight and weight\_unit. The frontend must normalize user inputs (e.g., kg, tonnes, lbs) into accepted API units (kg, t, ton, lb).

**Sample Payload Construction:**

JSON  
{  
  "route":,  
  "cargo": {  
    "weight": 100,  
    "weight\_unit": "t"  
  }  
}

**Scope Classification:** Freight emissions paid for by the reporting company for goods they do not own the transport vehicles for are typically **Scope 3, Category 4 (Upstream Transportation and Distribution)** or **Category 9 (Downstream)**. The system logic must default to Scope 3 unless configured otherwise.

### **4.2 Feature: Travel (Activity & Spend-based)**

Travel emissions require a dual approach: high-precision activity data (distance/class) and proxy spend-based data (general ledger entries).

Activity-Based Implementation (/travel/v1/distance):

This method is used when itinerary data is available.

* **Air Travel:** The system must capture air\_details. Specifically, the class field (economy, business, first) is critical; business class seats occupy more space and thus are allocated a higher carbon share (often 2-3x economy).1  
* **Car Travel:** The system must capture car\_details, specifically car\_type (petrol, diesel, hybrid, battery). For battery (EVs), the emissions calculated are indirect (electricity generation), whereas petrol involves direct combustion.  
* **Data Fields:** The backend must parse origin and destination objects similar to freight, utilizing IATA codes for airports to ensure accurate Great Circle Distance calculations.1

Spend-Based Implementation (/travel/v1/spend):

Used when only financial records exist.

* **Endpoint:** https://preview.api.climatiq.io/travel/v1-preview1/spend.  
* **Inflation Logic:** The backend **must** pass the spend\_year. If a user spent $1000 in 2020, but the emission factor is from 2023, the purchasing power differs. Climatiq automatically adjusts for this inflation if the year is provided.  
* **Location Sensitivity:** The spend\_location is vital. A $1000 hotel stay in South Africa (coal-heavy grid) emits significantly more CO2 than in Switzerland (hydro/nuclear grid) due to energy intensity differences. The system must prompt the user for location to avoid generic global averages.1

### **4.3 Feature: Energy (Electricity & Fuel)**

Energy calculations are the foundation of Scope 1 and 2 reporting.

**Electricity (/energy/v1/electricity):**

* **Region Specificity:** The region field is mandatory for accuracy. The system should present a dropdown of regions (e.g., US-CA, DE, FR).  
* **Connection Type:** The backend must handle the optional connection\_type. Users should be able to specify direct if they have a dedicated line to a power plant, otherwise grid is the default.  
* **Market-Based Reporting:** To support market-based Scope 2 reporting, the payload must support the recs (Renewable Energy Certificates) object. If a company purchases 1000 kWh of Green Power, this is passed in recs, effectively zeroing out the carbon for that portion.1

**Fuel (/energy/v1/fuel):**

* **Fuel Types:** The system must validate inputs against the supported fuel list (natural\_gas, diesel, biodiesel\_bio\_100).  
* **Biogenic Reporting:** For biofuels (e.g., biodiesel), the API returns biogenic\_emissions separate from fossil CO2e. The database schema must store this value separately, as GHG Protocol requires biogenic emissions to be reported "outside of scopes".1

### **4.4 Feature: Procurement & Classification**

This feature automates Scope 3.1 (Purchased Goods and Services) using the endpoint https://api.climatiq.io/classifications/v1/estimate.1

**Implementation Detail:**

* **Classification Schemes:** The database must be capable of storing various code standards. The API supports mcc (Merchant Category Codes), isic4 (International Standard Industrial Classification), nace2, and unspsc.  
* **Selector Logic:** The user interface should allow selecting the scheme. If a user enters an MCC code 742 (Veterinary Services) and a spend amount, the backend wraps this in the classification object.  
* **Region Nuance:** A purchase of "Textiles" in India (IN) has a different carbon intensity than in Italy (IT). The backend must default the region to the organization's home region if not specified, but allow override per transaction.1

### **4.5 Feature: Autopilot (AI Classification)**

Autopilot uses NLP to map unstructured text (e.g., "100x Dell Latitude Laptops") to specific emission factors, solving the "data gap" problem.

**Workflow:**

1. **Suggest:** The user types a description. The frontend debounces this input and calls the backend, which proxies the request to https://preview.api.climatiq.io/autopilot/v1-preview3/suggest.  
   * *Parameters:* The backend should filter by domain (general or manufacturing) to refine results.  
   * *Response:* The API returns a list of candidates with confidence scores.  
2. **Selection & Feedback:** The user selects the best match (e.g., "Computers \- Manufacturing").  
3. **Estimate:** The system performs the calculation using the estimate endpoint with the confirmed match.  
4. **Learning:** Crucially, when a user confirms a match for "Dell Latitude," the system saves this pair in the custom\_mappings table. Future uploads containing "Dell Latitude" will bypass Autopilot and use the stored mapping directly, improving performance and consistency.1

---

## **Part 5: Advanced Implementation Guidelines**

### **5.1 Robust Batch Estimation Strategy**

Processing a CSV with 50,000 procurement records requires a robust asynchronous pipeline.

**Process Flow:**

1. **Ingestion:** User uploads a CSV. The frontend ensures headers map to expected fields.  
2. **Storage:** The file is streamed to an S3-compatible object store (MinIO or AWS S3).  
3. **Job Creation:** A batch\_job record is created in Postgres (status: queued).  
4. **Celery Task:** A task is pushed to Redis. The worker downloads the file and utilizes **Pandas** to read it efficiently.  
5. **Chunking:** The worker splits the dataframe into chunks of **100 records** (Climatiq's batch limit).  
6. **Parallel Requests:** The worker sends these chunks to the Batch Endpoint (/estimate/batch) in parallel (using asyncio.gather within the worker).  
7. **Error Handling:** The Batch endpoint returns 200 OK even if individual lines fail. The worker must iterate through the results array.  
   * *Success:* Calculated CO2e is stored in emission\_activities.  
   * *Failure:* The specific error (e.g., "Invalid Region") is added to the error\_log JSONB column in the batch\_job table.  
8. **Completion:** Once all chunks are processed, the job status is updated to completed or partial\_failure. The user is notified via the frontend polling mechanism.11

### **5.2 Redis Caching Strategy**

Emission factors are static for long periods. Repeatedly querying the API for "Electricity in GB for 2023" is inefficient.

**Strategy:**

* **Key Construction:** Keys must be deterministic. Format: climatiq:factor:{activity\_id}:{region}:{year}:{data\_version}.  
* **TTL (Time-To-Live):** Set to 24 hours.  
* **Pattern:** Implement a "Cache-Aside" pattern.  
  1. Check Redis. If hit, return data.  
  2. If miss, call Climatiq API.  
  3. Store result in Redis with TTL.  
  4. Return result.  
* **Stale-While-Revalidate:** For critical paths, serve the stale cache immediately while triggering a background task to refresh the data, ensuring zero-latency for the user.15

### **5.3 Scope Classification Logic**

The system must automatically classify the **Greenhouse Gas Protocol Scope** (1, 2, or 3\) based on the inputs.

**Logic Matrix:**

* **Scope 1 (Direct):** If activity\_type is energy AND sub\_type is fuel (combustion).  
* **Scope 2 (Indirect Energy):** If activity\_type is energy AND sub\_type is electricity OR heat OR steam.  
* **Scope 3 (Value Chain):**  
  * If activity\_type is travel (Business Travel \- Category 6).  
  * If activity\_type is freight (Upstream Transportation \- Category 4).  
  * If activity\_type is procurement (Purchased Goods \- Category 1).  
  * *Exception:* If the freight/travel is in vehicles *owned* by the company, it becomes Scope 1\. The UI must provide a "Company Owned Asset?" toggle to override this default logic.

---

## **Part 6: Frontend Architecture (Next.js)**

### **6.1 Component Architecture**

The frontend mirrors the backend's domain separation.

* **components/freight/RouteBuilder.tsx:** A stateful component managing the multi-step route creation. It uses a dynamic list to allow users to "Add Leg" to the journey.  
* **components/autopilot/SmartClassifier.tsx:** An interactive input field. As the user types, it fires debounced requests to the suggest endpoint and renders a dropdown of candidates with confidence badges (e.g., "95% Match").  
* **components/dashboard/EmissionsChart.tsx:** Uses a library like **Recharts** to visualize the JSON data from emission\_activities, grouping by scope or activity\_type.

### **6.2 State Management and Polling**

For batch jobs, we utilize **React Query** (TanStack Query).

* **Pattern:** When a file is uploaded, a mutation is fired. On success, the UI enters a "Processing" state.  
* **Polling:** A useQuery hook polls the /api/v1/tasks/{job\_id} endpoint every 2 seconds.  
* **Updates:** When the status changes to completed, the query invalidates the activities list cache, automatically refreshing the dashboard with the new data.

---

## **Part 7: Deployment and Security**

### **7.1 Docker Composition**

The docker-compose.yml file defines the interactions.

YAML  
version: '3.8'

services:  
  db:  
    image: postgres:15-alpine  
    volumes:  
      \- postgres\_data:/var/lib/postgresql/data  
    environment:  
      \- POSTGRES\_USER=user  
      \- POSTGRES\_PASSWORD=password  
      \- POSTGRES\_DB=decarbonization

  redis:  
    image: redis:7-alpine  
    volumes:  
      \- redis\_data:/data

  backend:  
    build:   
      context:./backend  
      dockerfile: Dockerfile  
    command: uvicorn app.main:app \--host 0.0.0.0 \--port 8000 \--reload  
    volumes:  
      \-./backend:/app  
    environment:  
      \- DATABASE\_URL=postgresql://user:password@db/decarbonization  
      \- REDIS\_URL=redis://redis:6379/0  
      \- CLIMATIQ\_API\_KEY=${CLIMATIQ\_API\_KEY}  
    depends\_on:  
      \- db  
      \- redis

  celery\_worker:  
    build:  
      context:./backend  
      dockerfile: Dockerfile  
    command: celery \-A app.core.celery\_app worker \--loglevel=info  
    environment:  
      \- DATABASE\_URL=postgresql://user:password@db/decarbonization  
      \- REDIS\_URL=redis://redis:6379/0  
      \- CLIMATIQ\_API\_KEY=${CLIMATIQ\_API\_KEY}  
    depends\_on:  
      \- redis  
      \- db

  frontend:  
    build:  
      context:./frontend  
      dockerfile: Dockerfile  
    ports:  
      \- "3000:3000"  
    depends\_on:  
      \- backend

volumes:  
  postgres\_data:  
  redis\_data:

### **7.2 Security Considerations**

* **API Key Management:** The $CLIMATIQ\_API\_KEY is injected solely via environment variables. It serves as a "Bearer" token in the header of outgoing requests from the backend. The frontend **never** sees this key.  
* **Non-Root Containers:** All Dockerfiles should create a specific user (e.g., appuser) and switch to it using the USER instruction to prevent privilege escalation attacks.  
* **Rate Limiting:** Implementing a rate limiter (using Redis) on the FastAPI backend protects the system from abuse and ensures the application respects the Climatiq API rate limits (e.g., preventing cost overruns from excessive API calls).11

---

## **Conclusion**

This architectural blueprint provides a rigorous, technically comprehensive foundation for an AI-powered decarbonization platform. By strictly adhering to the modular monolith pattern and leveraging the asynchronous power of FastAPI and Celery, the system is engineered to handle the heavy computational loads of batch processing and complex freight logistics. The integration of Climatiq's Autopilot and specific domain endpoints ensures high-fidelity carbon accounting, transforming raw operational data into precise, auditable sustainability insights. This guide ensures that the implementation will not only meet current reporting requirements but is architected to scale with the evolving landscape of climate regulation.

