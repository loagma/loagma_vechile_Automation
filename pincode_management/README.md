# Pincode Management Scripts

This folder contains scripts for managing and analyzing pincode data in orders.

## Files

- `extract_pincodes.py` - Analyzes orders to identify which have pincodes and which are missing them
- `find_missing_pincodes.py` - Finds orders with missing pincode data
- `fill_missing_with_geocoding.py` - Uses geocoding API to fill missing pincodes from coordinates
- `batch_update_pincodes.py` - Batch updates pincodes in the database from CSV files
- `order_pin.txt` - Pincode reference data

## How to Run

From the `loagma_VA` directory:

```bash
# Extract and analyze pincodes
python pincode_management/extract_pincodes.py

# Find orders with missing pincodes
python pincode_management/find_missing_pincodes.py

# Fill missing pincodes using geocoding
python pincode_management/fill_missing_with_geocoding.py

# Batch update pincodes from CSV
python pincode_management/batch_update_pincodes.py
```

## Workflow

1. Run `extract_pincodes.py` to generate a report of pincode coverage
2. Use `find_missing_pincodes.py` to identify orders needing pincodes
3. Run `fill_missing_with_geocoding.py` to automatically fill pincodes using coordinates
4. Use `batch_update_pincodes.py` to update pincodes in bulk from CSV files

## Output

- `pincode_extraction_report.csv` - Detailed report of pincode analysis
- Console output showing statistics and top pincodes
