
# Render Deployment - Email Troubleshooting

If emails are working locally but failing on Render, please check the following:

## 1. Environment Variables
Ensure you have added the following Environment Variables in your Render Dashboard (Settings > Environment):
- `MAIL_SERVER`: smtp.gmail.com (or your provider)
- `MAIL_PORT`: 587
- `MAIL_USERNAME`: your-email@gmail.com
- `MAIL_PASSWORD`: your-app-password (NOT your standard Gmail password)
- `MAIL_USE_TLS`: True

## 2. Gmail "Less Secure Apps" vs App Passwords
If you are using Gmail:
- **"Less Secure Apps" is no longer supported.**
- You MUST use an **App Password**.
  1. Go to your [Google Account](https://myaccount.google.com/).
  2. Select **Security**.
  3. Under "Signing in to Google," select **2-Step Verification**.
  4. At the bottom of the page, select **App passwords**.
  5. Enter a name (e.g., "Render App") and click **Create**.
  6. Use the generated 16-character code as your `MAIL_PASSWORD` in Render.

## 3. Render Logs
I have added detailed logging to the application.
1. Go to your Render Dashboard.
2. Click on your service.
3. Click "Logs".
4. Trigger an email action (e.g., Book a room).
5. Look for logs starting with `Preparing to send email...`.
   - If you see `SMTPAuthenticationError`: Your `MAIL_USERNAME` or `MAIL_PASSWORD` is incorrect.
   - If you see `SMTPConnectError`: The `MAIL_SERVER` or `MAIL_PORT` is wrong, or blocked.

## 4. Debug Script
I've created a local script `debug_email.py` that you can run to verify your credentials work.
Refrain from uploading `debug_email.py` to production if it contains sensitive info, but the logic inside mimics the app's behavior.

## 5. Deployment
After verifying the environment variables, **Re-deploy** your service on Render for the changes (logging updates) to take effect.
