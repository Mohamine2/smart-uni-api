# Smart-Uni API: Connected University Residence Backend

[![CI/CD DevSecOps](https://github.com/Mohamine2/smart-uni-api/actions/workflows/ci-devsecops.yml/badge.svg)](https://github.com/Mohamine2/smart-uni-api/actions/workflows/ci-devsecops.yml)
[![Coverage](https://img.shields.io/badge/Coverage-≥80%25-brightgreen.svg)](https://github.com/Mohamine2/smart-uni-api)
[![Security Scan: Trivy](https://img.shields.io/badge/Security-Trivy_Passing-blue.svg)](https://github.com/aquasecurity/trivy)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-DRF-092E20.svg?logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Smart-Uni API** is a headless, RESTful backend service built with **Django REST Framework (DRF)**. It manages business logic, resident authentication, IoT smart home management, an engagement-driven gamification engine, and collaborative university residence services

---

## Project Context & Evolution

This repository represents an **independent, production-ready refactoring** of the original [Smart-Uni](https://github.com/Mohamine2/Smart-Uni.git) academic project completed during the ING1 Computer Science Engineering curriculum at CY Tech.

While the original university project was a monolithic Django web application (coupled with DTL templates), this initiative modernizes the architecture:
- **Headless Backend:** Complete migration to a decoupled REST API using **Django REST Framework (DRF)**.
- **Stateless Authentication:** Integration of **JWT (SimpleJWT)** for secure, stateless client authorization.
- **Client-Agnostic Design:** Frontend presentation layers were intentionally removed to serve any independent client (Web SPA, mobile application, CLI).
- **Interactive Documentation:** Fully documented with **Swagger UI** and OpenAPI specifications.
- **Infrastructure Decoupling:** Cloud provisioning, reverse proxy configs, and production deployments are isolated into the dedicated [smart-uni-infra](https://github.com/Mohamine2/smart-uni-infra) repository.

---

## 🏗️ Architecture & Repositories

* **`smart-uni-api` (this repository)**: REST endpoints, serialization layers, business logic, ORM models, custom permissions, and automated test suites.
* **`smart-uni-infra`**: Infrastructure as Code, container orchestration, networking, and cloud delivery pipelines.

To understand how the application components interact when deployed via the infrastructure repository, here is the architecture diagram:

<img width="1600" height="1600" alt="image" src="https://github.com/user-attachments/assets/2d7281b4-6749-4806-b198-5675f163c673" />

---

## 🔐 Authentication & API Endpoints

The API uses **stateless JWT authentication**. Protected endpoints require the `Authorization: Bearer <access_token>` header.

### 🔑 Authentication Routes
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/token/` | Obtain token pair (`access` and `refresh`) with credentials |
| `POST` | `/api/token/refresh/` | Renew an expired `access` token using a valid `refresh` token |

**Obtain Token (`POST /api/token/`)**
```json
// Request
{ "username": "student", "password": "secure_password" }

// Response (200 OK)
{ "access": "<jwt_access_token>", "refresh": "<jwt_refresh_token>" }
```

**Refresh Token (`POST /api/token/refresh/`)**
```json
// Request
{ "refresh": "<jwt_refresh_token>" }

// Response (200 OK)
{ "access": "<jwt_new_access_token>" }
```
</details>

---

## 📖 Interactive API Documentation (Swagger / OpenAPI)

The API exposes automated, interactive OpenAPI schema documentation:

* **Swagger UI:** `http://127.0.0.1:8000/api/docs/` - Interactive sandbox to test endpoints and inspect payload schemas.
* **OpenAPI Schema (JSON/YAML):** `http://127.0.0.1:8000/api/schema/` - Standard specification for generating client SDKs.
* **Django Admin:** `http://127.0.0.1:8000/admin/` — Administrative database dashboard.

---

## 🛡️ DevSecOps & Security Standards

This backend enforces enterprise-grade security and automated quality gating:

### 1. Hardened Container Security (Non-Root Execution)
- A dedicated unprivileged system user (`django-user`) is provisioned inside the `Dockerfile`.
- The application runtime executes strictly within this user context, preventing container breakout exploits.
- Filesystem permissions are locked down exclusively to the `/app` workspace.

### 2. Automated CI/DevSecOps Quality Gate (GitHub Actions)
The workflow `.github/workflows/ci-devsecops.yml` runs on every `push` and `pull_request` targeting `main`:

- **Automated Build:** Validates Dockerfile compilation and multi-layer caching with an unprivileged runtime user.
- **Automated Testing & Coverage:** Executes unit and integration test suites against an isolated in-memory SQLite database, enforcing a strict **80% minimum code coverage threshold** configured via `.coveragerc`.
- **Vulnerability Scanning (Aqua Security Trivy):** Scans the `python:3.11-slim-bookworm` base image and transitive dependencies. It breaks the build (`exit code 1`) if unmitigated `HIGH` or `CRITICAL` CVEs are found.
- **Image Publishing:** Pushes the verified, immutable production artifact to Docker Hub, tagged with the Git short-SHA commit hash and `latest`.
- **Continuous Deployment Handshake:** Dispatches a secure `repository_dispatch` event to [smart-uni-infra](https://github.com/Mohamine2/smart-uni-infra) to trigger downstream automated server deployment.

---

## Core API Features

### 🎮 Gamification & Experience Points (XP)
Access to IoT endpoints is guarded by custom DRF permissions matching the resident's XP tier:
- **Beginner (0-2 XP):** Read access to profile data, resident directory, and campus announcements.
- **Intermediate (3+ XP):** Create/Delete and rename connected appliances within the assigned room.
- **Advanced (5+ XP):** Control granular states (power levels, dimmers, toggle switches).
- **Expert (7+ XP):** Access Smart Grid aggregate energy consumption statistics and analytics.

### 🏠 Smart Home Management (IoT)
- CRUD REST endpoints for room-bound smart devices.
- Real-time device state toggling and power consumption metrics.

### 📅 Residence Services
- **Study Room Booking Engine:** Reservation lifecycle with automated conflict detection and scheduling validation.
- **Campus Newsfeed:** Real-time bulletin board for campus announcements and events.

---

## 🛠️ Technical Stack

- **Backend:** Python 3.11, Django, Django REST Framework (DRF)
- **Authentication:** JSON Web Tokens (`djangorestframework-simplejwt`)
- **API Documentation:** Swagger UI / drf-spectacular (OpenAPI 3.0)
- **Database:** PostgreSQL 16 (psycopg)
- **Security & Auth:** Token / Session Authentication, Custom DRF Permissions
- **Containerization:** Docker, Docker Compose

---

## 📦 Local Installation & Setup (Docker)

The repository is fully Dockerized to guarantee reproducible environments and eliminate local runtime setup friction.

### 1. Prerequisites
- Ensure [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) configured on your machine.

### 2. Environment Configuration
   Secure application settings are managed dynamically through decoupled environment scopes:

1. **Initialize your local configuration file from the distributed blueprint:**

   ```bash
   cp .env.example .env
   ```
2. **Generate a secure cryptographic signing key for your local Django instance:**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
3. **Update your .env:**
   Copy the generated key and paste it into your .env file:

### 3. Resolving Local Port Conflicts
If you have PostgreSQL installed natively on your machine, it may conflict with port 5432. Stop the local service before launching:
```bash
   sudo systemctl stop postgresql
```

### 4. Running the Multi-Container Cluster
Build and start your service topology from the repository root (this orchestrates the network layer, spins up the MySQL schema engine, compiles the hardened Python runner, and binds the Django server):
```bash
docker compose up --build
```
The application will be exposed locally at: http://127.0.0.1:8000.

### 5. Database Initializations & Migrations
The database container automatically initializes the core instance layout using the schema bootstrap file located at `docker/mysql/init.sql`. In a separate shell terminal, map the Django ORM schema constraints to the database:
```bash
docker compose exec web python manage.py migrate
```

### 6. Administrative Access (Optional)
To create an administrative operator to access the Django native administration panel (http://127.0.0.1:8000/admin):
```bash
docker compose exec web python manage.py createsuperuser
```

### 7. Seeding Mock Data (Development & Testing)
To instantly populate your local instance with deterministic, realistic data records (mock student profiles, pre-configured study rooms, smart devices, and structured bulletin stories), execute the seeding script:
```bash
docker compose exec web python manage.py seed_db
```

## 📂 Project Structure

```text
smart-uni-api/
├── .github/workflows/         # CI Automation (Tests, Coverage, Trivy, Docker Hub)
│   └── ci-devsecops.yml
│
├── core/                      # Project configuration
│   ├── settings.py            # Global settings (DRF, JWT, Swagger, CORS, Database)
│   ├── urls.py                # Root routing, JWT auth endpoints & Swagger UI
│   └── wsgi.py / asgi.py
│
├── smart_residence/           # Main API application
│   ├── management/            # Custom Django management commands
│   │   └── commands/
│   │       └── seed_db.py     # Database seeding command (News, StudyRooms, Students, Devices)
│   ├── migrations/            # Database migration history
│   ├── admin.py               # Django Admin definitions
│   ├── apps.py
│   ├── models.py              # ORM Entities (Student, Device, StudyRoom, Booking, News)
│   ├── serializers.py         # DRF Serializers (Schema validation & JSON transforms)
│   ├── permissions.py         # Custom DRF permissions for XP tiers
│   ├── tests.py               # Unit & API integration test suites
│   └── views.py               # DRF ViewSets and APIViews
│
├── Dockerfile                 # Hardened, unprivileged Python builder
├── docker-compose.yml         # Local development orchestrator (DRF API + PostgreSQL 16)
├── manage.py                  # Django CLI utility for administrative tasks and migrations
├── .env.example               # Template for environment variables and secrets (DB credentials, secret keys)
├── requirements.txt           # Python dependencies (Django, DRF, SimpleJWT, psycopg)
├── .coveragerc                # Coverage enforcement configuration (>= 80%)
└── .trivyignore               # Security scan exception rules
```
