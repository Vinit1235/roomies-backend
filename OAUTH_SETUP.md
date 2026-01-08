# 🔐 Supabase OAuth Setup Guide for Roomies

This guide explains how to configure Google and GitHub OAuth authentication for the Roomies application using Supabase.

## Prerequisites

1. A Supabase account ([supabase.com](https://supabase.com))
2. Your Roomies project running locally or deployed
3. Google Cloud Console account (for Google OAuth)
4. GitHub Developer account (for GitHub OAuth)

---

## Step 1: Get Supabase Credentials

1. Go to your Supabase project dashboard
2. Navigate to **Settings > API**
3. Copy these values:
   - **Project URL**: `https://your-project-ref.supabase.co`
   - **anon (public) key**: Your anonymous key
   - **service_role key**: Your service role key (keep this secret!)

4. Add these to your `.env` file:

```env
SUPABASE_URL=https://nlhhssjsbacghfrmacru.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
OAUTH_REDIRECT_URL=http://localhost:5000/auth/callback
```

---

## Step 2: Configure Google OAuth

### A. Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services > Credentials**
4. Click **Create Credentials > OAuth Client ID**
5. Choose **Web Application**
6. Set the following:
   - **Name**: Roomies OAuth
   - **Authorized JavaScript origins**: 
     - `https://nlhhssjsbacghfrmacru.supabase.co`
   - **Authorized redirect URIs**:
     - `https://nlhhssjsbacghfrmacru.supabase.co/auth/v1/callback`

7. Copy the **Client ID** and **Client Secret**

### B. Add to Supabase

1. In Supabase Dashboard, go to **Authentication > Providers**
2. Find **Google** and click **Enable**
3. Paste your:
   - **Client ID**
   - **Client Secret**
4. Click **Save**

---

## Step 3: Configure GitHub OAuth

### A. Create GitHub OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click **New OAuth App**
3. Fill in:
   - **Application name**: Roomies
   - **Homepage URL**: `http://localhost:5000` (or your production URL)
   - **Authorization callback URL**: `https://nlhhssjsbacghfrmacru.supabase.co/auth/v1/callback`

4. Click **Register application**
5. Copy the **Client ID**
6. Click **Generate a new client secret** and copy it

### B. Add to Supabase

1. In Supabase Dashboard, go to **Authentication > Providers**
2. Find **GitHub** and click **Enable**
3. Paste your:
   - **Client ID**
   - **Client Secret**
4. Click **Save**

---

## Step 4: Configure Redirect URLs

In Supabase Dashboard:

1. Go to **Authentication > URL Configuration**
2. Add your site URL:
   - **Development**: `http://localhost:5000`
   - **Production**: `https://your-render-app.onrender.com`
3. Add redirect URLs:
   - `http://localhost:5000/auth/callback`
   - `https://your-render-app.onrender.com/auth/callback`

---

## Step 5: Test the Integration

1. Install the supabase package:
   ```bash
   pip install supabase
   ```

2. Start your Flask app:
   ```bash
   flask run
   ```

3. Visit `/login` and click "Continue with Google" or "Continue with GitHub"

4. You should be redirected to the OAuth provider, then back to your app

---

## Environment Variables Summary

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_URL` | Your Supabase project URL | `https://nlhhssjsbacghfrmacru.supabase.co` |
| `SUPABASE_ANON_KEY` | Public anonymous key | `eyJhbGciOi...` |
| `SUPABASE_SERVICE_KEY` | Service role key (secret) | `eyJhbGciOi...` |
| `OAUTH_REDIRECT_URL` | Where OAuth redirects after auth | `http://localhost:5000/auth/callback` |

---

## Available OAuth Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/google` | GET | Start Google OAuth flow |
| `/auth/github` | GET | Start GitHub OAuth flow |
| `/auth/callback` | GET | OAuth callback handler |
| `/api/oauth/status` | GET | Check OAuth availability |

### Query Parameters

Both `/auth/google` and `/auth/github` accept:
- `role`: `student` or `owner` (default: `student`)

Example: `/auth/google?role=owner`

---

## Troubleshooting

### "OAuth not available" error
- Check that `SUPABASE_ANON_KEY` is set correctly
- Ensure `supabase` package is installed

### "Redirect URI mismatch"
- Verify the redirect URI in your OAuth provider matches Supabase's callback URL
- The format should be: `https://your-project.supabase.co/auth/v1/callback`

### User not created after OAuth
- Check Flask logs for errors
- Ensure your database is properly connected
- Verify the email is not already registered

---

## Security Notes

1. **Never commit `.env` files** - They contain secrets
2. **Use HTTPS in production** - OAuth requires secure connections
3. **Rotate service keys periodically** - Update in both Supabase and your app
4. **Limit OAuth scopes** - Request only necessary permissions

---

## Files Modified/Created

1. `utils/supabase_auth.py` - Supabase authentication service
2. `app.py` - Added OAuth routes
3. `templates/login.html` - Added OAuth buttons
4. `templates/signup.html` - Added OAuth buttons
5. `requirements.txt` - Added `supabase` package
6. `.env.example` - Added Supabase environment variables
7. `OAUTH_SETUP.md` - This documentation file
