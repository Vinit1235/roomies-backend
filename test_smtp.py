"""Quick SMTP test script for Gmail."""
import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

def test_gmail_smtp():
    """Test Gmail SMTP connection."""
    print("=" * 50)
    print("GMAIL SMTP CONNECTION TEST")
    print("=" * 50)
    
    # Get credentials from .env
    smtp_host = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("MAIL_PORT", "587"))
    smtp_user = os.getenv("MAIL_USERNAME")
    smtp_password = os.getenv("MAIL_PASSWORD")
    
    print(f"\n1. Checking environment variables:")
    print(f"   MAIL_SERVER: {smtp_host}")
    print(f"   MAIL_PORT: {smtp_port}")
    print(f"   MAIL_USERNAME: {smtp_user if smtp_user else '❌ NOT SET'}")
    print(f"   MAIL_PASSWORD: {'✅ SET (hidden)' if smtp_password else '❌ NOT SET'}")
    
    if not smtp_user or not smtp_password:
        print("\n❌ ERROR: MAIL_USERNAME and MAIL_PASSWORD must be set in .env file")
        print("\nTo use Gmail SMTP, add these to your .env file:")
        print("   MAIL_SERVER=smtp.gmail.com")
        print("   MAIL_PORT=587")
        print("   MAIL_USERNAME=your-email@gmail.com")
        print("   MAIL_PASSWORD=your-app-password")
        print("\n⚠️  Note: For Gmail, you need an 'App Password', not your regular password!")
        print("   Generate one at: https://myaccount.google.com/apppasswords")
        return False
    
    print(f"\n2. Testing SMTP connection to {smtp_host}:{smtp_port}...")
    
    try:
        # Connect to SMTP server
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        server.set_debuglevel(0)  # Set to 1 for debug output
        
        print("   ✅ Connected to SMTP server")
        
        # Start TLS
        server.starttls()
        print("   ✅ TLS encryption established")
        
        # Login
        server.login(smtp_user, smtp_password)
        print("   ✅ Authentication successful!")
        
        # Close connection
        server.quit()
        print("\n✅ GMAIL SMTP IS WORKING CORRECTLY!")
        
        # Offer to send test email
        print("\n3. Would you like to send a test email?")
        print(f"   Run: python test_smtp.py send your-email@example.com")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ AUTHENTICATION FAILED!")
        print(f"   Error: {e}")
        print("\n   Possible causes:")
        print("   1. Wrong email or password")
        print("   2. 2-Step Verification is enabled but you're using regular password")
        print("   3. 'Less secure apps' access is disabled")
        print("\n   Solution for Gmail:")
        print("   1. Enable 2-Step Verification: https://myaccount.google.com/security")
        print("   2. Generate App Password: https://myaccount.google.com/apppasswords")
        print("   3. Use the 16-character App Password in EMAIL_PASSWORD")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"\n❌ CONNECTION FAILED!")
        print(f"   Error: {e}")
        print("   Check your internet connection and firewall settings.")
        return False
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}")
        print(f"   Details: {e}")
        return False


def send_test_email(to_email):
    """Send a test email."""
    smtp_host = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("MAIL_PORT", "587"))
    smtp_user = os.getenv("MAIL_USERNAME")
    smtp_password = os.getenv("MAIL_PASSWORD")
    
    print(f"\nSending test email to: {to_email}")
    
    try:
        msg = MIMEText("""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h1 style="color: #dc2626;">🏠 Roomies SMTP Test</h1>
            <p>Congratulations! Your email configuration is working correctly.</p>
            <p>This is a test email from the Roomies platform.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                Sent via Gmail SMTP at {host}:{port}
            </p>
        </body>
        </html>
        """.format(host=smtp_host, port=smtp_port), 'html')
        
        msg['Subject'] = '✅ Roomies SMTP Test - Success!'
        msg['From'] = f"Roomies <{smtp_user}>"
        msg['To'] = to_email
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        print(f"✅ Test email sent successfully to {to_email}!")
        print("   Check your inbox (and spam folder).")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "send":
        if len(sys.argv) > 2:
            send_test_email(sys.argv[2])
        else:
            print("Usage: python test_smtp.py send your-email@example.com")
    else:
        test_gmail_smtp()
