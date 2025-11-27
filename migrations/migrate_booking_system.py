"""
Database migration script to add new booking system fields.
Run this to update existing database to support the new booking system.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from sqlalchemy import text

def migrate_database():
    """Add new columns to bookings table for enhanced booking system."""
    
    with app.app_context():
        print("Starting database migration...")
        
        # Get connection
        connection = db.engine.connect()
        
        try:
            # Check if columns already exist
            result = connection.execute(text("PRAGMA table_info(bookings)"))
            existing_columns = [row[1] for row in result]
            
            # Define new columns to add
            new_columns = {
                'security_deposit': 'REAL DEFAULT 0.0',
                'monthly_rent': 'REAL DEFAULT 0.0',
                'platform_fee': 'REAL DEFAULT 0.0',
                'total_paid': 'REAL DEFAULT 0.0',
                'razorpay_order_id': 'TEXT',
                'razorpay_payment_id': 'TEXT',
                'razorpay_signature': 'TEXT',
                'contract_start_date': 'DATE',
                'contract_end_date': 'DATE',
                'contract_duration_months': 'INTEGER DEFAULT 11',
                'contract_signed': 'BOOLEAN DEFAULT 0',
                'contract_signed_at': 'DATETIME',
                'contract_pdf_path': 'TEXT',
                'owner_notified': 'BOOLEAN DEFAULT 0',
                'student_notified': 'BOOLEAN DEFAULT 0',
                'owner_notification_sent_at': 'DATETIME',
                'student_notification_sent_at': 'DATETIME',
                'owner_approved': 'BOOLEAN DEFAULT 0',
                'owner_approved_at': 'DATETIME',
                'owner_rejection_reason': 'TEXT',
                'move_in_date': 'DATE',
                'move_in_completed': 'BOOLEAN DEFAULT 0',
                'move_in_confirmed_at': 'DATETIME',
                'updated_at': 'DATETIME',
                'confirmed_at': 'DATETIME',
                'cancelled_at': 'DATETIME',
                'cancellation_reason': 'TEXT',
                'cancelled_by': 'TEXT',
                'refund_amount': 'REAL DEFAULT 0.0',
                'refund_processed': 'BOOLEAN DEFAULT 0',
                'refund_processed_at': 'DATETIME',
            }
            
            # Add missing columns
            added_count = 0
            for column_name, column_type in new_columns.items():
                if column_name not in existing_columns:
                    try:
                        sql = f"ALTER TABLE bookings ADD COLUMN {column_name} {column_type}"
                        connection.execute(text(sql))
                        connection.commit()
                        print(f"✅ Added column: {column_name}")
                        added_count += 1
                    except Exception as e:
                        print(f"⚠️  Could not add {column_name}: {e}")
                else:
                    print(f"⏭️  Column {column_name} already exists")
            
            print(f"\n✅ Migration completed! Added {added_count} new columns.")
            print("\n📋 Next steps:")
            print("1. Install new dependency: pip install reportlab")
            print("2. Configure email settings in .env file")
            print("3. Test the booking flow with a student and owner account")
            print("4. Check static/contracts folder for generated PDFs")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            connection.rollback()
        finally:
            connection.close()

if __name__ == "__main__":
    migrate_database()
