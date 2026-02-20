# Testing Allocation Engine with Real Production Data

## Overview

This guide explains how to test the allocation algorithm with your actual production database data.

## Quick Start

```bash
# Test with sample data (database not required)
python test_real_data.py

# Test with real database (requires database connection)
# 1. Update .env with production database credentials
# 2. Run the test
python test_real_data.py
```

## Configuration

### Step 1: Update Database Connection

Edit `.env` file with your production database credentials:

```env
# Database Configuration
DB_HOST=your-production-host.com
DB_PORT=3306
DB_USER=readonly_user
DB_PASSWORD=your_password
DB_NAME=your_database
```

**IMPORTANT**: Use a READ-ONLY user for safety!

### Step 2: Customize the SQL Query

Edit `test_real_data.py` and update the `fetch_orders_from_database()` function:

```python
async def fetch_orders_from_database(limit: int = 100) -> list:
    # ... existing code ...
    
    # UPDATE THIS QUERY to match your actual table structure
    query = text("""
        SELECT 
            id as order_id,                    -- Your order ID column
            customer_latitude as latitude,      -- Your latitude column (or NULL)
            customer_longitude as longitude,    -- Your longitude column (or NULL)
            delivery_pincode as pincode,        -- Your pincode column (or NULL)
            order_weight as total_weight_kg     -- Your weight column (or NULL)
        FROM orders
        WHERE status = 'pending'                -- Filter for unallocated orders
        AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        ORDER BY created_at DESC
        LIMIT :limit
    """)
```

### Step 3: Map Your Columns

The allocation engine requires these fields:

| Required Field | Type | Description | If Missing |
|---------------|------|-------------|------------|
| order_id | int | Unique order identifier | Required |
| latitude | float | Delivery latitude | Generate dummy |
| longitude | float | Delivery longitude | Generate dummy |
| pincode | string | Delivery pincode | Generate dummy |
| total_weight_kg | float | Order weight in kg | Generate dummy |

## Example Queries for Different Schemas

### Example 1: Orders with Customer Address

```sql
SELECT 
    o.id as order_id,
    a.latitude,
    a.longitude,
    a.pincode,
    COALESCE(o.weight, 10.0) as total_weight_kg  -- Default 10kg if NULL
FROM orders o
LEFT JOIN addresses a ON o.delivery_address_id = a.id
WHERE o.status IN ('pending', 'confirmed')
AND o.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
LIMIT 100
```

### Example 2: Orders with Embedded Location

```sql
SELECT 
    order_id,
    delivery_lat as latitude,
    delivery_lon as longitude,
    delivery_zip as pincode,
    total_weight as total_weight_kg
FROM orders
WHERE allocated_zone_id IS NULL  -- Not yet allocated
AND created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
LIMIT 100
```

### Example 3: Orders Without Location Data

```sql
SELECT 
    order_id,
    NULL as latitude,      -- Will generate dummy
    NULL as longitude,     -- Will generate dummy
    NULL as pincode,       -- Will generate dummy
    item_weight as total_weight_kg
FROM orders
WHERE status = 'pending'
LIMIT 100
```

## Dummy Data Generation

When fields are missing, the script automatically generates realistic dummy data:

### Pincodes
- Randomly selected from major Indian cities
- Bangalore: 560001-560005
- Mumbai: 400001-400005
- Delhi: 110001-110005
- Chennai: 600001-600005
- Kolkata: 700001-700005

### Coordinates
- Generated near major city centers
- Small random offset (±5km) for variation
- Realistic Indian coordinates

### Weights
- Random between 1-50 kg
- Realistic distribution for e-commerce orders

## Running the Test

### Basic Test

```bash
python test_real_data.py
```

### With Custom Limit

Edit `test_real_data.py`:

```python
# Change this line
db_orders = await fetch_orders_from_database(limit=500)  # Fetch 500 orders
```

### With Different Vehicle Capacity

Edit `test_real_data.py`:

```python
# Change this line
vehicle_capacity = 200.0  # Use 200kg capacity instead of 100kg
```

## Output Interpretation

### Sample Output

```
======================================================================
ALLOCATION RESULTS
======================================================================

Vehicle Capacity: 100.0 kg
Total Orders Processed: 180

METRICS:
  Number of Trips: 18
  Average Utilization: 78.2%
  Total Distance: 1411.94 km
  Runtime: 0.0213 seconds

TRIP SUMMARY (First 10 trips):
  Trip   1:   3 orders,  89.94 kg ( 89.9% full),    4.20 km
  Trip   2:   3 orders,  61.89 kg ( 61.9% full),    3.04 km
  ...
```

### Metrics Explained

- **Number of Trips**: Total delivery trips generated
- **Average Utilization**: How full vehicles are on average (higher is better)
- **Total Distance**: Sum of all trip distances
- **Runtime**: Algorithm execution time

### Good Results

- ✅ Utilization > 80%
- ✅ Runtime < 5 seconds for 1000 orders
- ✅ Reasonable number of trips
- ✅ No unallocatable orders (unless weight > capacity)

### Poor Results

- ⚠️ Utilization < 60% - Consider increasing capacity or reviewing weights
- ⚠️ Too many trips - May need larger vehicles
- ⚠️ Very high distance - Orders may be too spread out

## Testing Different Scenarios

### Scenario 1: Peak Hour Orders

```python
query = text("""
    SELECT ...
    FROM orders
    WHERE created_at BETWEEN '2024-01-15 18:00:00' AND '2024-01-15 20:00:00'
    LIMIT 200
""")
```

### Scenario 2: Specific Region

```python
query = text("""
    SELECT ...
    FROM orders
    WHERE delivery_city = 'Bangalore'
    AND status = 'pending'
    LIMIT 100
""")
```

### Scenario 3: Heavy Orders Only

```python
query = text("""
    SELECT ...
    FROM orders
    WHERE order_weight > 20
    AND status = 'pending'
    LIMIT 50
""")
```

## Troubleshooting

### Issue: "Database not initialized"

**Solution**: Database is not running or connection failed
```bash
# Check if database is accessible
mysql -h your-host -u your-user -p

# Or start local database
docker-compose up -d
```

### Issue: "Table 'orders' doesn't exist"

**Solution**: Update table name in query
```python
query = text("SELECT ... FROM your_actual_table_name ...")
```

### Issue: "Column not found"

**Solution**: Update column names to match your schema
```python
# Check your actual column names
SHOW COLUMNS FROM orders;

# Update query accordingly
SELECT your_id_column as order_id, ...
```

### Issue: All orders unallocatable

**Solution**: Check weight values
```python
# Add debug output
print(f"Order weights: {[o['total_weight_kg'] for o in orders[:10]]}")
print(f"Vehicle capacity: {vehicle_capacity}")
```

## Safety Notes

### READ-ONLY Operation

This script is **READ-ONLY**. It:
- ✅ Fetches data from database
- ✅ Generates dummy data for missing fields
- ✅ Runs allocation algorithm
- ✅ Displays results
- ❌ Does NOT write to database
- ❌ Does NOT modify any data
- ❌ Does NOT create any records

### Production Safety

1. **Use READ-ONLY credentials**
   ```sql
   CREATE USER 'readonly'@'%' IDENTIFIED BY 'password';
   GRANT SELECT ON your_database.* TO 'readonly'@'%';
   ```

2. **Test on staging first**
   - Run on staging database before production
   - Verify query performance
   - Check result quality

3. **Limit query size**
   - Start with LIMIT 10
   - Gradually increase to 100, 500, 1000
   - Monitor query performance

4. **Off-peak testing**
   - Run during low-traffic hours
   - Avoid peak business hours
   - Monitor database load

## Next Steps

After successful testing:

1. **Review Results**
   - Analyze utilization rates
   - Check trip distances
   - Verify order groupings

2. **Tune Parameters**
   - Adjust vehicle capacity
   - Modify neighbor radius
   - Change seed selection strategy

3. **Integrate with API**
   - Create FastAPI endpoint
   - Add authentication
   - Implement batch processing

4. **Production Deployment**
   - Write allocation results to database
   - Update order status
   - Generate trip cards
   - Assign to vehicles

## Example Integration

```python
# After testing, integrate with your workflow:

async def allocate_pending_orders():
    """Allocate all pending orders."""
    # Fetch orders
    orders = await fetch_orders_from_database(limit=1000)
    
    # Run allocation
    engine = AllocationEngine(vehicle_capacity_kg=100.0)
    result = engine.run(orders)
    
    # Write results to database
    for trip in result['trips']:
        # Create trip card
        trip_card = await create_trip_card(trip)
        
        # Update orders
        for order_id in trip['orders']:
            await update_order_allocation(
                order_id=order_id,
                zone_id=trip_card.zone_id,
                batch_id=batch_id
            )
    
    return result
```

## Support

For issues or questions:
1. Check this guide
2. Review `test_real_data.py` comments
3. Check `app/allocation/README.md`
4. Review allocation algorithm documentation

---

**Last Updated**: 2026-02-19  
**Status**: Production Ready  
**Safety**: READ-ONLY Operation
