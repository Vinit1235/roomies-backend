# 🚀 Google OAuth Setup for Render Deployment

## 📋 Quick Reference

### Local Development (.env file)
```env
GOOGLE_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abcdefghijklmnopqrstuvwxyz
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback
```

### Production (Render Environment Variables)
```
GOOGLE_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abcdefghijklmnopqrstuvwxyz
GOOGLE_REDIRECT_URI=https://your-app-name.onrender.com/auth/google/callback
```

---

## 🔧 Step-by-Step Setup

### Part 1: Local Development (.env file)

1. **Open your `.env` file** in the Roomies project
2. **Find these lines** (around line 20-24):
   ```env
   # Google OAuth Configuration
   # ⬇️ PASTE YOUR GOOGLE CLIENT ID HERE (replace the text below)
   GOOGLE_CLIENT_ID=your_google_client_id_here
   # ⬇️ PASTE YOUR GOOGLE CLIENT SECRET HERE (replace the text below)
   GOOGLE_CLIENT_SECRET=your_google_client_secret_here
   # ⬇️ For local development, keep this as is. For Render, change to your production URL
   GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback
   ```

3. **Replace the placeholder values**:
   ```env
   GOOGLE_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=GOCSPX-abcdefghijklmnopqrstuvwxyz
   GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback
   ```
   
   ⚠️ **Important**: 
   - Your Client ID will look like: `123456789-xxxxx.apps.googleusercontent.com`
   - Your Client Secret will look like: `GOCSPX-xxxxxxxxxxxxx`
   - Keep the redirect URI as `http://localhost:5000/auth/google/callback` for local testing

4. **Save the file**

---

### Part 2: Render Environment Variables

#### Option A: Via Render Dashboard (Recommended)

1. **Go to your Render dashboard**: https://dashboard.render.com/
2. **Select your Roomies web service**
3. **Click "Environment" in the left sidebar**
4. **Click "Add Environment Variable"** button
5. **Add these THREE variables one by one**:

   **Variable 1:**
   - **Key**: `GOOGLE_CLIENT_ID`
   - **Value**: `123456789-abcdefghijklmnop.apps.googleusercontent.com` (your actual Client ID)
   - Click "Save"

   **Variable 2:**
   - **Key**: `GOOGLE_CLIENT_SECRET`
   - **Value**: `GOCSPX-abcdefghijklmnopqrstuvwxyz` (your actual Client Secret)
   - Click "Save"

   **Variable 3:**
   - **Key**: `GOOGLE_REDIRECT_URI`
   - **Value**: `https://your-app-name.onrender.com/auth/google/callback`
   - ⚠️ **Replace `your-app-name`** with your actual Render app name
   - Click "Save"

6. **Render will automatically redeploy** your app with the new environment variables

#### Option B: Via render.yaml (Alternative)

If you're using a `render.yaml` file for infrastructure as code:

```yaml
services:
  - type: web
    name: roomies-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: roomies-db
          property: connectionString
      - key: GOOGLE_CLIENT_ID
        value: 123456789-abcdefghijklmnop.apps.googleusercontent.com
      - key: GOOGLE_CLIENT_SECRET
        sync: false  # Mark as secret
      - key: GOOGLE_REDIRECT_URI
        value: https://your-app-name.onrender.com/auth/google/callback
```

---

## 🔐 Google Cloud Console Configuration

### You Need TWO Sets of Redirect URIs

In your Google Cloud Console OAuth credentials, add BOTH:

#### Authorized JavaScript Origins:
```
http://localhost:5000
https://your-app-name.onrender.com
```

#### Authorized Redirect URIs:
```
http://localhost:5000/auth/google/callback
https://your-app-name.onrender.com/auth/google/callback
```

### How to Add Them:

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Click on your OAuth 2.0 Client ID
3. Under **Authorized JavaScript origins**, click **+ ADD URI**:
   - Add: `http://localhost:5000`
   - Add: `https://your-app-name.onrender.com`
4. Under **Authorized redirect URIs**, click **+ ADD URI**:
   - Add: `http://localhost:5000/auth/google/callback`
   - Add: `https://your-app-name.onrender.com/auth/google/callback`
5. Click **SAVE**

---

## 📝 Complete Environment Variables Checklist

### Local (.env file) ✅
```env
SECRET_KEY=dev-secret-key-123
DATABASE_URL=sqlite:///roomies.db
GEMINI_API_KEY=AIzaSyDEfTw-zxJl4XMWITAkCavYmgWUFrQy42c

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=viniit881@gmail.com
MAIL_PASSWORD=hfmk tzsc ypxs oryi

# Razorpay Configuration
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret

# Google Maps
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# Google OAuth Configuration
GOOGLE_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abcdefghijklmnopqrstuvwxyz
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback
```

### Render (Environment Variables) ✅
```
SECRET_KEY=<auto-generated by Render>
DATABASE_URL=<from your PostgreSQL database>
GEMINI_API_KEY=AIzaSyDEfTw-zxJl4XMWITAkCavYmgWUFrQy42c

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=viniit881@gmail.com
MAIL_PASSWORD=hfmk tzsc ypxs oryi

# Razorpay Configuration
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret

# Google Maps
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# Google OAuth Configuration (NEW - ADD THESE)
GOOGLE_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abcdefghijklmnopqrstuvwxyz
GOOGLE_REDIRECT_URI=https://your-app-name.onrender.com/auth/google/callback
```

---

## 🧪 Testing

### Test Locally:
```bash
# 1. Make sure your .env has the credentials
# 2. Start your Flask app
python app.py

# 3. Open browser
http://localhost:5000/login

# 4. Click "Continue with Google"
# 5. You should see Google's OAuth consent screen
```

### Test on Render:
```bash
# 1. Deploy to Render (with environment variables set)
# 2. Open your Render URL
https://your-app-name.onrender.com/login

# 3. Click "Continue with Google"
# 4. You should see Google's OAuth consent screen
```

---

## 🚨 Common Issues & Solutions

### Issue 1: "redirect_uri_mismatch"
**Cause**: The redirect URI in your request doesn't match Google Cloud Console

**Solution**: 
- Check that `GOOGLE_REDIRECT_URI` in Render matches EXACTLY what's in Google Cloud Console
- Make sure you added `https://your-app-name.onrender.com/auth/google/callback` to Google Cloud Console

### Issue 2: "invalid_client"
**Cause**: Wrong Client ID or Client Secret

**Solution**:
- Double-check you copied the FULL Client ID (including `.apps.googleusercontent.com`)
- Double-check you copied the FULL Client Secret (including `GOCSPX-` prefix)
- Make sure there are no extra spaces

### Issue 3: OAuth works locally but not on Render
**Cause**: Forgot to add Render URL to Google Cloud Console

**Solution**:
- Add `https://your-app-name.onrender.com` to Authorized JavaScript origins
- Add `https://your-app-name.onrender.com/auth/google/callback` to Authorized redirect URIs

### Issue 4: "OAuth not configured" message
**Cause**: Environment variables not set in Render

**Solution**:
- Go to Render Dashboard → Environment
- Verify all three variables are present:
  - `GOOGLE_CLIENT_ID`
  - `GOOGLE_CLIENT_SECRET`
  - `GOOGLE_REDIRECT_URI`
- Redeploy if needed

---

## 📸 Visual Guide

### Where to Find Your Credentials:

1. **Google Cloud Console** → **APIs & Services** → **Credentials**
2. Click on your **OAuth 2.0 Client ID**
3. You'll see:
   ```
   Client ID: 123456789-abcdefghijklmnop.apps.googleusercontent.com
   Client Secret: GOCSPX-abcdefghijklmnopqrstuvwxyz
   ```
4. **Copy these EXACTLY** (including all characters)

### Where to Add in Render:

1. **Render Dashboard** → **Your Service** → **Environment**
2. Click **"Add Environment Variable"**
3. Add each variable:
   - Key: `GOOGLE_CLIENT_ID`
   - Value: `<paste your client ID>`
4. Repeat for `GOOGLE_CLIENT_SECRET` and `GOOGLE_REDIRECT_URI`

---

## ✅ Verification Checklist

Before deploying, verify:

- [ ] `.env` file has your Google Client ID
- [ ] `.env` file has your Google Client Secret
- [ ] `.env` file has `http://localhost:5000/auth/google/callback` as redirect URI
- [ ] Google Cloud Console has `http://localhost:5000/auth/google/callback` in redirect URIs
- [ ] Render has `GOOGLE_CLIENT_ID` environment variable
- [ ] Render has `GOOGLE_CLIENT_SECRET` environment variable
- [ ] Render has `GOOGLE_REDIRECT_URI` environment variable (with HTTPS and your Render URL)
- [ ] Google Cloud Console has `https://your-app-name.onrender.com/auth/google/callback` in redirect URIs
- [ ] OAuth routes are added to `app.py` (or you've run the integration)

---

## 🎯 Quick Summary

**For Local Development:**
1. Paste Client ID and Secret into `.env` file
2. Keep redirect URI as `http://localhost:5000/auth/google/callback`

**For Render Production:**
1. Add `GOOGLE_CLIENT_ID` to Render environment variables
2. Add `GOOGLE_CLIENT_SECRET` to Render environment variables
3. Add `GOOGLE_REDIRECT_URI=https://your-app-name.onrender.com/auth/google/callback` to Render environment variables
4. Add `https://your-app-name.onrender.com/auth/google/callback` to Google Cloud Console

**That's it!** 🚀

---

Need help? Check the logs:
- **Local**: Terminal output when running `python app.py`
- **Render**: Dashboard → Logs tab
