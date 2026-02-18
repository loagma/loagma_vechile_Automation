"""Database models."""
from sqlalchemy import Column, Integer, String, DateTime, func

from app.database.base import Base


class HealthCheckLog(Base):
    """Example model for storing health check logs."""
    __tablename__ = "health_check_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(String(50), nullable=False)
    checked_at = Column(DateTime, server_default=func.now(), nullable=False)
    details = Column(String(500), nullable=True)
