# Roomies - Premium Features Documentation

## Overview
Roomies is a comprehensive student housing platform with advanced features including flash deals, subscriptions, payments, PWA support, and AI-powered roommate matching.

---

## 🚀 Core Features

### 1. **Flash Deals (24hr Auto-Expire)**
- **What**: Limited-time offers on rooms with pulsing red markers on the map
- **Fee**: ₹29 per flash deal for owners
- **Duration**: Automatically expires after 24 hours
- **API Endpoints**:
  - `GET /api/flash-deals` - Get all active flash deals
  - `POST /api/flash-deals/create` - Create a new flash deal (owners only)
  - `POST /api/flash-deals/<id>/deactivate` - Deactivate a deal early
- **Features**:
  - Animated pulsing markers on map
  - Real-time countdown timer
  - Automatic discount percentage calculation
  - Revenue tracking in analytics

### 2. **Owner Pro Subscription**
- **What**: Premium subscription for room owners
- **Price**: ₹199/month
- **Payment**: Stripe integration (mock implementation included)
- **Benefits**: Priority listing, advanced analytics, bulk uploads, etc.
- **API Endpoints**:
  - `POST /api/subscriptions/create` - Start subscription
  - `GET /api/subscriptions/my` - Check subscription status
- **Features**:
  - Monthly billing cycle
  - Auto-renewal support
  - Pro badge display
  - Revenue tracking

### 3. **Referral & Wallet System**
- **What**: Referral program with wallet credits
- **Reward**: ₹200 to both referrer and referred student
- **API Endpoints**:
  - `GET /api/referrals/my-code` - Get personal referral code
  - `POST /api/referrals/apply` - Apply referral code
  - `GET /api/wallet/balance` - Check wallet balance
  - `GET /api/wallet/transactions` - View transaction history
- **Features**:
  - Unique referral codes (format: ROOM{id}{timestamp})
  - One-time use per student
  - Automatic wallet credit
  - Transaction history
  - 3% withdrawal fee

### 4. **Partial Payment Booking**
- **What**: Book rooms with ₹999 advance payment
- **Payment**: Razorpay integration (mock implementation)
- **Platform Fee**: 2% of booking amount
- **API Endpoints**:
  - `POST /api/bookings/create` - Create booking
  - `POST /api/bookings/<id>/confirm` - Confirm after payment
  - `GET /api/bookings/my` - View my bookings
- **Features**:
  - Razorpay payment gateway
  - SMS/Email notifications (Twilio integration ready)
  - Automatic room capacity update
  - Revenue tracking

### 5. **Mess Menu Calendar**
- **What**: Weekly mess menu with image uploads
- **API Endpoints**:
  - `GET /api/mess-menu/<room_id>` - Get weekly menu
  - `POST /api/mess-menu/add` - Add menu item (owners only)
- **Features**:
  - Day-wise and meal-wise organization
  - Image upload support
  - Organized by breakfast/lunch/dinner

### 6. **Safety Audit Scoring (10-Point Checklist)**
- **What**: Safety score out of 10 for each property
- **Checklist Items**:
  1. Fire Extinguisher
  2. Emergency Exit
  3. First Aid Kit
  4. CCTV Coverage
  5. Security Guard
  6. Smoke Detector
  7. Well-Lit Area
  8. Gated Community
  9. Women-Friendly
  10. Police Verification
- **API Endpoints**:
  - `GET /api/safety-audit/<room_id>` - Get safety score
  - `POST /api/safety-audit/update` - Update audit (owners only)
- **Features**:
  - Visual score badges (high/medium/low)
  - Automatic score calculation
  - Detailed breakdown

### 7. **AI Roommate Matching**
- **What**: Tag-based compatibility matching
- **Tags**: early_bird, night_owl, introvert, extrovert, vegetarian, etc.
- **API Endpoints**:
  - `GET /api/profile-tags/my` - Get my tags
  - `POST /api/profile-tags/update` - Update profile tags
  - `GET /api/roommate-match` - Find compatible roommates
- **Features**:
  - Compatibility score (percentage)
  - Top 10 matches
  - Shared tag highlighting
  - Budget and lifestyle filtering

### 8. **Progressive Web App (PWA)**
- **What**: Installable app with offline support
- **Files**:
  - `/static/manifest.json` - PWA manifest
  - `/static/service-worker.js` - Service worker
- **Features**:
  - Install prompt
  - Offline caching of last 50 listings
  - Background sync for bookings
  - Push notifications for flash deals
  - Native app experience

### 9. **Voice Search Widget**
- **What**: Voice-powered search using Web Speech API
- **Browser Support**: Chrome, Edge (Speech Recognition API)
- **Features**:
  - Floating microphone button
  - Real-time transcript to search
  - Visual listening indicator
  - Auto-execute search
  - Fallback for unsupported browsers

### 10. **Carbon Savings Calculator**
- **What**: Environmental impact comparison
- **Calculation**: Shared vs individual housing CO₂ savings
- **Metrics**:
  - Electricity savings
  - Water savings
  - Transport savings
  - Trees equivalent
- **Function**: `calculateCarbonSavings(roomType)`
- **Display**: `displayCarbonSavings(containerId)`

---

## 💰 Revenue Streams

### 1. **Subscription Revenue**
- Owner Pro: ₹199/month per owner
- Tracked in: `Analytics` table with metric_type = "subscription_revenue"

### 2. **Flash Deal Fees**
- ₹29 per flash deal
- Tracked in: `Analytics` table with metric_type = "flash_deal_revenue"

### 3. **Booking Fees**
- 2% of ₹999 booking amount = ₹19.98
- Tracked in: `Analytics` table with metric_type = "booking_fee"

### 4. **Future Revenue Opportunities**
- Banner ads (planned)
- Sponsored coupons (model exists)
- Lead-gen CSV exports (planned)
- Wallet withdrawal fees (3%)

---

## 📊 Admin Dashboard

### Revenue Analytics
- **Monthly Revenue Breakdown**: Shows all revenue streams
- **Active Subscriptions**: Count of Owner Pro subscribers
- **Active Flash Deals**: Real-time flash deals count
- **Total Bookings**: All bookings (pending + confirmed)
- **Wallet Balances**: Total student wallet credits

### Metrics Displayed
- Total revenue (this month)
- Subscription revenue + count
- Flash deal revenue + count
- Booking fees + count
- Active subscriptions
- Active flash deals
- Total/confirmed bookings
- Total wallet balance
- User statistics
- Listing statistics

---

## 🔧 Database Models

### New Tables
1. **FlashDeal** - Flash deal records
2. **ProfileTag** - Roommate matching tags
3. **Subscription** - Owner Pro subscriptions
4. **Referral** - Referral tracking
5. **Coupon** - Discount coupons
6. **Wallet** - Student wallet balances
7. **WalletTransaction** - Transaction history
8. **MessMenu** - Mess menu items
9. **SafetyAudit** - Safety checklist scores
10. **Booking** - Booking records
11. **Analytics** - Revenue analytics

---

## 🎨 UI/UX Features

### Visual Elements
- **Pulsing Flash Deal Markers**: Animated red markers with pulse effect
- **Voice Search Button**: Floating red button with pulse animation when listening
- **PWA Install Button**: Top-right prompt for app installation
- **Pro Badges**: Gold gradient badges for Owner Pro
- **Safety Score Badges**: Color-coded (green/yellow/red)
- **Compatibility Scores**: Percentage-based roommate matching
- **Carbon Calculator**: Green gradient with tree emoji
- **Wallet Display**: Blue gradient balance card
- **Transaction History**: Color-coded credit/debit items

### Animations
- Pulse effect for flash deals (`@keyframes pulse-deal`)
- Voice button animation (`@keyframes pulse-voice`)
- Hover transforms on cards
- Smooth transitions on all interactive elements

---

## 🔌 Integration Points

### Payment Gateways
- **Stripe**: For subscriptions (₹199/mo)
  - TODO: Add Stripe API keys to `.env`
  - Create test products and price IDs
  
- **Razorpay**: For bookings (₹999)
  - TODO: Add Razorpay API keys to `.env`
  - Implement webhook handlers

### Notification Services
- **Twilio**: For SMS/Email notifications
  - TODO: Add Twilio credentials to `.env`
  - Configure sender phone/email

### Maps
- **OpenStreetMap** (Leaflet.js): Already integrated
  - Flash deal markers with custom icons
  - Room location markers

---

## 📱 API Documentation

### Flash Deals
```
GET /api/flash-deals
Response: { deals: [...], count: number }

POST /api/flash-deals/create
Body: { room_id, deal_price }
Response: { success, deal, message }

POST /api/flash-deals/<id>/deactivate
Response: { success, message }
```

### Subscriptions
```
POST /api/subscriptions/create
Response: { success, subscription, message }

GET /api/subscriptions/my
Response: { has_subscription, subscription }
```

### Referrals & Wallet
```
GET /api/referrals/my-code
Response: { referral_code, total_referrals }

POST /api/referrals/apply
Body: { referral_code }
Response: { success, message, wallet_balance }

GET /api/wallet/balance
Response: { balance, student_id }

GET /api/wallet/transactions
Response: { transactions: [...] }
```

### Bookings
```
POST /api/bookings/create
Body: { room_id }
Response: { success, booking, message }

POST /api/bookings/<id>/confirm
Body: { razorpay_payment_id }
Response: { success, message }

GET /api/bookings/my
Response: { bookings: [...] }
```

### Mess Menu
```
GET /api/mess-menu/<room_id>
Response: { menu: { day: { meal_type: { text, image } } } }

POST /api/mess-menu/add
Form Data: { room_id, day_of_week, meal_type, menu_text, menu_image }
Response: { success, message }
```

### Safety Audit
```
GET /api/safety-audit/<room_id>
Response: { score, details: {...} }

POST /api/safety-audit/update
Body: { room_id, fire_extinguisher, emergency_exit, ... }
Response: { success, score, message }
```

### Roommate Matching
```
GET /api/profile-tags/my
Response: { tags: [...] }

POST /api/profile-tags/update
Body: { tags: [...] }
Response: { success, message }

GET /api/roommate-match
Response: { matches: [{ id, name, compatibility_score, ... }] }
```

---

## 🚧 TODO / Next Steps

1. **Payment Integration**
   - Add Stripe test/live API keys
   - Implement Stripe subscription webhooks
   - Add Razorpay order creation
   - Implement Razorpay payment verification

2. **Notifications**
   - Configure Twilio for SMS/Email
   - Create email templates
   - Implement booking confirmation emails
   - Add flash deal expiry reminders

3. **PWA Icons**
   - Create 192x192 and 512x512 app icons
   - Add favicon.ico
   - Create badge-72.png for notifications

4. **Additional Features**
   - Banner ad management
   - Coupon redemption UI
   - Lead-gen CSV export
   - Advanced analytics charts
   - User reviews and ratings

5. **Testing**
   - Test all payment flows
   - Test voice search across browsers
   - Test PWA installation
   - Test offline functionality
   - Load testing for flash deals

---

## 📝 Notes for Development

- All payment integrations are currently MOCKED for development
- Replace mock payment IDs with real Stripe/Razorpay integration
- Service worker requires HTTPS in production
- Voice search requires user permission for microphone
- PWA manifest needs real icon files
- Analytics table auto-populates on transactions

---

## 🎯 Key Selling Points

1. **Zero Broker Fees** - Direct owner-student connection
2. **24hr Flash Deals** - Time-limited discounts
3. **AI Roommate Matching** - Tag-based compatibility
4. **Safety First** - 10-point safety scoring
5. **Partial Payments** - Book with just ₹999
6. **Referral Rewards** - ₹200 for you and your friend
7. **PWA Experience** - Install like a native app
8. **Voice Search** - Hands-free browsing
9. **Eco-Friendly** - See your carbon savings
10. **Transparent Pricing** - No hidden fees

---

## 📞 Support & Documentation

For issues or questions:
- Check this documentation first
- Review API endpoint comments in `app.py`
- Check browser console for errors
- Verify database migrations ran successfully
- Ensure all required environment variables are set

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Framework**: Flask 3.0.0  
**Database**: SQLite (development) / PostgreSQL (production recommended)
