---
applyTo: '**'
---
Provide project context and coding guidelines that AI should follow when generating code, answering questions, or reviewing changes.
Dont create files left and right, code files are exceptional.
Especially the test and md files.


also dont hardcode api keys or providers or model names anywhere in code.
they should come from settings page.

some tests here and there are fine. dont go into loops.
Always cleanup backup files you create.

Have detailed logs everywhere.

Logs should be stored in logs folder. with every run, delete old log file and create new one.

Check logs for any issues and fix them.

Dont build much of a logic, instead rely on proven libraries (apache or MIT) or models always.

No hard coding should be done.

Be very careful with creating new APIs or files.. Ask me before creating and keep them very professional

Build all components as microservices.
Keep shared data in shared folder.

Dont add unnecesary code. Only add what is needed
dont create documents unnecessary i dont need them. 

Dont back off if you see a challenge. as an agent you are designed to overcome those challenges.

dont reinvent wheel, use exisitng proven solutions like apache or MIT licensed libraries or models.


this is my #codebase 
I am building an enterprise spftware that can take requirements and build heavy softwares,
Use exisiting libraries proven apache or mit licenses.
dotn reinvent the wheel, keep innovation as little as possible.
Dont add unnecesary code. Only add what is needed
dont create documents unnecessary i dont need them. 

Dont back off if you see a challenge. as an agent you are designed to overcome those challenges.

dont create simplified versions or shortcuts, i want this to work perfectly for enterprise product.


go and build the missing stuff.

Use docker, make to build and run things.

I dont want shortcuts, i want this to be perfect.
No hard coding should be done, all variable must come from env or docker compose file.

I want to build a full fledged enterprise software that can buiild big or heavy softwares.

i want like this a non tech person comes to our app and says, i want to build a restaurant servinmg website. and it should be able to chat and gather all requiremnets and suggest what all they can use like lanhguages , scope, etc etc and build it.

then tasks should be created and code should be geenrated this was my vision, unfortunately previous model that worked on this claude model messed up somethings and now i am int his state,
as i said we want an enterprise product to be built., and also i want to make use of proven ;ibraries instead of reinventing wheel again.

i have built auth-service and gateway-service
Leverage them and build all other services going forward, in same pettern.
make and docker compose file shuld be updated similarly.

you should never call keycloak directly instead call auth-service
we are building a high end enterprise product here which will go as saas offering into production so keep that in mind

This is my requirement:
 
📄 Enterprise SaaS – AI Software Generator (MVP Spec & Setup Guide)
 
1. Project Vision
What It Is
An enterprise SaaS platform where users describe a software requirement in plain English → the system automatically:
1.	Breaks it down into tasks (via AI PM).
2.	Generates working code (via AI Engineer).
3.	Tests it (via AI QA + sandbox).
4.	Stores repos/logs.
5.	Provides audit logs for compliance.
Why
•	Enterprises want faster software delivery with compliance & control.
•	Existing tools (GitHub Copilot, ChatGPT) are individual, not enterprise multi-tenant platforms.
•	We differentiate with Auth, RBAC, Audit, Secure Execution, Multi-tenancy, Integrations.
Users
•	Consulting firms
•	IT service companies
•	Enterprise dev teams with compliance needs
 
2. Repo Layout
/saas-devgen
 ├── /auth-service        # Authentication & tenant management (Keycloak)
 ├── /orchestrator        # Requirement intake, task breakdown, agent workflows
 ├── /codegen-service     # Code generation via AI agents (MetaGPT/OpenDevin)
 ├── /executor-service    # Secure sandbox execution (E2B/Docker)
 ├── /storage-service     # File/object storage + metadata
 ├── /audit-service       # Logging + telemetry (OpenTelemetry + Loki)
 ├── /api-gateway         # Unified entrypoint (FastAPI)
 ├── /frontend            # (Later) Next.js dashboard
 └── /infra               # Docker/K8s manifests
 
3. Architecture
[User] → [Auth: Keycloak] → [API Gateway]
       → [Orchestrator → MetaGPT (PM)]
       → [Codegen: Engineer → Repo]
       → [Storage: Save Repo/Metadata]
       → [Executor: Sandbox Run → Logs]
       → [Audit Service: Log Events]
       → [Response back to User]
 
4. Modules & Libraries
4.1 Auth Service
•	Purpose: Login, RBAC, tenant isolation.
•	Libraries: Keycloak (Apache 2.0), python-keycloak.
•	MVP: JWT auth + tenant claims.
4.2 Orchestrator Service
•	Purpose: Intake requirement → manage agent workflows.
•	Libraries: FastAPI, LangGraph, MetaGPT.
•	MVP: PM agent → breakdown → send to codegen.
4.3 Codegen Service
•	Purpose: Generate actual code.
•	Libraries: MetaGPT (Engineer role) OR OpenDevin.
•	MVP: Output repo + save to storage.
4.4 Executor Service
•	Purpose: Run code safely.
•	Libraries: E2B sandbox, Docker SDK for Python.
•	MVP: Execute tests, return logs.
4.5 Storage Service
•	Purpose: Store repos, artifacts, logs.
•	Libraries: Minio, SQLAlchemy + Postgres.
•	MVP: Save {tenant_id}/{project_id}/ repos + metadata.
4.6 Audit Service
•	Purpose: Audit logs.
•	Libraries: OpenTelemetry, Loki.
•	MVP: Log requirement submitted, code generated, execution run.
4.7 API Gateway
•	Purpose: Single entrypoint.
•	Libraries: FastAPI.
•	MVP: Routes requests to services.
4.8 Frontend (Later R2)
•	Libraries: Next.js, ReactFlow, Shadcn/UI.
•	MVP: Minimal Swagger / REST test only.
 
5. API Contracts
Auth Service
POST /auth/login
  Input: { username, password }
  Output: { access_token, tenant_id }

GET /auth/user
  Headers: Authorization: Bearer <token>
  Output: { user_id, tenant_id, roles }
Orchestrator
POST /requirements
  Input: { requirement: "Build REST API in FastAPI for employees" }
  Output: { requirement_id, tasks[], status }
Codegen
POST /codegen/{requirement_id}
  Input: { tasks[], language, framework }
  Output: { repo_url, commit_id, status }
Executor
POST /executor/run
  Input: { repo_url, command }
  Output: { execution_id, logs, status }
Storage
GET /storage/projects/{project_id}
  Output: { files[], repo_url, metadata }
Audit
GET /audit/logs?tenant_id=123
  Output: [ { timestamp, action, user_id, requirement_id } ]
 
6. Data Model (Postgres)
Users
id, username, email, tenant_id, roles[]
Tenants
id, name, org_id
Requirements
id, tenant_id, user_id, text, status, created_at
Tasks
id, requirement_id, description, status
Projects
id, tenant_id, requirement_id, repo_url, metadata
Executions
id, project_id, command, logs, status
Audit Logs
id, tenant_id, user_id, action, entity, timestamp
 
7. Setup Instructions
7.1 Prerequisites
•	Docker & Docker Compose
•	Python 3.10+
•	Node.js (for later frontend)
7.2 Environment Variables (.env)
POSTGRES_USER=devgen
POSTGRES_PASSWORD=secret
POSTGRES_DB=devgen
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=admin123
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin
7.3 Docker Compose (MVP infra)
/infra/docker-compose.yml
version: "3.9"
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports: [ "5432:5432" ]

  minio:
    image: minio/minio
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    command: server /data
    ports: [ "9000:9000", "9001:9001" ]

  keycloak:
    image: quay.io/keycloak/keycloak:24.0
    environment:
      KEYCLOAK_ADMIN: ${KEYCLOAK_ADMIN}
      KEYCLOAK_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD}
    command: start-dev
    ports: [ "8080:8080" ]

  loki:
    image: grafana/loki:2.9.0
    ports: [ "3100:3100" ]
7.4 Service Bootstraps
Orchestrator (FastAPI)
cd orchestrator
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn metagpt langgraph
uvicorn main:app --reload --port 8001
Codegen
cd codegen-service
pip install fastapi opendevin metagpt
uvicorn main:app --reload --port 8002
Executor
cd executor-service
pip install fastapi docker e2b
uvicorn main:app --reload --port 8003
Storage
cd storage-service
pip install fastapi sqlalchemy psycopg2 minio
uvicorn main:app --reload --port 8004
Audit
cd audit-service
pip install fastapi opentelemetry-api opentelemetry-sdk
uvicorn main:app --reload --port 8005
API Gateway
cd api-gateway
pip install fastapi httpx
uvicorn main:app --reload --port 8000
 
8. MVP Deliverables
✅ Auth with Keycloak (JWT)
✅ Requirement intake → MetaGPT PM breakdown
✅ Code generation → Engineer → repo in Minio
✅ Sandbox execution → logs returned
✅ Audit logging per tenant
✅ REST APIs exposed via FastAPI gateway
 
9. Roadmap
Release 2 (Enterprise-ready)
•	Add Temporal workflows for reliability.
•	UI Dashboard (Next.js + ReactFlow).
•	GitHub/Jira/Slack integrations.
•	Role-based Access Control (RBAC).
Release 3 (Ecosystem Integration)
•	Full CI/CD integration.
•	On-prem deployment option.
•	Analytics & reporting for managers.
 
✅ With this spec, devs can clone the repo, spin up infra, and begin coding each service.

