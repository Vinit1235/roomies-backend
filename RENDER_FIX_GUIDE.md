
# 🚨 Critical Deployment Fixes for Render

Your application is failing to send emails because the **Payment Process crashes first**.
The logs show: `Razorpay order creation error: Authentication failed`.

This means your Razorpay Keys on Render are **Invalid** or **Mismatched**.

## 🛠️ Step 1: Fix Razorpay (Critical)
Without this, payments fail, and the "Booking Confirmation" email is never triggered.

1.  Go to **Razorpay Dashboard** > Settings > API Keys.
2.  Generate a **new Key Pair** (Key ID and Key Secret).
3.  Go to **Render Dashboard** > Select your Service > **Environment**.
4.  Update/Add these variables:
    *   `RAZORPAY_KEY_ID`: `rzp_test_...` (Copy exact value)
    *   `RAZORPAY_KEY_SECRET`: `...` (Copy exact value)
5.  **Save Changes** (Render will redeploy).

**Note:** If you want to use "Demo Mode" (fake payments) on Render, execute the following:
*   **Delete** the `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` variables from Render entirely.
*   The code will detect they are missing and switch to a Mock Payment mode automatically.

## 📧 Step 2: Fix Email (Required)
After fixing Razorpay, emails might still fail if credentials are wrong.

1.  Go to **Render Dashboard** > **Environment**.
2.  Ensure you have:
    *   `MAIL_SERVER`: `smtp.gmail.com`
    *   `MAIL_PORT`: `587`
    *   `MAIL_USERNAME`: Your Gmail address.
    *   `MAIL_PASSWORD`: Your **App Password** (NOT your Google login password).
        *   *To get App Password:* Go to Google Account > Security > 2-Step Verification > App Passwords.

## 🚀 How to Verify
1.  Wait for redeployment.
2.  Try to **Book a Room**.
3.  If Razorpay works, the payment popup will open.
4.  After payment, check your email.
5.  If email fails, check Render Logs for `Preparing to send email...` messages we added.
