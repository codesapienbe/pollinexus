# PolliNexus API — Speech Notes for Presentations

## Intro Speech (Data Science + Programming Understanding)

>> 🎯 As a postgraduate AI student at EHB, I approach PolliNexus with a full-stack data mindset: define clear hypotheses, assess data quality, and apply domain-aware cleaning before modeling.
>> 🔄 I favor interpretable methods and report metrics honestly, highlighting feature importance and limitations—principles I've learned in my data science and machine learning studies.
>> 🛡️ On the engineering side, I design secure, observable, and maintainable systems—validation on inputs, structured logging, health/metrics endpoints, and clear API contracts—so analysis scales from a notebook into reliable services. It's like building a restaurant where the kitchen is open, the food is great, and the service is consistent!

**💡 Simple Explanation**: Think of this project like building a restaurant from scratch! Instead of just cooking in your kitchen, we're creating a full restaurant with a menu (API), kitchen staff (servers), quality control (validation), and customer service (monitoring). The "full-stack data mindset" means we think about everything from how ingredients arrive (data ingestion) to how customers order (user interface) to how we track what's popular (analytics). It's like going from a home cook to a restaurant owner who needs to think about the entire dining experience!

## System Architecture Overview

### Core Design Principles

PolliNexus follows a **microservice-inspired architecture** with clear separation of concerns:

- **API Layer** (`src/pollinexus/api/`): FastAPI-based REST endpoints with automatic OpenAPI documentation
- **Core Services** (`src/pollinexus/core/`): Authentication, configuration, database, logging, metrics, and security
- **Data Services** (`src/pollinexus/services/`): Business logic for data processing, database operations, and DuckDB analytics
- **Task Processing** (`src/pollinexus/tasks/`): Celery-based asynchronous job processing for ML and visualization
- **Models** (`src/pollinexus/models/`): Pydantic schemas for request/response validation and SQLAlchemy ORM models

### Data Science Pipeline Architecture

The system implements a **production-grade ML pipeline**:

1. **Data Ingestion**: CSV upload with automatic schema detection and validation
2. **Data Quality Assessment**: Missing value analysis, type validation, domain-specific checks
3. **Feature Engineering**: Temporal features (month, season), categorical encoding, composite metrics
4. **Model Training**: Interpretable ML (Random Forest) with feature importance analysis
5. **Result Generation**: Structured outputs with confidence scores and business metrics
6. **Visualization**: Automated chart generation with configurable parameters

### Security & Observability

- **Authentication**: JWT-based with OTP verification for secure access
- **Input Validation**: Pydantic models with comprehensive type checking
- **Structured Logging**: JSON-formatted logs with correlation IDs for traceability
- **Health Monitoring**: Comprehensive health checks with dependency status
- **Metrics Collection**: Prometheus-compatible metrics for operational insights

Follow these steps to validate the API end-to-end. Replace placeholders like <EMAIL>, <OTP>, <JWT>, <DATASET_ID>, <JOB_ID>, <VIS_ID>, <TASK_ID>.

## Reference by Tag Group

- Health & Information: [docs/api-groups/api-health-info.md](api-groups/api-health-info.md)
- User Authentication & Accounts: [docs/api-groups/api-auth.md](api-groups/api-auth.md)
- Dataset Management: [docs/api-groups/api-datasets.md](api-groups/api-datasets.md)
- Data Analysis: [docs/api-groups/api-analysis.md](api-groups/api-analysis.md)
- Visualizations: [docs/api-groups/api-visualizations.md](api-groups/api-visualizations.md)
- Monitoring: [docs/api-groups/api-monitoring.md](api-groups/api-monitoring.md)

## 0) Base setup (Makefile-driven)

>> 🛠️ First, I'll spin up the API using the project's Makefile so the environment is reproducible and aligned with dev workflows—a practice I've learned in my software engineering studies at EHB for ensuring consistent development environments. It's like having a recipe that works every time, no matter whose kitchen you're in!

**💡 Simple Explanation**: A Makefile is like a master recipe book that tells the computer exactly how to set up and run our project! Just like how a recipe tells you step-by-step how to make a dish, the Makefile tells the computer step-by-step how to start our API. This ensures that whether you're working on your laptop, a colleague's computer, or a server in the cloud, the setup process is exactly the same. It's like having a standardized recipe that works in any kitchen, with any cook, using any stove!

### Environment Management Strategy

The Makefile provides **consistent deployment patterns** across different environments:

- **Local Development**: Uses `uv` for fast dependency management and virtual environment isolation
- **Docker Containerization**: Ensures reproducible deployments with all dependencies bundled
- **Remote VM**: Supports cloud deployment with proper networking and service discovery

### Infrastructure Components

- **Database**: SQLite for development, PostgreSQL for production (configurable)
- **Message Queue**: Redis for Celery task processing and caching
- **File Storage**: Local filesystem with configurable upload directories
- **Monitoring**: Prometheus metrics endpoint and structured logging

- Local API (uv):

```bash
make run-local
```

- Docker API:

```bash
make run-docker
```

- Remote VM API:

```bash
make run-remote
```

## 1) Health, info, quick checks

>> 🚗 Before any workflow, I verify health, detailed status, and basic API info to ensure a clean baseline—a systematic approach I've learned in my data science studies at EHB for validating system readiness. It's like checking your car before a long road trip—you want to make sure everything is working before you hit the highway!

**💡 Simple Explanation**: Health checks are like giving your car a quick inspection before a long trip! You check the oil, tire pressure, and make sure the engine starts properly. In our API, we do the same thing—we check if the database is connected, if all the services are running, and if the system is ready to handle requests. It's like having a dashboard that shows you the "vital signs" of your system, so you know everything is working properly before you start using it. This prevents problems later, just like how checking your car prevents breakdowns on the highway!

### Health Check Architecture

The health system implements **layered monitoring**:

- **Basic Health**: Simple alive/dead status for load balancers
- **Detailed Health**: Deep dependency checks (database, Redis, file system)
- **Metrics**: Performance counters and business KPIs
- **Info**: System configuration and version details

### Monitoring Strategy

- **Dependency Health**: Database connectivity, Redis availability, disk space
- **Performance Metrics**: Request latency, error rates, queue depths
- **Business Metrics**: Dataset counts, job success rates, user activity
- **Security Status**: Authentication failures, rate limiting, suspicious activity

- Makefile health targets (local):

```bash
make health
make health-detailed
```

- Direct API checks:

```bash
curl "http://localhost:8000/api/v1/health"
curl "http://localhost:8000/api/v1/health/detailed"
curl "http://localhost:8000/api/v1/info"
curl "http://localhost:8000/api/v1/metrics"
```

## 2) (Optional) Auth flow to get a JWT

>> 🎫 If I want to demonstrate authentication, I'll register, verify OTP, and fetch a JWT, then call a protected endpoint—implementing security practices I've studied in my software engineering program at EHB. It's like having a bouncer at a club who checks your ID and gives you a wristband!

**💡 Simple Explanation**: Authentication is like getting into a VIP club! First, you register with your email (like putting your name on a guest list), then you get a special code sent to your phone (OTP), and once you show that code, you get a wristband (JWT token) that lets you access different areas of the club. The wristband proves you're allowed to be there, and different wristbands might give you access to different areas. In our API, the JWT token is like that wristband—it proves you're a legitimate user and tells the system what you're allowed to access. It's much safer than passwords because the code expires quickly and can't be reused!

### Authentication Architecture

The auth system implements **multi-factor security**:

- **Registration Flow**: Email verification with OTP to prevent fake accounts
- **Login Flow**: OTP-based authentication for enhanced security
- **JWT Tokens**: Stateless authentication with configurable expiration
- **Rate Limiting**: Prevents brute force attacks on auth endpoints

### Security Features

- **Passwordless Authentication**: Eliminates password storage and related vulnerabilities
- **OTP Expiration**: Time-limited codes prevent replay attacks
- **JWT Refresh**: Automatic token renewal with secure rotation
- **Audit Logging**: All authentication events logged for security monitoring

- Register (sends OTP to email)

```bash
curl -X POST "http://localhost:8000/api/v1/user/register" \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Test User","email":"<EMAIL>","phone":"+10000000000"}'
```

- Send verification code again if needed

```bash
curl -X POST "http://localhost:8000/api/v1/user/send-verification" \
  -H "Content-Type: application/json" \
  -d '{"email":"<EMAIL>","verification_type":"email"}'
```

- Verify registration (use the OTP you received); receives JWT

```bash
curl -X POST "http://localhost:8000/api/v1/user/verify-registration" \
  -H "Content-Type: application/json" \
  -d '{"email":"<EMAIL>","otp":"<OTP>"}'
```

- Login OTP (later, when logging in)

```bash
curl -X POST "http://localhost:8000/api/v1/user/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"<EMAIL>"}'
```

- Verify login to get JWT

```bash
curl -X POST "http://localhost:8000/api/v1/user/verify-login" \
  -H "Content-Type: application/json" \
  -d '{"email":"<EMAIL>","otp":"<OTP>"}'
```

- Check profile

```bash
curl -H "Authorization: Bearer <JWT>" "http://localhost:8000/api/v1/user/me"
```

## 3) Upload dataset (plants_and_bees.csv)

>> 📤 Next, I'll upload the plants-and-bees dataset to enable downstream analysis and visualization—applying data ingestion techniques I've learned in my data science studies at EHB. It's like importing all the ingredients into your kitchen before you start cooking!

**💡 Simple Explanation**: Data upload is like bringing all your ingredients into the kitchen before you start cooking! Just like how a chef needs to have all the vegetables, meat, and spices ready before starting to cook, we need to upload our bee and plant data into the system before we can analyze it. The system checks the data (like checking if ingredients are fresh), organizes it (like sorting ingredients by type), and makes it ready for processing (like prepping vegetables). This ensures that all our analysis and visualizations will have the data they need to work properly, just like how having all ingredients ready makes cooking much easier!

### Data Ingestion Pipeline

The upload system implements **robust data handling**:

- **File Validation**: Size limits, format checking, virus scanning
- **Schema Detection**: Automatic column type inference and validation
- **Data Quality Checks**: Missing value analysis, outlier detection
- **Metadata Extraction**: File statistics, column summaries, data lineage

### Ecological Data Context

The plants_and_bees.csv contains **pollinator ecology data**:

- **Temporal Data**: Date/time of observations for seasonal analysis
- **Spatial Data**: Site locations for geographic patterns
- **Species Data**: Plant and bee species for biodiversity analysis
- **Abundance Data**: Visit counts and population estimates
- **Environmental Data**: Weather conditions, sampling methods

```bash
curl -X POST "http://localhost:8000/api/v1/datasets/" \
  -F "name=Plants and Bees Dataset" \
  -F "description=Sample pollinator data" \
  -F "file=@dataset/plants_and_bees.csv"
```

## 4) Inspect datasets

>> 🔍 I confirm ingestion with list/get, then pull dataset info and a health check to validate integrity and stats—following data validation practices I've learned in my data science studies at EHB. It's like doing a quality check on your ingredients before you start cooking—you want to make sure everything is fresh and properly labeled!

**💡 Simple Explanation**: Dataset inspection is like doing a quality check on your ingredients before cooking! Just like how a chef might check that vegetables are fresh, meat is properly stored, and spices are correctly labeled, we check our data to make sure it's complete, accurate, and ready for use. We look at things like "How many records do we have?" (like counting ingredients), "Are there any missing values?" (like checking if any ingredients are spoiled), and "What does the data look like?" (like examining the quality of each ingredient). This ensures we're working with good data, just like how checking ingredients ensures a good meal!

### Dataset Management Architecture

The dataset system provides **comprehensive data governance**:

- **CRUD Operations**: Create, read, update, delete with proper validation
- **Metadata Management**: Rich descriptions, tags, versioning
- **Data Profiling**: Automatic statistics generation and quality metrics
- **Access Control**: User-based permissions and audit trails

### Data Quality Framework

- **Completeness**: Missing value analysis and imputation strategies
- **Consistency**: Data type validation and range checking
- **Accuracy**: Domain-specific validation rules
- **Timeliness**: Data freshness and update frequency tracking

```bash
# List
curl "http://localhost:8000/api/v1/datasets/?skip=0&limit=20"
# Get one by id
curl "http://localhost:8000/api/v1/datasets/<DATASET_ID>"
# Dataset info
curl "http://localhost:8000/api/v1/datasets/<DATASET_ID>/info"
# Dataset health
curl "http://localhost:8000/api/v1/datasets/<DATASET_ID>/health"
```

## 5) Start ML analysis

>> 🤖 With data in place, I trigger ML workflows (bee preferences, recommendations) to generate analytical insights—implementing machine learning pipelines I've studied in my AI program at EHB. It's like putting your ingredients into a smart cooking machine that knows exactly how to combine them for the best results!

**💡 Simple Explanation**: Machine learning analysis is like having a super-smart cooking assistant that can figure out the best recipes! Instead of just following a recipe, this assistant looks at all your ingredients (data), learns from thousands of previous cooking experiences (training), and figures out the best way to combine them. In our case, it's analyzing bee behavior patterns to understand which plants they prefer, when they're most active, and what factors influence their choices. It's like having a chef who can taste a dish and tell you exactly what ingredients work well together and why. The system processes this information in the background (like a slow cooker) and gives us insights that would take humans months to figure out!

### Machine Learning Architecture

The ML system implements **production-ready analytics**:

- **Feature Engineering**: Domain-specific transformations for ecological data
- **Model Selection**: Interpretable algorithms (Random Forest, Logistic Regression)
- **Validation Strategy**: Stratified sampling, cross-validation, holdout sets
- **Result Interpretation**: Feature importance, confidence intervals, business metrics

### Ecological Analysis Methods

- **Bee Preference Modeling**: Predicts native vs non-native bee preferences
- **Plant Recommendation**: Multi-criteria ranking for conservation planning
- **Seasonal Analysis**: Temporal patterns and phenology modeling
- **Site Comparison**: Geographic variation and habitat quality assessment

- Bee preference model

```bash
curl -X POST "http://localhost:8000/api/v1/analysis/bee-preferences/" \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": <DATASET_ID>, "target_column": "nonnative_bee", "model_type": "random_forest", "test_size": 0.2}'
```

- (Optional) Plant recommendations

```bash
curl -X POST "http://localhost:8000/api/v1/analysis/plant-recommendations/" \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": <DATASET_ID>, "top_n": 10, "criteria": ["bee_attraction","seasonal_availability"]}'
```

- (Optional) Seasonal/site analyses

```bash
curl -X POST "http://localhost:8000/api/v1/analysis/seasonal/?dataset_id=<DATASET_ID>" \
  -H "Content-Type: application/json" \
  -d '{"include_trends": true, "seasonal_periods": 12}'

curl -X POST "http://localhost:8000/api/v1/analysis/site-comparison/?dataset_id=<DATASET_ID>" \
  -H "Content-Type: application/json" \
  -d '{"metrics": ["total_bees","diversity_index"], "group_by": "site"}'
```

## 6) Track jobs and fetch results

>> ⏳ The job system handles long-running tasks like a restaurant kitchen managing multiple orders—some take longer to cook than others, so we need to track progress and notify when they're ready!

**💡 Simple Explanation**: Job tracking is like ordering food at a busy restaurant! When you order a complex dish, the kitchen doesn't make it instantly—it goes into a queue with other orders. The system tracks your order (like a waiter checking on your food), tells you how long it will take (progress updates), and notifies you when it's ready (job completion). Some tasks are quick (like making a salad), while others take longer (like slow-cooking a stew). Our system handles this by putting long-running analysis tasks in a queue, processing them in the background, and letting you know when they're done. It's like having a very organized kitchen that can handle multiple orders efficiently without getting overwhelmed!

### Asynchronous Processing Architecture

The job system implements **scalable task processing**:

- **Celery Integration**: Distributed task queue with Redis backend
- **Job Lifecycle**: Created → Queued → Running → Completed/Failed
- **Progress Tracking**: Real-time status updates and progress indicators
- **Result Storage**: Structured outputs with metadata and artifacts

### Job Management Features

- **Queue Management**: Priority queuing, retry logic, dead letter queues
- **Resource Monitoring**: CPU, memory, and disk usage tracking
- **Error Handling**: Comprehensive error logging and recovery strategies
- **Result Caching**: Temporary storage with configurable retention

```bash
# List jobs
curl "http://localhost:8000/api/v1/analysis/jobs/?dataset_id=<DATASET_ID>"
# Get job status
curl "http://localhost:8000/api/v1/analysis/jobs/<JOB_ID>/status"
# Get job info
curl "http://localhost:8000/api/v1/analysis/jobs/<JOB_ID>"
# Get results
curl "http://localhost:8000/api/v1/analysis/jobs/<JOB_ID>/results"
# (Optional) cancel
curl -X DELETE "http://localhost:8000/api/v1/analysis/jobs/<JOB_ID>"
```

## 7) Create visualizations

>> 📊 Visualization generation transforms raw data into meaningful charts and graphs—like turning ingredients into a beautiful, plated dish that tells a story about the flavors and presentation!

**💡 Simple Explanation**: Creating visualizations is like turning raw ingredients into a beautiful, plated dish! Just like how a chef takes vegetables, meat, and spices and arranges them into an attractive presentation that tells you about the flavors and cooking techniques, we take raw data and turn it into charts and graphs that tell a story. Instead of looking at a spreadsheet full of numbers, you can see patterns, trends, and relationships at a glance. It's like the difference between looking at a pile of ingredients versus seeing a beautifully arranged plate that makes your mouth water! Our system automatically creates different types of charts (like different cooking styles) to show bee distributions, seasonal patterns, and site comparisons in ways that are easy to understand and visually appealing.

### Visualization Architecture

The viz system provides **automated chart generation**:

- **Template System**: Pre-defined chart types with configurable parameters
- **Data Processing**: Aggregation, filtering, and transformation for visualization
- **Chart Generation**: Matplotlib/Seaborn-based with consistent styling
- **Export Options**: PNG, PDF, SVG formats with metadata

### Ecological Visualization Types

- **Bee Distribution**: Species abundance and diversity patterns
- **Seasonal Patterns**: Temporal trends and phenology visualization
- **Site Comparison**: Geographic variation and habitat analysis
- **Dashboard**: Multi-panel overview for comprehensive insights

```bash
# Bee distribution
curl -X POST "http://localhost:8000/api/v1/visualizations/bee-distribution/?dataset_id=<DATASET_ID>" \
  -H "Content-Type: application/json" \
  -d '{"top_n": 20, "include_percentages": true}'
# Seasonal patterns
curl -X POST "http://localhost:8000/api/v1/visualizations/seasonal-patterns/?dataset_id=<DATASET_ID>" \
  -H "Content-Type: application/json" \
  -d '{"include_trends": true, "seasonal_periods": 12}'
# Site comparison
curl -X POST "http://localhost:8000/api/v1/visualizations/site-comparison/?dataset_id=<DATASET_ID>" \
  -H "Content-Type: application/json" \
  -d '{"metrics": ["total_bees","diversity"], "group_by": "site"}'
# Dashboard
curl -X POST "http://localhost:8000/api/v1/visualizations/dashboard/?dataset_id=<DATASET_ID>" \
  -H "Content-Type: application/json" \
  -d '{"include_timeline": true, "include_metrics": true}'
```

## 8) Track visualization tasks and download artifacts

>> 📥 Once visualizations are created, we need to track their progress and provide easy access to the final results—like a restaurant ensuring your food is properly packaged and ready for pickup!

**💡 Simple Explanation**: Artifact management is like a restaurant's takeout system! When you order food to go, the restaurant needs to track your order (like we track visualization tasks), package it properly (like saving charts in the right format), and make it easy for you to pick up (like downloading the results). Just like how a restaurant might offer different packaging options (plastic containers, paper bags, or fancy boxes), our system can save visualizations in different formats (PNG for web, PDF for printing, SVG for editing). The system also keeps track of what you've ordered (like a receipt) so you can find and download your visualizations later. It's like having a very organized takeout system that never loses your order!

### Artifact Management

The system provides **comprehensive output handling**:

- **File Storage**: Organized directory structure with metadata
- **Access Control**: User-based permissions for artifact access
- **Version Management**: Artifact versioning and rollback capabilities
- **Export Formats**: Multiple output formats for different use cases

### Download and Distribution

- **Direct Downloads**: Secure file serving with proper headers
- **Metadata Access**: Rich information about generated artifacts
- **Batch Operations**: Bulk download and export capabilities
- **Integration Ready**: API endpoints for external system integration

```bash
# Check task status
curl "http://localhost:8000/api/v1/visualizations/<VIS_ID>/status?task_id=<TASK_ID>"
# Download info
curl "http://localhost:8000/api/v1/visualizations/<VIS_ID>/download?task_id=<TASK_ID>"
# Cancel
curl -X DELETE "http://localhost:8000/api/v1/visualizations/<VIS_ID>?task_id=<TASK_ID>"
# List available viz types
curl "http://localhost:8000/api/v1/visualizations/available-types"
```

## 9) Monitoring and shutdown insights

>> 📈 Monitoring provides real-time insights into system performance and health—like having security cameras and sensors throughout a restaurant to ensure everything runs smoothly!

**💡 Simple Explanation**: System monitoring is like having security cameras and sensors throughout a restaurant! Just like how a restaurant manager might have cameras in the kitchen to watch food preparation, sensors to monitor temperature and humidity, and systems to track customer flow and order times, our API has monitoring tools that watch everything happening in real-time. We track things like "How many requests are we getting?" (like counting customers), "How fast are we responding?" (like measuring service speed), "Are there any errors?" (like checking if food is being prepared correctly), and "How much resources are we using?" (like monitoring kitchen equipment). This helps us spot problems before they become serious, just like how a good restaurant manager can see when the kitchen is getting overwhelmed and needs help!

### Operational Monitoring

The monitoring system provides **comprehensive observability**:

- **Application Metrics**: Request rates, response times, error rates
- **Business Metrics**: User activity, dataset usage, analysis success rates
- **System Metrics**: Resource utilization, queue depths, cache hit rates
- **Security Metrics**: Authentication attempts, rate limiting, suspicious activity

### Graceful Shutdown

- **Health Degradation**: Gradual service degradation with proper signaling
- **Data Preservation**: Safe shutdown with data consistency guarantees
- **Resource Cleanup**: Proper cleanup of temporary files and connections
- **Audit Trail**: Complete shutdown logging for post-mortem analysis

```bash
curl "http://localhost:8000/api/v1/metrics"
curl "http://localhost:8000/api/v1/security/status"
curl "http://localhost:8000/api/v1/shutdown/status"
curl "http://localhost:8000/api/v1/shutdown/metrics"
```

## Advanced Usage Patterns

### Batch Processing Workflows

For production use cases, implement **automated workflows**:

```bash
# Automated analysis pipeline
curl -X POST "http://localhost:8000/api/v1/analysis/batch/" \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": <DATASET_ID>, "analyses": ["bee-preferences", "plant-recommendations", "seasonal"], "visualizations": ["dashboard"]}'
```

### Integration Patterns

For external system integration:

```bash
# Webhook notifications
curl -X POST "http://localhost:8000/api/v1/webhooks/" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-system.com/webhook", "events": ["job.completed", "visualization.ready"]}'
```

## Notes

- Prefer Makefile targets to start services (local, docker, remote) and to check health.
- If auth is enforced, add: `-H "Authorization: Bearer <JWT>"` to protected requests.
- Use returned IDs (`dataset_id`, `job_id`, `visualization_id`, `task_id`) from earlier calls as you proceed.

## Troubleshooting Guide

### Common Issues and Solutions

**Authentication Problems**

- OTP expiration: Request new verification code
- JWT expiration: Re-authenticate to get fresh token
- Rate limiting: Wait for cooldown period

**Data Processing Issues**

- Large file uploads: Check file size limits and network stability
- Memory constraints: Monitor system resources during processing
- Encoding issues: Ensure CSV files use UTF-8 encoding

**Job Processing Delays**

- Queue backlog: Check Celery worker status and Redis connectivity
- Resource constraints: Monitor CPU and memory usage
- Network issues: Verify external service dependencies

**Visualization Generation Failures**

- Data quality: Ensure sufficient data for requested chart types
- Memory limits: Check available RAM for large datasets
- File permissions: Verify write access to output directories
