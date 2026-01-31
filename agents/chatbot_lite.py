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
        self.roommate_provider = None  # New: for AI roommate matching
        self.model = None
        
        # Initialize Gemini
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # Use gemini-1.5-flash (fast and efficient)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                print("✅ Gemini chatbot initialized (gemini-2.5-flash)")
            except Exception as e:
                print(f"❌ Error initializing Gemini: {e}")
                self.model = None
        else:
            print("⚠️ GEMINI_API_KEY not found. Chatbot will use fallback responses.")

    def set_room_provider(self, provider_func):
        """Register a callback function to fetch room listings."""
        self.room_provider = provider_func

    def set_roommate_provider(self, provider_func):
        """Register a callback function to fetch roommate matches."""
        self.roommate_provider = provider_func

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

    def _detect_roommate_intent(self, message):
        """Detect if user wants roommate matching."""
        message_lower = message.lower()
        
        # Keywords for roommate matching
        roommate_keywords = ['roommate', 'roomie', 'room mate', 'flatmate', 'flat mate', 
                           'match me', 'find me a match', 'compatible', 'partner']
        find_keywords = ['find', 'search', 'looking', 'want', 'need', 'get', 'show']
        
        # Direct roommate request
        if any(k in message_lower for k in roommate_keywords):
            return True
        
        # Find + person context
        if any(f in message_lower for f in find_keywords):
            if any(p in message_lower for p in ['someone', 'person', 'student', 'buddy']):
                return True
        
        return False

    def _extract_preferences_from_message(self, message):
        """Extract roommate preferences from natural language."""
        preferences = {}
        message_lower = message.lower()
        
        # Sleep schedule
        if any(w in message_lower for w in ['early bird', 'morning person', 'wake up early', 'early riser']):
            preferences['sleep_schedule'] = 'early_bird'
        elif any(w in message_lower for w in ['night owl', 'late night', 'stay up late', 'night person']):
            preferences['sleep_schedule'] = 'night_owl'
        elif 'flexible' in message_lower:
            preferences['sleep_schedule'] = 'flexible'
        
        # Social level
        if any(w in message_lower for w in ['extrovert', 'social', 'outgoing', 'party', 'friends over']):
            preferences['social_level'] = 'extrovert'
        elif any(w in message_lower for w in ['introvert', 'quiet', 'private', 'alone']):
            preferences['social_level'] = 'introvert'
        elif any(w in message_lower for w in ['moderate', 'sometimes', 'occasional']):
            preferences['social_level'] = 'ambivert'
        
        # Cleanliness
        if any(w in message_lower for w in ['clean', 'neat', 'organized', 'tidy']):
            preferences['cleanliness_pref'] = 'neat_freak'
        elif any(w in message_lower for w in ['messy', 'relaxed', 'casual']):
            preferences['cleanliness_pref'] = 'messy'
        
        # Budget
        if '5k' in message_lower or '5000' in message_lower:
            preferences['budget_range'] = '5k-8k'
        elif '8k' in message_lower or '8000' in message_lower:
            preferences['budget_range'] = '8k-12k'
        elif '12k' in message_lower or '12000' in message_lower:
            preferences['budget_range'] = '12k-18k'
        elif '18k' in message_lower or '18000' in message_lower or '20k' in message_lower:
            preferences['budget_range'] = '18k+'
        
        return preferences

    def _format_roommate_matches(self, matches):
        """Format roommate matches for display."""
        if not matches:
            return None
        
        result = "🎯 **Top Roommate Matches:**\n\n"
        
        display_names = {
            "early_bird": "🌅 Early Bird",
            "night_owl": "🦉 Night Owl",
            "flexible": "⏰ Flexible",
            "extrovert": "🎉 Social",
            "ambivert": "🤝 Moderate",
            "introvert": "🧘 Private",
            "neat_freak": "✨ Very Clean",
            "moderate_clean": "🧹 Moderate",
            "messy": "😎 Relaxed",
        }
        
        for i, match in enumerate(matches[:5], 1):
            sleep = display_names.get(match.get('sleep_schedule'), match.get('sleep_schedule', 'N/A'))
            social = display_names.get(match.get('social_level'), match.get('social_level', 'N/A'))
            score = match.get('compatibility_score', 0)
            
            result += f"**{i}. {match['name']}** - {score}% Compatible\n"
            result += f"   🏫 {match.get('college', 'N/A')} | {sleep} | {social}\n\n"
        
        return result

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
• /ai-matching - AI-powered roommate matching based on lifestyle preferences
• /findmate - Find compatible roommates based on profile
• /list-room - Property owners can list their rooms for FREE (basic listing) or with premium features
• /dashboard - Students can manage their profile, bookings, saved listings, and verification status
• /flash-deals - 24-hour limited-time discounts on select properties

🤖 AI ROOMMATE MATCHING:
Our AI analyzes your profile including:
- Sleep schedule (early bird vs night owl)
- Social level (extrovert/introvert/ambivert)
- Cleanliness preferences (neat freak/moderate/relaxed)
- Budget range
And suggests compatible roommates with a compatibility score!

To use AI matching, users can:
1. Go to /ai-matching page
2. Fill out the preference questionnaire
3. Click "Find My Matches" to see compatible students
4. Or chat with me and describe what they're looking for!

💰 PRICING & FEES:
- Searching for rooms: FREE for all users
- Booking Fee: ₹999 one-time fee when booking a room
- Security Deposit: 2x monthly rent (refundable at end of stay)

📞 CONTACT & SUPPORT:
- Email: support@roomies.in
- Response time: Within 24 hours
"""
        context_parts.append(website_context)
        
        return "\n".join(context_parts)

    def get_response(self, user_message, user_id=None):
        """Get AI response for user message."""
        user_message = user_message.strip()
        
        # Quick responses for greetings
        greetings = ['hi', 'hello', 'hey', 'greetings', 'hii', 'hola']
        if user_message.lower() in greetings:
            return "👋 Hello! I'm the Roomies AI assistant. I can help you find hostels, PGs, flats, and **compatible roommates**! Just tell me what you're looking for."
        
        if user_message.lower() in ['bye', 'goodbye', 'exit', 'quit']:
            return "👋 Goodbye! Happy house hunting! Feel free to come back anytime."
        
        # ROOMMATE MATCHING INTENT
        if self._detect_roommate_intent(user_message):
            # Extract preferences from message
            preferences = self._extract_preferences_from_message(user_message)
            
            # Try to get matches if provider is available
            if self.roommate_provider:
                try:
                    matches = self.roommate_provider(user_id, preferences)
                    if matches and len(matches) > 0:
                        formatted = self._format_roommate_matches(matches)
                        return f"🎯 Great! I found some compatible roommates for you!\n\n{formatted}\n\n💡 Want more specific matches? Tell me your preferences for sleep schedule, social level, or budget. Or visit <a href='/ai-matching' class='text-blue-600 underline font-medium'>AI Matching page</a> for detailed questionnaire!"
                    else:
                        return f"🔍 I looked for roommates but couldn't find exact matches yet. To improve results:\n\n1. <a href='/ai-matching' class='text-blue-600 underline font-medium'>Complete the AI Matching questionnaire</a>\n2. Tell me your preferences (e.g., 'I'm a night owl looking for a quiet roommate with budget around 10k')\n\nMore students are joining daily!"
                except Exception as e:
                    print(f"Roommate provider error: {e}")
            
            # Fallback: Direct to AI matching page
            return f"🤝 I can help you find a compatible roommate! Here's how:\n\n1. **Quick Match**: <a href='/ai-matching' class='text-blue-600 underline font-medium'>Go to AI Matching</a> to fill out preferences and see matches instantly\n\n2. **Chat with me**: Tell me your preferences like:\n   - Sleep schedule (early bird/night owl)\n   - Social level (social/quiet)\n   - Budget (5k-8k, 8k-12k, etc.)\n\nWhat's your lifestyle like? 🌙☀️"
        
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
4. For navigation questions, provide the correct page URLs (e.g., /explore, /ai-matching, /findmate, /dashboard, etc.)
5. When discussing fees, always mention exact amounts: Booking Fee ₹999, etc.
6. For "how to" questions, provide step-by-step guidance based on the platform information.
7. Be concise but complete. 2-4 sentences for simple questions, more for detailed explanations.
8. Use Indian Rupee (₹) for all prices.
9. Only say "I don't know" if the question is truly outside the platform scope (like weather, politics, etc.)
10. Use emojis sparingly to be friendly but professional.
11. If relevant, include helpful links in HTML format: <a href='/page' class='text-blue-600 underline'>Click here</a>
12. For roommate matching questions, mention the /ai-matching page.
13. For general queries like "best home" or "best room", suggest exploring listings and provide helpful criteria.

RESPONSE:"""

                print(f"[Chatbot] Calling Gemini API for: '{user_message[:50]}...'")
                response = self.model.generate_content(prompt)
                
                if response and response.text:
                    print(f"[Chatbot] Gemini responded successfully")
                    return response.text.strip()
                else:
                    print(f"[Chatbot] Gemini returned empty response")
                    
            except Exception as e:
                print(f"[Chatbot] Gemini API error: {e}")
                import traceback
                traceback.print_exc()
                # Fall through to FAQ fallback
        
        # Fallback: Best matching FAQ
        relevant_faqs = self._get_relevant_faqs(user_message, max_results=1)
        if relevant_faqs:
            return relevant_faqs[0]['answer']
        
        return "I'm not sure about that specific question. You can browse our <a href='/explore' class='text-blue-600 underline'>room listings</a>, check the <a href='/faq' class='text-blue-600 underline'>FAQ page</a>, or contact us at support@roomies.in for more help!"


# Singleton instance
chatbot = ChatbotLite()

