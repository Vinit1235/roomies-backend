
"""
Simple script to trace email configuration loading.
This helps debug why emails might fail on Render.
"""
import os
import smtplib
import logging
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("email_debug")

def check_email_config():
    print("--- Email Configuration Check ---")
    
    # Check Environment Variables
    mail_server = os.getenv("MAIL_SERVER")
    mail_port = os.getenv("MAIL_PORT")
    mail_username = os.getenv("MAIL_USERNAME")
    mail_password = os.getenv("MAIL_PASSWORD")
    
    print(f"MAIL_SERVER: {mail_server}")
    print(f"MAIL_PORT: {mail_port}")
    print(f"MAIL_USERNAME: {mail_username}")
    print(f"MAIL_PASSWORD: {'*' * 8 if mail_password else 'NOT SET'}")
    
    if not all([mail_server, mail_port, mail_username, mail_password]):
        print("❌ Missing one or more required environment variables.")
        return

    print("\n--- Attempting SMTP Connection ---")
    try:
        server = smtplib.SMTP(mail_server, int(mail_port))
        server.set_debuglevel(1)  # verbose debugging
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(mail_username, mail_password)
        print("✅ SMTP Login Successful!")
        server.quit()
    except Exception as e:
        print(f"❌ SMTP Connection Failed: {e}")

if __name__ == "__main__":
    check_email_config()
