"""Email notification service for Roomies platform."""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Handle all email communications for the platform."""
    
    def __init__(self):
        self.smtp_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("EMAIL_PORT", "587"))
        self.smtp_user = os.getenv("EMAIL_USER")
        self.smtp_password = os.getenv("EMAIL_PASSWORD")
        self.from_email = os.getenv("EMAIL_FROM", "Roomies <noreply@roomies.in>")
    
    def send_email(self, to_email, subject, html_content, attachments=None):
        """Send email with optional attachments."""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Attach files if provided
            if attachments:
                for filename, filepath in attachments.items():
                    with open(filepath, 'rb') as f:
                        attach = MIMEApplication(f.read(), _subtype="pdf")
                        attach.add_header('Content-Disposition', 'attachment', filename=filename)
                        msg.attach(attach)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_booking_request_to_owner(self, booking, room, student, owner):
        """Notify owner about new booking request."""
        subject = f"🏠 New Booking Request for {room.title}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #ff385c; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .booking-details {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #ff385c; }}
                .student-info {{ background: #e8f5e9; padding: 15px; margin: 15px 0; border-radius: 6px; }}
                .action-buttons {{ text-align: center; margin: 30px 0; }}
                .btn {{ display: inline-block; padding: 12px 30px; margin: 10px; text-decoration: none; border-radius: 6px; font-weight: bold; }}
                .btn-approve {{ background: #4caf50; color: white; }}
                .btn-reject {{ background: #f44336; color: white; }}
                .footer {{ text-align: center; margin-top: 30px; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏠 New Booking Request!</h1>
                </div>
                <div class="content">
                    <p>Hello <strong>{owner.name}</strong>,</p>
                    
                    <p>Great news! You have a new booking request for your property:</p>
                    
                    <div class="booking-details">
                        <h3>📍 Property: {room.title}</h3>
                        <p><strong>Location:</strong> {room.location}</p>
                        <p><strong>Monthly Rent:</strong> ₹{booking.monthly_rent:,.2f}</p>
                        <p><strong>Booking Fee Paid:</strong> ₹{booking.booking_amount:,.2f}</p>
                        <p><strong>Contract Duration:</strong> {booking.contract_duration_months} months</p>
                        <p><strong>Requested Move-in Date:</strong> {booking.move_in_date.strftime('%d %B, %Y') if booking.move_in_date else 'Not specified'}</p>
                    </div>
                    
                    <div class="student-info">
                        <h3>👤 Student Details</h3>
                        <p><strong>Name:</strong> {student.name}</p>
                        <p><strong>Email:</strong> {student.email}</p>
                        <p><strong>College:</strong> {student.college}</p>
                        <p><strong>Verified:</strong> {'✅ Yes' if student.verified else '⚠️ Pending'}</p>
                    </div>
                    
                    <p><strong>⏰ Please respond within 24 hours to avoid automatic cancellation.</strong></p>
                    
                    <div class="action-buttons">
                        <a href="{os.getenv('APP_URL', 'http://localhost:5000')}/api/bookings/{booking.id}/owner-approve?token=SECURE_TOKEN" class="btn btn-approve">
                            ✅ Approve Booking
                        </a>
                        <a href="{os.getenv('APP_URL', 'http://localhost:5000')}/owner/bookings/{booking.id}" class="btn btn-reject">
                            📋 View Details
                        </a>
                    </div>
                    
                    <p><strong>What happens next?</strong></p>
                    <ol>
                        <li>Review the student's profile and verification status</li>
                        <li>Approve or reject the booking request</li>
                        <li>If approved, the student will complete the payment process</li>
                        <li>Digital contract will be generated automatically</li>
                        <li>Coordinate move-in date directly with the student</li>
                    </ol>
                    
                    <div class="footer">
                        <p>© 2024 Roomies Platform | Connecting Students with Safe Accommodations</p>
                        <p>For support, email us at support@roomies.in or call +91-1234567890</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(owner.email, subject, html_content)
    
    def send_booking_confirmation_to_student(self, booking, room, student, owner):
        """Notify student about booking confirmation."""
        subject = f"🎉 Booking Confirmed: {room.title}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #4caf50; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .success-box {{ background: #e8f5e9; padding: 20px; margin: 20px 0; border-radius: 8px; text-align: center; }}
                .payment-summary {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #4caf50; }}
                .next-steps {{ background: #fff3e0; padding: 20px; margin: 20px 0; border-radius: 8px; }}
                .owner-contact {{ background: #e3f2fd; padding: 15px; margin: 15px 0; border-radius: 6px; }}
                .btn {{ display: inline-block; padding: 12px 30px; margin: 10px; text-decoration: none; border-radius: 6px; background: #ff385c; color: white; font-weight: bold; }}
                .footer {{ text-align: center; margin-top: 30px; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Congratulations, {student.name}!</h1>
                    <h2>Your Booking is Confirmed</h2>
                </div>
                <div class="content">
                    <div class="success-box">
                        <h2>✅ Booking Successfully Confirmed</h2>
                        <p>The owner has approved your request!</p>
                    </div>
                    
                    <div class="payment-summary">
                        <h3>💰 Payment Summary</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr style="border-bottom: 1px solid #ddd;">
                                <td style="padding: 10px;">Booking Fee</td>
                                <td style="padding: 10px; text-align: right;">₹{booking.booking_amount:,.2f}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #ddd;">
                                <td style="padding: 10px;">Security Deposit (2x rent)</td>
                                <td style="padding: 10px; text-align: right;">₹{booking.security_deposit:,.2f}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #ddd;">
                                <td style="padding: 10px;">First Month Rent</td>
                                <td style="padding: 10px; text-align: right;">₹{booking.monthly_rent:,.2f}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #ddd;">
                                <td style="padding: 10px;">Platform Fee (2%)</td>
                                <td style="padding: 10px; text-align: right;">₹{booking.platform_fee:,.2f}</td>
                            </tr>
                            <tr style="border-top: 2px solid #333; font-weight: bold;">
                                <td style="padding: 10px;">Total Paid</td>
                                <td style="padding: 10px; text-align: right;">₹{booking.total_paid:,.2f}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div class="owner-contact">
                        <h3>🏠 Property & Owner Details</h3>
                        <p><strong>Property:</strong> {room.title}</p>
                        <p><strong>Location:</strong> {room.location}</p>
                        <p><strong>Owner:</strong> {owner.name}</p>
                        <p><strong>Owner Email:</strong> {owner.email}</p>
                        <p><strong>Move-in Date:</strong> {booking.move_in_date.strftime('%d %B, %Y') if booking.move_in_date else 'To be confirmed'}</p>
                    </div>
                    
                    <div class="next-steps">
                        <h3>📋 Next Steps</h3>
                        <ol>
                            <li><strong>Review & Sign Contract:</strong> Digital contract has been sent separately</li>
                            <li><strong>Contact Owner:</strong> Coordinate move-in logistics and house rules</li>
                            <li><strong>Prepare Documents:</strong> Keep your ID and college documents ready</li>
                            <li><strong>Move-in Checklist:</strong> Document property condition on arrival</li>
                            <li><strong>Monthly Rent:</strong> Set up auto-payment for hassle-free experience</li>
                        </ol>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{os.getenv('APP_URL', 'http://localhost:5000')}/my-bookings" class="btn">
                            View My Bookings
                        </a>
                    </div>
                    
                    <p><strong>Important Notes:</strong></p>
                    <ul>
                        <li>Security deposit is fully refundable at contract end (subject to property condition)</li>
                        <li>Monthly rent is due on the 1st of every month</li>
                        <li>Late payment charges: ₹100/day after 5-day grace period</li>
                        <li>Report any issues immediately via the platform</li>
                    </ul>
                    
                    <div class="footer">
                        <p>© 2024 Roomies Platform | Your Trust, Our Priority</p>
                        <p>Need help? Contact us at support@roomies.in | +91-1234567890</p>
                        <p>Download our mobile app for easier management!</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(student.email, subject, html_content)
    
    def send_owner_approval_notification(self, booking, room, student, owner):
        """Notify student that owner approved their request."""
        subject = f"✅ Owner Approved! Complete Payment for {room.title}"
        
        remaining_amount = booking.calculate_total_due() - booking.total_paid
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #4caf50; color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f9f9f9; padding: 30px; }}
                .payment-box {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; border: 2px solid #4caf50; }}
                .btn-pay {{ display: inline-block; padding: 15px 40px; background: #ff385c; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Great News, {student.name}!</h1>
                    <h2>Owner Approved Your Request</h2>
                </div>
                <div class="content">
                    <p>The owner of <strong>{room.title}</strong> has approved your booking request!</p>
                    
                    <div class="payment-box">
                        <h3>💳 Complete Payment to Confirm Booking</h3>
                        <p><strong>Amount Due:</strong> ₹{remaining_amount:,.2f}</p>
                        <ul>
                            <li>Security Deposit: ₹{booking.security_deposit:,.2f}</li>
                            <li>First Month Rent: ₹{booking.monthly_rent:,.2f}</li>
                            <li>Platform Fee: ₹{booking.platform_fee:,.2f}</li>
                        </ul>
                        
                        <div style="text-align: center; margin: 20px 0;">
                            <a href="{os.getenv('APP_URL', 'http://localhost:5000')}/bookings/{booking.id}/pay" class="btn-pay">
                                Pay Now ₹{remaining_amount:,.2f}
                            </a>
                        </div>
                        
                        <p style="color: #ff385c; font-weight: bold;">⏰ Complete payment within 48 hours to secure your booking!</p>
                    </div>
                    
                    <p><strong>Owner Details:</strong></p>
                    <p>Name: {owner.name}<br>Email: {owner.email}</p>
                    
                    <p>After payment confirmation, you'll receive the rental agreement for e-signature.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(student.email, subject, html_content)
    
    def send_booking_rejection_to_student(self, booking, room, student, owner, reason):
        """Notify student about booking rejection."""
        subject = f"Booking Update: {room.title}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #ff9800; color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f9f9f9; padding: 30px; }}
                .info-box {{ background: #fff3e0; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #ff9800; }}
                .btn {{ display: inline-block; padding: 12px 30px; background: #ff385c; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Booking Update</h1>
                </div>
                <div class="content">
                    <p>Hello {student.name},</p>
                    
                    <p>Thank you for your interest in <strong>{room.title}</strong>.</p>
                    
                    <div class="info-box">
                        <h3>❌ Unfortunately, the owner has declined this booking request</h3>
                        <p><strong>Reason:</strong> {reason if reason else 'Not specified'}</p>
                    </div>
                    
                    <p><strong>💰 Refund Information:</strong></p>
                    <p>Your booking fee of ₹{booking.booking_amount:,.2f} will be refunded to your original payment method within 5-7 business days.</p>
                    
                    <p>Don't worry! We have many other great properties available:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{os.getenv('APP_URL', 'http://localhost:5000')}/explore?college={student.college}" class="btn">
                            Explore Similar Properties
                        </a>
                    </div>
                    
                    <p>Our team is here to help you find the perfect accommodation. Feel free to reach out!</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(student.email, subject, html_content)
    
    def send_contract_for_signature(self, booking, room, student, owner, contract_pdf_path):
        """Send rental agreement for e-signature."""
        subject = f"📄 Sign Your Rental Agreement - {room.title}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2196f3; color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f9f9f9; padding: 30px; }}
                .contract-box {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; border: 2px solid #2196f3; }}
                .btn-sign {{ display: inline-block; padding: 15px 40px; background: #4caf50; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📄 Rental Agreement Ready</h1>
                </div>
                <div class="content">
                    <p>Hello {student.name},</p>
                    
                    <p>Your rental agreement for <strong>{room.title}</strong> is ready for review and signature!</p>
                    
                    <div class="contract-box">
                        <h3>📋 Contract Details</h3>
                        <p><strong>Property:</strong> {room.title}</p>
                        <p><strong>Owner:</strong> {owner.name}</p>
                        <p><strong>Tenant:</strong> {student.name}</p>
                        <p><strong>Monthly Rent:</strong> ₹{booking.monthly_rent:,.2f}</p>
                        <p><strong>Security Deposit:</strong> ₹{booking.security_deposit:,.2f}</p>
                        <p><strong>Contract Period:</strong> {booking.contract_start_date.strftime('%d %B, %Y')} to {booking.contract_end_date.strftime('%d %B, %Y')}</p>
                        <p><strong>Duration:</strong> {booking.contract_duration_months} months</p>
                    </div>
                    
                    <p><strong>⚠️ Important:</strong> Please review the attached contract carefully before signing.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{os.getenv('APP_URL', 'http://localhost:5000')}/bookings/{booking.id}/sign-contract" class="btn-sign">
                            Review & Sign Contract
                        </a>
                    </div>
                    
                    <p>The contract includes:</p>
                    <ul>
                        <li>Rent payment schedule</li>
                        <li>Security deposit terms</li>
                        <li>Property maintenance responsibilities</li>
                        <li>House rules and regulations</li>
                        <li>Termination conditions</li>
                    </ul>
                    
                    <p>After both parties sign, you'll receive a copy for your records.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        attachments = {
            f"Rental_Agreement_{booking.id}.pdf": contract_pdf_path
        } if contract_pdf_path and os.path.exists(contract_pdf_path) else None
        
        return self.send_email(student.email, subject, html_content, attachments)


# Initialize email service
email_service = EmailService()
