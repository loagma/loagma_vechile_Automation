# Database Seeding Guide

## Overview

This guide explains how to seed dummy data into your database for testing the vehicle allocation system.

## Prerequisites

1. ✅ Database is accessible
2. ✅ Migration has been run (`phase1_vehicle_allocation.sql`)
3. ✅ Tables created: `vehicles`, `trip_cards`, `trip_card_pincode`, `allocation_batches`

## Option 1: Run SQL Script (Recommended)

### Step 1: Connect to Database

```bash
# Using MySQL CLI
mysql -h gateway01.ap-northeast-1.prod.aws.tidbcloud.com \
      -P 4000 \
      -u 3JkMn3GrMm4dpze.root \
      -p \
      --ssl-mode=REQUIRED \
      loagma

# Or using any MySQL client (MySQL Workbench, DBeaver, etc.)
```

### Step 2: Run Seed Script

```sql
-- In MySQL CLI or your SQL client
source migrations/seed_dummy_data.sql;

-- Or copy-paste the contents of the file
```

### Step 3: Verify Data

The script includes verification queries at the end. You should see:
- 10 vehicles
- 20 trip cards (zones)
- ~60 pincode mappings
- 5 allocation batches

## Option 2: Run Python Script (When Database Connection Works)

```bash
python seed_dummy_data.py
```

This will automatically:
1. Connect to database
2. Insert dummy data
3. Verify insertion
4. Show summary

## What Gets Created

### 1. Vehicles (10 records)

| Vehicle Number | Capacity | Status |
|---------------|----------|--------|
| KA01AB1234 | 100 kg | Active |
| KA02CD5678 | 150 kg | Active |
| KA03EF9012 | 200 kg | Active |
| ... | ... | ... |

### 2. Trip Cards / Zones (20 records)

| Zone Name | Vehicle | Status | Pincodes |
|-----------|---------|--------|----------|
| Bangalore Zone 1 | KA01AB1234 | ACTIVE | 560001, 560002, 560003 |
| Mumbai Zone 1 | MH01GH3456 | ACTIVE | 400001, 400002, 400003 |
| Delhi Zone 1 | DL01KL1234 | ACTIVE | 110001, 110002, 110003 |
| ... | ... | ... | ... |

### 3. Pincode Mappings (~60 records)

Maps pincodes to zones for allocation logic:
- Bangalore: 560001-560015
- Mumbai: 400001-400012
- Delhi: 110001-110010
- Chennai: 600001-600010
- Kolkata: 700001-700003

### 4. Allocation Batches (5 records)

Historical batch runs for testing:
- 5 days ago: COMPLETED
- 4 days ago: COMPLETED
- 3 days ago: COMPLETED (ADMIN triggered)
- 2 days ago: COMPLETED
- 1 day ago: RUNNING

## Verification Queries

After seeding, run these queries to verify:

```sql
-- Count all records
SELECT 'Vehicles' as table_name, COUNT(*) as count FROM vehicles
UNION ALL
SELECT 'Trip Cards', COUNT(*) FROM trip_cards
UNION ALL
SELECT 'Pincodes', COUNT(*) FROM trip_card_pincode
UNION ALL
SELECT 'Batches', COUNT(*) FROM allocation_batches;

-- Show vehicle assignments
SELECT 
    tc.zone_name, 
    v.vehicle_number, 
    tc.status,
    COUNT(tcp.pincode) as pincode_count
FROM trip_cards tc
LEFT JOIN vehicles v ON tc.vehicle_id = v.vehicle_id
LEFT JOIN trip_card_pincode tcp ON tc.zone_id = tcp.zone_id
GROUP BY tc.zone_id
ORDER BY tc.zone_id;

-- Show pincode distribution
SELECT 
    tc.zone_name,
    GROUP_CONCAT(tcp.pincode ORDER BY tcp.pincode) as pincodes
FROM trip_cards tc
JOIN trip_card_pincode tcp ON tc.zone_id = tcp.zone_id
GROUP BY tc.zone_id
ORDER BY tc.zone_id;
```

## Testing After Seeding

### 1. Test Allocation Algorithm

```bash
# Run with real data
python test_real_data.py
```

This will:
- Fetch orders from database
- Generate dummy pincode/weight if missing
- Run allocation algorithm
- Show results

### 2. Test API Endpoints

```bash
# Start the server
python -m uvicorn app.main:app --reload

# Test health endpoint
curl http://localhost:8000/health

# View API docs
# Open http://localhost:8000/docs
```

### 3. Query Allocated Data

```sql
-- Show zones with vehicles
SELECT 
    tc.zone_name,
    v.vehicle_number,
    v.capacity_kg,
    tc.status,
    COUNT(tcp.pincode) as pincode_count
FROM trip_cards tc
LEFT JOIN vehicles v ON tc.vehicle_id = v.vehicle_id
LEFT JOIN trip_card_pincode tcp ON tc.zone_id = tcp.zone_id
WHERE tc.vehicle_id IS NOT NULL
GROUP BY tc.zone_id;

-- Show allocation batches
SELECT 
    batch_id,
    window_start,
    window_end,
    triggered_by,
    status,
    TIMESTAMPDIFF(MINUTE, window_start, window_end) as duration_minutes
FROM allocation_batches
ORDER BY batch_id DESC;
```

## Cleanup (If Needed)

To remove all seeded data:

```sql
-- WARNING: This will delete all data!
DELETE FROM trip_card_pincode;
DELETE FROM trip_cards;
DELETE FROM vehicles;
DELETE FROM allocation_batches;

-- Reset auto-increment
ALTER TABLE vehicles AUTO_INCREMENT = 1;
ALTER TABLE trip_cards AUTO_INCREMENT = 1;
ALTER TABLE trip_card_pincode AUTO_INCREMENT = 1;
ALTER TABLE allocation_batches AUTO_INCREMENT = 1;
```

## Troubleshooting

### Issue: "Table doesn't exist"

**Solution**: Run the migration first
```bash
mysql -h your-host -u your-user -p your-database < migrations/phase1_vehicle_allocation.sql
```

### Issue: "Duplicate entry"

**Solution**: Data already exists. Either:
1. Clean up existing data (see Cleanup section)
2. Modify the seed script to use different values

### Issue: "Access denied"

**Solution**: Check database credentials in `.env`
```env
DB_HOST=gateway01.ap-northeast-1.prod.aws.tidbcloud.com
DB_PORT=4000
DB_USER=3JkMn3GrMm4dpze.root
DB_PASSWORD=VNcMbAz5zqDYXKcd
DB_NAME=loagma
```

### Issue: "SSL connection required"

**Solution**: Add `--ssl-mode=REQUIRED` to MySQL CLI command
```bash
mysql -h your-host -u your-user -p --ssl-mode=REQUIRED your-database
```

## Next Steps

After seeding:

1. ✅ Verify data with queries above
2. ✅ Test allocation algorithm: `python test_real_data.py`
3. ✅ Start API server: `uvicorn app.main:app --reload`
4. ✅ Test API endpoints
5. ✅ Integrate with your application

## Sample Data Summary

```
Vehicles: 10
├── Capacities: 100kg, 150kg, 200kg, 250kg, 300kg, 500kg
└── All active

Trip Cards: 20
├── Bangalore: 6 zones
├── Mumbai: 5 zones
├── Delhi: 4 zones
├── Chennai: 4 zones
└── Kolkata: 1 zone

Pincodes: ~60 mappings
├── 2-4 pincodes per zone
└── Covers major Indian cities

Allocation Batches: 5
├── 4 completed
└── 1 running
```

---

**Last Updated**: 2026-02-19  
**Status**: Ready to Use  
**Database**: TiDB Cloud (MySQL Compatible)
