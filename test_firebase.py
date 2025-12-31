"""Test Firebase integration."""
import os
from utils.firebase_storage import init_firebase

print("=" * 60)
print("🔥 FIREBASE INTEGRATION TEST")
print("=" * 60)

# Check environment variables
print("\n1. Checking environment variables:")
cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
storage_bucket = os.getenv('FIREBASE_STORAGE_BUCKET')

print(f"   FIREBASE_CREDENTIALS_PATH: {cred_path if cred_path else '❌ NOT SET'}")
print(f"   FIREBASE_STORAGE_BUCKET: {storage_bucket if storage_bucket else '❌ NOT SET'}")

if not cred_path:
    print("\n❌ Firebase credentials path not set in .env file")
    print("\n📝 Add this to your .env file:")
    print("   FIREBASE_CREDENTIALS_PATH=firebase-credentials.json")
    print("   FIREBASE_STORAGE_BUCKET=your-project.appspot.com")
    exit(1)

if not os.path.exists(cred_path):
    print(f"\n❌ Credentials file not found: {cred_path}")
    print("\n📝 To fix this:")
    print("   1. Go to Firebase Console → Project Settings → Service Accounts")
    print("   2. Click 'Generate new private key'")
    print(f"   3. Save the JSON file as '{cred_path}'")
    exit(1)

# Test initialization
print("\n2. Testing Firebase initialization...")
if init_firebase():
    print("   ✅ Firebase initialized successfully!")
    print("\n✅ FIREBASE IS READY TO USE!")
    print("\n📦 You can now:")
    print("   - Upload room images")
    print("   - Store verification documents")
    print("   - Manage user profile pictures")
else:
    print("   ❌ Firebase initialization failed")
    print("   Check the error message above for details")
