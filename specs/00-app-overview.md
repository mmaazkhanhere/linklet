# Specification 01: Application Overview, Stack & Folder Structure

- **Spec ID**: `SPEC-00`
- **Title**: Application Architecture Overview, Tech Stack, Folder Structure & Deployment Guide
- **Traceability**: [docs/architecture.md](file:///e:/Web%203.0/Generative%20AI/Github/linklet/docs/architecture.md) — Sections 1-3, 10-11, 19
- **Status**: Approved & Confirmed

---

## 1. Executive Summary & Application Objectives

**Linklet** is an authenticated URL shortener web application featuring a modern React frontend and a high-performance, cache-less public redirect backend layer. Built as a clean decoupled project structure (`frontend/` and `backend/`), Linklet allows authenticated creators to create, list, regenerate, and delete short links, tracking total clicks with immediate invalidation upon link deletion or regeneration.

---

## 2. Confirmed Technology Stack

### Frontend Web Application
- **Build Tool & Framework**: Vite + React 18+ (TypeScript)
- **Styling**: Tailwind CSS
- **UI Component Library**: **shadcn/ui** (accessible UI primitives built on Radix UI & Tailwind CSS)
- **Icons**: Lucide React (`lucide-react`)
- **HTTP Client & API Integration**: Axios / Fetch API with custom hooks

### Backend & Core Application
- **Language**: Python 3.11+
- **Framework**: FastAPI (ASGI asynchronous REST framework)
- **Dependency & Package Manager**: `uv` (Fast Python package installer & resolver)
- **Data Validation & Settings**: Pydantic v2 & `pydantic-settings`
- **Server**: Uvicorn (ASGI HTTP Web Server) / Vercel Serverless ASGI Handler

### Persistence & Data Access
- **Database**:
  - **Local Development & Testing**: Dockerized PostgreSQL (via `docker-compose.yml` for dev & integration tests)
  - **Production (Vercel)**: **Neon Database** (Serverless PostgreSQL)
- **ORM / Query Builder**: SQLAlchemy 2.0 (Async Engine & Declarative Mapping)
- **Database Migrations**: Alembic

### Authentication & Security
- **Authentication**: OAuth2 Bearer JWT (`PyJWT` / `python-jose`)
- **Password Hashing**: `passlib` with `bcrypt` or `argon2-cffi`
- **API Authorization**: Server-side user identity context (`current_user`)

### Testing & Quality Assurance
- **Backend Test Runner**: `pytest` & `pytest-asyncio`
- **Async HTTP Test Client**: `httpx`
- **Linting & Code Formatting**: `ruff` (Backend) / ESLint & Prettier (Frontend)

### Deployment & Hosting Target
- **Target Platform**: **Vercel** (Deploying Vite SPA Frontend + FastAPI Serverless API)
- **Database Host**: **Neon Database** (Serverless PostgreSQL)

---

## 3. Project Folder Structure

```
linklet/
├── docs/                        # Architectural documentation & C4 diagrams
│   ├── architecture.md
│   └── diagram/
├── specs/                       # Executable Feature Specifications (SDD)
│   ├── 01-app-overview.md
│   ├── 01-auth-user-management.md
│   ├── 02-link-creation.md
│   ├── 03-redirect-resolution.md
│   ├── 04-link-management.md
│   ├── 05-idempotency-engine.md
│   └── 06-database-schema-migrations.md
├── frontend/                    # Vite + React + Tailwind CSS + shadcn/ui SPA
│   ├── public/                  # Static assets & favicons
│   ├── src/
│   │   ├── assets/
│   │   ├── components/          # Application UI components
│   │   │   ├── ui/              # shadcn/ui primitive components (Button, Card, Dialog, etc.)
│   │   │   ├── Navbar.tsx
│   │   │   ├── LinkTable.tsx
│   │   │   ├── CreateLinkModal.tsx
│   │   │   └── AnalyticsCard.tsx
│   │   ├── hooks/               # Custom React hooks (useAuth, useLinks)
│   │   ├── lib/                 # Utilities (api client, cn helper)
│   │   │   ├── api.ts
│   │   │   └── utils.ts
│   │   ├── pages/               # Application Pages / Views
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   └── NotFound.tsx
│   │   ├── App.tsx              # Root component & client router
│   │   ├── main.tsx             # React entry point
│   │   └── index.css            # Tailwind CSS directives & theme variables
│   ├── components.json          # shadcn/ui CLI configuration
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
├── backend/                     # Backend Application (FastAPI Modular Monolith)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app initialization & router inclusions
│   │   ├── config.py            # Pydantic environment settings
│   │   ├── core/                # Core utilities, security, and DB session
│   │   │   ├── __init__.py
│   │   │   ├── database.py      # Async SQLAlchemy engine and sessionmaker
│   │   │   ├── security.py      # Password hashing & JWT generation/decoding
│   │   │   └── dependencies.py  # get_db and get_current_user FastAPI dependencies
│   │   ├── models/              # SQLAlchemy DB ORM Models
│   │   │   ├── __init__.py
│   │   │   ├── user.py          # User ORM entity
│   │   │   ├── link.py          # Link ORM entity
│   │   │   └── idempotency.py   # IdempotencyRequest ORM entity
│   │   ├── schemas/             # Pydantic Request & Response Schemas
│   │   │   ├── __init__.py
│   │   │   ├── user.py          # User request/response DTOs
│   │   │   ├── link.py          # Link request/response DTOs
│   │   │   ├── idempotency.py   # Idempotency DTOs
│   │   │   └── error.py        # RFC 7807 problem details error schema
│   │   ├── api/                 # Route Controllers / Handlers
│   │   │   ├── __init__.py
│   │   │   ├── router.py        # Master APIRouter
│   │   │   └── v1/
│   │   │       ├── auth.py      # /auth/register, /auth/token, /auth/me
│   │   │       ├── links.py     # POST /links, GET /links, PUT /links/{id}, DELETE /links/{id}
│   │   │       └── redirect.py  # GET /{short_code}
│   │   ├── services/            # Business & Domain Logic Layer
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py  # Authentication and password business rules
│   │   │   ├── link_service.py  # Link management & redirect resolution logic
│   │   │   ├── generator_service.py # Short-code Base62 generator
│   │   │   └── idempotency_service.py # Scoped idempotency verification & status updates
│   │   └── repositories/        # Persistence / Data Access Abstraction
│   │       ├── __init__.py
│   │       ├── user_repository.py
│   │       ├── link_repository.py
│   │       └── idempotency_repository.py
│   ├── migrations/              # Alembic DB Migration Scripts
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   ├── tests/                   # Automated Backend Test Suite
│   │   ├── conftest.py          # Test fixtures (Async DB session, test client, auth headers)
│   │   ├── unit/
│   │   │   ├── test_generator.py
│   │   │   ├── test_security.py
│   │   │   └── test_validator.py
│   │   └── integration/
│   │       ├── test_auth_api.py
│   │       ├── test_link_creation_api.py
│   │       ├── test_redirect_api.py
│   │       ├── test_link_management_api.py
│   │       └── test_idempotency_api.py
│   ├── alembic.ini              # Alembic migration tool config
│   ├── pyproject.toml           # Backend `uv` managed dependencies & tool configs
│   └── uv.lock                  # Backend `uv` lockfile
├── api/                         # Vercel Serverless Entrypoint
│   └── index.py                 # Imports backend.app.main:app for Vercel functions
├── .env.example                 # Environment variable template
├── .gitignore
├── docker-compose.yml           # Local dev setup (Postgres DB)
├── vercel.json                  # Unified Vercel deployment (Frontend + Backend)
└── README.md
```

---

## 4. Deployment & Hosting Architecture (Vercel)

### 4.1 Deployment Setup
- **Unified Vercel Deployment**: Vercel hosts both the compiled Vite SPA static bundle and the serverless FastAPI backend.
- **`vercel.json` Routing Configuration**:
  ```json
  {
    "builds": [
      {
        "src": "frontend/package.json",
        "use": "@vercel/static-build",
        "config": { "distDir": "dist" }
      },
      {
        "src": "api/index.py",
        "use": "@vercel/python"
      }
    ],
    "routes": [
      {
        "src": "/api/(.*)",
        "dest": "api/index.py"
      },
      {
        "src": "/auth/(.*)",
        "dest": "api/index.py"
      },
      {
        "src": "/links(.*)",
        "dest": "api/index.py"
      },
      {
        "src": "/r/(.*)",
        "dest": "api/index.py"
      },
      {
        "handle": "filesystem"
      },
      {
        "src": "/(.*)",
        "dest": "/index.html"
      }
    ]
  }
  ```
- **Vercel Entrypoint (`api/index.py`)**:
  ```python
  from backend.app.main import app
  ```

### 4.2 Environment Configuration Matrix

| Variable Name | Purpose | Recommended Default |
|---------------|---------|---------------------|
| `ENVIRONMENT` | Runtime environment mode | `development` / `production` |
| `SECRET_KEY` | HMAC key for signing JWTs | Secret 64-byte random string |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `1440` (24 Hours) |
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://user:pass@host:5432/linklet` |
| `VITE_API_BASE_URL` | Frontend API base URL | `/api/v1` or `http://localhost:8000/api/v1` |
| `BASE_URL` | Base short link domain | `https://linklet.vercel.app` or `http://localhost:8000` |
