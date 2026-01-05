# Decarbonization Platform - Frontend Integration Guide

## Overview

This document provides all necessary information to build a Next.js frontend that integrates with the Decarbonization Platform backend.

---

## Environment Setup (WSL 2)

### System Info
- **OS**: Windows + WSL 2.6.1.0
- **Kernel**: 6.6.87.2-1
- **Backend Location**: `/home/dasaj/dev/ai_residency/Decarbonization_v2`

### Prerequisites
```bash
# In WSL terminal
node --version  # Should be 18+ for Next.js 14
npm --version

# If not installed:
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### Recommended Frontend Location
```bash
# Create frontend in same parent directory
cd /home/dasaj/dev/ai_residency/Decarbonization_v2
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir
```

---

## Backend API Reference

### Base URL
```
http://localhost:8000/api/v1
```

### API Documentation (Swagger)
```
http://localhost:8000/docs
```

---

## Authentication Endpoints

### POST `/auth/register`
Create new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass@123",
  "full_name": "John Doe",
  "organization_name": "Acme Corp"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "organization_id": "uuid",
  "created_at": "2025-01-01T00:00:00Z"
}
```

---

### POST `/auth/login`
Authenticate and get JWT token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass@123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

### GET `/auth/me`
Get current user info. **Requires Auth.**

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "organization_id": "uuid",
  "organization": {
    "id": "uuid",
    "name": "Acme Corp"
  }
}
```

---

## Project Endpoints

### POST `/projects/`
Create new project. **Requires Auth.**

**Request:**
```json
{
  "name": "2025 Q1 Emissions",
  "description": "Quarterly emissions report",
  "start_date": "2025-01-01",
  "end_date": "2025-03-31",
  "reporting_year": 2025
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "name": "2025 Q1 Emissions",
  "description": "Quarterly emissions report",
  "start_date": "2025-01-01",
  "end_date": "2025-03-31",
  "reporting_year": 2025,
  "organization_id": "uuid",
  "created_at": "2025-01-01T00:00:00Z"
}
```

---

### GET `/projects/`
List all projects for user's organization. **Requires Auth.**

**Response (200):**
```json
[
  {
    "id": "uuid",
    "name": "2025 Q1 Emissions",
    "description": "...",
    "reporting_year": 2025,
    "created_at": "2025-01-01T00:00:00Z"
  }
]
```

---

### GET `/projects/{project_id}`
Get single project. **Requires Auth.**

---

## Upload & Processing Endpoints

### POST `/upload/csv`
Upload CSV file for emissions calculation. **Requires Auth.**

**Request (multipart/form-data):**
- `file`: CSV file
- `project_id`: UUID string

**Response (200):**
```json
{
  "message": "CSV processing started",
  "job_id": "uuid",
  "total_records": 10,
  "file_name": "emissions.csv"
}
```

---

### GET `/batch/jobs`
List all batch jobs. **Requires Auth.**

**Response (200):**
```json
[
  {
    "id": "uuid",
    "status": "completed",
    "file_name": "emissions.csv",
    "total_records": 10,
    "processed_records": 10,
    "successful_records": 10,
    "failed_records": 0,
    "created_at": "2025-01-01T00:00:00Z",
    "completed_at": "2025-01-01T00:00:05Z"
  }
]
```

**Status values:** `pending`, `processing`, `completed`, `failed`

---

### GET `/batch/jobs/{job_id}`
Get specific batch job status. **Requires Auth.**

---

## Activity Endpoints

### GET `/activities/?project_id={uuid}`
List all activities for a project. **Requires Auth.**

**Response (200):**
```json
[
  {
    "id": "uuid",
    "activity_type": "electricity",
    "scope": "Scope 2",
    "co2e_kg": 3284.64,
    "co2e_unit": "kg",
    "region": "US",
    "activity_date": "2025-01-15",
    "input_data": {
      "description": "Office electricity",
      "amount": 8750.0,
      "unit": "kWh"
    },
    "created_at": "2025-01-01T00:00:00Z"
  }
]
```

---

### GET `/activities/project/{project_id}/summary`
Get project emissions summary. **Requires Auth.**

**Response (200):**
```json
{
  "project_id": "uuid",
  "total_activities": 10,
  "total_co2e_kg": 39776.77,
  "scope_breakdown": {
    "Scope 1": 11898.22,
    "Scope 2": 23180.15,
    "Scope 3": 4698.39
  },
  "activity_type_breakdown": {
    "electricity": 23180.15,
    "stationary_combustion": 11898.22,
    "business_travel": 966.27,
    "employee_commuting": 3732.12
  }
}
```

---

### DELETE `/activities/{activity_id}`
Delete an activity. **Requires Auth.**

---

## Data Models (TypeScript)

```typescript
// types/index.ts

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

export type Scope = 'Scope 1' | 'Scope 2' | 'Scope 3';

export type ActivityType = 
  | 'electricity'
  | 'stationary_combustion'
  | 'mobile_combustion'
  | 'business_travel'
  | 'employee_commuting'
  | 'purchased_goods'
  | 'waste';

export interface BatchJob {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  file_name: string;
  total_records: number;
  processed_records: number;
  successful_records: number;
  failed_records: number;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface ProjectSummary {
  project_id: string;
  total_activities: number;
  total_co2e_kg: number;
  scope_breakdown: Record<Scope, number>;
  activity_type_breakdown: Record<string, number>;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}
```

---

## CSV Upload Format

The backend expects CSV files with these columns:

| Column | Required | Description | Example |
|--------|----------|-------------|---------|
| description | Yes | Activity description | "Office electricity usage" |
| amount | Yes | Numeric value | 8750 |
| unit | Yes | Unit of measurement | kWh, gal, mi, USD |
| date | No | Activity date | 2025-01-15 |
| region | No | ISO region code | US, GB, DE |

**Example CSV:**
```csv
description,amount,unit,date,region
Quarterly electricity usage,8750,kWh,2025-01-15,US
Natural gas for heating,325,therms,2025-01-25,US
Diesel fuel for vehicles,620,gal,2025-02-12,US
Business flight NYC to LAX,1850,mi,2025-03-05,US
Employee commute survey,12500,mi,2025-03-20,US
```

---

## Recommended Next.js Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx                 # Dashboard home
│   │   │   ├── projects/
│   │   │   │   ├── page.tsx             # Project list
│   │   │   │   ├── new/page.tsx         # Create project
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx         # Project detail
│   │   │   │       └── upload/page.tsx  # CSV upload
│   │   │   └── settings/page.tsx
│   │   ├── layout.tsx
│   │   └── page.tsx                     # Landing page
│   ├── components/
│   │   ├── ui/                          # Shadcn/UI components
│   │   ├── charts/
│   │   │   ├── ScopeChart.tsx
│   │   │   └── ActivityBreakdown.tsx
│   │   ├── forms/
│   │   │   ├── LoginForm.tsx
│   │   │   └── ProjectForm.tsx
│   │   └── layout/
│   │       ├── Navbar.tsx
│   │       └── Sidebar.tsx
│   ├── lib/
│   │   ├── api.ts                       # API client
│   │   ├── auth.ts                      # Auth utilities
│   │   └── utils.ts
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useProjects.ts
│   │   └── useActivities.ts
│   ├── types/
│   │   └── index.ts                     # TypeScript types
│   └── styles/
│       └── globals.css
├── public/
├── .env.local
├── next.config.js
├── tailwind.config.js
└── package.json
```

---

## Environment Variables

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## API Client Example

```typescript
// src/lib/api.ts

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

class ApiClient {
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('token', token);
    }
  }

  getToken(): string | null {
    if (this.token) return this.token;
    if (typeof window !== 'undefined') {
      return localStorage.getItem('token');
    }
    return null;
  }

  clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken();
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      this.clearToken();
      window.location.href = '/login';
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'API Error');
    }

    return response.json();
  }

  // Auth
  async register(data: RegisterData) {
    return this.request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async login(email: string, password: string) {
    const response = await this.request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(response.access_token);
    return response;
  }

  async getMe() {
    return this.request<User>('/auth/me');
  }

  // Projects
  async getProjects() {
    return this.request<Project[]>('/projects/');
  }

  async createProject(data: CreateProjectData) {
    return this.request<Project>('/projects/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getProject(id: string) {
    return this.request<Project>(`/projects/${id}`);
  }

  // Upload
  async uploadCSV(projectId: string, file: File) {
    const token = this.getToken();
    const formData = new FormData();
    formData.append('file', file);
    formData.append('project_id', projectId);

    const response = await fetch(`${API_URL}/upload/csv`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Upload failed');
    }

    return response.json();
  }

  // Batch Jobs
  async getBatchJobs() {
    return this.request<BatchJob[]>('/batch/jobs');
  }

  async getBatchJob(id: string) {
    return this.request<BatchJob>(`/batch/jobs/${id}`);
  }

  // Activities
  async getActivities(projectId: string) {
    return this.request<Activity[]>(`/activities/?project_id=${projectId}`);
  }

  async getProjectSummary(projectId: string) {
    return this.request<ProjectSummary>(`/activities/project/${projectId}/summary`);
  }

  async deleteActivity(id: string) {
    return this.request(`/activities/${id}`, { method: 'DELETE' });
  }
}

export const api = new ApiClient();
```

---

## Recommended Libraries

```bash
# Core
npm install @tanstack/react-query axios recharts

# UI Components (choose one)
npx shadcn-ui@latest init  # Recommended
# or
npm install @radix-ui/themes

# Forms
npm install react-hook-form zod @hookform/resolvers

# File upload
npm install react-dropzone

# Date handling
npm install date-fns

# Icons
npm install lucide-react
```

---

## Key Features to Implement

1. **Authentication**
   - Login/Register forms
   - Token storage (localStorage)
   - Protected routes
   - Auto-redirect on 401

2. **Dashboard**
   - Total emissions summary
   - Scope breakdown pie chart
   - Activity type bar chart
   - Recent projects list

3. **Projects**
   - Create new project
   - List all projects
   - Project detail with activities

4. **CSV Upload**
   - Drag & drop file upload
   - Upload progress
   - Job status polling
   - Success/error feedback

5. **Activities View**
   - Table with sorting/filtering
   - Scope/type filters
   - Export to CSV
   - Delete functionality

6. **Charts (using Recharts)**
   - Scope breakdown (pie/donut)
   - Activity types (bar)
   - Monthly trends (line)
   - Comparison charts

---

## CORS Configuration

The backend is already configured to allow localhost origins. If you get CORS errors, the backend allows:
- `http://localhost:3000` (Next.js dev)
- `http://localhost:8000` (Backend)

---

## Testing Backend Connection

Before building the frontend, verify the backend is running:

```bash
# Health check
curl http://localhost:8000/health

# Should return: {"status": "healthy"}
```

---

## Quick Start Commands

```bash
# Terminal 1: Start backend
cd /home/dasaj/dev/ai_residency/Decarbonization_v2
docker compose up

# Terminal 2: Create and start frontend
cd /home/dasaj/dev/ai_residency/Decarbonization_v2
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir
cd frontend
npm run dev

# Frontend will be at: http://localhost:3000
# Backend API at: http://localhost:8000/api/v1
# API docs at: http://localhost:8000/docs
```
