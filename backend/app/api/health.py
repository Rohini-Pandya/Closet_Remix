from fastapi import APIRouter, Depends

from app.core.auth import AuthUser, get_current_user
from app.core.config import Settings, get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(settings: Settings = Depends(get_settings)) -> dict:
    """Public liveness check. Reports configuration presence only, never secrets."""
    return {"status": "ok", "supabase_configured": settings.supabase_configured}


@router.get("/ai/status")
async def ai_status(_: AuthUser = Depends(get_current_user)) -> dict:
    """Placeholder until Phase 3: real Ollama / RF-DETR probes are NOT implemented yet."""
    return {"implemented": False, "ollama": "unknown", "segmentation": "unknown", "note": "Probes arrive in Phase 3"}
