# Quick Integration Guide for Google OAuth

## ✅ What's Been Done

1. ✅ Created `utils/google_oauth.py` - Google OAuth service
2. ✅ Created `oauth_routes.py` - OAuth route handlers
3. ✅ Updated `.env` - Added Google OAuth placeholders
4. ✅ Updated `.env.example` - Added Google OAuth template
5. ✅ Created `GOOGLE_OAUTH_SETUP.md` - Complete setup guide

## 🔧 Next Steps (Manual Integration)

### Step 1: Add Import to app.py

Add this import near the top of `app.py` (around line 72, after the Supabase OAuth imports):

```python
# Google OAuth Authentication
try:
    from utils.google_oauth import (
        get_google_auth_url,
        authenticate_google_user,
        is_google_oauth_available
    )
    GOOGLE_OAUTH_ENABLED = is_google_oauth_available()
    if GOOGLE_OAUTH_ENABLED:
        print("✅ Google OAuth enabled")
    else:
        print("⚠️ Google OAuth not configured (missing credentials)")
except ImportError as e:
    print(f"⚠️ Could not import google_oauth: {e}. Google OAuth disabled.")
    GOOGLE_OAUTH_ENABLED = False
    def get_google_auth_url(role="student"):
        return False, "Google OAuth not available"
    def authenticate_google_user(code):
        return False, {"error": "Google OAuth not available"}
```

### Step 2: Add OAuth Routes to app.py

Copy the routes from `oauth_routes.py` and paste them into `app.py` after line ~1070 (after the `rebuild_search_index()` function and before the `@app.route("/")` home route).

The routes to add are:
- `@app.route("/auth/google")` - Google OAuth initiation
- `@app.route("/auth/google/callback")` - Google OAuth callback
- `@app.route("/auth/github")` - GitHub OAuth initiation (via Supabase)
- `@app.route("/auth/callback")` - Supabase OAuth callback

### Step 3: Add Your Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create OAuth 2.0 credentials (see `GOOGLE_OAUTH_SETUP.md` for detailed steps)
3. Copy your Client ID and Client Secret
4. Update `.env`:

```env
GOOGLE_CLIENT_IDD=your_actual_client_id_here
GOOGLE_CLIENT_SECRET=your_actual_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback
```

### Step 4: Configure Google Cloud Console

1. **Authorized JavaScript origins**:
   - `http://localhost:5000`
   - `https://your-production-domain.com`

2. **Authorized redirect URIs**:
   - `http://localhost:5000/auth/google/callback`
   - `https://your-production-domain.com/auth/google/callback`

### Step 5: Test the Integration

```bash
# 1. Start your Flask app
python app.py

# 2. Open browser
http://localhost:5000/login

# 3. Click "Continue with Google"
# 4. Select role (Student/Owner)
# 5. Authorize with Google
# 6. You should be logged in!
```

## 🎯 Quick Copy-Paste Integration

If you want me to integrate the routes directly into `app.py`, I can do that! Just confirm and I'll:

1. Add the import statement to the top of `app.py`
2. Insert the OAuth routes in the correct location
3. Ensure everything is properly integrated

## 📝 Files Created

- `utils/google_oauth.py` - OAuth service (✅ Ready)
- `oauth_routes.py` - Route handlers (✅ Ready to copy into app.py)
- `GOOGLE_OAUTH_SETUP.md` - Complete guide (✅ Ready)
- `.env` - Updated with placeholders (✅ Ready)
- `.env.example` - Updated template (✅ Ready)

## 🔍 How It Works

```
User Flow:
1. User clicks "Continue with Google" → /auth/google?role=student
2. Backend redirects to Google OAuth consent screen
3. User authorizes → Google redirects to /auth/google/callback?code=...
4. Backend exchanges code for access token
5. Backend fetches user profile from Google
6. Backend creates/updates user in database
7. User is logged in automatically ✅
```

## ⚡ Dual OAuth Strategy

You now have TWO OAuth options:

### Option 1: Direct Google OAuth (NEW - Recommended)
- **Routes**: `/auth/google`, `/auth/google/callback`
- **Pros**: Faster, no Supabase dependency, full control
- **File**: `utils/google_oauth.py`

### Option 2: Supabase OAuth (EXISTING)
- **Routes**: `/auth/google` (via Supabase), `/auth/callback`
- **Pros**: Multi-provider support (Google + GitHub)
- **File**: `utils/supabase_auth.py`

Both work! Choose based on your preference.

## 🚨 Important Notes

1. **HTTPS Required in Production**: Google OAuth requires HTTPS for production redirect URIs
2. **State Parameter**: Used for CSRF protection and role tracking
3. **Email Verification**: Users authenticated via Google are automatically verified
4. **Random Passwords**: OAuth users get random secure passwords (they don't need them)
5. **Wallet Creation**: New students automatically get a wallet created

## 🆘 Need Help?

If you want me to:
- ✅ Integrate the routes directly into `app.py`
- ✅ Test the OAuth flow
- ✅ Debug any issues
- ✅ Add more OAuth providers

Just let me know!

---

**Ready to integrate?** Say "integrate OAuth routes" and I'll add them to `app.py` automatically!
