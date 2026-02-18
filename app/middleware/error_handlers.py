"""Global error handlers for the application."""
import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


def setup_error_handlers(app: FastAPI) -> None:
    """
    Configure global error handlers for the application.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, 
        exc: RequestValidationError
    ) -> JSONResponse:
        """
        Handle validation errors (HTTP 422).
        
        Args:
            request: HTTP request
            exc: Validation error exception
            
        Returns:
            JSON response with validation error details
        """
        logger.warning(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation Error",
                "details": exc.errors()
            }
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(
        request: Request, 
        exc: SQLAlchemyError
    ) -> JSONResponse:
        """
        Handle database errors (HTTP 503).
        
        Args:
            request: HTTP request
            exc: SQLAlchemy error exception
            
        Returns:
            JSON response with generic database error message
        """
        logger.error(f"Database error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "Database Error",
                "message": "A database error occurred. Please try again later."
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, 
        exc: Exception
    ) -> JSONResponse:
        """
        Handle all other unhandled exceptions (HTTP 500).
        
        Args:
            request: HTTP request
            exc: Unhandled exception
            
        Returns:
            JSON response with generic error message
        """
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred. Please try again later."
            }
        )
