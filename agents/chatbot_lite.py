"""
Lightweight Gemini-powered Chatbot for Roomies
No heavy dependencies (FAISS, SentenceTransformers).
Uses direct Gemini API with prompt-based context.
"""
import json
import os
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class ChatbotLite:
    def __init__(self, data_path='data/faqs.json'):
        self.data_path = data_path
        self.faqs = self._load_faqs()
        self.room_provider = None
        self.model = None
        
        # Initialize Gemini
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # Use gemini-1.5-flash (fast and efficient)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                print("✅ Gemini chatbot initialized (Lite mode)")
            except Exception as e:
                print(f"❌ Error initializing Gemini: {e}")
                self.model = None
        else:
            print("⚠️ GEMINI_API_KEY not found. Chatbot will use fallback responses.")

    def set_room_provider(self, provider_func):
        """Register a callback function to fetch room listings."""
        self.room_provider = provider_func

    def _load_faqs(self):
        """Load FAQs from JSON file."""
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            full_path = os.path.join(base_path, self.data_path)
            with open(full_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading FAQs: {e}")
            return []

    def _get_relevant_faqs(self, query, max_results=3):
        """Simple keyword-based FAQ matching (no heavy ML)."""
        query_words = set(re.findall(r'\w+', query.lower()))
        scored = []
        
        for faq in self.faqs:
            question_words = set(re.findall(r'\w+', faq['question'].lower()))
            # Jaccard similarity
            if query_words and question_words:
                intersection = query_words & question_words
                union = query_words | question_words
                score = len(intersection) / len(union)
                if score > 0.1:
                    scored.append((score, faq))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:max_results]]

    def _build_context(self, user_message):
        """Build context for Gemini prompt."""
        context_parts = []
        
        # 1. Relevant FAQs
        relevant_faqs = self._get_relevant_faqs(user_message)
        if relevant_faqs:
            faq_text = "📚 FAQ Knowledge Base:\n"
            for faq in relevant_faqs:
                faq_text += f"Q: {faq['question']}\nA: {faq['answer']}\n\n"
            context_parts.append(faq_text)
        
        # 2. Available Rooms (if provider is set)
        if self.room_provider:
            try:
                rooms = self.room_provider(user_message)
                if rooms:
                    room_text = "🏠 Available Rooms/Listings:\n"
                    for room in rooms[:5]:
                        amenities = ", ".join(room.get('amenities', [])[:3]) if isinstance(room.get('amenities'), list) else room.get('amenities', '')[:50]
                        room_text += f"- {room['title']} in {room['location']}. Type: {room['property_type']}. Price: ₹{room['price']}/month. Amenities: {amenities}\n"
                    context_parts.append(room_text)
            except Exception as e:
                print(f"Room provider error: {e}")
        
        # 3. Website Info (always included - comprehensive context)
        website_context = """
🌐 ROOMIES PLATFORM - COMPLETE GUIDE:

📌 WHAT IS ROOMIES?
Roomies is India's leading student housing platform that helps students find hostels, PGs (Paying Guest accommodations), flats, and compatible roommates using AI-powered matching technology.

🏠 PROPERTY TYPES AVAILABLE:
- Hostel: Shared dormitory-style accommodation with common facilities
- PG (Paying Guest): Private or shared rooms in residential buildings, often with meals included
- Flat/Apartment: Independent rooms or entire flats for rent
- Shared Room: Share a room with other students to save costs

📍 KEY PAGES & FEATURES:
• /explore - Browse and search all available rooms with filters for location, price range, property type, and amenities
• /findmate - AI-powered roommate matching based on lifestyle preferences (sleep schedule, study habits, food preferences, etc.)
• /list-room - Property owners can list their rooms for FREE (basic listing) or with premium features
• /dashboard - Students can manage their profile, bookings, saved listings, and verification status
• /flash-deals - 24-hour limited-time discounts on select properties (owners pay ₹29 to create flash deals)
• /faq - Frequently asked questions about the platform
• /contact - Get in touch with support team

🏙️ SUPPORTED CITIES:
Mumbai, Pune, Bangalore, Delhi, Chennai, Hyderabad, Kota (major education hubs in India)

💰 PRICING & FEES:
- Searching for rooms: FREE for all users
- Booking Fee: ₹999 one-time fee when booking a room
- Security Deposit: 2x monthly rent (refundable at end of stay)
- Platform Fee: 2% of first month's rent
- Flash Deal Fee: ₹29 for owners to create 24-hour flash deals
- Owner Pro Subscription: ₹199/month for premium features

📋 BOOKING PROCESS:
1. Browse rooms on /explore page
2. Click "View Details" on a room you like
3. Click "Reserve" or "Contact Owner"
4. Pay the booking fee (₹999) + security deposit + first month rent
5. Sign the digital contract
6. Move in on your scheduled date!

✅ VERIFICATION SYSTEM:
- Students: Need College ID + Government ID (Aadhar/PAN)
- Owners: Need Government ID + Electricity Bill for the property
- Verified listings show a "Verified" badge
- Our team reviews documents within 24-48 hours

🔒 SAFETY FEATURES:
- All listings undergo safety audits (fire extinguisher, CCTV, security guard checks)
- Safety score displayed on each listing
- Report fake listings using the "Report" button
- Chats are monitored for harassment

🍽️ MESS/FOOD:
Some PGs and hostels include meals. Look for "Food" or "Mess" amenity icon. We display weekly mess menus where available.

👥 ROOMMATE MATCHING (FINDMATE):
Our AI analyzes your profile including:
- Sleep schedule (early bird vs night owl)
- Study habits
- Food preferences (vegetarian/non-vegetarian)
- Personality (introvert/extrovert)
- Cleanliness preferences
And suggests compatible roommates with a compatibility score!

💳 PAYMENT METHODS:
UPI, Credit/Debit Cards, Net Banking via secure Razorpay gateway

📞 CONTACT & SUPPORT:
- Email: support@roomies.in
- Technical issues: tech@roomies.in
- Response time: Within 24 hours
- Emergency: Dial 100 (Police) or 112

🏷️ SUBSCRIPTION PLANS:
FOR STUDENTS (Roomies Premium):
- Unlimited property inquiries
- Priority customer support
- Waived booking fees
- Early access to flash deals

FOR OWNERS (Owner Pro - ₹199/month):
- Unlimited listings
- Featured placement in search results
- Advanced analytics dashboard
- Reduced commission rates
- Priority support

💡 QUICK TIPS:
- Create a complete profile for better roommate matches
- Verify your account to build trust
- Schedule property visits before booking
- Read reviews from other students
- Check the safety audit score
- Look for the "Verified" badge on listings
"""
        context_parts.append(website_context)
        
        return "\n".join(context_parts)

    def get_response(self, user_message):
        """Get AI response for user message."""
        user_message = user_message.strip()
        
        # Quick responses for greetings
        greetings = ['hi', 'hello', 'hey', 'greetings', 'hii', 'hola']
        if user_message.lower() in greetings:
            return "👋 Hello! I'm the Roomies AI assistant. I can help you find hostels, PGs, flats, and answer questions about our platform. What are you looking for today?"
        
        if user_message.lower() in ['bye', 'goodbye', 'exit', 'quit']:
            return "👋 Goodbye! Happy house hunting! Feel free to come back anytime."
        
        # Search intent - quick redirect
        search_keywords = ['find', 'search', 'looking for', 'show me', 'want', 'need']
        room_keywords = ['room', 'hostel', 'pg', 'flat', 'apartment', 'place', 'accommodation']
        
        if any(k in user_message.lower() for k in search_keywords) and any(k in user_message.lower() for k in room_keywords):
            cities = ['mumbai', 'pune', 'bangalore', 'delhi', 'chennai', 'hyderabad', 'kota']
            for city in cities:
                if city in user_message.lower():
                    return f"🔍 I can help you find a place in {city.title()}! <a href='/explore?city={city}' class='text-blue-600 underline font-medium'>Click here to see listings in {city.title()}</a>. You can also use our filters to narrow down by price and property type."
            return "🔍 I can help you find a room! <a href='/explore' class='text-blue-600 underline font-medium'>Click here to browse all our verified listings</a>. Use the filters to find your perfect match!"

        # Use Gemini for complex queries
        if self.model:
            try:
                context = self._build_context(user_message)
                
                prompt = f"""You are 'Roomies AI', a knowledgeable and friendly customer support assistant for Roomies - India's leading student housing platform.

IMPORTANT: You have COMPLETE knowledge about the Roomies platform from the context below. Use this information to answer ALL questions accurately.

CONTEXT INFORMATION (This is your knowledge base - USE IT!):
{context}

USER QUESTION: {user_message}

INSTRUCTIONS:
1. You ARE the official Roomies assistant. Answer confidently using the context provided above.
2. For questions about pricing, fees, booking process, verification, safety, roommate matching, etc. - the answers ARE in your context. Use them!
3. If asked about specific rooms/properties, recommend from the 'Available Rooms' list if provided.
4. For navigation questions, provide the correct page URLs (e.g., /explore, /findmate, /dashboard, etc.)
5. When discussing fees, always mention exact amounts: Booking Fee ₹999, Flash Deal ₹29, Owner Pro ₹199/month, etc.
6. For "how to" questions, provide step-by-step guidance based on the platform information.
7. Be concise but complete. 2-4 sentences for simple questions, more for detailed explanations.
8. Use Indian Rupee (₹) for all prices.
9. Only say "I don't know" if the question is truly outside the platform scope (like weather, politics, etc.)
10. Use emojis sparingly to be friendly but professional.
11. If relevant, include helpful links in HTML format: <a href='/page' class='text-blue-600 underline'>Click here</a>

RESPONSE:"""

                response = self.model.generate_content(prompt)
                return response.text.strip()
                
            except Exception as e:
                print(f"Gemini API error: {e}")
                # Fall through to FAQ fallback
        
        # Fallback: Best matching FAQ
        relevant_faqs = self._get_relevant_faqs(user_message, max_results=1)
        if relevant_faqs:
            return relevant_faqs[0]['answer']
        
        return "I'm not sure about that specific question. You can browse our <a href='/explore' class='text-blue-600 underline'>room listings</a>, check the <a href='/faq' class='text-blue-600 underline'>FAQ page</a>, or contact us at support@roomies.in for more help!"


# Singleton instance
chatbot = ChatbotLite()
