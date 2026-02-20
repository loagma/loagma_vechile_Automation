-- ============================================================================
-- Phase 1: Vehicle Allocation - Production-Safe Migration
-- ============================================================================
-- IMPORTANT: This migration is ADDITIVE ONLY
-- - No existing columns modified
-- - No existing tables altered (except adding nullable columns)
-- - All new columns are NULLABLE
-- - Safe for rollback (foreign keys use SET NULL/CASCADE appropriately)
-- ============================================================================

-- ============================================================================
-- 1. CREATE NEW TABLE: vehicles
-- ============================================================================
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_number VARCHAR(50) NOT NULL UNIQUE,
    capacity_kg DECIMAL(10,2) NOT NULL CHECK (capacity_kg > 0),
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_vehicle_active (is_active),
    INDEX idx_vehicle_number (vehicle_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Vehicle master table for allocation system';

-- ============================================================================
-- 2. CREATE NEW TABLE: trip_cards
-- ============================================================================
CREATE TABLE IF NOT EXISTS trip_cards (
    zone_id INT AUTO_INCREMENT PRIMARY KEY,
    zone_name VARCHAR(100) NOT NULL UNIQUE,
    vehicle_id INT NULL,
    status ENUM('IDLE','ACTIVE','OVERWEIGHT') DEFAULT 'IDLE',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_zone_status (status),
    INDEX idx_zone_vehicle (vehicle_id),
    CONSTRAINT fk_trip_card_vehicle 
        FOREIGN KEY (vehicle_id) 
        REFERENCES vehicles(vehicle_id) 
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Trip cards (zones) for vehicle allocation';

-- ============================================================================
-- 3. CREATE NEW TABLE: trip_card_pincode
-- ============================================================================
CREATE TABLE IF NOT EXISTS trip_card_pincode (
    id INT AUTO_INCREMENT PRIMARY KEY,
    zone_id INT NOT NULL,
    pincode VARCHAR(10) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_zone_pincode (zone_id, pincode),
    INDEX idx_pincode (pincode),
    CONSTRAINT fk_trip_card_pincode_zone 
        FOREIGN KEY (zone_id) 
        REFERENCES trip_cards(zone_id) 
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Pincode assignments to trip card zones';

-- ============================================================================
-- 4. CREATE NEW TABLE: allocation_batches
-- ============================================================================
CREATE TABLE IF NOT EXISTS allocation_batches (
    batch_id INT AUTO_INCREMENT PRIMARY KEY,
    window_start DATETIME NOT NULL,
    window_end DATETIME NOT NULL,
    triggered_by ENUM('CRON','ADMIN') NOT NULL,
    status ENUM('RUNNING','COMPLETED','FAILED') DEFAULT 'RUNNING',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_batch_status (status),
    INDEX idx_batch_window (window_start, window_end),
    INDEX idx_batch_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Allocation batch execution tracking';

-- ============================================================================
-- 5. ALTER EXISTING TABLE: orders
-- ============================================================================
-- Add new NULLABLE columns to existing orders table
-- These columns support the allocation system without breaking existing data

-- Add pincode column (nullable)
ALTER TABLE orders 
ADD COLUMN IF NOT EXISTS pincode VARCHAR(10) NULL
COMMENT 'Delivery pincode for allocation';

-- Add total_weight_kg column (nullable)
ALTER TABLE orders 
ADD COLUMN IF NOT EXISTS total_weight_kg DECIMAL(10,2) NULL
COMMENT 'Total order weight in kilograms';

-- Add allocated_zone_id column (nullable)
ALTER TABLE orders 
ADD COLUMN IF NOT EXISTS allocated_zone_id INT NULL
COMMENT 'Assigned trip card zone ID';

-- Add allocation_batch_id column (nullable)
ALTER TABLE orders 
ADD COLUMN IF NOT EXISTS allocation_batch_id INT NULL
COMMENT 'Allocation batch that processed this order';

-- ============================================================================
-- 6. ADD FOREIGN KEYS TO orders TABLE
-- ============================================================================

-- Foreign key: allocated_zone_id → trip_cards(zone_id)
ALTER TABLE orders 
ADD CONSTRAINT fk_order_allocated_zone 
    FOREIGN KEY (allocated_zone_id) 
    REFERENCES trip_cards(zone_id) 
    ON DELETE SET NULL;

-- Foreign key: allocation_batch_id → allocation_batches(batch_id)
ALTER TABLE orders 
ADD CONSTRAINT fk_order_allocation_batch 
    FOREIGN KEY (allocation_batch_id) 
    REFERENCES allocation_batches(batch_id) 
    ON DELETE SET NULL;

-- ============================================================================
-- 7. ADD PERFORMANCE INDEX TO orders TABLE
-- ============================================================================

-- Composite index for allocation queries
CREATE INDEX IF NOT EXISTS idx_allocation_filter 
ON orders (allocated_zone_id, pincode, created_at)
COMMENT 'Performance index for allocation filtering';

-- Additional helpful indexes for allocation queries
CREATE INDEX IF NOT EXISTS idx_orders_pincode 
ON orders (pincode)
COMMENT 'Index for pincode-based queries';

CREATE INDEX IF NOT EXISTS idx_orders_weight 
ON orders (total_weight_kg)
COMMENT 'Index for weight-based queries';

-- ============================================================================
-- VERIFICATION QUERIES (Run these after migration to verify)
-- ============================================================================

-- Verify new tables exist
-- SELECT TABLE_NAME, TABLE_COMMENT 
-- FROM INFORMATION_SCHEMA.TABLES 
-- WHERE TABLE_SCHEMA = DATABASE() 
-- AND TABLE_NAME IN ('vehicles', 'trip_cards', 'trip_card_pincode', 'allocation_batches');

-- Verify new columns in orders table
-- SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_COMMENT 
-- FROM INFORMATION_SCHEMA.COLUMNS 
-- WHERE TABLE_SCHEMA = DATABASE() 
-- AND TABLE_NAME = 'orders' 
-- AND COLUMN_NAME IN ('pincode', 'total_weight_kg', 'allocated_zone_id', 'allocation_batch_id');

-- Verify foreign keys
-- SELECT CONSTRAINT_NAME, TABLE_NAME, REFERENCED_TABLE_NAME 
-- FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
-- WHERE TABLE_SCHEMA = DATABASE() 
-- AND REFERENCED_TABLE_NAME IN ('vehicles', 'trip_cards', 'allocation_batches');

-- Verify indexes
-- SELECT TABLE_NAME, INDEX_NAME, COLUMN_NAME 
-- FROM INFORMATION_SCHEMA.STATISTICS 
-- WHERE TABLE_SCHEMA = DATABASE() 
-- AND TABLE_NAME = 'orders' 
-- AND INDEX_NAME LIKE 'idx_%allocation%';

-- ============================================================================
-- ROLLBACK SCRIPT (Use only if needed)
-- ============================================================================

-- DROP INDEX IF EXISTS idx_orders_weight ON orders;
-- DROP INDEX IF EXISTS idx_orders_pincode ON orders;
-- DROP INDEX IF EXISTS idx_allocation_filter ON orders;
-- ALTER TABLE orders DROP FOREIGN KEY IF EXISTS fk_order_allocation_batch;
-- ALTER TABLE orders DROP FOREIGN KEY IF EXISTS fk_order_allocated_zone;
-- ALTER TABLE orders DROP COLUMN IF EXISTS allocation_batch_id;
-- ALTER TABLE orders DROP COLUMN IF EXISTS allocated_zone_id;
-- ALTER TABLE orders DROP COLUMN IF EXISTS total_weight_kg;
-- ALTER TABLE orders DROP COLUMN IF EXISTS pincode;
-- DROP TABLE IF EXISTS trip_card_pincode;
-- DROP TABLE IF EXISTS trip_cards;
-- DROP TABLE IF EXISTS allocation_batches;
-- DROP TABLE IF EXISTS vehicles;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
