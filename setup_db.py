import sqlite3

conn = sqlite3.connect('roomies.db')
c = conn.cursor()

# Students
c.execute('''CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE,
    password TEXT,
    name TEXT,
    college TEXT,
    role TEXT DEFAULT 'student',
    verified BOOLEAN DEFAULT 0,
    budget INTEGER,
    lifestyle TEXT,
    study_hours TEXT,
    commute_pref TEXT
)''')

# Owners
c.execute('''CREATE TABLE IF NOT EXISTS owners (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE,
    password TEXT,
    name TEXT,
    kyc_verified BOOLEAN DEFAULT 0
)''')

# Rooms
c.execute('''CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY,
    title TEXT,
    price INTEGER,
    location TEXT,
    college_nearby TEXT,
    amenities TEXT,
    images TEXT,
    owner_id INTEGER,
    verified BOOLEAN DEFAULT 0
)''')

# Verification Docs
c.execute('''CREATE TABLE IF NOT EXISTS verification_docs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    user_type TEXT,
    doc_type TEXT,
    file_path TEXT,
    status TEXT DEFAULT 'pending'
)''')

# Payments
c.execute('''CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY,
    student_id INTEGER,
    room_id INTEGER,
    amount INTEGER,
    status TEXT DEFAULT 'pending',
    method TEXT
)''')

# Insert sample rooms (including St. John College)
sample_rooms = [
    ("Cozy Single Room near St. John", 8500, "Palghar", "St. John College of Engineering", "wifi,ac,laundry", "room1.jpg", 1, 1),
    ("Shared 2BHK - Walk to Campus", 6000, "Palghar", "St. John College of Engineering", "wifi,kitchen", "room2.jpg", 1, 1),
    ("Studio Apartment - Vidyavihar", 12000, "Mumbai", "KJ Somaiya", "wifi,ac,security", "room3.jpg", 2, 1),
    ("Affordable Shared Dorm", 5000, "Vashi", "Fr. C Rodrigues", "wifi,laundry", "room4.jpg", 3, 0)
]

c.executemany('''INSERT OR IGNORE INTO rooms 
    (title, price, location, college_nearby, amenities, images, owner_id, verified) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', sample_rooms)

conn.commit()
conn.close()
print("✅ Database created with sample rooms!")