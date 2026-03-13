# kast - Task Manager

**Kast** is a simple task manager that allows you to collaborate with a small teams in projects.
Task are created within a project, so you need to create a project or join an existing one to create tasks. 
As project owner you can manage all tasks of your project, also asign tasks to a member.
As member you can manage your own tasks (created by you or assigned to you).
Everyone in a project can see all the tasks.

Kast is under construction. Today, kast has its API rest working, you can generate some mock users, tasks and project and start testing how works all available endpoints running instructions below.

## How to run it?
### Backend Setup

**Environment Variables:** 
You will need to write a .env file with the following variables:

POSTGRES_USER=taskmanager  
POSTGRES_PASSWORD=taskmanager  
POSTGRES_DB=taskmanager  
POSTGRES_HOST=localhost  
POSTGRES_PORT=5433  
APP_SECRET_KEY=dev-secret-key-change-in-production  
APP_JWT_ALGORITHM=HS256  
APP_ACCESS_TOKEN_EXPIRE_MINUTES=60  

These values are just examples. Please, change these values in production.


Make sure you have uv astral installed
```bash
uv --version
```
If not installed, you can install it with pip:
```bash
pip install uv # with pip
```
If you prefer your OS package manager:

**For linux**
```bash
sudo snap install astral-uv --classic # with snap
```
 
**For macOS**
```bash
brew install uv # homebrew
```

**For Windows**
```bash
winget install --id=astral-sh.uv  -e # WinGet
```
or:
```bash
scoop install main/uv # Scoop
```

Then:

```bash
# Create a virtual environment
uv venv
# Activate virtual environment
source .venv/bin/activate
# Install dependencies
uv pip install -e ".[dev]"
# Start database
docker compose up -d db
# Run alembic migrations
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
# Run script to generate demo entities
python -m src.scripts.seed
# Run the API
uvicorn src.main:app --reload
```
