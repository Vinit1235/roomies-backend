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
        
        # 3. Website Info (always included)
        website_context = """
🌐 Roomies Website Information:
- Roomies is a student housing platform for finding hostels, PGs, and flats in India.
- Key Pages:
  • /explore - Search for rooms with filters (location, price, property type)
  • /findmate - AI-powered roommate matching based on lifestyle preferences
  • /list-room - For property owners to list their rooms
  • /dashboard - Manage bookings, profile, and saved listings
  • /flash-deals - Limited-time discounts on select properties
- Supported Cities: Mumbai, Pune, Bangalore, Delhi, Chennai, Hyderabad, Kota
- Contact: support@roomies.in
- Features: Verified listings, Safety audits, Mess menu info, Direct booking
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
                
                prompt = f"""You are 'Roomies AI', a friendly and helpful assistant for a student housing platform in India.

CONTEXT INFORMATION:
{context}

USER QUESTION: {user_message}

INSTRUCTIONS:
1. Answer based on the context provided above.
2. If asked about specific rooms, recommend from the 'Available Rooms' list if they match.
3. For navigation questions, provide the correct page URLs.
4. Be concise, friendly, and helpful (2-3 sentences max unless explaining something complex).
5. If you don't have specific information, say so honestly and suggest contacting support@roomies.in.
6. Use emojis sparingly to be friendly but professional.

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
