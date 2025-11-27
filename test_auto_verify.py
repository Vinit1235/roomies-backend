"""
Test auto-verification dependencies and functionality
"""

print("="*70)
print("Testing Auto-Verification System")
print("="*70)

# Test 1: Import dependencies
print("\n1. Testing Dependencies...")
dependencies_ok = True

try:
    import cv2
    print("   ✓ OpenCV installed:", cv2.__version__)
except ImportError as e:
    print("   ✗ OpenCV NOT installed:", e)
    dependencies_ok = False

try:
    import easyocr
    print("   ✓ EasyOCR installed")
except ImportError as e:
    print("   ✗ EasyOCR NOT installed:", e)
    dependencies_ok = False

try:
    from geopy.geocoders import Nominatim
    print("   ✓ Geopy installed")
except ImportError as e:
    print("   ✗ Geopy NOT installed:", e)
    dependencies_ok = False

try:
    from thefuzz import fuzz
    print("   ✓ TheFuzz installed")
except ImportError as e:
    print("   ✗ TheFuzz NOT installed:", e)
    dependencies_ok = False

# Test 2: Import verification module
print("\n2. Testing Verification Module...")
try:
    from utils.verification import process_verification, extract_text_from_image
    print("   ✓ Verification module imported successfully")
except ImportError as e:
    print("   ✗ Failed to import verification module:", e)
    dependencies_ok = False

# Test 3: Check if EasyOCR reader initialized
if dependencies_ok:
    print("\n3. Testing EasyOCR Initialization...")
    from utils.verification import reader
    if reader is not None:
        print("   ✓ EasyOCR reader initialized successfully")
        print("   Note: First-time initialization downloads ~500MB model (one-time only)")
    else:
        print("   ✗ EasyOCR reader failed to initialize")

print("\n" + "="*70)
if dependencies_ok:
    print("✅ AUTO-VERIFICATION IS READY!")
    print("\nWhen you upload documents:")
    print("  1. System extracts text using OCR")
    print("  2. Parses name, college, ID, address")
    print("  3. Fuzzy matches with your registered data")
    print("  4. Auto-approves if confidence > 70%")
    print("\nFirst upload will be slower (EasyOCR model download ~500MB)")
else:
    print("❌ AUTO-VERIFICATION NOT AVAILABLE")
    print("\nTo enable, install missing packages:")
    print("  pip install opencv-python-headless easyocr geopy thefuzz")
print("="*70)
