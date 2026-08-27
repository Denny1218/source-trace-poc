from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analysis import router as analysis_router
from app.api.equipment import router as equipment_router
from app.api.git_repository import equipment_router as repo_equipment_router
from app.api.git_repository import repository_router as git_repository_router
from app.api.git_history import equipment_router as git_equipment_router
from app.api.git_history import git_router as git_commit_router
from app.api.health import router as health_router
from app.api.ppt_cache import router as ppt_cache_router
from app.api.trace import router as trace_router
from app.api.trace_extension import router as trace_extension_router
from app.api.trace_selection import router as trace_selection_router
from app.core.frontend_static import configure_frontend_static
from app.core.logging import get_logger, setup_logging
from app.db.database import init_database

setup_logging()
logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Application start")
    try:
        init_database()
    except Exception as exc:
        logger.error("Database init failed: %s", exc)
    yield
    logger.info("Application shutdown")


app = FastAPI(
    title="Equipment Change Trace",
    description="AI 기반 장비 소스 변경 이력 추적 및 유지보수 지원 POC",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(equipment_router)
app.include_router(repo_equipment_router)
app.include_router(git_repository_router)
app.include_router(git_equipment_router)
app.include_router(git_commit_router)
app.include_router(trace_router)
app.include_router(analysis_router)
app.include_router(trace_extension_router)
app.include_router(trace_selection_router)
app.include_router(ppt_cache_router)

if not configure_frontend_static(app):

    @app.get("/")
    def root() -> dict:
        return {"message": "Equipment Change Trace API"}
