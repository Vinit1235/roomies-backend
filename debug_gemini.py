import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("="*50)
print("DIAGNOSTIC: Gemini API Connection")
print("="*50)

if not api_key:
    print("❌ ERROR: GEMINI_API_KEY not found in environment.")
    exit(1)

print(f"✅ API Key found: {api_key[:5]}...{api_key[-5:]}")

# Configure GenAI
genai.configure(api_key=api_key)

print("\n1. Listing Available Models for this Key:")
print("-" * 30)
try:
    found_flash = False
    found_pro = False
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f" - {m.name}")
            if 'gemini-1.5-flash' in m.name:
                found_flash = True
            if 'gemini-pro' in m.name:
                found_pro = True
    
    print("-" * 30)
    if found_flash:
        print("✅ 'gemini-1.5-flash' is available.")
    else:
        print("❌ 'gemini-1.5-flash' NOT found in list.")
        
    if found_pro:
        print("✅ 'gemini-pro' is available.")
    else:
        print("❌ 'gemini-pro' NOT found in list.")

except Exception as e:
    print(f"❌ Error listing models: {e}")
    exit(1)

print("\n2. Testing Generation with 'gemini-1.5-flash':")
print("-" * 30)
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hello, are you working?")
    print(f"✅ Success! Response: {response.text}")
except Exception as e:
    print(f"❌ Failed: {e}")

print("\n3. Testing Generation with 'gemini-pro':")
print("-" * 30)
try:
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Hello, are you working?")
    print(f"✅ Success! Response: {response.text}")
except Exception as e:
    print(f"❌ Failed: {e}")

print("\n" + "="*50)
