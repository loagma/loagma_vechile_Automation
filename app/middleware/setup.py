"""Middleware setup and configuration."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.middleware.logging import LoggingMiddleware


def setup_middleware(app: FastAPI) -> None:
    """
    Configure all middleware for the application.
    
    Args:
        app: FastAPI application instance
    """
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """Add security headers to all responses."""
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response
