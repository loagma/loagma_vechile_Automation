"""Shared pytest fixtures for testing."""
import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def app():
    """Create FastAPI application for testing."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client for API testing."""
    return TestClient(app)
