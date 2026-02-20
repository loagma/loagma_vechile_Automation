"""
SQLAlchemy ORM models for the application.
Phase 1: Vehicle Allocation System
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    ForeignKey,
    Numeric,
    Enum,
    Index,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import relationship
from app.database.base import Base


class HealthCheckLog(Base):
    """Example model for storing health check logs."""
    
    __tablename__ = "health_check_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(String(50), nullable=False)
    checked_at = Column(DateTime, server_default=func.now(), nullable=False)
    details = Column(String(500), nullable=True)


# ============================================================================
# Phase 1: Vehicle Allocation Models
# ============================================================================

class TripCardStatus(str, PyEnum):
    """Trip card status enumeration."""
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    OVERWEIGHT = "OVERWEIGHT"


class AllocationTrigger(str, PyEnum):
    """Allocation batch trigger type."""
    CRON = "CRON"
    ADMIN = "ADMIN"


class AllocationBatchStatus(str, PyEnum):
    """Allocation batch status."""
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Vehicle(Base):
    """Vehicle master table for allocation system."""
    
    __tablename__ = "vehicles"
    
    vehicle_id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_number = Column(String(50), nullable=False, unique=True, index=True)
    capacity_kg = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    trip_cards = relationship("TripCard", back_populates="vehicle")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('capacity_kg > 0', name='chk_vehicle_capacity_positive'),
    )
    
    def __repr__(self):
        return f"<Vehicle(id={self.vehicle_id}, number={self.vehicle_number}, capacity={self.capacity_kg}kg)>"


class TripCard(Base):
    """Trip cards (zones) for vehicle allocation."""
    
    __tablename__ = "trip_cards"
    
    zone_id = Column(Integer, primary_key=True, autoincrement=True)
    zone_name = Column(String(100), nullable=False, unique=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.vehicle_id', ondelete='SET NULL'), nullable=True, index=True)
    status = Column(Enum(TripCardStatus), default=TripCardStatus.IDLE, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="trip_cards")
    pincodes = relationship("TripCardPincode", back_populates="trip_card", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="allocated_zone", foreign_keys="Order.allocated_zone_id")
    
    def __repr__(self):
        return f"<TripCard(id={self.zone_id}, name={self.zone_name}, status={self.status})>"


class TripCardPincode(Base):
    """Pincode assignments to trip card zones."""
    
    __tablename__ = "trip_card_pincode"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    zone_id = Column(Integer, ForeignKey('trip_cards.zone_id', ondelete='CASCADE'), nullable=False)
    pincode = Column(String(10), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    trip_card = relationship("TripCard", back_populates="pincodes")
    
    # Constraints
    __table_args__ = (
        Index('uk_zone_pincode', 'zone_id', 'pincode', unique=True),
    )
    
    def __repr__(self):
        return f"<TripCardPincode(zone_id={self.zone_id}, pincode={self.pincode})>"


class AllocationBatch(Base):
    """Allocation batch execution tracking."""
    
    __tablename__ = "allocation_batches"
    
    batch_id = Column(Integer, primary_key=True, autoincrement=True)
    window_start = Column(DateTime, nullable=False, index=True)
    window_end = Column(DateTime, nullable=False, index=True)
    triggered_by = Column(Enum(AllocationTrigger), nullable=False)
    status = Column(Enum(AllocationBatchStatus), default=AllocationBatchStatus.RUNNING, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    orders = relationship("Order", back_populates="allocation_batch", foreign_keys="Order.allocation_batch_id")
    
    __table_args__ = (
        Index('idx_batch_window', 'window_start', 'window_end'),
    )
    
    def __repr__(self):
        return f"<AllocationBatch(id={self.batch_id}, status={self.status}, trigger={self.triggered_by})>"


class Order(Base):
    """
    Orders table - EXISTING TABLE with new nullable columns added.
    
    NOTE: This model represents the orders table with Phase 1 allocation columns.
    Existing columns are not shown here but exist in the database.
    Only the new allocation-related columns are defined.
    
    IMPORTANT: If your existing orders table has different columns,
    add them here to match your actual schema.
    """
    
    __tablename__ = "orders"
    
    # Existing primary key (adjust if your table uses different name)
    order_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Add other existing columns here as needed, for example:
    # created_at = Column(DateTime, server_default=func.now())
    # customer_id = Column(Integer)
    # status = Column(String(50))
    # etc.
    
    # NEW NULLABLE COLUMNS for Phase 1 Vehicle Allocation
    pincode = Column(String(10), nullable=True, index=True, comment='Delivery pincode for allocation')
    total_weight_kg = Column(Numeric(10, 2), nullable=True, index=True, comment='Total order weight in kilograms')
    allocated_zone_id = Column(
        Integer, 
        ForeignKey('trip_cards.zone_id', ondelete='SET NULL'), 
        nullable=True,
        comment='Assigned trip card zone ID'
    )
    allocation_batch_id = Column(
        Integer, 
        ForeignKey('allocation_batches.batch_id', ondelete='SET NULL'), 
        nullable=True,
        comment='Allocation batch that processed this order'
    )
    
    # Relationships
    allocated_zone = relationship("TripCard", back_populates="orders", foreign_keys=[allocated_zone_id])
    allocation_batch = relationship("AllocationBatch", back_populates="orders", foreign_keys=[allocation_batch_id])
    
    # Performance index for allocation queries
    __table_args__ = (
        Index('idx_allocation_filter', 'allocated_zone_id', 'pincode', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Order(id={self.order_id}, pincode={self.pincode}, zone={self.allocated_zone_id})>"
