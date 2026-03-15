import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.controllers import (
    activity_controller,
    auth_controller,
    comment_controller,
    notification_controller,
    project_controller,
    task_controller,
)
from src.core.scheduler import overdue_checker_loop
from src.services.task_service import NotFoundError, PermissionDeniedError, ValidationError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background scheduler on boot, cancel on shutdown."""
    task = asyncio.create_task(overdue_checker_loop())
    logger.info("Background scheduler started")
    yield
    task.cancel()
    logger.info("Background scheduler stopped")


app = FastAPI(
    title="Task Manager API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Routers
app.include_router(auth_controller.router)
app.include_router(project_controller.router)
app.include_router(task_controller.router)
app.include_router(comment_controller.router)
app.include_router(activity_controller.router)
app.include_router(notification_controller.router)


# Global exception handlers — map service exceptions to HTTP status codes
@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(PermissionDeniedError)
async def permission_denied_handler(request: Request, exc: PermissionDeniedError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}