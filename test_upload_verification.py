#!/usr/bin/env python3
"""
Verification script for Decarbonization Platform CSV upload functionality.
This script tests that our sample data file can be processed correctly.
"""

import pandas as pd
import os
from datetime import datetime

def verify_csv_structure(filename):
    """Verify that the CSV file has the correct structure."""
    print(f"Verifying CSV structure for {filename}")

    # Check if file exists
    if not os.path.exists(filename):
        print(f"ERROR: File {filename} not found")
        return False

    try:
        # Read the CSV file
        df = pd.read_csv(filename)
        print(f"Successfully read CSV with {len(df)} rows")

        # Check required columns
        required_columns = [
            'description', 'amount', 'unit', 'category',
            'supplier_name', 'region', 'activity_date', 'year'
        ]

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"ERROR: Missing columns: {missing_columns}")
            return False

        print("✓ All required columns present")

        # Check data types
        print(f"Data shape: {df.shape}")
        print("\nColumn data types:")
        print(df.dtypes)

        # Check for basic data quality
        print(f"\nChecking data quality:")
        print(f"- Missing values per column:")
        print(df.isnull().sum())

        # Validate date format
        try:
            df['activity_date'] = pd.to_datetime(df['activity_date'])
            print("✓ Date format validation passed")
        except Exception as e:
            print(f"ERROR: Date format validation failed: {e}")
            return False

        # Validate amount column is numeric
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        if df['amount'].isnull().sum() > 0:
            print("ERROR: Some amount values are not numeric")
            return False
        else:
            print("✓ Amount column validation passed")

        print("\n✓ CSV structure verification completed successfully")
        return True

    except Exception as e:
        print(f"ERROR: Failed to process CSV file: {e}")
        return False

def main():
    """Main verification function."""
    print("=== Decarbonization Platform Upload Verification ===\n")

    test_file = "test_upload_fresh.csv"

    # Verify the CSV structure
    success = verify_csv_structure(test_file)

    if success:
        print("\n✅ VERIFICATION PASSED: CSV file is properly formatted for upload")
        print("The file can be successfully processed by the Decarbonization Platform")
    else:
        print("\n❌ VERIFICATION FAILED: Issues found with CSV structure")
        return 1

    # Show sample data
    try:
        df = pd.read_csv(test_file)
        print(f"\nSample data (first 5 rows):")
        print(df.head())

        print(f"\nData summary:")
        print(f"- Total records: {len(df)}")
        print(f"- Categories: {df['category'].unique()}")
        print(f"- Regions: {df['region'].unique()}")
        print(f"- Years: {df['year'].unique()}")

    except Exception as e:
        print(f"Warning: Could not display sample data: {e}")

    return 0

if __name__ == "__main__":
    exit(main())