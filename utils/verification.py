import numpy as np
from geopy.geocoders import Nominatim
from thefuzz import fuzz
import os
import json
import re

# Optional imports for Verification
try:
    import cv2
    import easyocr
    # Initialize EasyOCR Reader (loads model into memory)
    # gpu=False for compatibility, set to True if you have CUDA
    reader = easyocr.Reader(['en'], gpu=False)
except ImportError as e:
    print(f"Warning: Verification dependencies missing ({e}). AI Verification will be disabled.")
    cv2 = None
    easyocr = None
    reader = None

# Initialize Geolocator
geolocator = Nominatim(user_agent="roomies_verification_system")

def extract_text_from_image(image_path):
    """
    Uses EasyOCR to extract text from an ID card image.
    Preprocesses with OpenCV for better results.
    """
    if cv2 is None or reader is None:
        print("Verification dependencies not installed.")
        return None

    try:
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            return None

        # Preprocessing: Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Preprocessing: Thresholding (optional, helps with high contrast text)
        # _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Extract text
        # detail=0 returns just the list of strings
        result = reader.readtext(gray, detail=0)
        
        return " ".join(result)
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""

def parse_id_details_with_nlp(ocr_text):
    """
    Uses enhanced regex and NLP patterns to parse ID card text.
    No API key required - runs entirely offline.
    """
    return parse_id_details_regex(ocr_text)

def parse_id_details_regex(text):
    """
    Enhanced regex-based parser with intelligent pattern matching.
    Works offline without any API keys.
    """
    data = {
        "name": None,
        "phone": None,
        "college": None,
        "pid": None,
        "address": None
    }
    
    # Convert to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    # 1. Extract Name (after keywords like "name", "student name", etc.)
    name_patterns = [
        r'(?:name|student\s*name|full\s*name)[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        r'\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
    ]
    for pattern in name_patterns:
        match = re.search(pattern, text)
        if match:
            potential_name = match.group(1).strip()
            # Validate: should be 2-4 words, each capitalized
            words = potential_name.split()
            if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words):
                data["name"] = potential_name
                break
    
    # 2. Extract Phone (10-digit Indian number)
    phone_patterns = [
        r'\b([6-9]\d{9})\b',  # Indian mobile numbers start with 6-9
        r'(?:phone|mobile|contact)[\s:]+(\d{10})',
    ]
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            data["phone"] = match.group(1)
            break
    
    # 3. Extract College/Institution
    college_keywords = ['college', 'university', 'institute', 'engineering', 'polytechnic', 'school']
    college_patterns = [
        r'((?:[A-Z][a-z]+\s+){1,5}(?:College|University|Institute|Engineering|Polytechnic))',
        r'(?:college|institution)[\s:]+(.+?)(?:\n|$)',
    ]
    
    # First try exact patterns
    for pattern in college_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data["college"] = match.group(1).strip()
            break
    
    # If not found, search for college keywords in text
    if not data["college"]:
        for keyword in college_keywords:
            if keyword in text_lower:
                # Extract surrounding context (5 words before and after)
                idx = text_lower.find(keyword)
                start = max(0, idx - 50)
                end = min(len(text), idx + 50)
                snippet = text[start:end]
                # Try to extract college name from snippet
                words = snippet.split()
                college_words = []
                for i, word in enumerate(words):
                    if keyword in word.lower():
                        # Take 3 words before and 2 after
                        college_words = words[max(0, i-2):min(len(words), i+3)]
                        break
                if college_words:
                    data["college"] = ' '.join(college_words)
                    break
    
    # 4. Extract Student ID / PID / Roll Number
    pid_patterns = [
        r'(?:id|pid|roll|enrollment|student\s*id)[\s:]+([A-Z0-9]{5,15})',
        r'\b([A-Z]{2,4}\d{6,10})\b',  # Pattern like ABC123456
        r'\b(20\d{2}[A-Z0-9]{4,8})\b',  # Year-based IDs like 2024ABC123
        r'\b(\d{8,12})\b'  # Pure numeric IDs
    ]
    for pattern in pid_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            potential_pid = match.group(1)
            # Don't confuse with phone number
            if potential_pid != data["phone"]:
                data["pid"] = potential_pid
                break
    
    # 5. Extract Address (city, state, pincode)
    address_patterns = [
        r'(?:address|addr)[\s:]+(.+?)(?:\n\n|$)',
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z][a-z]+)\s*[-,]?\s*(\d{6})',  # City, State - PIN
        r'(Mumbai|Delhi|Bangalore|Pune|Hyderabad|Chennai|Kolkata|Ahmedabad|Thane|Navi Mumbai)',
    ]
    for pattern in address_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if len(match.groups()) > 1:
                # Multi-group match (City, State, PIN)
                data["address"] = f"{match.group(1)}, {match.group(2)} - {match.group(3)}"
            else:
                data["address"] = match.group(1).strip()
            break
    
    # If still no address, look for pincode
    if not data["address"]:
        pincode_match = re.search(r'\b(\d{6})\b', text)
        if pincode_match:
            data["address"] = f"PIN: {pincode_match.group(1)}"
    
    return data

def verify_location_on_map(address):
    """
    Verifies if the address exists using Geopy.
    Returns (latitude, longitude, full_address) or None.
    """
    if not address:
        return None
        
    try:
        location = geolocator.geocode(address)
        if location:
            return {
                "lat": location.latitude,
                "lon": location.longitude,
                "address": location.address
            }
    except Exception as e:
        print(f"Geocoding Error: {e}")
    return None

def process_verification(image_path, user_record):
    """
    Main function to orchestrate the verification process.
    
    Args:
        image_path: Path to the uploaded ID card image.
        user_record: Database object or dict containing user's expected details.
        
    Returns:
        dict: Verification results
    """
    results = {
        "verified": False,
        "confidence": 0,
        "extracted_data": {},
        "checks": {
            "name_match": False,
            "college_match": False,
            "location_valid": False
        },
        "message": ""
    }
    
    # 1. Extract Text
    print(f"Scanning image: {image_path}")
    ocr_text = extract_text_from_image(image_path)
    if not ocr_text:
        results["message"] = "Could not read text from image."
        return results
        
    print(f"Extracted Text: {ocr_text[:100]}...")

    # 2. Parse Data (using offline NLP/regex - no API key needed)
    extracted_data = parse_id_details_with_nlp(ocr_text)
    results["extracted_data"] = extracted_data
    
    # 3. Verify Name (Fuzzy Match)
    if extracted_data.get("name") and user_record.name:
        ratio = fuzz.token_sort_ratio(extracted_data["name"], user_record.name)
        results["checks"]["name_match"] = ratio > 70  # Threshold
        print(f"Name Match: {extracted_data['name']} vs {user_record.name} = {ratio}%")
    
    # 4. Verify College (Fuzzy Match) - Only if user has college attribute
    user_college = getattr(user_record, 'college', None)
    if extracted_data.get("college") and user_college:
        ratio = fuzz.token_sort_ratio(extracted_data["college"], user_college)
        results["checks"]["college_match"] = ratio > 60
        print(f"College Match: {extracted_data['college']} vs {user_college} = {ratio}%")

    # 5. Verify Location
    if extracted_data.get("address"):
        loc = verify_location_on_map(extracted_data["address"])
        if loc:
            results["checks"]["location_valid"] = True
            results["extracted_data"]["geo_location"] = loc
            print(f"Location Verified: {loc['address']}")
    
    # 6. Final Decision
    # We require at least Name Match AND (College Match OR Location Valid)
    if results["checks"]["name_match"] and (results["checks"]["college_match"] or results["checks"]["location_valid"]):
        results["verified"] = True
        results["confidence"] = 90
        results["message"] = "Verification Successful"
    else:
        results["message"] = "Verification Failed: Details did not match."
        
    return results
