
from app import app, db, Room

def check_db():
    with app.app_context():
        try:
            count = Room.query.count()
            print(f"✅ CONNECTION SUCCESSFUL: Found {count} rooms in the database.")
            
            if count > 0:
                print("\nSample Rooms:")
                for room in Room.query.limit(3).all():
                    print(f"- {room.title} (₹{room.price}) - Verified: {room.verified}")
            else:
                print("⚠️ Database is connected but EMPTY. Seeding might have failed.")
                
        except Exception as e:
            print(f"❌ DATABASE ERROR: {e}")

if __name__ == "__main__":
    check_db()
