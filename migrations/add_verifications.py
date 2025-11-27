"""Database migration to add verifications table."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from sqlalchemy import text

def add_verifications_table():
    """Add verifications table to database."""
    with app.app_context():
        # Check if table exists
        inspector = db.inspect(db.engine)
        if 'verifications' not in inspector.get_table_names():
            print("Creating verifications table...")
            db.create_all()
            print("✓ Verifications table created successfully")
        else:
            print("✓ Verifications table already exists")
            
            # Check if electricity_bill_path column exists
            columns = {col["name"] for col in inspector.get_columns("verifications")}
            if "electricity_bill_path" not in columns:
                print("Adding electricity_bill_path column...")
                try:
                    db.session.execute(text("ALTER TABLE verifications ADD COLUMN electricity_bill_path VARCHAR(512)"))
                    db.session.commit()
                    print("✓ electricity_bill_path column added successfully")
                except Exception as e:
                    db.session.rollback()
                    print(f"❌ Error adding column: {e}")
            else:
                print("✓ electricity_bill_path column already exists")
        
        # Add uploads directory
        upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'verifications')
        os.makedirs(upload_dir, exist_ok=True)
        print(f"✓ Upload directory created: {upload_dir}")

if __name__ == "__main__":
    add_verifications_table()
