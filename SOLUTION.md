# Solution

## How to Run

### Prerequisites

- Python 3.13+
- Node.js 18+
- Docker and Docker Compose
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### Setup

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd task-manager

# 2. Create .env from the example
cp .env.example .env

# 3. Start PostgreSQL
docker compose up -d db

# 4. Install backend dependencies
uv pip install -e ".[dev]"

# 5. Run database migrations
alembic upgrade head

# 6. Seed the database with demo data
python -m src.scripts.seed

# 7. Start the API (terminal 1)
uvicorn src.main:app --reload

# 8. Install and start the frontend (terminal 2)
cd frontend
npm install
npm run dev
```

The API runs at `http://localhost:8000` (docs at `/api/docs`).
The frontend runs at `http://localhost:5173`.

### Demo Credentials

| User  | Email                    | Password  | Role   |
|-------|--------------------------|-----------|--------|
| Admin | admin@taskmanager.com    | admin123  | Owner  |
| Alice | alice@taskmanager.com    | alice123  | Member |
| Bob   | bob@taskmanager.com      | bob123    | Member |

### Running Tests

```bash
# Create the test database (first time only)
docker compose exec db psql -U taskmanager -c "CREATE DATABASE taskmanager_test;"

# Run tests
pytest -v
```

---

## Features Implemented

### MVP (Required)

- **User authentication** — JWT-based login with bcrypt password hashing. Protected endpoints verify tokens via a FastAPI dependency.
- **Task CRUD** — Create, read, update, and delete tasks with title, description, status, priority, assignment, and due dates.
- **Role-based access** — Project-based model with owner and member roles. Owners can manage all tasks; members can only modify tasks they created or are assigned to.
- **React frontend** — Login, project selection, task management with inline editing, status toggling, and filtering.

### Should Have

- **Task filtering by status** — Filter tasks by To Do, In Progress, or Done via query parameter and frontend filter tabs.
- **Task assignment** — Assign tasks to project members with a dropdown picker. Backend validates that the assignee is a project member.

### Nice to Have (Bonus)

- **Task comments** — Any project member can comment on tasks. Only the comment author or the project owner can delete comments. Collapsible per-task comment section with author names and relative timestamps.
- **Due date notifications** — Background scheduler (asyncio task via FastAPI lifespan) checks for overdue tasks every 5 minutes. Creates one notification per overdue task per user (idempotent). Bell icon in the header with unread count badge, dropdown panel with mark-as-read functionality.
- **Activity log** — All mutations (task CRUD, comments, member additions) are logged with actor name and detail message. Collapsible activity feed per project with pagination.
- **Pagination** — Task listing returns paginated results with total count. Frontend shows page navigation.
- **Rate limiting** — In-memory sliding window rate limiter on the login endpoint (10 attempts per minute per IP).
- **Member management UI** — Collapsible member panel showing names, emails, and roles. Project owners can add members by email.

---

## Architectural Decisions

### Layered Backend Architecture

I chose a strict layered architecture that separates concerns clearly:

```
Controllers (FastAPI routers)
    ↓ validates input with Pydantic schemas
Services (business logic)
    ↓ works only with domain dataclasses
Repositories (data access)
    ↓ maps between domain entities and ORM models
ORM Models (SQLAlchemy)
```

**Why this matters:**

- **Domain entities are pure Python dataclasses** with zero framework dependencies. Services never import SQLAlchemy. This means business logic is testable without a database and portable if the persistence layer changes.
- **ORM models are confined to the repository layer.** They never leak into services or controllers. Repositories handle the `_to_domain()` mapping, acting as the single translation point.
- **Schemas exist only for input validation.** Response serialization uses domain dataclasses directly — FastAPI serializes them natively, eliminating a redundant "response schema" layer.

This gives us three clear data shapes: **schemas** (API boundary), **domain entities** (business logic), and **ORM models** (database). Each layer has a single responsibility.

**Trade-off:** More files and indirection than a flat structure. For a small-team project this could be considered over-engineering, but it demonstrates separation of concerns and makes the codebase maintainable as it grows.

### Async SQLAlchemy

I used `AsyncSession` with `asyncpg` instead of synchronous SQLAlchemy with `psycopg2`. FastAPI is async-native — synchronous database calls block the event loop and get offloaded to a thread pool. With async SQLAlchemy, database I/O integrates naturally with the event loop, enabling better throughput under concurrent load without the thread pool overhead.

**Trade-off:** Async requires more careful session management (no lazy loading, explicit `selectinload` for relationships), and Alembic needs an async-compatible `env.py`. The added complexity is small and well worth it for a production FastAPI application.

### Project-Based Access Model

Rather than a flat "task creator = owner" model, I implemented a project-based structure:

- Users create **projects** and become the project **owner**
- Owners can add **members** to a project by email
- Tasks belong to a project
- **Permission rules:**
  - All project members can view all tasks in the project
  - Any member can create tasks
  - Members can edit/delete only tasks they created or are assigned to
  - Project owners can edit/delete any task in their project

This maps well to real team workflows (similar to Todoist's shared projects) and provides a natural scope for permissions without over-complicating the model.

### Background Scheduler for Notifications

Rather than checking due dates on every request (which adds latency) or relying on frontend-only logic (which misses users not currently viewing tasks), I implemented a background scheduler using FastAPI's `lifespan` context manager and `asyncio.create_task`.

The scheduler runs a loop every 5 minutes, queries overdue tasks, and creates notifications. It's idempotent — it checks `exists_for_task` before creating a notification, so a task that stays overdue only generates one notification.

**Trade-off:** This runs in-process with the API server. In a production system with multiple API instances, you'd want a dedicated worker (Celery, ARQ) or a database-level scheduler to avoid duplicate checks. For a single-instance deployment, the lifespan approach is simple and reliable.

### Environment Configuration

All configuration flows from a single `.env` file:

- Docker Compose reads it for PostgreSQL setup
- `pydantic-settings` reads it for the application
- Alembic reads it through the application settings
- **No hardcoded defaults** — the app fails loudly if `.env` is missing, preventing silent misconfigurations

### UUID Primary Keys

All entities use UUIDs instead of sequential integers. UUIDs are safer to expose in APIs (no enumeration attacks), work better in distributed systems, and don't leak information about record count or creation order.

### Connection Pooling

The async engine is configured with explicit pool settings (`pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`, `pool_recycle=300`) rather than relying on defaults. `pool_pre_ping` detects stale connections after database restarts, and `pool_recycle` prevents long-lived connections from going stale.

---

## Security Measures

**Current protections:**

- **Authentication** — JWT-based with bcrypt password hashing. Tokens are validated on every protected request via a FastAPI dependency.
- **Rate limiting** — Login endpoint is limited to 10 attempts per minute per IP using an in-memory sliding window. Returns 429 when exceeded.
- **CORS** — Restricted to the frontend origin (`localhost:5173`). Not open to `*`.
- **Security headers** — The API sets `X-Frame-Options: DENY` (prevents clickjacking), `X-Content-Type-Options: nosniff` (prevents MIME sniffing), `X-XSS-Protection: 1; mode=block`, and `Referrer-Policy: strict-origin-when-cross-origin`.
- **XSS** — React escapes all rendered content by default. The frontend never uses `dangerouslySetInnerHTML`.
- **CSRF** — Not a concern because authentication uses the `Authorization` header with Bearer tokens, not cookies. CSRF attacks exploit automatic cookie inclusion, which doesn't apply here.
- **SQL injection** — SQLAlchemy's parameterized queries prevent injection. No raw SQL with string interpolation.
- **Input validation** — Pydantic schemas validate all request bodies. Invalid data is rejected before reaching business logic.
- **Assignment validation** — Backend verifies that `assigned_to` is a project member before accepting task creation or updates.

**Token storage trade-off:**

JWT tokens are stored in `localStorage`. This is the standard approach for SPA + API architectures, but it comes with a known trade-off: if an XSS vulnerability exists, malicious JavaScript could read the token from `localStorage` and exfiltrate it. Once stolen, the token can be used from anywhere — CORS is a browser-only enforcement and doesn't protect against direct HTTP requests from outside the browser.

The alternative is `httpOnly` cookies, which JavaScript cannot read — making token theft via XSS impossible. However, cookies introduce CSRF vulnerabilities and require additional backend complexity (`SameSite` configuration, CSRF tokens, cookie-based session management).

For this project, `localStorage` is the pragmatic choice: React's built-in XSS protection (all rendered content is escaped, no use of `dangerouslySetInnerHTML`) makes the XSS vector unlikely, and the simpler auth flow keeps the codebase focused. In a higher-security context, migrating to `httpOnly` cookies with `SameSite=Strict` would be the next step.

---

## What I Prioritized

1. **Clean architecture** — The layered structure with domain/ORM separation was the foundation. I spent time getting this right because it affects every subsequent decision.

2. **Permission model** — The project-based access control with owner/member roles is the core business logic. Tests specifically cover permission boundaries (member can't modify other's tasks, owner can modify any task, non-member can't access project).

3. **API correctness** — Proper HTTP status codes (201 for creation, 204 for deletion, 403 for permission denied, 409 for conflicts, 422 for validation errors, 429 for rate limiting), JWT authentication, and input validation.

4. **Test coverage** — 42+ tests covering authentication, project management, task CRUD, status filtering, permission enforcement, comments, activity logging, notifications, and the background scheduler.

5. **Functional frontend** — Clean, Todoist-inspired UI that covers all core flows: login, project management, task CRUD with inline editing, status toggling, filtering, comments, member management, activity feed, and notifications.

---

## What I Would Improve With More Time

### Backend
- **Token storage** — Currently JWTs are stateless. Adding a `tokens` table to track issued tokens would enable proper token revocation on logout and mass invalidation if the secret key is compromised. This is important for incident response — without it, a leaked secret key means all tokens are valid until they expire.
- **Registration endpoint** — Currently relies on seeded users. Adding registration with email validation would be a natural next step.
- **Refresh tokens** — Current JWT setup uses only access tokens. A refresh token flow would improve security and UX.
- **WebSocket notifications** — Currently the frontend polls for unread count every 30 seconds. WebSockets or Server-Sent Events would provide real-time push notifications without polling overhead.

### Frontend
- **Responsive design** — The layout works on desktop but could be improved for mobile screens.
- **Better error handling** — More specific error messages and toast notifications instead of inline error banners.
- **Loading skeletons** — Replace "Loading..." text with skeleton placeholders.
- **Content Security Policy** — Add a strict CSP header to prevent inline script injection. Currently not needed since React handles rendering safely, but it's a defense-in-depth measure.
- **Dependency auditing** — Add `npm audit` to the development workflow and pin dependency versions in `package-lock.json`.

### Infrastructure
- **CI/CD pipeline** — GitHub Actions for running tests and linting on push.
- **Dockerfile for backend** — Containerize the API for consistent deployments.
- **Database backups** — Automated PostgreSQL backup strategy.
- **Dedicated scheduler worker** — Move the overdue checker to a separate process for multi-instance deployments.

---

## Project Structure

```
task-manager/
├── docker-compose.yml
├── pyproject.toml
├── alembic.ini
├── .env.example
├── SOLUTION.md
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── src/
│   ├── main.py                          # FastAPI app, lifespan, middleware, routers
│   ├── core/
│   │   ├── config.py                    # pydantic-settings, .env loading
│   │   ├── database.py                  # Async engine, session factory
│   │   ├── security.py                  # JWT, bcrypt
│   │   ├── dependencies.py              # get_current_user, get_project_member
│   │   ├── rate_limit.py                # In-memory sliding window limiter
│   │   └── scheduler.py                 # Background overdue task checker
│   ├── domain/                          # Pure dataclasses, zero dependencies
│   │   ├── enums.py
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── task.py
│   │   ├── comment.py
│   │   ├── activity.py
│   │   └── notification.py
│   ├── models/                          # SQLAlchemy ORM, confined to repositories
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── project_member.py
│   │   ├── task.py
│   │   ├── comment.py
│   │   ├── activity.py
│   │   └── notification.py
│   ├── repositories/                    # DB queries, ORM ↔ domain mapping
│   │   ├── user_repository.py
│   │   ├── project_repository.py
│   │   ├── task_repository.py
│   │   ├── comment_repository.py
│   │   ├── activity_repository.py
│   │   └── notification_repository.py
│   ├── services/                        # Business logic, permission checks
│   │   ├── auth_service.py
│   │   ├── project_service.py
│   │   ├── task_service.py
│   │   ├── comment_service.py
│   │   └── activity_service.py
│   ├── controllers/                     # Thin FastAPI routers
│   │   ├── auth_controller.py
│   │   ├── project_controller.py
│   │   ├── task_controller.py
│   │   ├── comment_controller.py
│   │   ├── activity_controller.py
│   │   └── notification_controller.py
│   ├── schemas/                         # Pydantic input validation only
│   │   ├── auth.py
│   │   ├── project.py
│   │   ├── task.py
│   │   └── comment.py
│   └── scripts/
│       └── seed.py                      # Demo data seeder
├── tests/
│   ├── conftest.py                      # Async fixtures, test DB
│   ├── test_auth.py
│   ├── test_projects.py
│   ├── test_tasks.py
│   ├── test_comments.py
│   ├── test_activity.py
│   └── test_notifications.py
└── frontend/
    ├── package.json
    ├── vite.config.js                   # API proxy to backend
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx                      # Router setup
        ├── api/
        │   └── client.js               # Fetch wrapper with JWT
        ├── context/
        │   └── AuthContext.jsx          # Auth state management
        ├── pages/
        │   ├── LoginPage.jsx
        │   ├── ProjectsPage.jsx
        │   └── TasksPage.jsx
        ├── components/
        │   ├── Header.jsx
        │   ├── ProtectedRoute.jsx
        │   ├── TaskItem.jsx
        │   ├── TaskForm.jsx
        │   ├── CommentSection.jsx
        │   ├── MemberList.jsx
        │   ├── ActivityFeed.jsx
        │   └── NotificationBell.jsx
        └── styles/
            ├── global.css               # CSS variables, typography, utilities
            └── *.module.css             # Scoped component styles
```

---

## Tech Stack Summary

### Backend
- **Python 3.13+** with type hints throughout
- **FastAPI** — async web framework with lifespan for background tasks
- **SQLAlchemy 2.0** — async ORM with mapped column annotations
- **asyncpg** — async PostgreSQL driver
- **Alembic** — database migrations
- **pydantic-settings** — environment configuration
- **python-jose** — JWT encoding/decoding
- **bcrypt** — password hashing
- **pytest + httpx** — async API testing

### Frontend
- **React 18** with hooks
- **Vite** — build tool with API proxy
- **react-router-dom** — client-side routing
- **CSS Modules** — scoped component styles
- **Plain CSS** — no framework dependencies

### Infrastructure
- **PostgreSQL 16** — via Docker Compose
- **Docker Compose** — database provisioning
- **.env** — centralized configuration