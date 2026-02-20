"""Simple table creation script for TiDB"""
import pymysql

conn = pymysql.connect(
    host='gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
    port=4000,
    user='3JkMn3GrMm4dpze.root',
    password='VNcMbAz5zqDYXKcd',
    database='loagma',
    ssl={'ssl': True}
)

cursor = conn.cursor()

print("Creating tables...")

# trip_cards
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trip_cards (
            zone_id INT AUTO_INCREMENT PRIMARY KEY,
            zone_name VARCHAR(100) NOT NULL UNIQUE,
            vehicle_id INT NULL,
            status VARCHAR(20) DEFAULT 'IDLE',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE SET NULL
        )
    """)
    print("OK trip_cards")
except Exception as e:
    print(f"trip_cards: {e}")

# trip_card_pincode
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trip_card_pincode (
            id INT AUTO_INCREMENT PRIMARY KEY,
            zone_id INT NOT NULL,
            pincode VARCHAR(10) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uk_zone_pincode (zone_id, pincode),
            FOREIGN KEY (zone_id) REFERENCES trip_cards(zone_id) ON DELETE CASCADE
        )
    """)
    print("OK trip_card_pincode")
except Exception as e:
    print(f"trip_card_pincode: {e}")

# allocation_batches
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS allocation_batches (
            batch_id INT AUTO_INCREMENT PRIMARY KEY,
            window_start DATETIME NOT NULL,
            window_end DATETIME NOT NULL,
            triggered_by VARCHAR(10) NOT NULL,
            status VARCHAR(20) DEFAULT 'RUNNING',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("OK allocation_batches")
except Exception as e:
    print(f"allocation_batches: {e}")

conn.commit()
print("\nNow seeding data...")

# Seed vehicles
cursor.execute("INSERT INTO vehicles (vehicle_number, capacity_kg, is_active) VALUES ('KA01AB1234', 100, TRUE), ('KA02CD5678', 150, TRUE), ('KA03EF9012', 200, TRUE), ('MH01GH3456', 100, TRUE), ('MH02IJ7890', 250, TRUE)")

# Seed trip_cards
cursor.execute("INSERT INTO trip_cards (zone_name, vehicle_id, status) VALUES ('Bangalore Zone 1', 1, 'ACTIVE'), ('Bangalore Zone 2', 2, 'IDLE'), ('Mumbai Zone 1', 4, 'ACTIVE')")

# Seed pincodes
cursor.execute("INSERT INTO trip_card_pincode (zone_id, pincode) VALUES (1, '560001'), (1, '560002'), (2, '560003'), (3, '400001')")

# Seed batches
cursor.execute("INSERT INTO allocation_batches (window_start, window_end, triggered_by, status) VALUES (NOW() - INTERVAL 1 DAY, NOW() - INTERVAL 1 DAY + INTERVAL 2 HOUR, 'CRON', 'COMPLETED')")

conn.commit()

# Verify
cursor.execute("SELECT COUNT(*) FROM vehicles")
print(f"\nVehicles: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM trip_cards")
print(f"Trip Cards: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM trip_card_pincode")
print(f"Pincodes: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM allocation_batches")
print(f"Batches: {cursor.fetchone()[0]}")

conn.close()
print("\nDone!")
