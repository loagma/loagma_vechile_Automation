import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from sqlalchemy import text
from dotenv import load_dotenv
import csv
from datetime import datetime

load_dotenv()

db = SessionLocal()

try:
    print("=== Batch Update Pincodes from CSV ===\n")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    csv_filename = input("Enter CSV filename (default: pincode_extraction_report.csv): ").strip()
    if not csv_filename:
        csv_filename = 'pincode_extraction_report.csv'
    
    print(f"\nReading from: {csv_filename}")
    
    with open(csv_filename, 'r', encoding='utf-8') as f:
        csv_reader = csv.DictReader(f)
        mappings = list(csv_reader)
    
    print(f"Loaded {len(mappings):,} records\n")
    
    updates_to_apply = []
    for mapping in mappings:
        order_id = mapping['order_id']
        pincode_db = mapping.get('pincode_in_db', 'NULL')
        pincode_from_address = mapping.get('pincode_from_address', 'NULL')
        
        if (pincode_db == 'NULL' or not pincode_db) and pincode_from_address != 'NULL':
            updates_to_apply.append({
                'order_id': order_id,
                'pincode': pincode_from_address
            })
    
    print(f"Found {len(updates_to_apply):,} orders to update\n")
    
    if len(updates_to_apply) == 0:
        print("✓ No updates needed!")
    else:
        print("Preview of updates:")
        for i, update in enumerate(updates_to_apply[:5], 1):
            print(f"  {i}. Order {update['order_id']} -> Pincode {update['pincode']}")
        if len(updates_to_apply) > 5:
            print(f"  ... and {len(updates_to_apply) - 5} more")
        
        print("\nProceed with update? (yes/no): ", end='')
        confirm = input().strip().lower()
        
        if confirm != 'yes':
            print("\n✗ Update cancelled")
        else:
            print("\nUpdating in batches...")
            batch_size = 1000
            updated = 0
            
            for i in range(0, len(updates_to_apply), batch_size):
                batch = updates_to_apply[i:i+batch_size]
                
                db.execute(text("START TRANSACTION"))
                
                for update in batch:
                    db.execute(text("""
                        UPDATE `orders` 
                        SET pincode = :pincode 
                        WHERE order_id = :order_id
                    """), update)
                    updated += 1
                
                db.execute(text("COMMIT"))
                
                if (i + batch_size) % 5000 == 0 or i + batch_size >= len(updates_to_apply):
                    progress = min(i + batch_size, len(updates_to_apply))
                    print(f"  Progress: {progress:,} / {len(updates_to_apply):,} ({progress/len(updates_to_apply)*100:.1f}%)")
            
            print(f"\n✓ Update complete! Updated {updated:,} orders")
            
            print("\nVerifying...")
            verify_result = db.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(pincode) as with_pincode,
                    COUNT(DISTINCT pincode) as unique_pincodes
                FROM `orders`
            """))
            stats = verify_result.fetchone()
            
            print(f"  Total orders: {stats[0]:,}")
            print(f"  Orders with pincode: {stats[1]:,}")
            print(f"  Unique pincodes: {stats[2]:,}")
            print(f"  Coverage: {stats[1]/stats[0]*100:.2f}%")
            
            print(f"\n{'='*80}")
            print("UPDATE COMPLETE")
            print(f"{'='*80}")
            print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

except FileNotFoundError:
    print(f"\n✗ Error: File '{csv_filename}' not found")
    print("Please run extract_pincodes.py first to generate the CSV file")
except Exception as e:
    print(f"\n✗ Error: {e}")
    try:
        db.execute(text("ROLLBACK"))
        print("Rolled back current batch")
    except:
        pass
    import traceback
    traceback.print_exc()
finally:
    db.close()
