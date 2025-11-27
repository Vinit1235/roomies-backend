"""
Script to reset the database (Clear all data)
WARNING: This will delete all users, rooms, and bookings!
"""
import os
from app import app, db

def reset_database():
    print("="*50)
    print("WARNING: DATABASE RESET")
    print("="*50)
    print("This will drop all tables and recreate them.")
    print("All data (Owners, Students, Rooms, Bookings) will be LOST.")
    
    confirm = input("\nAre you sure you want to continue? (type 'yes' to confirm): ")
    
    if confirm.lower() == 'yes':
        with app.app_context():
            print("\nDropping all tables...")
            db.drop_all()
            
            print("Creating all tables...")
            db.create_all()
            
            print("\n✅ Database has been reset successfully!")
            print("You can now create a new admin user or run populate_real_data.py")
    else:
        print("\nOperation cancelled.")

if __name__ == "__main__":
    reset_database()
