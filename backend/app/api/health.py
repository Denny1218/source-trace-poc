from fastapi import APIRouter

from app.services.health_service import get_health_status

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health_check() -> dict:
    return get_health_status()
