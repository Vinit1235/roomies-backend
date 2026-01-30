# Google OAuth Setup Guide for Roomies

## Overview
This guide will help you configure Google OAuth authentication for your Roomies platform. You already have Supabase OAuth working, and we'll integrate Google OAuth alongside it.

## Prerequisites
✅ You have Google OAuth Client ID and Client Secret
✅ Supabase OAuth is already configured and working

## Step 1: Add Google OAuth Credentials to `.env`

Add these lines to your `.env` file:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback
```

**For Production (Render/Heroku):**
```env
GOOGLE_REDIRECT_URI=https://your-domain.com/auth/google/callback
```

## Step 2: Configure Google Cloud Console

### 2.1 Create OAuth 2.0 Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create a new one)
3. Navigate to **APIs & Services** → **Credentials**
4. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
5. Choose **Web application**
6. Configure:
   - **Name**: Roomies OAuth
   - **Authorized JavaScript origins**:
     - `http://localhost:5000` (development)
     - `https://your-domain.com` (production)
   - **Authorized redirect URIs**:
     - `http://localhost:5000/auth/google/callback` (development)
     - `https://your-domain.com/auth/google/callback` (production)
7. Click **CREATE**
8. Copy the **Client ID** and **Client Secret**

### 2.2 Configure OAuth Consent Screen
1. Go to **OAuth consent screen**
2. Choose **External** (for public access)
3. Fill in:
   - **App name**: Roomies
   - **User support email**: your-email@gmail.com
   - **Developer contact**: your-email@gmail.com
4. Add scopes:
   - `userinfo.email`
   - `userinfo.profile`
5. Save and continue

## Step 3: Update `.env.example`

Add the Google OAuth configuration template:

```env
# Google OAuth Configuration
# Get credentials from: https://console.cloud.google.com/apis/credentials
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback
```

## Step 4: OAuth Routes Implementation

The OAuth routes need to be added to `app.py`. Here's what they do:

### `/auth/google` - Initiate Google OAuth
- Redirects user to Google's OAuth consent screen
- Passes the user's selected role (student/owner) via state parameter

### `/auth/google/callback` - Handle OAuth Response
- Receives authorization code from Google
- Exchanges code for access token
- Fetches user profile from Google
- Creates or updates user in local database
- Logs user in automatically

### `/auth/github` - Initiate GitHub OAuth (via Supabase)
- Uses existing Supabase OAuth for GitHub
- Already implemented in `utils/supabase_auth.py`

### `/auth/callback` - Handle Supabase OAuth Callback
- Handles both Google and GitHub via Supabase
- Alternative to direct Google OAuth

## Step 5: How It Works

### User Flow:
```
1. User clicks "Continue with Google" on login page
   ↓
2. User selects role (Student/Owner)
   ↓
3. Redirected to /auth/google?role=student
   ↓
4. Backend redirects to Google OAuth consent screen
   ↓
5. User authorizes Roomies app
   ↓
6. Google redirects to /auth/google/callback?code=...&state=...
   ↓
7. Backend exchanges code for access token
   ↓
8. Backend fetches user profile from Google
   ↓
9. Backend creates/updates user in database
   ↓
10. User is logged in and redirected to dashboard
```

### Database Integration:
- **Students**: Created in `students` table
- **Owners**: Created in `owners` table
- **Email**: Used as unique identifier
- **Name**: Extracted from Google profile
- **Password**: Set to random secure password (OAuth users don't need it)
- **Verified**: Automatically set to `True` (Google verifies email)

## Step 6: Testing

### Local Testing:
```bash
# 1. Start your Flask app
python app.py

# 2. Open browser to:
http://localhost:5000/login

# 3. Click "Continue with Google"

# 4. Select role (Student/Owner)

# 5. Authorize with Google account

# 6. You should be redirected to dashboard
```

### Verify in Database:
```python
# Check if user was created
from app import db, Student, Owner

# For students
student = Student.query.filter_by(email='your-google-email@gmail.com').first()
print(f"Student: {student.name}, Verified: {student.verified}")

# For owners
owner = Owner.query.filter_by(email='your-google-email@gmail.com').first()
print(f"Owner: {owner.name}, KYC: {owner.kyc_verified}")
```

## Step 7: Security Considerations

### CSRF Protection:
- State parameter includes role and random token
- Verified on callback to prevent CSRF attacks

### Token Storage:
- Access tokens are NOT stored in database
- Only user profile information is stored
- Users authenticate via Google each time

### HTTPS Requirement:
- Production MUST use HTTPS
- Google OAuth requires secure redirect URIs in production

## Step 8: Dual OAuth Strategy

You now have TWO OAuth options:

### Option 1: Direct Google OAuth (New)
- **Pros**: Full control, faster, no Supabase dependency
- **Cons**: Need to manage OAuth flow yourself
- **Routes**: `/auth/google`, `/auth/google/callback`

### Option 2: Supabase OAuth (Existing)
- **Pros**: Handles multiple providers (Google, GitHub), managed service
- **Cons**: Requires Supabase configuration, extra dependency
- **Routes**: `/auth/google` (via Supabase), `/auth/callback`

**Recommendation**: Use **Direct Google OAuth** for simplicity and speed.

## Step 9: Environment Variables Summary

Your `.env` should now have:

```env
# Core
SECRET_KEY=dev-secret-key-123
DATABASE_URL=sqlite:///roomies.db

# Google OAuth (NEW)
GOOGLE_CLIENT_ID=your_actual_client_id
GOOGLE_CLIENT_SECRET=your_actual_client_secret
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback

# Supabase OAuth (EXISTING - Optional)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key
OAUTH_REDIRECT_URL=http://localhost:5000/auth/callback

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=viniit881@gmail.com
MAIL_PASSWORD=hfmk tzsc ypxs oryi

# Razorpay
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret

# Google Maps
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# Gemini AI
GEMINI_API_KEY=AIzaSyDEfTw-zxJl4XMWITAkCavYmgWUFrQy42c
```

## Step 10: Troubleshooting

### Error: "redirect_uri_mismatch"
**Solution**: Ensure the redirect URI in Google Cloud Console EXACTLY matches the one in your `.env`

### Error: "invalid_client"
**Solution**: Double-check your Client ID and Client Secret

### Error: "access_denied"
**Solution**: User cancelled OAuth flow - this is normal

### User not created in database
**Solution**: Check Flask logs for errors, ensure database is writable

### OAuth works but user not logged in
**Solution**: Check Flask-Login session configuration, ensure `SECRET_KEY` is set

## Next Steps

1. ✅ Add Google OAuth credentials to `.env`
2. ✅ Configure Google Cloud Console
3. ✅ Add OAuth routes to `app.py` (see implementation below)
4. ✅ Test locally
5. ✅ Deploy to production with HTTPS redirect URIs

## Support

If you encounter issues:
- Check Flask logs: `tail -f logs/app.log`
- Enable debug mode: `FLASK_DEBUG=1`
- Test OAuth flow step-by-step
- Verify Google Cloud Console configuration

---

**Version**: 1.0  
**Last Updated**: January 2026  
**Compatible with**: Flask 3.0+, Python 3.8+
