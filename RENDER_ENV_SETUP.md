# Render.com Environment Variables Setup Guide

## 🔐 Security First
**NEVER commit `.env` files to GitHub!** Instead, set environment variables directly in Render's dashboard.

---

## 📋 Step-by-Step Instructions

### 1. Access Render Dashboard
1. Go to https://dashboard.render.com/
2. Login with your account
3. Select your **roomies-demo** web service

### 2. Navigate to Environment Tab
- Click on your service name
- Click **"Environment"** in the left sidebar
- Scroll to **"Environment Variables"** section

### 3. Add Required Environment Variables

Click **"Add Environment Variable"** for each of these:

#### Core Application Settings
```
SECRET_KEY=your-random-secret-key-generate-new-one
DATABASE_URL=postgresql://user:password@host/dbname
```
> **Note:** If using Render PostgreSQL, `DATABASE_URL` is auto-populated

#### Google Services (Generate NEW keys!)
```
GEMINI_API_KEY=AIzaSy[your-new-key-here]
GOOGLE_MAPS_API_KEY=AIzaSy[your-new-key-here]
```
- Get Gemini Key: https://aistudio.google.com/app/apikey
- Get Maps Key: https://console.cloud.google.com/apis/credentials

#### Email Configuration (Gmail SMTP)
```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=xxxx xxxx xxxx xxxx
```
- **IMPORTANT:** Use a NEW Gmail App Password
- Generate here: https://myaccount.google.com/apppasswords
- Enable 2-Step Verification first if not already enabled

#### Payment Gateway (Razorpay)
```
RAZORPAY_KEY_ID=rzp_test_or_live_key
RAZORPAY_KEY_SECRET=your_razorpay_secret
```
- Get from: https://dashboard.razorpay.com/app/keys

---

## 🔄 After Adding Variables

1. **Save** - Render automatically saves each variable
2. **Deploy** - Render will auto-redeploy your service
3. **Wait** - Deployment takes 2-5 minutes
4. **Verify** - Check logs for any errors

---

## ✅ Verification Checklist

After deployment, verify everything works:

- [ ] App starts without errors (check Render logs)
- [ ] Database connection works
- [ ] Email sending works (test password reset)
- [ ] Google Maps integration works
- [ ] Payment gateway works (if applicable)
- [ ] API calls to Gemini work

---

## 🚨 Security Reminders

### DO:
✅ Generate NEW API keys after the leak
✅ Use strong, unique SECRET_KEY
✅ Keep credentials only in Render dashboard
✅ Regularly rotate sensitive credentials
✅ Use `.env.example` for documentation

### DON'T:
❌ Commit `.env` to GitHub
❌ Share credentials in chat/email
❌ Reuse leaked credentials
❌ Use production keys in development

---

## 🔧 Troubleshooting

### App won't start after adding variables?
1. Check Render logs: Dashboard → Logs tab
2. Verify variable names match exactly (case-sensitive)
3. Check for typos in values
4. Ensure no extra quotes around values

### Environment variable not working?
- Render variables don't need quotes
- Just paste the raw value
- Example: `smtp.gmail.com` not `"smtp.gmail.com"`

### Need to update a variable?
1. Go to Environment tab
2. Click the pencil icon next to the variable
3. Update the value
4. Save (auto-redeploys)

---

## 📞 Support Resources

- **Render Docs:** https://render.com/docs/environment-variables
- **Gmail App Passwords:** https://support.google.com/accounts/answer/185833
- **Gemini API:** https://ai.google.dev/gemini-api/docs/api-key

---

## 📌 Quick Commands for Local Development

To run locally, make sure your `.env` file is properly configured:

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your LOCAL credentials
# (Use different credentials than production!)

# Run the app
python app.py
```

Remember: **Local `.env` ≠ Production Render variables**
Keep them separate for security!
