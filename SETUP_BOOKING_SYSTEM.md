# 🚀 Booking System Setup Guide

## Prerequisites
- Python 3.8+
- Flask application running
- Gmail account (for email notifications)

---

## 📦 Installation

### Step 1: Install Required Package
```bash
pip install reportlab
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

---

## 🔧 Configuration

### Step 2: Update Environment Variables

Edit your `.env` file and add email configuration:

```env
# Email Configuration (Gmail SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your_app_password_here
EMAIL_FROM=Roomies Platform <noreply@roomies.in>

# Application URL (for email links)
APP_URL=http://localhost:5000

# Razorpay Configuration (Optional - for production)
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
```

---

### Step 3: Generate Gmail App Password

1. Go to your **Google Account** → [Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** (if not already enabled)
3. Go to **App Passwords** section
4. Select **Mail** and **Windows Computer** (or other device)
5. Click **Generate**
6. Copy the **16-character password** (format: xxxx xxxx xxxx xxxx)
7. Paste it in `.env` as `EMAIL_PASSWORD` (remove spaces)

**Example:**
```env
EMAIL_USER=roomies.platform@gmail.com
EMAIL_PASSWORD=abcd efgh ijkl mnop  # Your actual app password
```

---

## 🗄️ Database Migration

### Step 4: Run Migration Script

This adds new columns to the `bookings` table:

```bash
python migrations/migrate_booking_system.py
```

**Expected Output:**
```
Starting database migration...
✅ Added column: security_deposit
✅ Added column: monthly_rent
✅ Added column: platform_fee
... (30+ columns)

✅ Migration completed! Added 32 new columns.
```

---

## ✅ Verify Setup

### Step 5: Check Directory Structure

Ensure these folders exist (auto-created on first run):
```
roomies-demo/
├── static/
│   └── contracts/       # Generated PDFs
├── utils/
│   ├── email_service.py      # Email notifications
│   └── contract_generator.py # PDF contracts
└── migrations/
    └── migrate_booking_system.py
```

---

## 🧪 Testing the System

### Step 6: Test Email Functionality

Create a simple test script (`test_email.py`):

```python
import os
from dotenv import load_dotenv
load_dotenv()

from utils.email_service import email_service

# Test email
result = email_service.send_email(
    to_email="your-email@gmail.com",
    subject="Roomies Test Email",
    html_content="<h1>Email system working!</h1><p>This is a test email from Roomies.</p>"
)

if result:
    print("✅ Email sent successfully!")
else:
    print("❌ Email failed to send. Check your .env configuration.")
```

Run:
```bash
python test_email.py
```

---

### Step 7: Test Complete Booking Flow

#### As Student:
1. **Create booking:**
```bash
curl -X POST http://localhost:5000/api/bookings/create \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": 1,
    "move_in_date": "2024-08-01",
    "contract_duration_months": 11
  }'
```

2. **Pay booking fee (₹999):**
```bash
curl -X POST http://localhost:5000/api/bookings/1/pay-booking-fee \
  -H "Content-Type: application/json" \
  -d '{
    "razorpay_payment_id": "pay_test123",
    "razorpay_signature": "signature123"
  }'
```

3. **Check owner's email** - Should receive booking request

#### As Owner:
4. **Approve booking:**
```bash
curl -X POST http://localhost:5000/api/bookings/1/owner-approve \
  -H "Content-Type: application/json" \
  -d '{
    "approved": true
  }'
```

5. **Check student's email** - Should receive approval notification

#### As Student (again):
6. **Complete payment:**
```bash
curl -X POST http://localhost:5000/api/bookings/1/complete-payment \
  -H "Content-Type: application/json" \
  -d '{
    "razorpay_payment_id": "pay_final456",
    "razorpay_signature": "signature456"
  }'
```

7. **Check both emails** - Student gets confirmation, Owner gets payment notice
8. **Check `static/contracts/`** - PDF should be generated

---

## 🎯 Email Templates Overview

Your system will send these emails automatically:

| Trigger | Recipient | Subject | Purpose |
|---------|-----------|---------|---------|
| Student pays ₹999 | **Owner** | "🏠 New Booking Request" | Notify about new request |
| Student pays ₹999 | **Student** | "Booking Request Sent" | Confirmation of submission |
| Owner approves | **Student** | "✅ Owner Approved!" | Request to complete payment |
| Owner rejects | **Student** | "Booking Update" | Rejection + refund info |
| Full payment done | **Student** | "🎉 Booking Confirmed" | Payment confirmation + contract |
| Full payment done | **Owner** | "💰 Payment Received" | Payment notification |
| Contract ready | **Both** | "📄 Sign Your Rental Agreement" | Contract signing |

---

## 🔍 Troubleshooting

### Email Not Sending?

**Check 1: SMTP Connection**
```python
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@gmail.com', 'your_app_password')
print("✅ SMTP connection successful!")
server.quit()
```

**Check 2: Firewall/Antivirus**
- Ensure port 587 is not blocked
- Temporarily disable firewall to test

**Check 3: Gmail Settings**
- Verify 2FA is enabled
- Regenerate App Password if needed
- Check "Less secure app access" (should be OFF when using App Password)

---

### PDF Not Generating?

**Check 1: ReportLab Installation**
```bash
pip install reportlab --upgrade
```

**Check 2: Directory Permissions**
```bash
# Windows
icacls "static/contracts" /grant Users:F

# Linux/Mac
chmod 777 static/contracts
```

**Check 3: Test PDF Generation**
```python
from utils.contract_generator import contract_generator
print("✅ Contract generator imported successfully!")
```

---

### Database Errors?

**Solution: Recreate Database**
```bash
# Backup existing data
python export_to_excel.py

# Delete old database
rm roomies.db

# Reinitialize
python setup_db.py
python populate_real_data.py

# Run migration
python migrations/migrate_booking_system.py
```

---

## 🔐 Security Best Practices

1. **Never commit `.env` to Git**
```bash
# Add to .gitignore
echo ".env" >> .gitignore
```

2. **Use Environment Variables in Production**
- Heroku: Use Config Vars
- AWS: Use Secrets Manager
- Docker: Use secrets

3. **Enable HTTPS in Production**
- Update `APP_URL` to `https://yourdomain.com`

4. **Rate Limiting** (Add to `app.py`):
```python
from flask_limiter import Limiter

limiter = Limiter(
    app=app,
    key_func=lambda: request.remote_addr,
    default_limits=["200 per day", "50 per hour"]
)

@app.route("/api/bookings/create", methods=["POST"])
@limiter.limit("10 per hour")  # Max 10 bookings per hour
def create_booking():
    # ... existing code
```

---

## 📊 Monitoring & Logs

### Enable Detailed Logging
Add to `app.py`:
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/booking_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

### Track Email Delivery
Check `logs/booking_system.log` for:
```
2024-01-15 10:30:45 - Email sent successfully to owner@example.com
2024-01-15 10:31:12 - Contract generated: /static/contracts/Rental_Agreement_123.pdf
```

---

## 🎉 You're All Set!

Your booking system is now fully configured with:
- ✅ Automated email notifications
- ✅ PDF contract generation
- ✅ Owner-student communication flow
- ✅ Payment tracking
- ✅ Refund management
- ✅ Digital signatures

### Next Steps:
1. Test the complete flow end-to-end
2. Customize email templates (in `utils/email_service.py`)
3. Integrate production payment gateway (Razorpay)
4. Deploy to production server
5. Monitor logs for any issues

---

## 📞 Support

Need help? 
- 📧 Email: support@roomies.in
- 📖 Documentation: See `BOOKING_SYSTEM_GUIDE.md`
- 🐛 Issues: GitHub Issues

**Happy Booking! 🏠**
