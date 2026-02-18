# Backend Structure Documentation

## Project Overview

**Project Name**: Vehicle Automation Microservice  
**Current Phase**: Phase 1 - Infrastructure Scaffold  
**Version**: 0.1.0  
**Framework**: FastAPI (Python 3.11+)  
**Database**: TiDB/MySQL with SQLAlchemy ORM  
**Architecture**: Layered architecture with async support

---

## Technology Stack

### Core Dependencies
- **FastAPI** (>=0.104.0) - Modern async web framework
- **Uvicorn** (>=0.24.0) - ASGI server with standard extras
- **SQLAlchemy** (>=2.0.0) - Async ORM for database operations
- **Alembic** (>=1.12.0) - Database migration tool
- **Pydantic** (>=2.5.0) - Data validation and settings management
- **aiomysql** (>=0.2.0) - Async MySQL driver

### Development Dependencies
- **pytest** (>=7.4.0) - Testing framework
- **pytest-asyncio** (>=0.21.0) - Async test support
- **pytest-cov** (>=4.1.0) - Code coverage
- **hypothesis** (>=6.92.0) - Property-based testing
- **httpx** (>=0.25.0) - HTTP client for testing
- **ruff** (>=0.1.0) - Fast Python linter and formatter

---

## Project Structure

```
.
├── app/                          # Main application code
│   ├── api/                      # API routes and endpoints
│   │   ├── health.py            # Health check endpoints
│   │   └── __init__.py
│   ├── config/                   # Configuration management
│   │   ├── settings.py          # Pydantic settings with env vars
│   │   └── __init__.py
│   ├── database/                 # Database layer
│   │   ├── base.py              # SQLAlchemy base class
│   │   ├── connection.py        # Connection pool & health checks
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   └── __init__.py
│   ├── middleware/               # Middleware components
│   │   ├── error_handlers.py   # Global exception handlers
│   │   ├── logging.py           # Request logging middleware
│   │   ├── setup.py             # Middleware configuration
│   │   └── __init__.py
│   ├── utils/                    # Utility functions
│   │   ├── logging.py           # Structured logging setup
│   │   └── __init__.py
│   ├── main.py                   # Application entry point
│   └── __init__.py
├── tests/                        # Test suite
│   ├── conftest.py              # Pytest fixtures
│   └── __init__.py
├── alembic/                      # Database migrations
│   ├── versions/                # Migration scripts
│   ├── env.py                   # Alembic environment config
│   └── script.py.mako           # Migration template
├── docs/                         # Documentation
│   └── ARCHITECTURE.md          # Architecture documentation
├── .env.example                  # Environment variables template
├── .gitignore                    # Git ignore rules
├── alembic.ini                   # Alembic configuration
├── docker-compose.yml            # Docker services (TiDB)
├── Makefile                      # Common commands
├── pyproject.toml                # Project metadata & dependencies
└── README.md                     # Project README
```

---

## Architecture Layers

### 1. API Layer (`app/api/`)
Handles HTTP requests and responses using FastAPI routers.

**Current Endpoints**:
- `GET /health` - Health check with database connectivity verification
- `GET /status` - Service metadata (version, uptime, environment)
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

**Response Formats**:
- Health check returns 200 (healthy) or 503 (unhealthy)
- All errors return consistent JSON structure with error type, message, and details

### 2. Middleware Layer (`app/middleware/`)
Processes all requests/responses with cross-cutting concerns.

**Components**:
- **LoggingMiddleware**: Logs all HTTP requests with correlation IDs, duration, and status
- **Security Headers**: Adds X-Content-Type-Options, X-Frame-Options, X-XSS-Protection
- **CORS**: Configurable cross-origin resource sharing
- **Error Handlers**: Global exception handling for validation, database, and server errors

### 3. Database Layer (`app/database/`)
Manages async database connections and ORM models.

**Features**:
- Async SQLAlchemy engine with connection pooling
- QueuePool with configurable size (default: 10, max overflow: 20)
- Pre-ping enabled for connection health verification
- Graceful connection cleanup on shutdown
- Database health check function

**Current Models**:
- `HealthCheckLog` - Example model for storing health check logs

### 4. Configuration Layer (`app/config/`)
Centralized configuration using Pydantic Settings.

**Configuration Categories**:
- **API**: host, port, debug mode, log level
- **Database**: host, port, user, password, database name, pool settings
- **CORS**: allowed origins
- **Security**: Sensitive values masked in logs and string representations

**Environment Variables** (from `.env`):
```
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
LOG_LEVEL=INFO
DB_HOST=localhost
DB_PORT=4000
DB_USER=root
DB_PASSWORD=***
DB_NAME=vehicle_automation
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
CORS_ORIGINS=["*"]
```

### 5. Utilities Layer (`app/utils/`)
Shared utilities and helper functions.

**Components**:
- **Logging**: Structured JSON logging with correlation IDs, timestamps, and request metadata

---

## Request Flow

1. Client sends HTTP request
2. **LoggingMiddleware** logs request start with correlation ID
3. **Security headers middleware** adds security headers
4. **CORS middleware** handles cross-origin requests
5. **Router** handles request and executes business logic
6. **Database operations** (if needed) via async session
7. Response returned through middleware chain
8. **LoggingMiddleware** logs request completion with duration
9. Response includes `X-Correlation-ID` header

---

## Database Architecture

### Connection Management
- **Engine**: Async SQLAlchemy engine with aiomysql driver
- **Pool**: QueuePool with pre-ping for connection validation
- **Sessions**: Async session maker with dependency injection pattern
- **Lifecycle**: Initialized on app startup, disposed on shutdown

### Migrations
- **Tool**: Alembic for schema versioning
- **Location**: `alembic/versions/`
- **Commands**:
  - `alembic revision --autogenerate -m "message"` - Generate migration
  - `alembic upgrade head` - Apply migrations
  - `alembic downgrade -1` - Rollback one migration

### Database URL Format
```
mysql+aiomysql://{user}:{password}@{host}:{port}/{database}
```

---

## Error Handling

### Error Categories

1. **Validation Errors (422)**
   - Triggered by: Invalid request data (Pydantic validation)
   - Response: `{"error": "Validation Error", "details": [...]}`

2. **Database Errors (503)**
   - Triggered by: SQLAlchemy exceptions
   - Response: `{"error": "Database Error", "message": "..."}`

3. **Server Errors (500)**
   - Triggered by: Unhandled exceptions
   - Response: `{"error": "Internal Server Error", "message": "..."}`

### Error Response Structure
```json
{
  "error": "Error Type",
  "message": "Human-readable message",
  "details": {}
}
```

---

## Security Features

### Implemented Security Measures
- **Parameterized queries** via SQLAlchemy ORM (SQL injection prevention)
- **Security headers**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection
- **CORS configuration** with allowed origins
- **Sensitive value masking** in logs and settings output
- **No stack traces** in API error responses
- **Connection pool pre-ping** to prevent stale connections

---

## Logging

### Structured Logging Format
- **Format**: JSON for easy parsing
- **Fields**: timestamp, level, message, correlation_id, method, path, status_code, duration_ms
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Correlation IDs**: UUID v4 for request tracing across services

### Log Examples
```json
{
  "timestamp": "2026-02-18T10:30:00Z",
  "level": "INFO",
  "message": "Request completed",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "GET",
  "path": "/health",
  "status_code": 200,
  "duration_ms": 45.23
}
```

---

## Development Commands

### Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env

# Start TiDB
docker-compose up -d

# Run migrations
alembic upgrade head
```

### Running
```bash
# Start development server
uvicorn app.main:app --reload

# Start production server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_health.py
```

### Code Quality
```bash
# Lint code
ruff check .

# Format code
ruff format .

# Type checking (if mypy added)
mypy app/
```

---

## API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Health Check Endpoints

#### GET /health
Returns service and database health status.

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "service": "running",
  "database": {
    "status": "healthy",
    "database": "connected"
  }
}
```

**Response (503 Service Unavailable)**:
```json
{
  "status": "unhealthy",
  "service": "running",
  "database": {
    "status": "unhealthy",
    "database": "disconnected",
    "error": "Connection refused"
  }
}
```

#### GET /status
Returns service metadata.

**Response (200 OK)**:
```json
{
  "service": "vehicle-automation-microservice",
  "version": "0.1.0",
  "phase": "1-scaffold",
  "uptime_seconds": 3600,
  "environment": "development"
}
```

---

## Current Implementation Status

### ✅ Completed (Phase 1)
- FastAPI application setup with async support
- TiDB/MySQL database integration with SQLAlchemy
- Connection pooling with health checks
- Structured logging with correlation IDs
- Global error handling
- Security headers and CORS
- Health check endpoints
- API documentation (Swagger/ReDoc)
- Database migrations with Alembic
- Docker Compose for local TiDB
- Development tooling (pytest, ruff, coverage)

### 🚧 Future Enhancements (Phase 2+)
- Vehicle automation business logic
- Additional API endpoints for vehicle operations
- Service layer implementation
- Enhanced database models for vehicles
- Authentication and authorization
- Rate limiting
- Caching layer
- Monitoring and observability
- CI/CD pipeline

---

## Key Design Decisions

1. **Async-first architecture**: All database operations and HTTP handlers use async/await
2. **Dependency injection**: Database sessions provided via FastAPI dependencies
3. **Configuration management**: Pydantic Settings with environment variable validation
4. **Structured logging**: JSON format with correlation IDs for distributed tracing
5. **Error handling**: Consistent error response format across all endpoints
6. **Security by default**: Security headers, parameterized queries, sensitive data masking
7. **Connection pooling**: Pre-configured pool with health checks and graceful shutdown
8. **Migration-based schema**: Alembic for version-controlled database changes

---

## Notes for External Use

When sharing this backend structure with ChatGPT or other tools:

1. **Current State**: This is a Phase 1 scaffold focused on infrastructure, not business logic
2. **Database**: Uses TiDB (MySQL-compatible) with async SQLAlchemy
3. **Testing**: Includes pytest setup with async support and property-based testing (Hypothesis)
4. **Extensibility**: Designed for easy addition of new routers, models, and services
5. **Production-ready**: Includes logging, error handling, health checks, and security headers
6. **Development-friendly**: Hot reload, interactive docs, structured logging, and comprehensive testing

---

**Last Updated**: February 18, 2026  
**Maintained By**: Development Team
