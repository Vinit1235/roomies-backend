"""
Fix Missing Database Columns
=============================
Adds missing columns to existing tables that were added in the revenue system.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from sqlalchemy import inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_missing_columns():
    """Add missing columns to existing tables."""
    
    with app.app_context():
        logger.info("Checking for missing columns...")
        
        try:
            inspector = inspect(db.engine)
            
            # Check owners table
            owners_columns = [col['name'] for col in inspector.get_columns('owners')]
            logger.info(f"Owners table columns: {owners_columns}")
            
            # Add missing columns to owners table
            with db.engine.connect() as conn:
                if 'active_listings_count' not in owners_columns:
                    logger.info("Adding active_listings_count to owners table...")
                    conn.execute(db.text("""
                        ALTER TABLE owners ADD COLUMN active_listings_count INTEGER DEFAULT 0
                    """))
                    conn.commit()
                    logger.info("✅ Added active_listings_count column")
                else:
                    logger.info("active_listings_count column already exists")
            
            # Check students table
            students_columns = [col['name'] for col in inspector.get_columns('students')]
            logger.info(f"Students table columns: {students_columns}")
            
            # Add missing columns to students table
            with db.engine.connect() as conn:
                if 'property_inquiries_count' not in students_columns:
                    logger.info("Adding property_inquiries_count to students table...")
                    conn.execute(db.text("""
                        ALTER TABLE students ADD COLUMN property_inquiries_count INTEGER DEFAULT 0
                    """))
                    conn.commit()
                    logger.info("✅ Added property_inquiries_count column")
                else:
                    logger.info("property_inquiries_count column already exists")
                
                if 'inquiries_reset_date' not in students_columns:
                    logger.info("Adding inquiries_reset_date to students table...")
                    conn.execute(db.text("""
                        ALTER TABLE students ADD COLUMN inquiries_reset_date DATE
                    """))
                    conn.commit()
                    logger.info("✅ Added inquiries_reset_date column")
                else:
                    logger.info("inquiries_reset_date column already exists")
            
            # Check rooms table
            if inspector.has_table('rooms'):
                rooms_columns = [col['name'] for col in inspector.get_columns('rooms')]
                logger.info(f"Rooms table columns: {rooms_columns}")
                
                with db.engine.connect() as conn:
                    if 'is_featured' not in rooms_columns:
                        logger.info("Adding is_featured to rooms table...")
                        conn.execute(db.text("""
                            ALTER TABLE rooms ADD COLUMN is_featured BOOLEAN DEFAULT 0
                        """))
                        conn.commit()
                        logger.info("✅ Added is_featured column")
                    else:
                        logger.info("is_featured column already exists")
                    
                    if 'is_premium_listing' not in rooms_columns:
                        logger.info("Adding is_premium_listing to rooms table...")
                        conn.execute(db.text("""
                            ALTER TABLE rooms ADD COLUMN is_premium_listing BOOLEAN DEFAULT 0
                        """))
                        conn.commit()
                        logger.info("✅ Added is_premium_listing column")
                    else:
                        logger.info("is_premium_listing column already exists")
            
            logger.info("✅ All missing columns have been added!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = fix_missing_columns()
    if success:
        print("\n" + "="*60)
        print("✅ DATABASE COLUMNS FIXED SUCCESSFULLY!")
        print("="*60)
        print("\nFixed Issues:")
        print("  • Added active_listings_count to owners table")
        print("  • Added property_inquiries_count to students table")
        print("  • Added inquiries_reset_date to students table")
        print("  • Added is_featured to rooms table")
        print("  • Added is_premium_listing to rooms table")
        print("\nYou can now:")
        print("  1. Restart your Flask application")
        print("  2. Sign in without errors")
        print("  3. Test subscription features")
        print("\n" + "="*60)
    else:
        print("\n❌ Migration failed. Check the logs above for errors.")
