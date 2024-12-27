from fastapi import APIRouter

from langfarm_tracing.api.routes import ingestion

api_router = APIRouter()
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["ingestion"])
