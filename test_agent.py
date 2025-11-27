import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure we can import from the agents module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from agents.chatbot import chatbot
except ImportError as e:
    print(f"Error importing chatbot: {e}")
    print("Make sure you have installed the requirements: pip install -r requirements.txt")
    sys.exit(1)

# Mock room provider for testing (Simulates the database lookup)
def mock_room_provider(query):
    print(f"\n[DEBUG] System searching for rooms matching: '{query}'...")
    query = query.lower()
    
    # Return dummy data based on keywords
    if "mumbai" in query:
        return [
            {"id": 101, "title": "Student Haven Hostel", "location": "Andheri, Mumbai", "property_type": "hostel", "price": 8000, "amenities": ["WiFi", "Mess", "AC"]},
            {"id": 102, "title": "Sea Breeze Apartment", "location": "Bandra, Mumbai", "property_type": "flat", "price": 25000, "amenities": ["Gym", "Security", "Parking"]}
        ]
    elif "pune" in query:
        return [
            {"id": 201, "title": "Tech Park PG", "location": "Hinjewadi, Pune", "property_type": "pg", "price": 6000, "amenities": ["WiFi", "Cleaning"]}
        ]
    
    return []

# Register the mock provider
chatbot.set_room_provider(mock_room_provider)

def main():
    print("="*50)
    print("🤖 Roomies AI Agent - Terminal Test Mode")
    print("="*50)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️  WARNING: GEMINI_API_KEY not found in .env file.")
        print("   The agent will use basic keyword matching (Fallback Mode).")
        print("   To test RAG, add your key to .env: GEMINI_API_KEY=your_key")
    else:
        print("✅ Gemini API Key found. RAG System is ACTIVE.")
        if hasattr(chatbot, 'index') and chatbot.index:
            print("✅ FAISS Vector Index is loaded.")
        else:
            print("ℹ️  Using Keyword Search (FAISS not loaded or dependencies missing).")

    print("\nType 'exit' to quit.")
    print("-" * 50)

    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
            
            if not user_input.strip():
                continue

            print("Agent is thinking...", end="\r")
            response = chatbot.get_response(user_input)
            print(" " * 20, end="\r") # Clear "thinking" message
            print(f"Agent: {response}")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()
