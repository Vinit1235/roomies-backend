# 🔐 Supabase OAuth Setup Guide for Roomies

This guide explains how to configure Google and GitHub OAuth authentication for the Roomies application using Supabase.

## Prerequisites

1. A Supabase account ([supabase.com](https://supabase.com))
2. Your Roomies project running locally or deployed on Render
3. Google Cloud Console account (for Google OAuth)
4. GitHub Developer account (for GitHub OAuth)

---

## Step 1: Get Supabase Credentials

1. Go to your Supabase project dashboard
2. Navigate to **Settings > API**
3. Copy these values:
   - **Project URL**: `https://nlhhssjsbacghfrmacru.supabase.co`
   - **anon (public) key**: Your anonymous key
   - **service_role key**: Your service role key (keep this secret!)

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
   - **Homepage URL**: `https://your-app.onrender.com` (or localhost for dev)
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

## Step 4: Configure Redirect URLs in Supabase

In Supabase Dashboard:

1. Go to **Authentication > URL Configuration**
2. **Site URL**: Set to your primary production URL
   - `https://your-app.onrender.com`
3. **Redirect URLs** (add ALL of these):
   - `http://localhost:5000/auth/callback` (for local development)
   - `https://your-app.onrender.com/auth/callback` (for Render production)

---

## Step 5: Configure Environment Variables

### Local Development (.env file)

```env
SUPABASE_URL=https://nlhhssjsbacghfrmacru.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5saGhzc2pzYmFjZ2hmcm1hY3J1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQyMjI0NTMsImV4cCI6MjA3OTc5ODQ1M30.xdN0Pn2xOQSCck4uJkrFx79W2521ECAr0oYOZwmRXg8
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5saGhzc2pzYmFjZ2hmcm1hY3J1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NDIyMjQ1MywiZXhwIjoyMDc5Nzk4NDUzfQ.ZL4rNdzFYklP_QUBLbbVLLTu40hICyg_RlihxunXPis
```

### Render.com Environment Variables

In your Render dashboard, add these environment variables:

| Variable | Value |
|----------|-------|
| `SUPABASE_URL` | `https://nlhhssjsbacghfrmacru.supabase.co` |
| `SUPABASE_ANON_KEY` | Your anon key |
| `SUPABASE_SERVICE_KEY` | Your service role key |

> **Note**: The OAuth redirect URL is auto-generated using Flask's `url_for()` with `_external=True`, so it automatically uses the correct URL (localhost or Render) based on the incoming request.

---

## Step 6: Test the Integration

### Local Testing
```bash
# Start your Flask app
flask run

# Visit http://localhost:5000/login
# Click "Continue with Google" or "Continue with GitHub"
```

### Production Testing (Render)
1. Deploy your app to Render
2. Visit `https://your-app.onrender.com/login`
3. Test both Google and GitHub login buttons

---

## Environment Variables Summary

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | ✅ | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | ✅ | Public anonymous key for auth |
| `SUPABASE_SERVICE_KEY` | ❌ | Service role key (for admin operations) |

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
- Check that `SUPABASE_ANON_KEY` is set in your environment
- Verify the env variable names are exactly correct

### "Redirect URI mismatch"
- Ensure your Render URL is added to Supabase's Redirect URLs list
- The callback URL format is: `https://your-app.onrender.com/auth/callback`

### User not created after OAuth
- Check Flask/Render logs for errors
- Ensure your database is properly connected
- Verify the email is not already registered

### OAuth works locally but not on Render
1. Check Render environment variables are set
2. Verify Supabase redirect URLs include your Render domain
3. Check Render logs for specific error messages

---

## Security Notes

1. **Never commit `.env` files** - They contain secrets
2. **Use HTTPS in production** - Render provides this automatically
3. **Add Render URL to Supabase** - Both in providers and redirect URLs
4. **The anon key is safe to expose** - It's designed for client-side use

---

## Render.com Deployment Checklist

- [ ] Add `SUPABASE_URL` to Render environment variables
- [ ] Add `SUPABASE_ANON_KEY` to Render environment variables  
- [ ] Add `SUPABASE_SERVICE_KEY` to Render environment variables (optional)
- [ ] Add Render callback URL to Supabase redirect URLs
- [ ] Enable Google OAuth in Supabase (with Google credentials)
- [ ] Enable GitHub OAuth in Supabase (with GitHub credentials)
- [ ] Test login flow on deployed app

---

## Files Modified/Created

1. `utils/supabase_auth.py` - Supabase OAuth service (HTTP-based, no extra packages)
2. `app.py` - Added OAuth routes
3. `templates/login.html` - Added OAuth buttons
4. `templates/signup.html` - Added OAuth buttons
5. `.env.example` - Added Supabase environment variables
6. `OAUTH_SETUP.md` - This documentation file
