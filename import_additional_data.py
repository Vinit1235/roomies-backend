import random
import re
from app import app, db, Room, Owner, rebuild_search_index

raw_data = """Indian Institute of Technology Bombay (IIT Bombay)	Powai	Premium Co-living PG	Stanza Living, Housr (Powai)	₹18,000 - ₹30,000	All meals, Wi-Fi, Gym, Laundry, Housekeeping	Hassle-free, premium living
Veermata Jijabai Technological Institute (VJTI)	Matunga	College Hostel	VJTI Hostel	₹5,000 - ₹9,000	Basic lodging, Mess Food	Extreme budget focus
Sardar Patel Institute of Technology (SPIT)	Andheri West	Shared Flat (2BHK)	Lokhandwala, Azad Nagar	₹12,000 - ₹18,000/person	Semi-furnished, Security, Parking	Students wanting private space
Mukesh Patel School of Technology (MPSTME)	JVLR, Andheri	Standard PG	Zolo Life (JVLR)	₹10,000 - ₹16,000	Food, Wi-Fi, Common Lounge	Balanced convenience & cost
Dwarkadas J. Sanghvi College (DJSCE)	Vile Parle	Shared Flat (1BHK)	Vile Parle East	₹14,000 - ₹20,000/person	Prime Location, Basic Furnishing	High budget, small group sharing
K. J. Somaiya Institute of Technology	Vidyavihar	Student PG	Local PGs (Ghatkopar)	₹7,000 - ₹12,000	Food, Wi-Fi, Security	Proximity at moderate cost
Bharati Vidyapeeth College of Engineering	Navi Mumbai	Shared Flat (2BHK)	Kharghar, Sector 12	₹6,000 - ₹10,000/person	Newer Buildings, More Amenities	Good value for money
Pillai College of Engineering	New Panvel	Budget PG	Local PGs (Panvel)	₹5,000 - ₹9,000	Basic Food, Wi-Fi	Most economical option
Thadomal Shahani Engineering College	Bandra	Premium PG	Colive (Bandra West)	₹15,000 - ₹22,000	All meals, Wi-Fi, Security	Comfort in prime location
Fr. Conceicao Rodrigues College of Engineering	Bandra	Standard PG	Local Trust-run Hostels	₹10,000 - ₹16,000	Food, Wi-Fi, Curfew	Structured environment
Atharva College of Engineering	Malad	Shared Flat (3BHK)	Malad East, Kurar Village	₹8,000 - ₹13,000/person	More Space, Local Market Access	Group of friends
Vivekanand Education Society's Institute of Technology (VESIT)	Chembur	Shared Flat (2BHK)	Chembur Camp, Tilak Nagar	₹7,000 - ₹12,000/person	Community Park, Security	Good value, spacious rooms
Rizvi College of Engineering	Bandra	Standard PG	Local PGs (Bandra East)	₹9,000 - ₹15,000	Vegetarian Food, Wi-Fi	Homely environment
Lokmanya Tilak College of Engineering	Kopar Khairane	Budget PG	Local PGs (Kopar Khairane)	₹6,000 - ₹10,000	Basic Food, Wi-Fi	Budget-conscious students
Padmabhushan Vasantdada Patil Pratishthan's College of Engineering	Sion	Shared Flat (1BHK)	Sion East	₹10,000 - ₹15,000/person	Semi-furnished, Balcony	Small group independence
Konkan Gyanpeeth College of Engineering	Karjat	College Hostel	College Official Hostel	₹4,000 - ₹8,000	Basic Accommodation, Mess	Essential for remote location
Ramrao Adik Institute of Technology	Nerul, Navi Mumbai	Shared Flat (2BHK)	Nerul, Seawoods	₹6,000 - ₹10,000/person	Newer Buildings, Peaceful	Great quality of life
Xavier Institute of Engineering	Mahim	Standard PG	Local PGs (Mahim)	₹9,000 - ₹14,000	Food, Wi-Fi, Room Cleaning	Central location access
Yadavrao Tasgaonkar Institute of Engineering & Technology	Bhivpuri Road	Private Room / PG	Local Homeowners	₹3,000 - ₹6,000	Very Basic, Home-cooked Food	Only private option available
Rustomjee Academy for Global Careers	Dhule	College Hostel	College Hostel	₹4,500 - ₹8,500	Basic lodging, Mess Food	Mandatory for out-of-town students
Mahatma Gandhi Mission's College of Engineering and Technology	Navi Mumbai	Shared Flat (2BHK)	Kamothe, Sector 6	₹5,500 - ₹9,500/person	Newer Buildings, Amenities	Affordable Navi Mumbai option
Universal College of Engineering	Vasai	Budget PG	Local PGs (Vasai)	₹5,000 - ₹8,000	Basic Food, Wi-Fi	Low-cost local option
Watumull Institute of Electronics Engineering and Computer Technology	Ulhasnagar	Shared Flat (1BHK)	Ulhasnagar Area	₹4,000 - ₹7,000/person	Basic Furnishing, Security	Most economical independent living
Vidyalankar Institute of Technology	Wadala	Student PG	Local PGs (Wadala East)	₹7,000 - ₹11,000	Food, Wi-Fi, Security	Central location convenience
Shah and Anchor Kutchhi Engineering College	Chembur	Standard PG	Local PGs (Chembur)	₹7,000 - ₹12,000	Food, Wi-Fi, Laundry	Balanced option for Chembur
Thakur College of Engineering and Technology	Kandivali	Shared Flat (2BHK)	Kandivali East	₹8,000 - ₹13,000/person	Semi-furnished, Parking	Group living in suburban area
K.J. Somaiya College of Engineering and Commerce	Vidyavihar	Student PG	Local PGs (Ghatkopar)	₹7,000 - ₹12,000	Food, Wi-Fi, Security	Somaiya campus proximity
Rajiv Gandhi Institute of Technology	Juhu	Shared Flat (1BHK)	Juhu Scheme	₹15,000 - ₹22,000/person	Prime Location, Basic Furnishing	High budget for prime location
D. Y. Patil College of Engineering	Nerul, Navi Mumbai	Shared Flat (2BHK)	Nerul, Sector 6	₹6,000 - ₹10,000/person	Newer Buildings, Amenities	Good value in Navi Mumbai
Sardar Patel College of Engineering	Andheri	Shared Flat (2BHK)	Andheri West	₹12,000 - ₹18,000/person	Semi-furnished, Security, Parking	Students wanting private space
Lokmanya Tilak College of Engineering, Kopar Khairane	Kopar Khairane	Budget PG	Local PGs (Kopar Khairane)	₹6,000 - ₹10,000	Basic Food, Wi-Fi	Budget-conscious students
Dr. D. Y. Patil Institute of Technology	Pimpri	College Hostel	College Hostel	₹5,000 - ₹9,000	Basic Accommodation, Mess	Official college accommodation
Indian Institute of Information Technology and Management	Andheri West	Premium Co-living PG	Zolo Life (Andheri West)	₹14,000 - ₹20,000	All meals, Wi-Fi, Gym, Laundry	Hassle-free, all-inclusive living
Don Bosco Institute of Technology	Kurla	Standard PG	Local PGs (Kurla East)	₹8,000 - ₹13,000	Food, Wi-Fi, Security	Moderate cost for central location
St. John College of Engineering	Vevoor, Palghar	College Hostel	College Official Hostel	₹4,000 - ₹7,000	Basic lodging, Mess Food"""

def parse_price(price_str):
    # Extract first number
    nums = re.findall(r'[\d,]+', price_str)
    if nums:
        return int(nums[0].replace(',', ''))
    return 5000

def import_data():
    with app.app_context():
        owner = Owner.query.filter_by(email="system@roomies.in").first()
        if not owner:
            print("System owner not found! Creating one...")
            owner = Owner(email="system@roomies.in", name="System", kyc_verified=True)
            owner.set_password("system123")
            db.session.add(owner)
            db.session.commit()

        room_images = [
            "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=600&q=80",
            "https://images.unsplash.com/photo-1595526114035-0d45ed16cfbf?w=600&q=80",
            "https://images.unsplash.com/photo-1522771753035-4a50354b6063?w=600&q=80",
            "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=600&q=80",
            "https://images.unsplash.com/photo-1505693416388-b0346efee539?w=600&q=80",
            "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=600&q=80",
            "https://images.unsplash.com/photo-1540518614846-7eded433c457?w=600&q=80",
            "https://images.unsplash.com/photo-1628624747186-a941c476b7ef?w=600&q=80",
            "https://images.unsplash.com/photo-1595526114035-0d45ed16cfbf?w=600&q=80",
            "https://images.unsplash.com/photo-1512918760532-3c50f8f2c5d7?w=600&q=80",
        ]

        lines = raw_data.strip().split('\n')
        count = 0
        for line in lines:
            parts = line.split('\t')
            if len(parts) < 6:
                continue
            
            college = parts[0].strip()
            location = parts[1].strip()
            acc_type = parts[2].strip()
            provider = parts[3].strip()
            price_str = parts[4].strip()
            amenities = parts[5].strip()
            
            price = parse_price(price_str)
            
            # Determine property type
            prop_type = "shared"
            if "PG" in acc_type: prop_type = "pg"
            elif "Hostel" in acc_type: prop_type = "hostel"
            elif "Flat" in acc_type: prop_type = "flat"
            
            # Random images
            selected_images = random.sample(room_images, 3)
            image_string = ",".join(selected_images)
            
            # Check if exists
            existing = Room.query.filter_by(title=f"{acc_type} at {provider}", college_nearby=college).first()
            if existing:
                continue

            room = Room(
                title=f"{acc_type} at {provider}",
                price=price,
                location=location,
                college_nearby=college,
                amenities=amenities,
                property_type=prop_type,
                capacity_total=random.choice([1, 2, 3, 4]),
                capacity_occupied=0,
                owner_id=owner.id,
                verified=True,
                images=image_string
            )
            db.session.add(room)
            count += 1
        
        db.session.commit()
        print(f"Imported {count} new listings.")
        
        # Rebuild index
        rebuild_search_index()

if __name__ == "__main__":
    import_data()
