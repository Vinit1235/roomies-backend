import json
import random
from app import app, db, Room, Owner, Admin

def populate_db():
    with app.app_context():
        # 0. Create Admin User
        admin_email = "admin@roomies.in"
        admin = Admin.query.filter_by(email=admin_email).first()
        if not admin:
            print("Creating Admin User...")
            admin = Admin(
                email=admin_email,
                name="System Admin",
                role="admin"
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
        print(f"Admin user ready: {admin_email}")

        # 1. Create a System Owner if not exists
        owner = Owner.query.filter_by(email="system@roomies.in").first()
        if not owner:
            print("Creating System Owner...")
            owner = Owner(
                email="system@roomies.in",
                name="Roomies System",
                kyc_verified=True
            )
            owner.set_password("system123")
            db.session.add(owner)
            db.session.commit()
        
        print(f"Using Owner ID: {owner.id}")

        # 2. Load Real Data
        try:
            with open('data/real_data_dump.json', 'r', encoding='utf-8') as f:
                colleges_data = json.load(f)
        except FileNotFoundError:
            print("Error: data/real_data_dump.json not found. Run fetch_real_data.py first.")
            return

        # CLEAR EXISTING ROOMS to focus only on the new data (Mumbai)
        print("Clearing existing rooms...")
        try:
            num_deleted = db.session.query(Room).delete()
            db.session.commit()
            print(f"Deleted {num_deleted} old rooms.")
        except Exception as e:
            db.session.rollback()
            print(f"Error clearing rooms: {e}")

        # 3. Create Rooms
        
        # Curated list of realistic hostel/student room images from Unsplash
        room_images = [
            "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=600&q=80", # Bunk beds
            "https://images.unsplash.com/photo-1595526114035-0d45ed16cfbf?w=600&q=80", # Bedroom
            "https://images.unsplash.com/photo-1522771753035-4a50354b6063?w=600&q=80", # Cozy
            "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=600&q=80", # Modern
            "https://images.unsplash.com/photo-1505693416388-b0346efee539?w=600&q=80", # Student room
            "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=600&q=80", # Window view
            "https://images.unsplash.com/photo-1540518614846-7eded433c457?w=600&q=80", # Bedroom 2
            "https://images.unsplash.com/photo-1628624747186-a941c476b7ef?w=600&q=80", # Hostel corridor
            "https://images.unsplash.com/photo-1595526114035-0d45ed16cfbf?w=600&q=80", # Clean room
            "https://images.unsplash.com/photo-1512918760532-3c50f8f2c5d7?w=600&q=80", # Small apartment
        ]

        count = 0
        updated_count = 0
        
        for college_entry in colleges_data:
            college_name = college_entry['college']
            hostels = college_entry.get('nearby_hostels', [])
            
            for hostel in hostels:
                # Pick 3 random images for this hostel
                selected_images = random.sample(room_images, 3)
                image_string = ",".join(selected_images)

                # Check if room already exists
                existing = Room.query.filter_by(
                    title=hostel['name'], 
                    latitude=hostel['lat'], 
                    longitude=hostel['lon']
                ).first()
                
                if existing:
                    # Update images for existing rooms
                    existing.images = image_string
                    updated_count += 1
                    continue

                # Generate random attributes
                price = random.choice([8000, 9500, 10000, 12000, 15000, 18000])
                capacity = random.choice([1, 2, 3, 4])
                occupied = random.randint(0, capacity)
                
                room = Room(
                    title=hostel['name'],
                    price=price,
                    location=f"Near {college_name}",
                    college_nearby=college_name,
                    amenities="WiFi,AC,Laundry,Security",
                    property_type="Hostel" if hostel['type'] == 'hostel' else "PG",
                    capacity_total=capacity,
                    capacity_occupied=occupied,
                    latitude=hostel['lat'],
                    longitude=hostel['lon'],
                    owner_id=owner.id,
                    verified=True,
                    images=image_string
                )
                db.session.add(room)
                count += 1
        
        db.session.commit()
        print(f"Successfully added {count} new hostels and updated {updated_count} existing ones with real photos!")

if __name__ == "__main__":
    populate_db()
