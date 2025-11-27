from app import app, db, Room

# Approximate coordinates for Mumbai areas
AREA_COORDINATES = {
    "Powai": (19.1176, 72.9060),
    "Matunga": (19.0178, 72.8478),
    "Andheri West": (19.1363, 72.8277),
    "Andheri": (19.1136, 72.8697),
    "JVLR": (19.1243, 72.8754),
    "Vile Parle": (19.1013, 72.8437),
    "Vidyavihar": (19.0790, 72.8970),
    "Navi Mumbai": (19.0330, 73.0297),
    "Kharghar": (19.0269, 73.0553),
    "New Panvel": (18.9894, 73.1175),
    "Panvel": (18.9894, 73.1175),
    "Bandra": (19.0596, 72.8295),
    "Malad": (19.1797, 72.8512),
    "Chembur": (19.0522, 72.9005),
    "Kopar Khairane": (19.1034, 73.0113),
    "Sion": (19.0390, 72.8619),
    "Karjat": (18.9102, 73.3283),
    "Nerul": (19.0338, 73.0196),
    "Mahim": (19.0354, 72.8401),
    "Bhivpuri": (18.9367, 73.3283),
    "Dhule": (20.9042, 74.7749),
    "Kamothe": (19.0167, 73.0917),
    "Vasai": (19.3919, 72.8397),
    "Ulhasnagar": (19.2183, 73.1632),
    "Wadala": (19.0178, 72.8561),
    "Kandivali": (19.2047, 72.8526),
    "Juhu": (19.1075, 72.8263),
    "Pimpri": (18.6298, 73.7997),
    "Kurla": (19.0726, 72.8845),
    "Palghar": (19.6936, 72.7655),
    "Vevoor": (19.70, 72.78),
    "Ghatkopar": (19.0860, 72.9090),
    "Mulund": (19.1726, 72.9425),
    "Thane": (19.2183, 72.9781),
    "Borivali": (19.2372, 72.8441),
    "Dadar": (19.0178, 72.8478),
    "Worli": (19.0166, 72.8168),
    "Colaba": (18.9067, 72.8147),
    "Churchgate": (18.9322, 72.8264),
    "Byculla": (18.9750, 72.8295),
    "Santacruz": (19.0843, 72.8360),
    "Goregaon": (19.1663, 72.8526),
    "Dahisar": (19.2575, 72.8591),
    "Mira Road": (19.2813, 72.8561),
    "Bhayandar": (19.2952, 72.8544),
    "Virar": (19.47, 72.8),
    "Nalasopara": (19.4167, 72.8167),
    "Kalyan": (19.2403, 73.1305),
    "Dombivli": (19.2184, 73.0867),
    "Ambernath": (19.20, 73.18),
    "Badlapur": (19.15, 73.26),
    "Titwala": (19.30, 73.20),
    "Asangaon": (19.43, 73.30),
    "Kasara": (19.63, 73.48),
    "Mumbra": (19.17, 73.02),
    "Kalwa": (19.20, 72.98),
    "Airoli": (19.1590, 72.9986),
    "Rabale": (19.13, 73.00),
    "Ghansoli": (19.11, 73.00),
    "Vashi": (19.0771, 72.9980),
    "Sanpada": (19.06, 73.01),
    "Juinagar": (19.05, 73.01),
    "Seawoods": (19.02, 73.02),
    "Belapur": (19.02, 73.03),
    "Uran": (18.88, 72.94),
    "Panvel": (18.9894, 73.1175),
    "Taloja": (19.06, 73.11),
    "Rasayani": (18.90, 73.15),
    "Pen": (18.73, 73.08),
    "Alibag": (18.64, 72.87),
    "Roha": (18.43, 73.12),
    "Mangaon": (18.27, 73.37),
    "Mahad": (18.08, 73.42),
    "Poladpur": (17.98, 73.47),
    "Chiplun": (17.53, 73.52),
    "Ratnagiri": (16.99, 73.31),
    "Sindhudurg": (16.11, 73.68),
    "Goa": (15.29, 74.12),
    "Pune": (18.5204, 73.8567),
    "Nashik": (19.9975, 73.7898),
    "Aurangabad": (19.8762, 75.3433),
    "Nagpur": (21.1458, 79.0882),
    "Kolhapur": (16.7050, 74.2433),
    "Solapur": (17.6599, 75.9064),
    "Satara": (17.6805, 74.0183),
    "Sangli": (16.8524, 74.5815),
    "Ahmednagar": (19.0952, 74.7496),
    "Jalgaon": (21.0077, 75.5626),
    "Akola": (20.7002, 77.0082),
    "Amravati": (20.9374, 77.7796),
    "Latur": (18.4088, 76.5604),
    "Nanded": (19.1383, 77.3210),
    "Parbhani": (19.2644, 76.7739),
    "Beed": (18.9891, 75.7601),
    "Osmanabad": (18.1853, 76.0419),
    "Hingoli": (19.7178, 77.1486),
    "Washim": (20.1110, 77.1317),
    "Buldhana": (20.5305, 76.1814),
    "Yavatmal": (20.3888, 78.1204),
    "Wardha": (20.7453, 78.6022),
    "Chandrapur": (19.9615, 79.2961),
    "Gadchiroli": (20.1849, 80.0088),
    "Gondia": (21.4624, 80.2210),
    "Bhandara": (21.1777, 79.6570),
    "Nandurbar": (21.3700, 74.2400),
    "Dhule": (20.9042, 74.7749),
}

def update_coords():
    with app.app_context():
        rooms = Room.query.filter(Room.latitude == None).all()
        print(f"Found {len(rooms)} rooms without coordinates.")
        
        updated = 0
        for room in rooms:
            # Try to match location or college name to our coordinate map
            found = False
            
            # 1. Check Location field
            for area, coords in AREA_COORDINATES.items():
                if area.lower() in room.location.lower():
                    room.latitude = coords[0]
                    room.longitude = coords[1]
                    found = True
                    break
            
            # 2. If not found, check College Name
            if not found:
                for area, coords in AREA_COORDINATES.items():
                    if area.lower() in room.college_nearby.lower():
                        room.latitude = coords[0]
                        room.longitude = coords[1]
                        found = True
                        break
            
            # 3. Fallback for specific known colleges if location didn't match
            if not found:
                if "IIT Bombay" in room.college_nearby:
                    room.latitude, room.longitude = AREA_COORDINATES["Powai"]
                    found = True
                elif "VJTI" in room.college_nearby:
                    room.latitude, room.longitude = AREA_COORDINATES["Matunga"]
                    found = True
                elif "SPIT" in room.college_nearby:
                    room.latitude, room.longitude = AREA_COORDINATES["Andheri West"]
                    found = True
            
            if found:
                updated += 1
                # Add small random jitter so markers don't overlap perfectly
                import random
                room.latitude += random.uniform(-0.002, 0.002)
                room.longitude += random.uniform(-0.002, 0.002)
        
        db.session.commit()
        print(f"Successfully updated coordinates for {updated} rooms.")

if __name__ == "__main__":
    update_coords()
