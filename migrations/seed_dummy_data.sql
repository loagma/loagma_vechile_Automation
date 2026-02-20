-- ============================================================================
-- Seed Dummy Data for Vehicle Allocation System
-- ============================================================================
-- This script creates sample data for testing the allocation system
-- Run this AFTER running phase1_vehicle_allocation.sql
-- ============================================================================

-- ============================================================================
-- 1. SEED VEHICLES
-- ============================================================================
INSERT INTO vehicles (vehicle_number, capacity_kg, is_active) VALUES
('KA01AB1234', 100, TRUE),
('KA02CD5678', 150, TRUE),
('KA03EF9012', 200, TRUE),
('MH01GH3456', 100, TRUE),
('MH02IJ7890', 250, TRUE),
('DL01KL1234', 300, TRUE),
('DL02MN5678', 150, TRUE),
('TN01OP9012', 200, TRUE),
('TN02QR3456', 500, TRUE),
('WB01ST7890', 100, TRUE);

-- ============================================================================
-- 2. SEED TRIP CARDS (ZONES)
-- ============================================================================
INSERT INTO trip_cards (zone_name, vehicle_id, status) VALUES
('Bangalore Zone 1', 1, 'ACTIVE'),
('Bangalore Zone 2', 2, 'IDLE'),
('Bangalore Zone 3', 3, 'IDLE'),
('Mumbai Zone 1', 4, 'ACTIVE'),
('Mumbai Zone 2', 5, 'IDLE'),
('Delhi Zone 1', 6, 'ACTIVE'),
('Delhi Zone 2', 7, 'IDLE'),
('Chennai Zone 1', 8, 'ACTIVE'),
('Chennai Zone 2', 9, 'IDLE'),
('Kolkata Zone 1', 10, 'IDLE'),
('Bangalore Zone 4', NULL, 'IDLE'),
('Mumbai Zone 3', NULL, 'IDLE'),
('Delhi Zone 3', NULL, 'IDLE'),
('Chennai Zone 3', NULL, 'IDLE'),
('Bangalore Zone 5', 1, 'OVERWEIGHT'),
('Mumbai Zone 4', 4, 'IDLE'),
('Delhi Zone 4', 6, 'IDLE'),
('Chennai Zone 4', 8, 'IDLE'),
('Bangalore Zone 6', 2, 'IDLE'),
('Mumbai Zone 5', 5, 'IDLE');

-- ============================================================================
-- 3. SEED TRIP CARD PINCODES
-- ============================================================================
-- Bangalore Zones
INSERT INTO trip_card_pincode (zone_id, pincode) VALUES
(1, '560001'), (1, '560002'), (1, '560003'),
(2, '560004'), (2, '560005'), (2, '560006'),
(3, '560007'), (3, '560008'), (3, '560009'),
(11, '560010'), (11, '560011'),
(15, '560012'), (15, '560013'),
(19, '560014'), (19, '560015');

-- Mumbai Zones
INSERT INTO trip_card_pincode (zone_id, pincode) VALUES
(4, '400001'), (4, '400002'), (4, '400003'),
(5, '400004'), (5, '400005'), (5, '400006'),
(12, '400007'), (12, '400008'),
(16, '400009'), (16, '400010'),
(20, '400011'), (20, '400012');

-- Delhi Zones
INSERT INTO trip_card_pincode (zone_id, pincode) VALUES
(6, '110001'), (6, '110002'), (6, '110003'),
(7, '110004'), (7, '110005'), (7, '110006'),
(13, '110007'), (13, '110008'),
(17, '110009'), (17, '110010');

-- Chennai Zones
INSERT INTO trip_card_pincode (zone_id, pincode) VALUES
(8, '600001'), (8, '600002'), (8, '600003'),
(9, '600004'), (9, '600005'), (9, '600006'),
(14, '600007'), (14, '600008'),
(18, '600009'), (18, '600010');

-- Kolkata Zone
INSERT INTO trip_card_pincode (zone_id, pincode) VALUES
(10, '700001'), (10, '700002'), (10, '700003');

-- ============================================================================
-- 4. SEED ALLOCATION BATCHES
-- ============================================================================
INSERT INTO allocation_batches (window_start, window_end, triggered_by, status) VALUES
(DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 5 DAY) + INTERVAL 2 HOUR, 'CRON', 'COMPLETED'),
(DATE_SUB(NOW(), INTERVAL 4 DAY), DATE_SUB(NOW(), INTERVAL 4 DAY) + INTERVAL 2 HOUR, 'CRON', 'COMPLETED'),
(DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY) + INTERVAL 2 HOUR, 'ADMIN', 'COMPLETED'),
(DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY) + INTERVAL 2 HOUR, 'CRON', 'COMPLETED'),
(DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY) + INTERVAL 2 HOUR, 'CRON', 'RUNNING');

-- ============================================================================
-- 5. VERIFICATION QUERIES
-- ============================================================================
-- Run these to verify the data was inserted correctly

-- Count vehicles
SELECT 'Vehicles' as table_name, COUNT(*) as count FROM vehicles;

-- Count trip cards
SELECT 'Trip Cards' as table_name, COUNT(*) as count FROM trip_cards;

-- Count pincode mappings
SELECT 'Pincode Mappings' as table_name, COUNT(*) as count FROM trip_card_pincode;

-- Count allocation batches
SELECT 'Allocation Batches' as table_name, COUNT(*) as count FROM allocation_batches;

-- Show vehicles with capacity
SELECT vehicle_number, capacity_kg, is_active FROM vehicles ORDER BY vehicle_id;

-- Show trip cards with vehicle assignments
SELECT 
    tc.zone_name, 
    v.vehicle_number, 
    tc.status,
    COUNT(tcp.pincode) as pincode_count
FROM trip_cards tc
LEFT JOIN vehicles v ON tc.vehicle_id = v.vehicle_id
LEFT JOIN trip_card_pincode tcp ON tc.zone_id = tcp.zone_id
GROUP BY tc.zone_id, tc.zone_name, v.vehicle_number, tc.status
ORDER BY tc.zone_id;

-- Show pincode distribution
SELECT 
    tc.zone_name,
    GROUP_CONCAT(tcp.pincode ORDER BY tcp.pincode SEPARATOR ', ') as pincodes
FROM trip_cards tc
JOIN trip_card_pincode tcp ON tc.zone_id = tcp.zone_id
GROUP BY tc.zone_id, tc.zone_name
ORDER BY tc.zone_id;

-- ============================================================================
-- END OF SEED SCRIPT
-- ============================================================================
