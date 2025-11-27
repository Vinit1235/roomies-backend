"""
Migration: Add missing columns to bookings table
This adds all the columns needed for the revenue system booking flow
"""

import sqlite3
from datetime import datetime

def migrate():
    conn = sqlite3.connect('instance/roomies.db')
    cursor = conn.cursor()
    
    # List of columns to add
    columns_to_add = [
        ("monthly_rent", "FLOAT DEFAULT 0.0"),
        ("security_deposit", "FLOAT DEFAULT 0.0"),
        ("platform_fee", "FLOAT DEFAULT 0.0"),
        ("total_paid", "FLOAT DEFAULT 0.0"),
        ("razorpay_order_id", "VARCHAR(100)"),
        ("razorpay_payment_id", "VARCHAR(100)"),
        ("razorpay_signature", "VARCHAR(255)"),
        ("contract_start_date", "DATE"),
        ("contract_end_date", "DATE"),
        ("contract_duration_months", "INTEGER DEFAULT 11"),
        ("contract_signed", "BOOLEAN DEFAULT 0"),
        ("contract_signed_at", "DATETIME"),
        ("contract_pdf_path", "VARCHAR(512)"),
        ("owner_notified", "BOOLEAN DEFAULT 0"),
        ("student_notified", "BOOLEAN DEFAULT 0"),
        ("owner_notification_sent_at", "DATETIME"),
        ("student_notification_sent_at", "DATETIME"),
        ("owner_approved", "BOOLEAN DEFAULT 0"),
        ("owner_approved_at", "DATETIME"),
        ("owner_rejection_reason", "TEXT"),
        ("move_in_date", "DATE"),
        ("move_in_completed", "BOOLEAN DEFAULT 0"),
        ("move_in_confirmed_at", "DATETIME"),
        ("updated_at", "DATETIME"),
        ("confirmed_at", "DATETIME"),
        ("cancelled_at", "DATETIME"),
        ("cancellation_reason", "TEXT"),
        ("cancelled_by", "VARCHAR(20)"),
        ("refund_amount", "FLOAT DEFAULT 0.0"),
        ("refund_processed", "BOOLEAN DEFAULT 0"),
        ("refund_processed_at", "DATETIME"),
    ]
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(bookings)")
    existing_columns = {col[1] for col in cursor.fetchall()}
    
    print("Current bookings table columns:", existing_columns)
    print(f"\nAdding {len(columns_to_add)} new columns...\n")
    
    # Add each missing column
    added_count = 0
    for col_name, col_type in columns_to_add:
        if col_name not in existing_columns:
            try:
                sql = f"ALTER TABLE bookings ADD COLUMN {col_name} {col_type}"
                print(f"  ✓ Adding: {col_name} ({col_type})")
                cursor.execute(sql)
                added_count += 1
            except sqlite3.OperationalError as e:
                print(f"  ✗ Failed to add {col_name}: {e}")
        else:
            print(f"  - Skipping: {col_name} (already exists)")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Migration complete! Added {added_count} columns to bookings table.")
    print("\nServer restart required to apply changes.")

if __name__ == "__main__":
    print("="*70)
    print("MIGRATION: Fix Bookings Table Schema")
    print("="*70)
    print()
    migrate()
