# 🏠 Roomies Complete Booking System Guide

## Overview
The Roomies booking system implements a comprehensive, secure, and transparent rental booking flow with email notifications, digital contracts, and proper owner-student communication.

---

## 📋 Business Model

### Revenue Streams
1. **Booking Fee**: ₹999 (Non-refundable, paid by student)
2. **Platform Service Fee**: 2% of first month's rent
3. **Flash Deal Fee**: ₹29 per 24-hour listing boost
4. **Owner Pro Subscription**: ₹199/month

### Payment Structure
- **Booking Fee**: ₹999
- **Security Deposit**: 2× Monthly Rent (Refundable)
- **First Month Rent**: As per property listing
- **Platform Fee**: 2% of monthly rent

**Example:**
- Room Rent: ₹10,000/month
- Booking Fee: ₹999
- Security Deposit: ₹20,000
- Platform Fee: ₹200 (2% of ₹10,000)
- **Total Initial Payment: ₹31,199**

---

## 🔄 Complete Booking Flow

### **Step 1: Student Initiates Booking**
**Endpoint:** `POST /api/bookings/create`

**Request:**
```json
{
  "room_id": 1,
  "move_in_date": "2024-07-01",
  "contract_duration_months": 11
}
```

**Response:**
```json
{
  "success": true,
  "booking": {
    "id": 123,
    "booking_amount": 999.0,
    "monthly_rent": 10000.0,
    "security_deposit": 20000.0,
    "platform_fee": 200.0,
    "total_due": 31199.0,
    "razorpay_order_id": "order_booking_123_..."
  },
  "message": "Booking initiated! Pay ₹999 to send request to owner."
}
```

**Status:** `booking_status: "pending"`, `payment_status: "pending"`

---

### **Step 2: Student Pays Booking Fee (₹999)**
**Endpoint:** `POST /api/bookings/{booking_id}/pay-booking-fee`

**Request:**
```json
{
  "razorpay_payment_id": "pay_abc123...",
  "razorpay_signature": "signature..."
}
```

**What Happens:**
1. ✅ Payment verified
2. 📧 **Owner receives email notification** with student details
3. 📧 **Student receives confirmation** that request was sent
4. Status updates: `booking_status: "payment_initiated"`, `payment_status: "partial"`

**Owner Email Content:**
- Student name, college, verification status
- Property details
- Move-in date request
- Action buttons: Approve / View Details
- 24-hour response deadline

---

### **Step 3: Owner Approves/Rejects Request**
**Endpoint:** `POST /api/bookings/{booking_id}/owner-approve`

**Request:**
```json
{
  "approved": true,
  "rejection_reason": "Optional reason if rejected"
}
```

#### **If APPROVED:**
1. ✅ `booking_status: "confirmed"`
2. 📧 **Student receives email** to complete remaining payment
3. Email includes:
   - Total amount due breakdown
   - Payment deadline (48 hours)
   - Owner contact information

#### **If REJECTED:**
1. ❌ `booking_status: "cancelled"`
2. 💰 Automatic refund initiated (₹999)
3. 📧 **Student receives rejection email** with reason
4. Suggestions for similar properties

---

### **Step 4: Student Completes Full Payment**
**Endpoint:** `POST /api/bookings/{booking_id}/complete-payment`

**Request:**
```json
{
  "razorpay_payment_id": "pay_xyz789...",
  "razorpay_signature": "signature..."
}
```

**What Happens:**
1. ✅ Full payment verified (Security Deposit + Rent + Platform Fee)
2. 🏠 Room occupancy updated (`capacity_occupied += 1`)
3. 📄 **Rental agreement PDF auto-generated**
4. 📧 **Student receives**:
   - Payment confirmation
   - Digital contract for signature
   - Owner contact details
   - Move-in instructions
5. 📧 **Owner receives**:
   - Payment received notification
   - Contract signing instructions
   - Student contact details
6. Status: `booking_status: "active"`, `payment_status: "completed"`

---

### **Step 5: Digital Contract Signing**
**Endpoint:** `POST /api/bookings/{booking_id}/sign-contract`

**Request:**
```json
{
  "signature": "Student digital signature/checkbox"
}
```

**What Happens:**
1. ✅ `contract_signed: true`
2. 📧 **Owner notified** to sign contract
3. Both parties receive signed copy via email

---

## 📄 Rental Agreement (Auto-Generated PDF)

### Contract Includes:
1. **Parties**: Owner & Tenant details
2. **Property**: Full address, amenities, type
3. **Financial Terms**: Rent, deposit, fees
4. **Contract Period**: Start/end dates, duration
5. **Terms & Conditions**:
   - Rent payment schedule & late fees
   - Security deposit refund policy
   - Tenant responsibilities
   - Owner obligations
   - Termination clauses
   - Prohibited activities
   - Dispute resolution
   - Insurance requirements

### Features:
- PDF format with proper formatting
- Professional layout using ReportLab
- Signature sections for all parties
- Legally binding clauses
- Compliant with Indian rental laws

---

## 📧 Email Notifications System

### Email Types:

#### 1. **Booking Request to Owner**
- Student details with verification badge
- Property summary
- Financial breakdown
- Approve/Reject action buttons
- 24-hour response deadline

#### 2. **Owner Approval to Student**
- Congratulations message
- Payment breakdown
- Payment link/button
- 48-hour deadline
- Owner contact information

#### 3. **Owner Rejection to Student**
- Polite rejection message
- Reason (if provided)
- Refund details (5-7 business days)
- Explore similar properties link

#### 4. **Payment Confirmation to Student**
- Payment summary table
- Property & owner details
- Next steps checklist
- Contract download link
- Move-in preparation tips

#### 5. **Payment Received to Owner**
- Payment success notification
- Tenant contact information
- Contract signing instructions
- Move-in coordination reminder

#### 6. **Contract for Signature**
- Contract PDF attachment
- Review instructions
- Digital signature link
- Terms acceptance checkbox

---

## 🔒 Email Configuration

### Setup Gmail SMTP (Recommended):

1. **Update `.env` file:**
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=roomies.platform@gmail.com
EMAIL_PASSWORD=your_16_character_app_password
EMAIL_FROM=Roomies Platform <noreply@roomies.in>
```

2. **Generate Gmail App Password:**
   - Go to Google Account → Security
   - Enable 2-Factor Authentication
   - App Passwords → Select "Mail" → Generate
   - Copy 16-character password to `.env`

3. **Alternative Providers:**
   - **SendGrid**: Professional email service
   - **AWS SES**: Scalable email solution
   - **Mailgun**: Developer-friendly API

---

## 💰 Refund Policy

### Automated Refund Scenarios:

| Scenario | Refund Amount | Processing Time |
|----------|--------------|-----------------|
| Owner rejects request | Full ₹999 | 5-7 business days |
| Student cancels before approval | Full ₹999 | 5-7 business days |
| Student cancels after approval, before move-in | ₹999 - Processing fee (₹99) | 7-10 business days |
| Early termination of active contract | Security deposit - 1 month rent penalty | 30 days |
| Contract completion (no damages) | Full security deposit | 15-30 days |

---

## 📊 Booking Status Flow

```
pending (Initial creation)
    ↓
payment_initiated (₹999 paid, sent to owner)
    ↓
confirmed (Owner approved, awaiting full payment)
    ↓
active (Full payment done, contract signed)
    ↓
completed (Contract ended successfully)

Alternative flows:
pending/payment_initiated/confirmed → cancelled (Rejection or cancellation)
```

---

## 🛡️ Security Features

1. **Payment Verification**: Razorpay signature validation
2. **Authorization Checks**: User-booking ownership verification
3. **Email Notifications**: All parties kept informed
4. **Digital Contracts**: Legally binding PDF agreements
5. **Audit Trail**: Complete timestamp tracking
6. **Refund Protection**: Automated refund processing
7. **Dispute Resolution**: Platform mediation clause in contract

---

## 🎯 API Endpoints Summary

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `/api/bookings/create` | POST | Initiate booking | Student |
| `/api/bookings/{id}/pay-booking-fee` | POST | Pay ₹999 | Student |
| `/api/bookings/{id}/owner-approve` | POST | Approve/Reject | Owner |
| `/api/bookings/{id}/complete-payment` | POST | Full payment | Student |
| `/api/bookings/{id}/sign-contract` | POST | Sign agreement | Student |
| `/api/bookings/my` | GET | Student bookings | Student |
| `/api/owner/bookings` | GET | Owner's bookings | Owner |
| `/api/bookings/{id}/cancel` | POST | Cancel booking | Both |

---

## 📱 Future Enhancements

1. **SMS Notifications**: Via Twilio
2. **WhatsApp Updates**: Via WhatsApp Business API
3. **In-App Chat**: Real-time owner-student messaging
4. **Auto-Rent Reminders**: Monthly payment notifications
5. **Maintenance Requests**: Built-in ticketing system
6. **Review System**: Post-stay ratings
7. **Renewal Automation**: Auto-renew contracts
8. **Dispute Management**: Formal complaint system

---

## 🧪 Testing the System

### Test Flow:
1. Create student account
2. Create owner account
3. List a property (as owner)
4. Book the property (as student)
5. Pay booking fee
6. Check owner email
7. Approve booking (as owner)
8. Check student email
9. Complete payment (as student)
10. Verify contract PDF generation
11. Sign contract
12. Check final confirmation emails

### Test Cards (Razorpay):
- **Success**: 4111 1111 1111 1111
- **Failure**: 4000 0000 0000 0002

---

## 📞 Support

- **Email**: support@roomies.in
- **Phone**: +91-1234567890
- **Issues**: GitHub Issues
- **Documentation**: [Roomies Docs](https://docs.roomies.in)

---

## 📜 License

This booking system is proprietary to Roomies Platform.  
© 2024 Roomies. All rights reserved.
