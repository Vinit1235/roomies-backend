import os
import pandas as pd
from app import app, db, Room, Owner, Student, ContactMessage, Verification, FlashDeal

def export_data():
    print("Starting data export...")
    
    with app.app_context():
        # 1. Export Rooms
        rooms_query = Room.query.all()
        rooms_data = []
        for r in rooms_query:
            rooms_data.append({
                "id": r.id,
                "title": r.title,
                "price": r.price,
                "location": r.location,
                "college_nearby": r.college_nearby,
                "amenities": r.amenities,
                "property_type": r.property_type,
                "capacity_total": r.capacity_total,
                "capacity_occupied": r.capacity_occupied,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "owner_id": r.owner_id,
                "verified": r.verified,
                "created_at": r.created_at,
                "updated_at": r.updated_at
            })
        df_rooms = pd.DataFrame(rooms_data)

        # 2. Export Owners
        owners_query = Owner.query.all()
        owners_data = []
        for o in owners_query:
            owners_data.append({
                "id": o.id,
                "name": o.name,
                "email": o.email,
                "kyc_verified": o.kyc_verified,
                "created_at": o.created_at
            })
        df_owners = pd.DataFrame(owners_data)

        # 3. Export Students
        students_query = Student.query.all()
        students_data = []
        for s in students_query:
            students_data.append({
                "id": s.id,
                "name": s.name,
                "email": s.email,
                "college": s.college,
                "budget": s.budget,
                "lifestyle": s.lifestyle,
                "study_hours": s.study_hours,
                "commute_pref": s.commute_pref,
                "verified": s.verified,
                "created_at": s.created_at
            })
        df_students = pd.DataFrame(students_data)

        # 4. Export Messages
        msgs_query = ContactMessage.query.all()
        msgs_data = []
        for m in msgs_query:
            msgs_data.append({
                "id": m.id,
                "name": m.name,
                "email": m.email,
                "subject": m.subject,
                "message": m.message,
                "source": m.source,
                "disposition": m.disposition,
                "created_at": m.created_at
            })
        df_msgs = pd.DataFrame(msgs_data)

        # Create Excel Writer
        output_file = os.path.join("exports", "roomies_data_dump.xlsx")
        
        # Ensure exports directory exists
        os.makedirs("exports", exist_ok=True)
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            if not df_rooms.empty:
                df_rooms.to_excel(writer, sheet_name='Rooms', index=False)
            if not df_owners.empty:
                df_owners.to_excel(writer, sheet_name='Owners', index=False)
            if not df_students.empty:
                df_students.to_excel(writer, sheet_name='Students', index=False)
            if not df_msgs.empty:
                df_msgs.to_excel(writer, sheet_name='Messages', index=False)
        
        print(f"Export successful! File saved to: {output_file}")

if __name__ == "__main__":
    export_data()
