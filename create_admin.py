from app import app, db, Admin

def create_admin():
    with app.app_context():
        email = "admin@roomies.in"
        password = "admin123"
        
        existing_admin = Admin.query.filter_by(email=email).first()
        if existing_admin:
            print(f"Admin {email} already exists.")
            return

        admin = Admin(
            email=email,
            name="System Admin",
            role="admin"
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        print(f"Successfully created admin user: {email} / {password}")

if __name__ == "__main__":
    create_admin()
