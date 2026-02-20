"""Phase 1: Vehicle Allocation - Production Safe Migration

Revision ID: 001_phase1_vehicle_allocation
Revises: 
Create Date: 2026-02-19 12:00:00.000000

IMPORTANT: This migration is ADDITIVE ONLY
- No existing columns modified
- No existing tables altered (except adding nullable columns)
- All new columns are NULLABLE
- Safe for rollback
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '001_phase1_vehicle_allocation'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply Phase 1 Vehicle Allocation schema changes."""
    
    # ========================================================================
    # 1. CREATE TABLE: vehicles
    # ========================================================================
    op.create_table(
        'vehicles',
        sa.Column('vehicle_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('vehicle_number', sa.String(length=50), nullable=False),
        sa.Column('capacity_kg', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('capacity_kg > 0', name='chk_vehicle_capacity_positive'),
        sa.PrimaryKeyConstraint('vehicle_id'),
        sa.UniqueConstraint('vehicle_number'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        comment='Vehicle master table for allocation system'
    )
    op.create_index('idx_vehicle_active', 'vehicles', ['is_active'])
    op.create_index('idx_vehicle_number', 'vehicles', ['vehicle_number'])
    
    # ========================================================================
    # 2. CREATE TABLE: trip_cards
    # ========================================================================
    op.create_table(
        'trip_cards',
        sa.Column('zone_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('zone_name', sa.String(length=100), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('IDLE', 'ACTIVE', 'OVERWEIGHT', name='tripcardstatus'), 
                  server_default='IDLE', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.vehicle_id'], 
                                name='fk_trip_card_vehicle', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('zone_id'),
        sa.UniqueConstraint('zone_name'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        comment='Trip cards (zones) for vehicle allocation'
    )
    op.create_index('idx_zone_status', 'trip_cards', ['status'])
    op.create_index('idx_zone_vehicle', 'trip_cards', ['vehicle_id'])
    
    # ========================================================================
    # 3. CREATE TABLE: trip_card_pincode
    # ========================================================================
    op.create_table(
        'trip_card_pincode',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('zone_id', sa.Integer(), nullable=False),
        sa.Column('pincode', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['zone_id'], ['trip_cards.zone_id'], 
                                name='fk_trip_card_pincode_zone', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        comment='Pincode assignments to trip card zones'
    )
    op.create_index('uk_zone_pincode', 'trip_card_pincode', ['zone_id', 'pincode'], unique=True)
    op.create_index('idx_pincode', 'trip_card_pincode', ['pincode'])
    
    # ========================================================================
    # 4. CREATE TABLE: allocation_batches
    # ========================================================================
    op.create_table(
        'allocation_batches',
        sa.Column('batch_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('window_start', sa.DateTime(), nullable=False),
        sa.Column('window_end', sa.DateTime(), nullable=False),
        sa.Column('triggered_by', sa.Enum('CRON', 'ADMIN', name='allocationtrigger'), nullable=False),
        sa.Column('status', sa.Enum('RUNNING', 'COMPLETED', 'FAILED', name='allocationbatchstatus'), 
                  server_default='RUNNING', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('batch_id'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        comment='Allocation batch execution tracking'
    )
    op.create_index('idx_batch_status', 'allocation_batches', ['status'])
    op.create_index('idx_batch_window', 'allocation_batches', ['window_start', 'window_end'])
    op.create_index('idx_batch_created', 'allocation_batches', ['created_at'])
    
    # ========================================================================
    # 5. ALTER TABLE: orders - Add new NULLABLE columns
    # ========================================================================
    
    # Add pincode column
    op.add_column('orders', 
        sa.Column('pincode', sa.String(length=10), nullable=True, 
                  comment='Delivery pincode for allocation')
    )
    
    # Add total_weight_kg column
    op.add_column('orders', 
        sa.Column('total_weight_kg', sa.Numeric(precision=10, scale=2), nullable=True, 
                  comment='Total order weight in kilograms')
    )
    
    # Add allocated_zone_id column
    op.add_column('orders', 
        sa.Column('allocated_zone_id', sa.Integer(), nullable=True, 
                  comment='Assigned trip card zone ID')
    )
    
    # Add allocation_batch_id column
    op.add_column('orders', 
        sa.Column('allocation_batch_id', sa.Integer(), nullable=True, 
                  comment='Allocation batch that processed this order')
    )
    
    # ========================================================================
    # 6. ADD FOREIGN KEYS to orders table
    # ========================================================================
    
    op.create_foreign_key(
        'fk_order_allocated_zone', 
        'orders', 'trip_cards',
        ['allocated_zone_id'], ['zone_id'],
        ondelete='SET NULL'
    )
    
    op.create_foreign_key(
        'fk_order_allocation_batch', 
        'orders', 'allocation_batches',
        ['allocation_batch_id'], ['batch_id'],
        ondelete='SET NULL'
    )
    
    # ========================================================================
    # 7. ADD INDEXES to orders table
    # ========================================================================
    
    op.create_index('idx_allocation_filter', 'orders', 
                    ['allocated_zone_id', 'pincode', 'created_at'])
    op.create_index('idx_orders_pincode', 'orders', ['pincode'])
    op.create_index('idx_orders_weight', 'orders', ['total_weight_kg'])


def downgrade() -> None:
    """Rollback Phase 1 Vehicle Allocation schema changes."""
    
    # Drop indexes from orders table
    op.drop_index('idx_orders_weight', table_name='orders')
    op.drop_index('idx_orders_pincode', table_name='orders')
    op.drop_index('idx_allocation_filter', table_name='orders')
    
    # Drop foreign keys from orders table
    op.drop_constraint('fk_order_allocation_batch', 'orders', type_='foreignkey')
    op.drop_constraint('fk_order_allocated_zone', 'orders', type_='foreignkey')
    
    # Drop columns from orders table
    op.drop_column('orders', 'allocation_batch_id')
    op.drop_column('orders', 'allocated_zone_id')
    op.drop_column('orders', 'total_weight_kg')
    op.drop_column('orders', 'pincode')
    
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('trip_card_pincode')
    op.drop_table('trip_cards')
    op.drop_table('allocation_batches')
    op.drop_table('vehicles')
