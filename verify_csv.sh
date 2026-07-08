#!/bin/bash

echo "=== Decarbonization Platform CSV Verification ==="
echo ""

# Check if file exists
if [ ! -f "test_upload_fresh.csv" ]; then
    echo "ERROR: test_upload_fresh.csv not found"
    exit 1
fi

echo "File exists: test_upload_fresh.csv"
echo ""

# Count lines (should be 21 including header)
line_count=$(wc -l < test_upload_fresh.csv)
echo "Line count: $line_count (including header)"

# Check header row
echo ""
echo "Header row:"
head -n 1 test_upload_fresh.csv

# Verify required columns
echo ""
echo "Verifying required columns..."
required_columns=("description" "amount" "unit" "category" "supplier_name" "region" "activity_date" "year")

header_row=$(head -n 1 test_upload_fresh.csv)
all_present=true

for col in "${required_columns[@]}"; do
    if [[ "$header_row" == *"$col"* ]]; then
        echo "✓ Column found: $col"
    else
        echo "✗ Column missing: $col"
        all_present=false
    fi
done

if [ "$all_present" = true ]; then
    echo ""
    echo "✅ All required columns present"

    # Show sample data
    echo ""
    echo "Sample data (first 5 rows):"
    head -n 6 test_upload_fresh.csv

    echo ""
    echo "CSV verification completed successfully!"
    echo "The file is ready for upload to the Decarbonization Platform."
else
    echo ""
    echo "❌ Some required columns are missing"
    exit 1
fi