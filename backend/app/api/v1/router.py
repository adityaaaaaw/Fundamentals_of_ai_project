from fastapi import APIRouter
from app.api.v1.routes.tasks import router as tasks_router
from app.api.v1.routes.sessions import router as sessions_router
from app.api.v1.routes.exams import router as exams_router
from app.api.v1.routes.dashboard import router as dashboard_router
from app.api.v1.routes.ai import router as ai_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(tasks_router)
api_v1_router.include_router(sessions_router)
api_v1_router.include_router(exams_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(ai_router)
