import json
import os
import re
import numpy as np
import google.generativeai as genai
from dotenv import load_dotenv

# Try importing vector DB libraries
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    HAS_VECTOR_DB = True
except ImportError:
    HAS_VECTOR_DB = False
    print("Warning: sentence-transformers or faiss-cpu not installed. Falling back to keyword matching.")

# Load environment variables
load_dotenv()

class ChatbotAgent:
    def __init__(self, data_path='data/faqs.json'):
        self.data_path = data_path
        self.faqs = self._load_faqs()
        self.context = {} # To store user context if needed
        self.room_provider = None # Callback to fetch room data
        
        # Initialize Vector DB (FAISS + Sentence Transformers)
        self.encoder = None
        self.index = None
        if HAS_VECTOR_DB:
            try:
                print("Loading embedding model... (this may take a moment)")
                self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
                self._build_vector_index()
                print("Vector index built successfully.")
            except Exception as e:
                print(f"Failed to initialize vector DB: {e}")
        
        # Initialize Gemini
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            
            # Dynamically find a working model
            try:
                self.model = None
                available_models = []
                print("Checking available Gemini models...")
                
                # Priority list for stable, high-quota models
                priority_models = ['gemini-1.5-flash', 'gemini-1.0-pro', 'gemini-pro']
                
                all_models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                
                # 1. Try to find a priority model first
                for p_model in priority_models:
                    for m in all_models:
                        if p_model in m.name:
                            self.model = genai.GenerativeModel(m.name)
                            print(f"Selected Priority Model: {m.name}")
                            break
                    if self.model:
                        break
                
                # 2. Fallback to any available model if no priority model found
                if not self.model and all_models:
                    fallback = all_models[0]
                    self.model = genai.GenerativeModel(fallback.name)
                    print(f"Selected Fallback Model: {fallback.name}")
                
                if not self.model:
                    print("Warning: No suitable Gemini models found.")
                    
            except Exception as e:
                print(f"Error configuring Gemini model: {e}")
                self.model = None
        else:
            print("Warning: GEMINI_API_KEY not found in environment variables.")
            self.model = None

    def set_room_provider(self, provider_func):
        """Register a callback function to fetch room listings."""
        self.room_provider = provider_func

    def _load_faqs(self):
        try:
            # Adjust path to be relative to the app root if needed
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            full_path = os.path.join(base_path, self.data_path)
            
            with open(full_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading FAQs: {e}")
            return []

    def _build_vector_index(self):
        """Builds the FAISS index from FAQ questions."""
        if not self.faqs or not self.encoder:
            return
        
        # Create embeddings for all questions
        questions = [faq['question'] for faq in self.faqs]
        embeddings = self.encoder.encode(questions)
        
        # Initialize FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings).astype('float32'))

    def _calculate_similarity(self, query, question):
        # Simple Jaccard similarity on words (Fallback)
        query_words = set(re.findall(r'\w+', query.lower()))
        question_words = set(re.findall(r'\w+', question.lower()))
        
        if not query_words or not question_words:
            return 0.0
            
        intersection = query_words.intersection(question_words)
        union = query_words.union(question_words)
        
        return len(intersection) / len(union)

    def _get_relevant_context(self, query, top_k=3):
        """Retrieve top K relevant FAQs using Semantic Search (FAISS) or Fallback."""
        if self.index and self.encoder:
            try:
                # Semantic Search
                query_vector = self.encoder.encode([query])
                distances, indices = self.index.search(np.array(query_vector).astype('float32'), top_k)
                
                results = []
                for i, idx in enumerate(indices[0]):
                    if idx < len(self.faqs) and idx >= 0:
                        # You can add a distance threshold here if needed
                        results.append(self.faqs[idx])
                return results
            except Exception as e:
                print(f"Vector search error: {e}")
                # Fall through to fallback
        
        # Fallback: Keyword Matching
        scored_faqs = []
        for faq in self.faqs:
            score = self._calculate_similarity(query, faq['question'])
            scored_faqs.append((score, faq))
        
        # Sort by score descending
        scored_faqs.sort(key=lambda x: x[0], reverse=True)
        
        # Return top K matches if they have some relevance
        relevant = [item[1] for item in scored_faqs[:top_k] if item[0] > 0.1]
        return relevant

    def get_response(self, user_message):
        user_message = user_message.strip()
        
        # 1. Basic Intent Recognition (Client-side speed)
        if user_message.lower() in ['hi', 'hello', 'hey', 'greetings']:
            return "Hello! I'm the Roomies AI assistant. How can I help you find your perfect home today?"
        
        if user_message.lower() in ['bye', 'goodbye', 'exit']:
            return "Goodbye! Happy house hunting!"

        # 1.5 Search Intent (Workflow)
        search_keywords = ['find', 'search', 'looking for', 'show me', 'want']
        room_keywords = ['room', 'hostel', 'pg', 'flat', 'apartment', 'place']
        
        if any(k in user_message.lower() for k in search_keywords) and any(k in user_message.lower() for k in room_keywords):
            # Extract potential location (very basic)
            common_cities = ['mumbai', 'pune', 'bangalore', 'delhi', 'chennai', 'hyderabad', 'kota']
            location = ""
            for city in common_cities:
                if city in user_message.lower():
                    location = city
                    break
            
            if location:
                return f"I can help you find a place in {location.title()}! <a href='/explore?city={location}' class='text-blue-600 underline'>Click here to see listings in {location.title()}</a>."
            else:
                return "I can help you find a room! <a href='/explore' class='text-blue-600 underline'>Click here to browse all our listings</a>."

        # 2. RAG with Gemini
        if self.model:
            try:
                # A. Retrieve FAQ Context
                context_items = self._get_relevant_context(user_message)
                faq_text = ""
                if context_items:
                    faq_text = "FAQ Information:\n" + "\n".join([f"Q: {item['question']}\nA: {item['answer']}" for item in context_items])
                
                # B. Retrieve Room/Listing Context
                room_text = ""
                if self.room_provider:
                    # Fetch relevant rooms based on the user message
                    rooms = self.room_provider(user_message)
                    if rooms:
                        room_text = "\n\nAvailable Rooms/Listings (Suggest these if they match user needs):\n"
                        for room in rooms:
                            # Format room info concisely
                            amenities = ", ".join(room.get('amenities', [])[:3]) # Top 3 amenities
                            room_text += f"- ID {room['id']}: {room['title']} in {room['location']}. Type: {room['property_type']}. Price: ₹{room['price']}. Amenities: {amenities}.\n"

                # C. General Website Context
                website_text = """
                \nWebsite Navigation & Features:
                - 'Explore': Search for hostels, PGs, and flats.
                - 'Findmate': AI-powered roommate matching.
                - 'List Room': For owners to post properties.
                - 'Dashboard': Manage bookings and profile.
                - 'Flash Deals': Limited time discounts on rooms.
                """

                # Construct Prompt
                full_context = f"{faq_text}{room_text}{website_text}"
                
                prompt = f"""
                You are 'Roomies AI', a smart assistant for a student housing platform.
                Your goal is to help students find rooms, answer questions, and guide them through the website.
                
                Context Information:
                {full_context}
                
                User Question: {user_message}
                
                Instructions:
                1. Use the provided Context Information to answer.
                2. If the user asks for rooms, recommend specific options from the 'Available Rooms' list if they match.
                3. If suggesting a room, provide its ID and key details.
                4. Be friendly, concise, and helpful.
                5. If the answer is not in the context, answer generally about student housing in India but mention you don't have specific data.
                """
                
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"Gemini API Error: {e}")
                return "I'm having trouble connecting to my brain right now. Please try again later."

        # 3. Fallback (Legacy Logic if API key missing)
        best_match = None
        highest_score = 0.0
        
        for faq in self.faqs:
            score = self._calculate_similarity(user_message, faq['question'])
            if score > highest_score:
                highest_score = score
                best_match = faq

        if highest_score > 0.2:
            return best_match['answer']
        
        return "I'm not sure about that. You can try searching our FAQ page or contact support at support@roomies.in."

# Singleton instance
chatbot = ChatbotAgent()
