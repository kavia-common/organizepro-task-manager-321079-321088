import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .init_db import init_db
from .routes_categories import router as categories_router
from .routes_tasks import router as tasks_router


def _split_csv_env(name: str, default: str) -> list[str]:
    value = os.getenv(name, default)
    return [v.strip() for v in value.split(",") if v.strip()]


openapi_tags = [
    {"name": "System", "description": "Health and system endpoints."},
    {"name": "Categories", "description": "Create, update, list, and delete categories."},
    {"name": "Tasks", "description": "CRUD tasks, filtering, sorting, and status updates."},
]

app = FastAPI(
    title="OrganizePro Task Manager API",
    description=(
        "Backend API for a task management application.\n\n"
        "Features:\n"
        "- Categories CRUD\n"
        "- Tasks CRUD\n"
        "- Filter tasks by status/category\n"
        "- Sort and paginate tasks\n"
    ),
    version="1.0.0",
    openapi_tags=openapi_tags,
)

allowed_origins = _split_csv_env("ALLOWED_ORIGINS", "*")
allowed_headers = _split_csv_env("ALLOWED_HEADERS", "*")
allowed_methods = _split_csv_env("ALLOWED_METHODS", "*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=allowed_methods if allowed_methods != ["*"] else ["*"],
    allow_headers=allowed_headers if allowed_headers != ["*"] else ["*"],
)


@app.on_event("startup")
def _startup():
    init_db()


@app.get("/", tags=["System"], summary="Health check")
def health_check():
    """
    Health check endpoint.

    Returns:
        {"message": "Healthy"}
    """
    return {"message": "Healthy"}


@app.get("/healthz", tags=["System"], summary="K8s-style health probe")
def healthz():
    """Health probe used by frontend config/healthcheck."""
    return {"status": "ok"}


app.include_router(categories_router)
app.include_router(tasks_router)
