"""FastAPI application entry point."""
from fastapi import FastAPI

from app.api import health
from app.config.settings import settings
from app.database.connection import init_db, close_db
from app.middleware.setup import setup_middleware
from app.middleware.error_handlers import setup_error_handlers
from app.utils.logging import setup_logging


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title="Vehicle Automation Microservice",
        description="Phase 1: Infrastructure Scaffold",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Setup middleware (logging, CORS, security headers)
    setup_middleware(app)
    
    # Setup error handlers
    setup_error_handlers(app)
    
    # Register routers
    app.include_router(health.router, tags=["health"])
    
    # Import and register allocation router
    from app.api import allocation
    app.include_router(allocation.router)
    
    # Lifecycle events
    app.add_event_handler("startup", init_db)
    app.add_event_handler("shutdown", close_db)
    
    return app


# Create application instance
app = create_app()

# Setup logging
setup_logging(settings.log_level)
