from fastapi import APIRouter

from app.api.v1 import analysis, assistant, auth, centres, dashboard, documents, health, profile

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(dashboard.router)
api_router.include_router(documents.router)
api_router.include_router(analysis.router)
api_router.include_router(analysis.comparisons_router)
api_router.include_router(centres.router)
api_router.include_router(assistant.router)
