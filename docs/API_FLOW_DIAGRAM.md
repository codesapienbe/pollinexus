# Pollinexus API Flow & Endpoints Guide

## API Architecture Overview

```mermaid
graph TB
    subgraph "Client Applications"
        A[Web Frontend]
        B[Mobile App]
        C[Data Science Tools]
        D[Environmental Agencies]
    end
    
    subgraph "API Gateway & Security"
        E[FastAPI Application]
        F[Security Middleware]
        G[CORS Middleware]
        H[Request Logging]
    end
    
    subgraph "Authentication & Users"
        I[User Registration]
        J[OTP Verification]
        K[JWT Tokens]
        L[User Management]
    end
    
    subgraph "Core Services"
        M[Dataset Management]
        N[Data Analysis]
        O[Visualizations]
        P[Background Tasks]
    end
    
    subgraph "Data Layer"
        Q[SQLite Database]
        R[DuckDB Analytics]
        S[File Storage]
        T[Redis Cache]
    end
    
    subgraph "Monitoring & Health"
        U[Health Checks]
        V[Logging System]
        W[Metrics Collection]
        X[Error Tracking]
    end
    
    A --> E
    B --> E
    C --> E
    D --> E
    
    E --> F
    E --> G
    E --> H
    
    E --> I
    E --> J
    E --> K
    E --> L
    
    E --> M
    E --> N
    E --> O
    E --> P
    
    M --> Q
    M --> S
    N --> Q
    N --> R
    O --> Q
    O --> R
    P --> T
    
    E --> U
    E --> V
    E --> W
    E --> X
```

## API Endpoint Flow Sequence

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI App
    participant Auth as Authentication
    participant Dataset as Dataset Service
    participant Analysis as Analysis Service
    participant Viz as Visualization Service
    participant DB as Database
    participant Redis as Redis Cache
    participant Celery as Background Tasks

    Note over Client, Celery: 1. Initial Setup & Health Check
    Client->>API: GET /api/v1/health
    API->>Client: Health Status
    
    Client->>API: GET /api/v1/info
    API->>Client: API Information
    
    Note over Client, Celery: 2. User Authentication Flow
    Client->>API: POST /user/register
    API->>Auth: Create User
    Auth->>Client: User Created + OTP Sent
    
    Client->>API: POST /user/verify-registration
    API->>Auth: Verify OTP
    Auth->>Client: JWT Token
    
    Client->>API: POST /user/login
    API->>Auth: Send Login OTP
    Auth->>Client: OTP Sent
    
    Client->>API: POST /user/verify-login
    API->>Auth: Verify Login OTP
    Auth->>Client: JWT Token
    
    Note over Client, Celery: 3. Dataset Management Flow
    Client->>API: POST /api/v1/datasets/ (with file)
    API->>Dataset: Upload & Process File
    Dataset->>DB: Store Dataset Metadata
    Dataset->>Client: Dataset Created
    
    Client->>API: GET /api/v1/datasets/
    API->>Dataset: Get Datasets
    Dataset->>DB: Query Datasets
    Dataset->>Client: Dataset List
    
    Client->>API: GET /api/v1/datasets/{dataset_id}
    API->>Dataset: Get Dataset Details
    Dataset->>DB: Query Dataset
    Dataset->>Client: Dataset Details
    
    Note over Client, Celery: 4. Data Analysis Flow
    Client->>API: POST /api/v1/analysis/bee-preferences/
    API->>Analysis: Start Analysis
    Analysis->>Celery: Queue Analysis Task
    Analysis->>Client: Task ID
    
    Client->>API: GET /api/v1/analysis/jobs/{job_id}
    API->>Analysis: Get Job Status
    Analysis->>Celery: Check Task Status
    Analysis->>Client: Job Status
    
    Client->>API: GET /api/v1/analysis/jobs/{job_id}/result
    API->>Analysis: Get Results
    Analysis->>Redis: Get Cached Results
    Analysis->>Client: Analysis Results
    
    Note over Client, Celery: 5. Visualization Flow
    Client->>API: POST /api/v1/visualizations/bee-distribution/
    API->>Viz: Create Visualization
    Viz->>Celery: Queue Viz Task
    Viz->>Client: Task ID
    
    Client->>API: GET /api/v1/visualizations/{viz_id}
    API->>Viz: Get Visualization
    Viz->>Redis: Get Cached Viz
    Viz->>Client: Visualization Data
    
    Note over Client, Celery: 6. Monitoring & Metrics
    Client->>API: GET /api/v1/monitoring/metrics/
    API->>Client: System Metrics
    
    Client->>API: GET /api/v1/health/detailed
    API->>Client: Detailed Health Status
```

## Detailed API Endpoints Flow

```mermaid
flowchart TD
    Start([Start]) --> Health{Health Check}
    Health -->|Success| Info[Get API Info]
    Health -->|Failed| Error[System Error]
    
    Info --> Auth{Authentication Required?}
    Auth -->|Yes| Register[User Registration]
    Auth -->|No| Public[Public Endpoints]
    
    Register --> Verify[Email Verification]
    Verify --> Login[User Login]
    Login --> OTP[OTP Verification]
    OTP --> Token[JWT Token Generated]
    
    Token --> Dataset{Upload Dataset?}
    Dataset -->|Yes| Upload[Upload Dataset File]
    Dataset -->|No| List[List Datasets]
    
    Upload --> Checksum[Calculate File Checksum]
    Checksum --> Duplicate{Duplicate File?}
    Duplicate -->|Yes| DuplicateError[409 Conflict Error]
    Duplicate -->|No| Store[Store Dataset]
    
    Store --> Analysis{Run Analysis?}
    Analysis -->|Yes| AnalysisJob[Start Analysis Job]
    Analysis -->|No| Viz{Create Visualization?}
    
    AnalysisJob --> Celery[Queue Celery Task]
    Celery --> Status[Check Job Status]
    Status --> Complete{Job Complete?}
    Complete -->|No| Status
    Complete -->|Yes| Results[Get Analysis Results]
    
    Viz -->|Yes| VizJob[Start Visualization Job]
    Viz -->|No| Monitor{Monitor System?}
    
    VizJob --> VizCelery[Queue Visualization Task]
    VizCelery --> VizStatus[Check Viz Status]
    VizStatus --> VizComplete{Viz Complete?}
    VizComplete -->|No| VizStatus
    VizComplete -->|Yes| VizResults[Get Visualization]
    
    Monitor -->|Yes| Metrics[Get System Metrics]
    Monitor -->|No| End([End])
    
    Metrics --> HealthCheck[Detailed Health Check]
    HealthCheck --> End
    
    Public --> End
    List --> Analysis
    Results --> Viz
    VizResults --> Monitor
    DuplicateError --> End
    Error --> End
```

## User Journey Flow

```mermaid
journey
    title Pollinexus API User Journey
    section New User Onboarding
      Health Check: 5: API
      Register Account: 4: User
      Verify Email: 3: User
      Upload First Dataset: 5: User
      Run Initial Analysis: 4: User
      View Results: 5: User
    section Regular User Workflow
      Login: 3: User
      View Datasets: 4: User
      Upload New Data: 4: User
      Run Analysis: 5: User
      Create Visualizations: 4: User
      Export Results: 3: User
    section Advanced User Workflow
      Batch Processing: 5: User
      Custom Analysis: 5: User
      Dashboard Creation: 4: User
      Data Export: 3: User
      System Monitoring: 2: User
```

## System Components Interaction

```mermaid
graph LR
    subgraph "Frontend Layer"
        A[Web UI]
        B[Mobile App]
        C[CLI Tools]
    end
    
    subgraph "API Layer"
        D[FastAPI Router]
        E[Middleware Stack]
        F[Authentication]
    end
    
    subgraph "Service Layer"
        G[Dataset Service]
        H[Analysis Service]
        I[Visualization Service]
        J[User Service]
    end
    
    subgraph "Data Layer"
        K[SQLite DB]
        L[DuckDB]
        M[File Storage]
        N[Redis Cache]
    end
    
    subgraph "Background Processing"
        O[Celery Workers]
        P[Task Queue]
        Q[Result Backend]
    end
    
    subgraph "Monitoring"
        R[Health Checks]
        S[Logging System]
        T[Metrics Collection]
        U[Error Tracking]
    end
    
    A --> D
    B --> D
    C --> D
    
    D --> E
    E --> F
    
    F --> G
    F --> H
    F --> I
    F --> J
    
    G --> K
    G --> M
    H --> K
    H --> L
    I --> K
    I --> L
    J --> K
    
    H --> O
    I --> O
    O --> P
    O --> Q
    O --> N
    
    D --> R
    D --> S
    D --> T
    D --> U
```

## API Endpoints Summary

### Health & Information
- `GET /api/v1/health` - Quick health check
- `GET /api/v1/health/detailed` - Comprehensive health status
- `GET /api/v1/info` - API information and capabilities
- `GET /api/v1/` - Root endpoint
- `GET /api/v1/security/status` - Security monitoring status
- `GET /api/v1/metrics` - System metrics

### User Authentication
- `POST /user/register` - Register new user
- `POST /user/send-verification` - Send verification code
- `POST /user/verify-registration` - Verify registration OTP
- `POST /user/login` - Request login OTP
- `POST /user/verify-login` - Verify login OTP
- `GET /api/v1/user/me` - Get current user info

### Dataset Management
- `POST /api/v1/datasets/` - Upload new dataset
- `GET /api/v1/datasets/` - List all datasets
- `GET /api/v1/datasets/{id}` - Get specific dataset
- `PUT /api/v1/datasets/{id}` - Update dataset
- `DELETE /api/v1/datasets/{id}` - Delete dataset
- `POST /api/v1/datasets/search` - Search datasets
- `POST /api/v1/datasets/filter` - Filter datasets
- `GET /api/v1/datasets/{id}/health` - Dataset health check

### Data Analysis
- `POST /api/v1/analysis/bee-preferences/` - Bee preferences analysis
- `POST /api/v1/analysis/plant-recommendations/` - Plant recommendations
- `POST /api/v1/analysis/seasonal/` - Seasonal analysis
- `POST /api/v1/analysis/site-comparison/` - Site comparison
- `GET /api/v1/analysis/jobs/` - List analysis jobs
- `GET /api/v1/analysis/jobs/{id}` - Get job status
- `GET /api/v1/analysis/jobs/{id}/result` - Get job results
- `DELETE /api/v1/analysis/jobs/{id}` - Cancel job

### Visualizations
- `POST /api/v1/visualizations/bee-distribution/` - Bee distribution plot
- `POST /api/v1/visualizations/seasonal-patterns/` - Seasonal patterns
- `POST /api/v1/visualizations/site-comparison/` - Site comparison plot
- `POST /api/v1/visualizations/dashboard/` - Interactive dashboard
- `GET /api/v1/visualizations/{id}` - Get visualization
- `POST /api/v1/visualizations/batch/` - Batch visualization
- `GET /api/v1/visualizations/jobs/` - List viz jobs
- `GET /api/v1/visualizations/jobs/{id}` - Get viz job status
- `DELETE /api/v1/visualizations/jobs/{id}` - Cancel viz job

### Monitoring
- `GET /api/v1/monitoring/metrics/` - Get monitoring metrics
- `POST /api/v1/monitoring/metrics/reset/` - Reset monitoring metrics

## Key Features

- **File Upload with Checksum Validation**: Prevents duplicate uploads
- **Background Processing**: Long-running tasks via Celery
- **Real-time Monitoring**: Job status and system metrics
- **Comprehensive Logging**: Structured JSON logs with correlation IDs
- **Security Middleware**: Rate limiting, input validation, CORS
- **Health Checks**: System and component health monitoring
- **User Authentication**: OTP-based email verification
- **Data Analysis**: Bee preferences, plant recommendations, seasonal analysis
- **Visualizations**: Interactive plots and dashboards 