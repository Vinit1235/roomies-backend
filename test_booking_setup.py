"""
Quick test script to verify booking system setup.
Run this after completing setup to ensure everything works.
"""

import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test if all required modules can be imported."""
    print("Testing imports...")
    try:
        from app import app, db, Booking, Room, Student, Owner
        print("✅ Core modules imported successfully")
        
        from utils.email_service import email_service
        print("✅ Email service imported successfully")
        
        from utils.contract_generator import contract_generator
        print("✅ Contract generator imported successfully")
        
        from reportlab.pagesizes import letter
        print("✅ ReportLab installed correctly")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_email_configuration():
    """Test if email is configured correctly."""
    print("\nTesting email configuration...")
    
    email_host = os.getenv("EMAIL_HOST")
    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")
    
    if not email_host:
        print("❌ EMAIL_HOST not set in .env")
        return False
    
    if not email_user:
        print("❌ EMAIL_USER not set in .env")
        return False
    
    if not email_password:
        print("❌ EMAIL_PASSWORD not set in .env")
        return False
    
    print(f"✅ Email configured: {email_user}")
    return True


def test_database_schema():
    """Test if database has required booking columns."""
    print("\nTesting database schema...")
    
    try:
        from app import app, db
        from sqlalchemy import inspect
        
        with app.app_context():
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('bookings')]
            
            required_columns = [
                'security_deposit', 'monthly_rent', 'platform_fee',
                'contract_start_date', 'contract_pdf_path', 'owner_approved'
            ]
            
            missing = [col for col in required_columns if col not in columns]
            
            if missing:
                print(f"❌ Missing columns: {', '.join(missing)}")
                print("   Run: python migrations/migrate_booking_system.py")
                return False
            
            print(f"✅ Database schema up to date ({len(columns)} columns)")
            return True
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def test_directories():
    """Test if required directories exist."""
    print("\nTesting directory structure...")
    
    required_dirs = [
        'static/contracts',
        'static/uploads',
        'utils',
        'migrations'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path} exists")
        else:
            print(f"❌ {dir_path} missing")
            all_exist = False
    
    return all_exist


def test_email_send(test_email=None):
    """Test sending a real email (optional)."""
    print("\nTesting email sending...")
    
    if not test_email:
        test_email = input("Enter your email to receive test message (or press Enter to skip): ").strip()
    
    if not test_email:
        print("⏭️  Skipped email send test")
        return True
    
    try:
        from utils.email_service import email_service
        
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h1 style="color: #ff385c;">🎉 Roomies Booking System Test</h1>
            <p>Congratulations! Your email system is working correctly.</p>
            <p><strong>Timestamp:</strong> {}</p>
            <p>You're all set to start receiving booking notifications!</p>
        </body>
        </html>
        """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        result = email_service.send_email(
            to_email=test_email,
            subject="✅ Roomies Booking System - Test Email",
            html_content=html_content
        )
        
        if result:
            print(f"✅ Test email sent to {test_email}")
            print("   Check your inbox (and spam folder)")
            return True
        else:
            print("❌ Failed to send email")
            print("   Check your .env email configuration")
            return False
            
    except Exception as e:
        print(f"❌ Email test error: {e}")
        return False


def test_contract_generation():
    """Test PDF contract generation."""
    print("\nTesting contract generation...")
    
    try:
        from utils.contract_generator import contract_generator
        from app import app, db, Room, Student, Owner, Booking
        from datetime import date
        
        # Create mock data
        with app.app_context():
            # Mock owner
            class MockOwner:
                name = "Test Owner"
                email = "owner@test.com"
                kyc_verified = True
            
            # Mock student
            class MockStudent:
                name = "Test Student"
                email = "student@test.com"
                college = "Test College"
                verified = True
            
            # Mock room
            class MockRoom:
                title = "Test Property"
                location = "Test Location, City"
                college_nearby = "Test College"
                property_type = "shared"
                amenities = "WiFi, AC, Bed"
                price = 10000.0
            
            # Mock booking
            class MockBooking:
                id = 999
                monthly_rent = 10000.0
                booking_amount = 999.0
                security_deposit = 20000.0
                platform_fee = 200.0
                total_paid = 31199.0
                contract_duration_months = 11
                contract_start_date = date.today()
                contract_end_date = date.today() + timedelta(days=330)
                move_in_date = date.today()
            
            # Generate test contract
            pdf_path = contract_generator.generate_rental_agreement(
                MockBooking(), MockRoom(), MockStudent(), MockOwner()
            )
            
            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path) / 1024  # KB
                print(f"✅ Contract generated: {pdf_path}")
                print(f"   Size: {file_size:.1f} KB")
                return True
            else:
                print("❌ Contract file not created")
                return False
                
    except Exception as e:
        print(f"❌ Contract generation error: {e}")
        return False


def run_all_tests():
    """Run all verification tests."""
    print("=" * 60)
    print("ROOMIES BOOKING SYSTEM - VERIFICATION TESTS")
    print("=" * 60)
    
    results = {
        "Imports": test_imports(),
        "Email Config": test_email_configuration(),
        "Database Schema": test_database_schema(),
        "Directories": test_directories(),
        "Contract Generation": test_contract_generation(),
    }
    
    # Optional email test
    print("\n" + "=" * 60)
    send_test = input("Send a test email? (y/N): ").strip().lower()
    if send_test == 'y':
        test_email = input("Your email: ").strip()
        results["Email Sending"] = test_email_send(test_email)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("Your booking system is ready to use.")
        print("\nNext steps:")
        print("1. Start your Flask app: python app.py")
        print("2. Test the booking flow via API or frontend")
        print("3. Check documentation: BOOKING_SYSTEM_GUIDE.md")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("Please fix the issues above before proceeding.")
        print("\nCommon fixes:")
        print("- Run: pip install reportlab")
        print("- Run: python migrations/migrate_booking_system.py")
        print("- Configure email in .env file")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    success = run_all_tests()
    sys.exit(0 if success else 1)
