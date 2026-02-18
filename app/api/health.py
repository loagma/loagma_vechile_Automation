"""Health check and status endpoints."""
import logging
import time

from fastapi import APIRouter, Response, status

from app.database.connection import check_db_health
from app.config.settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Track application start time
start_time = time.time()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(response: Response) -> dict:
    """
    Health check endpoint that verifies service and database status.
    
    Returns:
        - 200 OK if service and database are healthy
        - 503 Service Unavailable if database is unhealthy
    
    Args:
        response: FastAPI response object for setting status code
        
    Returns:
        dict: Health status information
    """
    db_health = await check_db_health()
    
    if db_health["status"] == "unhealthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unhealthy",
            "service": "running",
            "database": db_health
        }
    
    return {
        "status": "healthy",
        "service": "running",
        "database": db_health
    }


@router.get("/status", status_code=status.HTTP_200_OK)
async def status_check() -> dict:
    """
    Status endpoint that returns service metadata.
    
    Returns service version, uptime, and environment information.
    
    Returns:
        dict: Service metadata
    """
    uptime_seconds = int(time.time() - start_time)
    
    return {
        "service": "vehicle-automation-microservice",
        "version": "0.1.0",
        "phase": "1-scaffold",
        "uptime_seconds": uptime_seconds,
        "environment": "development" if settings.debug else "production"
    }
