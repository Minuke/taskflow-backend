from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import auth, categories, dashboard, tasks
from app.core.config import settings
from app.core.error_handlers import register_error_handlers
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(level="DEBUG" if settings.environment == "development" else "INFO")
    yield


app = FastAPI(title=settings.project_name, lifespan=lifespan)
register_error_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(tasks.router)
app.include_router(dashboard.router)

app.mount("/media/tasks", StaticFiles(directory=settings.upload_dir), name="task-media")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
