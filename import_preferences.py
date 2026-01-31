"""
Script to import student roommate preferences from CSV file.
Run this script to populate the database with sample student data for AI matching.
"""
import csv
import os
import sys
import random
import string

# Fix console encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Student, ProfileTag


def generate_email(name):
    """Generate a unique email from name."""
    base = name.lower().replace(' ', '.').replace("'", "")
    random_suffix = ''.join(random.choices(string.digits, k=3))
    return f"{base}{random_suffix}@student.roomies.in"


def map_sleep_schedule(value):
    """Map CSV sleep schedule value to database value."""
    if "Early bird" in value:
        return "early_bird"
    elif "Night owl" in value:
        return "night_owl"
    else:
        return "flexible"


def map_social_level(value):
    """Map CSV social level value to database value."""
    if "Very social" in value:
        return "extrovert"
    elif "Moderately social" in value:
        return "ambivert"
    else:
        return "introvert"


def map_cleanliness(value):
    """Map CSV cleanliness value to database value."""
    if "Very organized" in value:
        return "neat_freak"
    elif "Moderately clean" in value:
        return "moderate_clean"
    else:
        return "messy"


def map_budget_range(value):
    """Map CSV budget range value to database value."""
    if "5,000" in value:
        return "5k-8k"
    elif "8,000" in value:
        return "8k-12k"
    elif "12,000" in value:
        return "12k-18k"
    else:
        return "18k+"


def import_preferences(csv_path, college="DJ Sanghvi College of Engineering"):
    """Import student preferences from CSV file."""
    
    with app.app_context():
        imported = 0
        skipped = 0
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                name = row.get('Name', '').strip()
                if not name:
                    continue
                
                # Generate unique email
                email = generate_email(name)
                
                # Check if student with this email exists
                existing = Student.query.filter_by(email=email).first()
                if existing:
                    skipped += 1
                    continue
                
                # Map values
                sleep = map_sleep_schedule(row.get("What's your sleep schedule?", ""))
                social = map_social_level(row.get("How social are you?", ""))
                cleanliness = map_cleanliness(row.get("Cleanliness preference?", ""))
                budget = map_budget_range(row.get("Budget range (monthly)", ""))
                
                # Create student
                student = Student(
                    email=email,
                    name=name,
                    college=college,
                    verified=True,  # Auto-verify for demo data
                    sleep_schedule=sleep,
                    social_level=social,
                    cleanliness_pref=cleanliness,
                    budget_range=budget
                )
                student.set_password("demo123")  # Default password
                db.session.add(student)
                db.session.flush()  # Get the ID
                
                # Also create ProfileTags for backward compatibility
                tags = [sleep, social, cleanliness]
                for tag in tags:
                    profile_tag = ProfileTag(student_id=student.id, tag=tag)
                    db.session.add(profile_tag)
                
                imported += 1
        
        db.session.commit()
        print(f"Imported {imported} students, skipped {skipped} duplicates")
        return imported, skipped


if __name__ == "__main__":
    csv_file = os.path.join(os.path.dirname(__file__), "student_roommate_preferences.csv")
    
    if not os.path.exists(csv_file):
        print(f"CSV file not found: {csv_file}")
        sys.exit(1)
    
    print(f"Reading from: {csv_file}")
    imported, skipped = import_preferences(csv_file)
    print(f"Import complete! {imported} new students added.")
