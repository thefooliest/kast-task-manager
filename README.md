# Kast

**Kast** is a simple task manager designed for small teams to collaborate on projects efficiently.

Tasks are organized within projects. To start creating tasks, you'll need to either create a new project or join an existing one.

## Permissions

- **Project Owners** have full control over all tasks within their project and can assign tasks to team members.
- **Team Members** can manage tasks they've created or those assigned to them.
- All project participants can view every task within the project.

## Current Status

🚧 **Kast is under active development**

The REST API and frontend are functional. You can run the application locally, log in, and perform CRUD operations on tasks and projects through the React interface.

Follow the instructions below to test it out.

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
