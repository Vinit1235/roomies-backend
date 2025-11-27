"""
Manually approve verification record in database
"""
import sqlite3
from datetime import datetime

conn = sqlite3.connect('instance/roomies.db')
cursor = conn.cursor()

print("="*70)
print("Manual Verification Approval")
print("="*70)

# Get pending verifications
cursor.execute("""
    SELECT v.id, v.user_type, v.user_id, s.name, s.email
    FROM verifications v
    LEFT JOIN students s ON v.user_id = s.id AND v.user_type = 'student'
    WHERE v.status = 'pending'
    ORDER BY v.created_at DESC
""")
pending = cursor.fetchall()

print(f"\nFound {len(pending)} pending verification(s):\n")
for p in pending:
    print(f"  [{p[0]}] {p[3]} ({p[4]}) - Type: {p[1]}, User ID: {p[2]}")

if pending:
    # Approve the most recent one
    ver_id = pending[0][0]
    user_id = pending[0][2]
    user_type = pending[0][1]
    
    print(f"\nApproving verification ID {ver_id}...")
    
    # Update verification record
    now = datetime.utcnow().isoformat()
    cursor.execute("""
        UPDATE verifications 
        SET status = 'verified', 
            reviewed_at = ?,
            rejection_reason = 'Manually approved via script'
        WHERE id = ?
    """, (now, ver_id))
    
    # Update student verified flag
    if user_type == 'student':
        cursor.execute("""
            UPDATE students 
            SET verified = 1 
            WHERE id = ?
        """, (user_id,))
    
    conn.commit()
    print(f"✅ Verification {ver_id} approved!")
    print(f"✅ Student {user_id} verified flag set to True")
    
    # Verify the changes
    cursor.execute("SELECT status, reviewed_at FROM verifications WHERE id = ?", (ver_id,))
    result = cursor.fetchone()
    print(f"\nVerification record now: status={result[0]}, reviewed_at={result[1]}")
    
    cursor.execute("SELECT verified FROM students WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    print(f"Student verified flag now: {result[0]}")
else:
    print("\nNo pending verifications found.")

conn.close()
print("\n" + "="*70)
