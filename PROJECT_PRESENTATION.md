# 📊 Roomies: Investor & Technical Deck

## Slide 1: Title
**Project Name:** Roomies
**Tagline:** AI-Powered Student Accommodation Marketplace
**Version:** 2.0 (Production Ready)
**Presenter:** [Your Name]

---

## Slide 2: The Core Problem
- **Student Pain Points:**
  - Unverified listings lead to scames.
  - No centralized platform for detailed room info (WiFi speed, curfew).
  - Manual booking processes are slow and paper-heavy.
- **Owner Pain Points:**
  - High brokerage fees.
  - Difficulty in tracking payments and occupancy.
  - Lack of trusted tenant verification.

---

## Slide 3: Our Solution
**Roomies** is a full-stack integrated platform that solves trust and efficiency gaps:
1.  **Verified Inventory:** "Blue Tick" verification for owners and properties.
2.  **Instant Bookings:** Real-time inventory with 3-click booking flow.
3.  **AI Assistant:** 24/7 Concierge for query resolution using **Google Gemini 1.5**.
4.  **Financial Safety:** Escrow-like payment flow via **Razorpay**.

---

## Slide 4: Market Opportunity
- **TAM (Total Addressable Market):** 40M+ Higher Education students in India.
- **SAM (Serviceable Available Market):** Urban students in Metro cities (Delhi, Mumbai, Bangalore).
- **Growth:** Co-living sector growing at 17% CAGR.

---

## Slide 5: Product Demo - Student Journey
1.  **Explore:** Map-based search with "Locate Me" and clustering (Google Maps API).
2.  **Select:** View 360 images, amenities list, and "Distance to College".
3.  **AI Chat:** Ask "Is this safe for girls?" or "What's the transit like?".
4.  **Book:** Digital contract generation -> E-Sign -> Payment (Razorpay).
5.  **Move-In:** QR Code entry pass generated.

---

## Slide 6: Product Demo - Owner Journey
1.  **Dashboard:** Live view of "Occupancy Rate" and "Revenue this Month".
2.  **Listing Mgr:** Easy photo upload and amenity selection.
3.  **Tenant requests:** Approve/Reject incoming booking requests.
4.  **Wallet:** Withdraw earnings to bank account.

---

## Slide 7: Technical Architecture
- **Frontend:** Vanilla JS with ES6 Modules (Lightweight, Fast).
- **Backend:** Python Flask (Scalable REST API).
- **Database:** PostgreSQL (Relational integrity for bookings).
- **Search Engine:** `TheFuzz` for fuzzy logic matching + SQL optimization.
- **AI Engine:** `google-generativeai` SDK (Gemini 1.5 Flash).
- **Maps:** Google Maps JavaScript API (Client-side rendering).

---

## Slide 8: Database Schema Overview
- **Users:** Single table with Polymorphic identity (Student/Owner/Admin).
- **Properties:** Rooms linked to Owners.
- **Bookings:** State machine (Pending -> Approved -> Paid -> Active).
- **Transactions:** Ledger for every Razorpay event.
- **Reviews:** Weighted ratings system.

---

## Slide 9: Key Innovation - The Verification Engine
- **Step 1:** User uploads ID (Aadhar/PAN).
- **Step 2:** (Planned) OpenCV checks for blur/glare.
- **Step 3:** Admin reviews in Admin Panel.
- **Step 4:** System sends "Verification Success" email via SMTP.
- **Step 5:** "Verified" Batch unlocks on profile.

---

## Slide 10: Key Innovation - Usage of Generative AI
- **Context-Aware:** The AI knows the specific room details the user is viewing.
- **RAG Implementation:** Retrieval Augmented Generation using room database.
- **Guardrails:** Prevents hallucination by restricting scope to housing.

---

## Slide 11: Security Implementation
- **Auth:** Flask-Login with specialized session handling.
- **Data:** SQL Injection protection via SQLAlchemy ORM.
- **Payments:** Server-side signature verification (HMAC-SHA256) for Razorpay to prevent tampering.
- **Environment:** Strict `.gitignore` policy (managed via `.env`).

---

## Slide 12: Business Model
- **Commission:** 5% fee on every successful booking (Student side).
- **Subscription:** ₹199/month for Owners (Premium Listing).
- **Ads:** Sponsored spots on Explore Map.

---

## Slide 13: Future Roadmap (Q1 2026)
- **Mobile App:** React Native port.
- **Video Tours:** WebRTC real-time viewing.
- **Roommate Matching:** Tinder-style swipe for finding roommates based on "Lifestyle Tags".

---

## Slide 14: Team
- **Vinit:** Lead Full Stack Developer.
- **Team Roomies:** Design & Marketing.

---

## Slide 15: Q & A
*Ready for Deployment.*
