import sqlite3

conn = sqlite3.connect('instance/roomies.db')
cursor = conn.cursor()

# Check if bookings table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bookings'")
result = cursor.fetchone()

if result:
    print("✓ Bookings table exists")
    
    # Get table schema
    cursor.execute("PRAGMA table_info(bookings)")
    columns = cursor.fetchall()
    print(f"\nBookings table has {len(columns)} columns:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
else:
    print("✗ Bookings table does NOT exist!")
    print("\nAvailable tables:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        print(f"  - {table[0]}")

conn.close()
