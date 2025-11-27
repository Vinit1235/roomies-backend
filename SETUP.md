# Roomies - Quick Setup Guide

## Prerequisites
- Python 3.10 or higher
- pip package manager
- Web browser (Chrome/Edge recommended for voice search)

## Installation Steps

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Initialize Database
The database will auto-initialize on first run. Tables will be created automatically.

### 3. Run the Application
```powershell
python app.py
```

The app will start at: `http://127.0.0.1:5000`

### 4. Admin Access
Default admin account:
- Email: `admin@roomies.com`
- Password: `admin123`

Access admin panel: `http://127.0.0.1:5000/admin/login`

## Features Overview

### For Students
- ✅ Browse verified rooms with map view
- ✅ Voice search support
- ✅ Flash deals (24hr limited offers)
- ✅ Roommate matching with AI
- ✅ Referral rewards (₹200)
- ✅ Wallet system for credits
- ✅ Book rooms with ₹999 advance
- ✅ Safety scoring (10-point checklist)
- ✅ PWA - Install as mobile app

### For Owners
- ✅ List properties with KYC
- ✅ Create flash deals (₹29 fee)
- ✅ Owner Pro subscription (₹199/mo)
- ✅ Mess menu management
- ✅ Safety audit updates
- ✅ Booking management

### For Admins
- ✅ Revenue analytics dashboard
- ✅ User management
- ✅ Listing approval workflow
- ✅ Contact message handling
- ✅ Real-time statistics

## Testing the Features

### 1. Test Flash Deals
- Login as owner
- Navigate to your listings
- Create a flash deal with discounted price
- Check explore page - see pulsing red marker on map

### 2. Test Referrals
- Login as student
- Get your referral code: `/api/referrals/my-code`
- Share with friend
- Friend uses code during signup
- Both get ₹200 wallet credit

### 3. Test Voice Search
- Go to explore page
- Click the red microphone button (bottom-right)
- Allow microphone access
- Say "Andheri" or "2BHK"
- See search results update

### 4. Test PWA
- Open app in Chrome/Edge
- Look for install prompt (or "Install App" button top-right)
- Install as app
- Use offline (cached last 50 listings)

### 5. Test Roommate Matching
- Login as student
- Update profile tags: `/api/profile-tags/update`
  ```json
  { "tags": ["early_bird", "vegetarian", "introvert"] }
  ```
- View matches: `/api/roommate-match`
- See compatibility scores

### 6. Test Bookings
- Login as student
- Select a room
- Book with ₹999 advance
- Complete payment (mock)
- Check booking status

## API Testing with cURL

### Get Flash Deals
```powershell
curl http://127.0.0.1:5000/api/flash-deals
```

### Get Wallet Balance (requires auth)
```powershell
curl http://127.0.0.1:5000/api/wallet/balance -b cookies.txt
```

### Create Flash Deal (requires owner auth)
```powershell
curl -X POST http://127.0.0.1:5000/api/flash-deals/create `
  -H "Content-Type: application/json" `
  -d '{"room_id": 1, "deal_price": 8000}' `
  -b cookies.txt
```

## Environment Variables (Optional)

Create `.env` file for production:
```env
# Flask
FLASK_ENV=production
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost/roomies

# Stripe
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...

# Razorpay
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...

# Twilio
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+91...
```

## Database Schema

All tables auto-create on startup:
- `students` - Student accounts
- `owners` - Owner accounts
- `admins` - Admin accounts
- `rooms` - Property listings
- `flash_deals` - 24hr deals
- `subscriptions` - Owner Pro
- `referrals` - Referral tracking
- `wallets` - Student wallets
- `wallet_transactions` - Transaction history
- `bookings` - Room bookings
- `profile_tags` - Roommate tags
- `mess_menus` - Mess calendars
- `safety_audits` - Safety scores
- `coupons` - Discount codes
- `analytics` - Revenue tracking
- `contact_messages` - Contact form

## Troubleshooting

### Voice Search Not Working
- Check browser compatibility (Chrome/Edge)
- Ensure HTTPS or localhost (required for mic access)
- Check browser console for errors

### PWA Not Installing
- Must be served over HTTPS (or localhost)
- Check manifest.json is accessible
- Verify service worker registered

### Flash Deals Not Showing
- Check deal is active and not expired
- Verify room has lat/lng coordinates
- Check browser console for JS errors

### Payment Integration
- Current implementation is MOCKED
- Add real Stripe/Razorpay keys for production
- Implement webhook handlers

## Next Steps

1. **Customize Branding**
   - Update `/static/manifest.json` with your app name
   - Create app icons (192x192, 512x512)
   - Update color theme in CSS variables

2. **Configure Payments**
   - Get Stripe test keys from dashboard.stripe.com
   - Get Razorpay keys from dashboard.razorpay.com
   - Update `.env` file

3. **Setup Notifications**
   - Create Twilio account
   - Configure SMS/Email templates
   - Update booking confirmation logic

4. **Deploy to Production**
   - Use PostgreSQL instead of SQLite
   - Set FLASK_ENV=production
   - Configure HTTPS
   - Add proper SECRET_KEY
   - Enable service worker

## Support

For detailed feature documentation, see `FEATURES.md`

For API documentation, check inline comments in `app.py`

---

**Happy Building! 🚀**
