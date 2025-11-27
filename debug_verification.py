"""
Debug script to check verification status in database
"""
import sqlite3

conn = sqlite3.connect('instance/roomies.db')
cursor = conn.cursor()

print("="*70)
print("Verification Status Debug")
print("="*70)

# Check verifications table
print("\n1. Recent Verifications:")
cursor.execute("""
    SELECT id, user_type, user_id, status, rejection_reason, 
           created_at, reviewed_at 
    FROM verifications 
    ORDER BY created_at DESC 
    LIMIT 5
""")
verifications = cursor.fetchall()

for v in verifications:
    print(f"\nVerification ID: {v[0]}")
    print(f"  User Type: {v[1]}")
    print(f"  User ID: {v[2]}")
    print(f"  Status: {v[3]}")
    print(f"  Rejection Reason: {v[4]}")
    print(f"  Created: {v[5]}")
    print(f"  Reviewed: {v[6]}")

# Check students table
print("\n2. Students Verified Status:")
cursor.execute("""
    SELECT id, name, email, verified, college 
    FROM students 
    ORDER BY id DESC 
    LIMIT 5
""")
students = cursor.fetchall()

for s in students:
    print(f"\nStudent ID: {s[0]}")
    print(f"  Name: {s[1]}")
    print(f"  Email: {s[2]}")
    print(f"  Verified: {s[3]}")
    print(f"  College: {s[4]}")

# Cross-check
print("\n3. Cross-Check (Verification vs Student):")
cursor.execute("""
    SELECT v.id, v.user_id, v.status, s.verified, s.name
    FROM verifications v
    LEFT JOIN students s ON v.user_id = s.id
    WHERE v.user_type = 'student'
    ORDER BY v.created_at DESC
    LIMIT 5
""")
cross = cursor.fetchall()

for c in cross:
    print(f"\nVerification {c[0]} for Student {c[1]} ({c[4]}):")
    print(f"  Verification Status: {c[2]}")
    print(f"  Student Verified Flag: {c[3]}")
    if c[2] == 'verified' and c[3] != 1:
        print("  ⚠️ MISMATCH! Verification approved but student.verified = False")

conn.close()
print("\n" + "="*70)
