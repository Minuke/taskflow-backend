from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth
from app.api import categories
from app.api import tasks
from app.api import dashboard
from fastapi.staticfiles import StaticFiles
from app.core.config import settings

app = FastAPI(title=settings.project_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media/tasks", StaticFiles(directory=settings.upload_dir), name="task-media")

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(tasks.router)
app.include_router(dashboard.router)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}