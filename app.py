"""Roomies demo backend with login, signup, and room search endpoints."""

from __future__ import annotations

import logging
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

from datetime import datetime, timedelta, date
from typing import Any, Dict, Optional, cast
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import traceback

from flask import (
    Flask,
    flash,
    has_request_context,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
    send_file,
)
import io
import pandas as pd
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, func, inspect, or_, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from functools import wraps
from search_engine import SearchTrie
# Use lightweight chatbot (no FAISS/SentenceTransformers - better for Render)
try:
    from agents.chatbot_lite import chatbot
    print("✅ Lightweight Gemini chatbot loaded")
except ImportError as e:
    # Mock chatbot if agents module is missing or fails to load
    class MockChatbot:
        def get_response(self, msg):
            return "Chatbot is currently disabled. Please try again later."
        def set_room_provider(self, func):
            pass
    chatbot = MockChatbot()
    print(f"⚠️ Could not import chatbot_lite: {e}. Chat functionality disabled.")

# from utils.verification import process_verification  # Import verification logic
try:
    from utils.verification import process_verification
except ImportError:
    # Mock verification if utils module is missing or fails to load
    def process_verification(image_path, user_record):
        return {"verified": False, "message": "Auto-verification disabled on this server."}
    print("Warning: Could not import utils.verification. Auto-verification disabled.")

# Supabase OAuth Authentication
try:
    from utils.supabase_auth import (
        supabase_auth,
        get_google_oauth_url,
        get_github_oauth_url,
        handle_oauth_callback,
        is_oauth_available
    )
    OAUTH_ENABLED = is_oauth_available()
    if OAUTH_ENABLED:
        print("✅ Supabase OAuth enabled")
    else:
        print("⚠️ Supabase OAuth not configured (missing credentials)")
except ImportError as e:
    print(f"⚠️ Could not import supabase_auth: {e}. OAuth disabled.")
    OAUTH_ENABLED = False
    def get_google_oauth_url(redirect_to=None):
        return False, "OAuth not available"
    def get_github_oauth_url(redirect_to=None):
        return False, "OAuth not available"
    def handle_oauth_callback(code=None, access_token=None):
        return False, {"error": "OAuth not available"}

# from services.news_service import NewsService
try:
    from services.news_service import NewsService
except ImportError as e:
    print(f"Warning: Could not import services.news_service: {e}")
    # Mock NewsService if module is missing
    class NewsService:
        def get_latest_news(self, limit=5):
            return []

# Initialize News Service
news_service = NewsService()

# Import config
try:
    import config
except ImportError:
    config = None

# ---------------------------------------------------------------------------
# Flask application factory-style setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", getattr(config, "SECRET_KEY", "roomies-dev-secret"))

# Database Configuration
database_url = os.environ.get("DATABASE_URL", getattr(config, "DATABASE_URL", "sqlite:///roomies.db"))

# Debug: Print which database is being used
print(f"🔧 DATABASE_URL from env: {'SET' if os.environ.get('DATABASE_URL') else 'NOT SET'}")

# Google Maps Configuration
app.config["GOOGLE_MAPS_API_KEY"] = os.environ.get("GOOGLE_MAPS_API_KEY", "")
print(f"🔧 Using database: {'PostgreSQL' if 'postgres' in database_url.lower() else 'SQLite'}")

# Fix for Render's postgres:// usage (SQLAlchemy requires postgresql://)
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Add SSL requirement for Supabase/PostgreSQL connections
if "postgresql" in database_url or "postgres" in database_url:
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "connect_args": {
            "sslmode": "require"
        },
        "pool_pre_ping": True,  # Check connection health before use
        "pool_recycle": 300,    # Recycle connections every 5 minutes
    }
    print("🔒 SSL mode enabled for PostgreSQL connection")

# Razorpay Payment Gateway Configuration
try:
    import razorpay
    RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
    if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
        razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        print("✅ Razorpay payment gateway initialized")
    else:
        razorpay_client = None
        print("⚠️ Razorpay keys not configured. Payment gateway disabled.")
except ImportError:
    razorpay_client = None
    print("⚠️ Razorpay not installed. Payment gateway disabled.")

# Initialize Search Trie
search_trie = SearchTrie()

# Admin configuration
ADMIN_EMAIL = getattr(config, "ADMIN_EMAIL", "admin@roomies.in")
ADMIN_PASSWORD = getattr(config, "ADMIN_PASSWORD", "admin123")

@app.route("/test-email")
def test_email_route():
    """Debug route to test email sending."""
    recipient = request.args.get("to")
    if not recipient:
        return "Missing 'to' parameter. Usage: /test-email?to=your@email.com", 400
    
    try:
        from utils.email_service import email_service
        subject = "Test Email from Render"
        content = "<h1>It Works!</h1><p>Email sending is active on this server.</p>"
        
        success, error_msg = email_service.send_email_with_details(recipient, subject, content)
        if success:
            return f"✅ Email sent successfully to {recipient}"
        else:
            return f"❌ Failed to send email: {error_msg}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

CORS(app)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "warning"

@login_manager.user_loader
def load_user(user_id: str):
    """Load user by ID for Flask-Login."""
    if not user_id or ":" not in user_id:
        return None
    
    try:
        role, id_str = user_id.split(":", 1)
        uid = int(id_str)
        
        if role == "student":
            return Student.query.get(uid)
        elif role == "owner":
            return Owner.query.get(uid)
        elif role == "admin":
            return Admin.query.get(uid)
    except (ValueError, AttributeError):
        return None
    
    return None

logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
            flash("You need admin privileges to access this page.", "error")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function

# Ensure upload directories exist for future use
for folder in ("uploads", "exports", "static/contracts"):
    os.makedirs(os.path.join(app.root_path, folder), exist_ok=True)


# ---------------------------------------------------------------------------
# Model helpers
# ---------------------------------------------------------------------------
class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class PasswordMixin:
    """Reusable password helpers for SQLAlchemy models."""

    password = db.Column(db.String(255), nullable=False)

    def set_password(self, raw_password: str) -> None:
        self.password = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def verify_password(self, raw_password: str) -> bool:
        if not self.password:
            return False
        try:
            return bcrypt.check_password_hash(self.password, raw_password)
        except ValueError:
            # Gracefully fall back for legacy plain-text rows
            return self.password == raw_password


# ---------------------------------------------------------------------------
# Database models
# ---------------------------------------------------------------------------
class Student(TimestampMixin, PasswordMixin, UserMixin, db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    college = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default="student")
    verified = db.Column(db.Boolean, default=False)
    budget = db.Column(db.Integer)
    lifestyle = db.Column(db.String(50))
    study_hours = db.Column(db.String(50))
    commute_pref = db.Column(db.String(50))
    
    # Free tier limits
    property_inquiries_count = db.Column(db.Integer, default=0)  # Reset monthly
    inquiries_reset_date = db.Column(db.Date)

    def get_id(self) -> str:  # type: ignore[override]
        return f"student:{self.id}"
    
    @property
    def active_subscription(self):
        """Get active subscription if any."""
        sub = UserSubscription.query.filter_by(
            user_id=self.id,
            user_type="student",
            status="active"
        ).filter(UserSubscription.end_date > datetime.utcnow()).first()
        return sub
    
    @property
    def is_premium(self):
        """Check if user has active premium subscription."""
        return self.active_subscription is not None


class Owner(TimestampMixin, PasswordMixin, UserMixin, db.Model):
    __tablename__ = "owners"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    kyc_verified = db.Column(db.Boolean, default=False)
    rooms = db.relationship(
        "Room",
        back_populates="owner",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    
    # Free tier limits
    active_listings_count = db.Column(db.Integer, default=0)

    @property
    def role(self) -> str:
        return "owner"

    def get_id(self) -> str:  # type: ignore[override]
        return f"owner:{self.id}"
    
    @property
    def active_subscription(self):
        """Get active subscription if any."""
        sub = UserSubscription.query.filter_by(
            user_id=self.id,
            user_type="owner",
            status="active"
        ).filter(UserSubscription.end_date > datetime.utcnow()).first()
        return sub
    
    @property
    def is_premium(self):
        """Check if user has active premium subscription."""
        return self.active_subscription is not None
    
    @property
    def commission_rate(self):
        """Get applicable commission rate based on subscription."""
        if self.is_premium and self.active_subscription.plan.commission_discount > 0:
            base_rate = 25.0  # Base 25% commission
            discount = self.active_subscription.plan.commission_discount
            return base_rate - (base_rate * discount / 100)
        return 25.0  # Default 25%


class Room(TimestampMixin, db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    college_nearby = db.Column(db.String(255), nullable=False)
    amenities = db.Column(db.String(255))
    images = db.Column(db.String(255))
    property_type = db.Column(db.String(50), default="shared", nullable=False)
    capacity_total = db.Column(db.Integer, nullable=False, default=1)
    capacity_occupied = db.Column(db.Integer, nullable=False, default=0)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("owners.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    verified = db.Column(db.Boolean, default=False)
    owner = db.relationship("Owner", back_populates="rooms", lazy="joined")

    @property
    def available_slots(self) -> int:
        return max((self.capacity_total or 0) - (self.capacity_occupied or 0), 0)

    @property
    def availability_status(self) -> str:
        """
        green: Instant Booking (Verified Room & Verified Owner)
        yellow: Approval Required (Unverified)
        red: Sold Out
        """
        if self.available_slots <= 0:
            return "red"
        if self.verified and self.owner and getattr(self.owner, 'kyc_verified', False):
            return "green"
        return "yellow"

    def to_dict(self) -> dict:
        image_url: Optional[str] = None
        if self.images:
            parts = [part.strip() for part in self.images.split(",") if part.strip()]
            if parts:
                candidate = parts[0].lstrip("/")
                if candidate.startswith(("http://", "https://")):
                    image_url = candidate
                else:
                    static_variants = [
                        candidate,
                        f"images/{candidate}",
                        f"uploads/{candidate}",
                    ]
                    for variant in static_variants:
                        static_path = os.path.join(app.static_folder, variant)
                        if os.path.exists(static_path):
                            if has_request_context():
                                image_url = url_for("static", filename=variant, _external=True)
                            else:
                                image_url = f"/static/{variant}".replace("//", "/")
                            break
        amenities_list = []
        if self.amenities:
            amenities_list = [item.strip() for item in self.amenities.split(",") if item.strip()]
        return {
            "id": self.id,
            "title": self.title,
            "price": self.price,
            "location": self.location,
            "college": self.college_nearby,
            "property_type": self.property_type,
            "amenities": amenities_list,
            "image_url": image_url or "https://placehold.co/600x400?text=Roomies",
            "verified": bool(self.verified),
            "owner": {
                "id": self.owner.id,
                "name": self.owner.name,
            }
            if self.owner
            else None,
            "capacity_total": self.capacity_total,
            "capacity_occupied": self.capacity_occupied,
            "available_slots": self.available_slots,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "created_at": self.created_at.isoformat() if getattr(self, "created_at", None) else None,
            "updated_at": self.updated_at.isoformat() if getattr(self, "updated_at", None) else None,
        }


class ContactMessage(TimestampMixin, db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(50), nullable=False, default="web")
    disposition = db.Column(db.String(50), nullable=False, default="new")


class Admin(TimestampMixin, PasswordMixin, UserMixin, db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default="admin")

    def get_id(self) -> str:  # type: ignore[override]
        return f"admin:{self.id}"


class Verification(TimestampMixin, db.Model):
    """User verification with document uploads."""
    __tablename__ = "verifications"

    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String(32), nullable=False)  # 'student' or 'owner'
    user_id = db.Column(db.Integer, nullable=False)
    student_id_path = db.Column(db.String(512))
    college_letter_path = db.Column(db.String(512))
    gov_id_path = db.Column(db.String(512))
    electricity_bill_path = db.Column(db.String(512))
    status = db.Column(db.String(32), default="pending", nullable=False)  # pending, verified, rejected
    rejection_reason = db.Column(db.Text)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("admins.id"))
    reviewed_at = db.Column(db.DateTime)

    reviewer = db.relationship("Admin", backref="verifications_reviewed")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_type": self.user_type,
            "user_id": self.user_id,
            "status": self.status,
            "rejection_reason": self.rejection_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }


class FlashDeal(TimestampMixin, db.Model):
    """Flash deals - 24hr limited offers with pulsing map markers."""
    __tablename__ = "flash_deals"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)
    original_price = db.Column(db.Float, nullable=False)
    deal_price = db.Column(db.Float, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)  # Auto-set to +24hrs
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    fee_paid = db.Column(db.Float, default=29.0, nullable=False)  # ₹29 flash deal fee

    room = db.relationship("Room", backref="flash_deals")

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "room_id": self.room_id,
            "original_price": self.original_price,
            "deal_price": self.deal_price,
            "discount_percent": round((1 - self.deal_price / self.original_price) * 100, 1),
            "expires_at": self.expires_at.isoformat(),
            "is_active": self.is_active and not self.is_expired,
            "time_remaining_hours": max(0, (self.expires_at - datetime.utcnow()).total_seconds() / 3600),
        }


class ProfileTag(TimestampMixin, db.Model):
    """Roommate matching tags (early_bird, night_owl, introvert, etc)."""
    __tablename__ = "profile_tags"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    tag = db.Column(db.String(50), nullable=False)  # early_bird, night_owl, introvert, extrovert, vegetarian, etc.

    student = db.relationship("Student", backref="tags")


class Subscription(TimestampMixin, db.Model):
    """Owner Pro subscriptions - ₹199/mo via Stripe."""
    __tablename__ = "subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("owners.id"), nullable=False)
    stripe_subscription_id = db.Column(db.String(255), unique=True)
    status = db.Column(db.String(50), default="active")  # active, cancelled, expired
    plan_price = db.Column(db.Float, default=199.0, nullable=False)
    current_period_start = db.Column(db.DateTime)
    current_period_end = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)

    owner = db.relationship("Owner", backref="subscriptions")

    @property
    def is_active(self) -> bool:
        if self.status != "active":
            return False
        if self.current_period_end:
            return datetime.utcnow() < self.current_period_end
        return True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "status": self.status,
            "plan_price": self.plan_price,
            "is_active": self.is_active,
            "current_period_end": self.current_period_end.isoformat() if self.current_period_end else None,
        }


class Referral(TimestampMixin, db.Model):
    """Referral tracking - ₹200 wallet credit for both parties."""
    __tablename__ = "referrals"

    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    referred_id = db.Column(db.Integer, db.ForeignKey("students.id"))
    referral_code = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(50), default="pending")  # pending, completed
    reward_amount = db.Column(db.Float, default=200.0)

    referrer = db.relationship("Student", foreign_keys=[referrer_id], backref="referrals_made")
    referred = db.relationship("Student", foreign_keys=[referred_id], backref="referrals_received")

class Booking(db.Model):
    __tablename__ = "bookings"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)
    
    # Booking Status Flow: pending -> payment_initiated -> confirmed -> active -> completed/cancelled
    booking_status = db.Column(db.String(50), default="pending")  # pending, payment_initiated, confirmed, active, completed, cancelled
    payment_status = db.Column(db.String(50), default="pending")  # pending, partial, completed, refunded
    
    # Financial Details
    booking_amount = db.Column(db.Float, default=999.0)  # Booking fee ₹999
    security_deposit = db.Column(db.Float, default=0.0)  # 2x monthly rent
    monthly_rent = db.Column(db.Float, default=0.0)
    platform_fee = db.Column(db.Float, default=0.0)  # 2% of first month rent
    total_paid = db.Column(db.Float, default=0.0)
    
    # Payment Gateway Details
    razorpay_order_id = db.Column(db.String(100))
    razorpay_payment_id = db.Column(db.String(100))
    razorpay_signature = db.Column(db.String(255))
    
    # Contract Details
    contract_start_date = db.Column(db.Date)
    contract_end_date = db.Column(db.Date)
    contract_duration_months = db.Column(db.Integer, default=11)  # Standard 11-month academic year
    contract_signed = db.Column(db.Boolean, default=False)
    contract_signed_at = db.Column(db.DateTime)
    contract_pdf_path = db.Column(db.String(512))
    
    # Communication Tracking
    owner_notified = db.Column(db.Boolean, default=False)
    student_notified = db.Column(db.Boolean, default=False)
    owner_notification_sent_at = db.Column(db.DateTime)
    student_notification_sent_at = db.Column(db.DateTime)
    
    # Owner Response
    owner_approved = db.Column(db.Boolean, default=False)
    owner_approved_at = db.Column(db.DateTime)
    owner_rejection_reason = db.Column(db.Text)
    
    # Move-in Details
    move_in_date = db.Column(db.Date)
    move_in_completed = db.Column(db.Boolean, default=False)
    move_in_confirmed_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    
    # Cancellation Details
    cancellation_reason = db.Column(db.Text)
    cancelled_by = db.Column(db.String(20))  # 'student' or 'owner'
    refund_amount = db.Column(db.Float, default=0.0)
    refund_processed = db.Column(db.Boolean, default=False)
    refund_processed_at = db.Column(db.DateTime)

    student = db.relationship("Student", backref="bookings")
    room = db.relationship("Room", backref="bookings")
    
    def calculate_platform_fee(self):
        """Calculate 2% platform fee on first month rent."""
        if self.monthly_rent:
            self.platform_fee = round(self.monthly_rent * 0.02, 2)
        return self.platform_fee
    
    def calculate_security_deposit(self):
        """Security deposit is 2x monthly rent."""
        if self.monthly_rent:
            self.security_deposit = round(self.monthly_rent * 2, 2)
        return self.security_deposit
    
    def calculate_total_due(self):
        """Total amount due: booking fee + security deposit + first month rent + platform fee."""
        return round(
            self.booking_amount + 
            self.security_deposit + 
            self.monthly_rent + 
            self.platform_fee,
            2
        )

    @property
    def room_availability_status(self):
        """Proxy for room availability status."""
        return self.room.availability_status if self.room else 'red'
    
    def to_dict(self):
        return {
            "id": self.id,
            "room": self.room.to_dict() if self.room else None,
            "booking_status": self.booking_status,
            "payment_status": self.payment_status,
            "booking_amount": self.booking_amount,
            "security_deposit": self.security_deposit,
            "monthly_rent": self.monthly_rent,
            "platform_fee": self.platform_fee,
            "total_paid": self.total_paid,
            "total_due": self.calculate_total_due(),
            "contract_start_date": self.contract_start_date.isoformat() if self.contract_start_date else None,
            "contract_end_date": self.contract_end_date.isoformat() if self.contract_end_date else None,
            "contract_signed": self.contract_signed,
            "owner_approved": self.owner_approved,
            "move_in_date": self.move_in_date.isoformat() if self.move_in_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
        }

class Wallet(db.Model):
    __tablename__ = "wallets"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), unique=True, nullable=False)
    balance = db.Column(db.Float, default=0.0)
    
    student = db.relationship("Student", backref=db.backref("wallet", uselist=False))

class WalletTransaction(db.Model):
    __tablename__ = "wallet_transactions"
    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey("wallets.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # credit, debit
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    wallet = db.relationship("Wallet", backref="transactions")

class MessMenu(db.Model):
    __tablename__ = "mess_menus"
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)
    day_of_week = db.Column(db.String(20), nullable=False)
    breakfast = db.Column(db.String(200))
    lunch = db.Column(db.String(200))
    dinner = db.Column(db.String(200))

    room = db.relationship("Room", backref="mess_menus")

class SafetyAudit(db.Model):
    __tablename__ = "safety_audits"
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), unique=True, nullable=False)
    fire_extinguisher = db.Column(db.Boolean, default=False)
    cctv = db.Column(db.Boolean, default=False)
    security_guard = db.Column(db.Boolean, default=False)
    last_audit_date = db.Column(db.DateTime, default=datetime.utcnow)
    audit_score = db.Column(db.Integer, default=0)

    room = db.relationship("Room", backref=db.backref("safety_audit", uselist=False))

class SubscriptionPlan(TimestampMixin, db.Model):
    """Subscription plans for students and owners."""
    __tablename__ = "subscription_plans"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Roomies Premium, Owner Pro, etc.
    user_type = db.Column(db.String(20), nullable=False)  # 'student' or 'owner'
    price_monthly = db.Column(db.Float, nullable=False)
    price_yearly = db.Column(db.Float, nullable=False)
    
    # Features (JSON stored as string)
    features = db.Column(db.Text)  # JSON string of features
    
    # Limits
    property_inquiries_limit = db.Column(db.Integer)  # -1 for unlimited
    listings_limit = db.Column(db.Integer)  # -1 for unlimited
    
    # Discounts & Benefits
    commission_discount = db.Column(db.Float, default=0)  # % discount on commission
    booking_fee_waived = db.Column(db.Boolean, default=False)
    
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        import json
        return {
            "id": self.id,
            "name": self.name,
            "user_type": self.user_type,
            "price_monthly": self.price_monthly,
            "price_yearly": self.price_yearly,
            "features": json.loads(self.features) if self.features else [],
            "property_inquiries_limit": self.property_inquiries_limit,
            "listings_limit": self.listings_limit,
            "commission_discount": self.commission_discount,
            "booking_fee_waived": self.booking_fee_waived,
        }


class UserSubscription(TimestampMixin, db.Model):
    """User's active subscription."""
    __tablename__ = "user_subscriptions"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'student' or 'owner'
    plan_id = db.Column(db.Integer, db.ForeignKey("subscription_plans.id"), nullable=False)
    
    status = db.Column(db.String(20), default="active")  # active, cancelled, expired
    billing_cycle = db.Column(db.String(20), nullable=False)  # 'monthly' or 'yearly'
    
    # Payment
    amount_paid = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))  # razorpay, stripe, etc.
    transaction_id = db.Column(db.String(255))
    
    # Dates
    start_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    next_billing_date = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    
    # Auto-renewal
    auto_renew = db.Column(db.Boolean, default=True)
    
    plan = db.relationship("SubscriptionPlan", backref="subscriptions")
    
    @property
    def is_active(self):
        return self.status == "active" and self.end_date > datetime.utcnow()
    
    def to_dict(self):
        return {
            "id": self.id,
            "plan": self.plan.to_dict() if self.plan else None,
            "status": self.status,
            "billing_cycle": self.billing_cycle,
            "amount_paid": self.amount_paid,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "is_active": self.is_active,
            "auto_renew": self.auto_renew,
        }


class ListingFee(TimestampMixin, db.Model):
    """Listing fees paid by property owners."""
    __tablename__ = "listing_fees"
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("owners.id"), nullable=False)
    
    fee_type = db.Column(db.String(50), nullable=False)  # basic, featured, premium
    amount = db.Column(db.Float, nullable=False)
    validity_days = db.Column(db.Integer, nullable=False)  # 30, 60, 90 days
    
    payment_status = db.Column(db.String(20), default="pending")
    transaction_id = db.Column(db.String(255))
    
    expires_at = db.Column(db.DateTime, nullable=False)
    
    room = db.relationship("Room", backref="listing_fees")
    owner = db.relationship("Owner", backref="listing_fees")
    
    @property
    def is_active(self):
        return self.payment_status == "completed" and self.expires_at > datetime.utcnow()


class Commission(TimestampMixin, db.Model):
    """Commission earned on successful bookings."""
    __tablename__ = "commissions"
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    
    # Commission Details
    commission_type = db.Column(db.String(50), default="booking")  # booking, referral, service
    base_amount = db.Column(db.Float, nullable=False)  # Amount commission is calculated on
    commission_rate = db.Column(db.Float, nullable=False)  # Percentage
    commission_amount = db.Column(db.Float, nullable=False)  # Actual commission
    
    # Discount applied (from subscription)
    discount_applied = db.Column(db.Float, default=0)
    final_commission = db.Column(db.Float, nullable=False)
    
    # Payment
    status = db.Column(db.String(20), default="pending")  # pending, processed, paid
    paid_at = db.Column(db.DateTime)
    
    booking = db.relationship("Booking", backref="commissions")
    
    def to_dict(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "commission_type": self.commission_type,
            "base_amount": self.base_amount,
            "commission_rate": self.commission_rate,
            "commission_amount": self.commission_amount,
            "discount_applied": self.discount_applied,
            "final_commission": self.final_commission,
            "status": self.status,
        }


class ValueAddedService(TimestampMixin, db.Model):
    """Value-added services offered to users."""
    __tablename__ = "value_added_services"
    
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(100), nullable=False)
    service_type = db.Column(db.String(50), nullable=False)  # photography, verification, legal, moving, etc.
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    
    # For which user type
    target_user = db.Column(db.String(20))  # 'student', 'owner', 'both'
    
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "service_name": self.service_name,
            "service_type": self.service_type,
            "price": self.price,
            "description": self.description,
            "target_user": self.target_user,
        }


class ServicePurchase(TimestampMixin, db.Model):
    """Tracking purchases of value-added services."""
    __tablename__ = "service_purchases"
    
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey("value_added_services.id"), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    
    # Related entities
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"))  # If service is for a property
    
    # Payment
    amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), default="pending")
    transaction_id = db.Column(db.String(255))
    
    # Fulfillment
    service_status = db.Column(db.String(20), default="pending")  # pending, in_progress, completed
    scheduled_date = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    service = db.relationship("ValueAddedService", backref="purchases")
    room = db.relationship("Room", backref="service_purchases")
    
    def to_dict(self):
        return {
            "id": self.id,
            "service": self.service.to_dict() if self.service else None,
            "amount": self.amount,
            "payment_status": self.payment_status,
            "service_status": self.service_status,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
        }


class TransactionFee(TimestampMixin, db.Model):
    """Transaction fees on rent payments."""
    __tablename__ = "transaction_fees"
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    
    # Transaction details
    transaction_amount = db.Column(db.Float, nullable=False)  # Rent amount
    fee_percentage = db.Column(db.Float, default=2.0)  # 1.5-2.5%
    fee_amount = db.Column(db.Float, nullable=False)
    
    transaction_type = db.Column(db.String(50))  # rent, security_deposit, refund
    payment_method = db.Column(db.String(50))
    
    # Payment gateway charges (if applicable)
    gateway_fee = db.Column(db.Float, default=0)
    net_fee = db.Column(db.Float, nullable=False)  # Our actual earning
    
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    booking = db.relationship("Booking", backref="transaction_fees")


class RevenueAnalytics(TimestampMixin, db.Model):
    """Daily revenue analytics aggregation."""
    __tablename__ = "revenue_analytics"
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    
    # Revenue by stream
    subscription_revenue = db.Column(db.Float, default=0)
    commission_revenue = db.Column(db.Float, default=0)
    listing_fee_revenue = db.Column(db.Float, default=0)
    service_revenue = db.Column(db.Float, default=0)
    transaction_fee_revenue = db.Column(db.Float, default=0)
    advertising_revenue = db.Column(db.Float, default=0)
    
    # Counts
    new_subscriptions = db.Column(db.Integer, default=0)
    total_bookings = db.Column(db.Integer, default=0)
    services_sold = db.Column(db.Integer, default=0)
    
    # Total
    total_revenue = db.Column(db.Float, default=0)
    
    def calculate_total(self):
        self.total_revenue = (
            self.subscription_revenue +
            self.commission_revenue +
            self.listing_fee_revenue +
            self.service_revenue +
            self.transaction_fee_revenue +
            self.advertising_revenue
        )
        return self.total_revenue


class Analytics(db.Model):
    __tablename__ = "analytics"
    id = db.Column(db.Integer, primary_key=True)
    metric_type = db.Column(db.String(50), nullable=False)
    count = db.Column(db.Integer, default=0)
    amount = db.Column(db.Float, default=0.0)
    date = db.Column(db.Date, default=datetime.utcnow().date)

def get_current_owner():
    if current_user.is_authenticated and getattr(current_user, 'role', None) == 'owner':
        return current_user
    return None

def get_current_student():
    if current_user.is_authenticated and getattr(current_user, 'role', None) == 'student':
        return current_user
    return None

# ---------------------------------------------------------------------------
# Search Index Initialization (Must be after Models)
# ---------------------------------------------------------------------------
def rebuild_search_index():
    """Populate the Trie with current database data."""
    with app.app_context():
        try:
            # Check if tables exist before querying
            inspector = inspect(db.engine)
            if not inspector.has_table("rooms"):
                return

            rooms = Room.query.all()
            for room in rooms:
                # Index title, location, and college
                search_trie.insert(room.title, room.id)
                search_trie.insert(room.location, room.id)
                search_trie.insert(room.college_nearby, room.id)
            app.logger.info(f"Search index rebuilt with {len(rooms)} rooms.")
        except Exception as e:
            app.logger.error(f"Failed to rebuild search index: {e}")

# Rebuild index on startup
rebuild_search_index()

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/pricing")
def pricing():
    """Pricing and subscription plans page."""
    return render_template("pricing.html")


@app.route("/explore")
def explore():
    return render_template("explore.html")


@app.route("/list-room")
@login_required
def list_room():
    """Page to list a new room (Owners & Students)."""
    # Debug print to help diagnose role issues
    user_role = getattr(current_user, 'role', 'unknown')
    print(f"DEBUG: /list-room accessed by User: {current_user.get_id()}, Role: {user_role}")

    # Allow both Owners and Students to access
    if user_role not in ['owner', 'student']:
         flash(f"Access denied. Please login as a Student or Owner to list a property.", "warning")
         return redirect(url_for('home'))
        
    return render_template("list_room.html")


@app.route("/room/<int:room_id>")
def room_details(room_id):
    """Room details page."""
    try:
        room = Room.query.get_or_404(room_id)
        if not room.owner:
             app.logger.warning(f"Room {room_id} has no owner!")
        return render_template("room_details.html", room=room)
    except Exception as e:
        app.logger.error(f"Error in room_details: {e}")
        return f"<h3>Error loading room details</h3><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>", 500


@app.route("/book")
@app.route("/book/<int:room_id>")
@login_required
def book_room(room_id=None):
    """Booking page for a room."""
    return render_template("booking.html", room_id=room_id)


@app.route("/payment")
@login_required
def payment_page():
    """Payment gateway page."""
    booking_id = request.args.get("booking_id")
    amount = request.args.get("amount")
    return render_template(
        "payment_gateway.html",
        booking_id=booking_id,
        amount=amount,
        razorpay_key=os.environ.get("RAZORPAY_KEY_ID", "")
    )


@app.route("/my-bookings")
@login_required
def my_bookings_page():
    """User's bookings page."""
    return render_template("my_bookings.html")


@app.route("/booking-confirmation")
@app.route("/bookings/<int:booking_id>")
@login_required
def booking_confirmation_page(booking_id=None):
    """Booking confirmation page."""
    if not booking_id:
        booking_id = request.args.get("booking_id")
    
    if booking_id:
        booking = Booking.query.get_or_404(booking_id)
        # Check if user owns this booking
        if current_user.role == 'student' and booking.student_id != current_user.id:
            flash("You don't have permission to view this booking.", "error")
            return redirect(url_for("home"))
        return render_template("booking_confirmation.html", booking=booking)
    
    return redirect(url_for("my_bookings_page"))



@app.route("/verify")
@login_required
def verify_page():
    """User verification page with document upload."""
    # Get verification status
    verification_status = None
    rejection_reason = None
    
    if hasattr(current_user, 'role'):
        user_type = current_user.role
        user_id = current_user.id
        
        verification = Verification.query.filter_by(
            user_type=user_type,
            user_id=user_id
        ).order_by(Verification.created_at.desc()).first()
        
        if verification:
            verification_status = verification.status
            rejection_reason = verification.rejection_reason
    
    return render_template(
        "verify_upload.html",
        verification_status=verification_status,
        rejection_reason=rejection_reason
    )


@app.route("/api/verification/upload", methods=["POST"])
@login_required
def upload_verification():
    """Handle verification document uploads."""
    try:
        if not hasattr(current_user, 'role'):
            return jsonify({"error": "Invalid user"}), 400
        
        user_type = current_user.role
        user_id = current_user.id
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'verifications')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Get uploaded files
        student_id = request.files.get('student_id')
        college_letter = request.files.get('college_letter')
        gov_id = request.files.get('gov_id')
        electricity_bill = request.files.get('electricity_bill')
        
        # Validate based on user type
        if user_type == 'student':
            if not student_id or not gov_id:
                return jsonify({"error": "Student ID and Government ID are required for students"}), 400
        elif user_type == 'owner':
            if not gov_id or not electricity_bill:
                return jsonify({"error": "Government ID and Electricity Bill are required for owners"}), 400
        
        # Validate file sizes (5MB max)
        max_size = 5 * 1024 * 1024
        for file in [student_id, college_letter, gov_id, electricity_bill]:
            if file and file.filename:
                file.seek(0, 2)  # Seek to end
                size = file.tell()
                file.seek(0)  # Reset
                if size > max_size:
                    return jsonify({"error": f"File {file.filename} exceeds 5MB limit"}), 400
        
        # Save files with unique names
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        student_id_path = None
        if student_id and student_id.filename:
            ext = os.path.splitext(student_id.filename)[1]
            filename = f"{user_type}_{user_id}_studentid_{timestamp}{ext}"
            filepath = os.path.join(upload_dir, filename)
            student_id.save(filepath)
            student_id_path = f"uploads/verifications/{filename}"
        
        college_letter_path = None
        if college_letter and college_letter.filename:
            ext = os.path.splitext(college_letter.filename)[1]
            filename = f"{user_type}_{user_id}_college_{timestamp}{ext}"
            filepath = os.path.join(upload_dir, filename)
            college_letter.save(filepath)
            college_letter_path = f"uploads/verifications/{filename}"
        
        gov_id_path = None
        if gov_id and gov_id.filename:
            ext = os.path.splitext(gov_id.filename)[1]
            filename = f"{user_type}_{user_id}_govid_{timestamp}{ext}"
            filepath = os.path.join(upload_dir, filename)
            gov_id.save(filepath)
            gov_id_path = f"uploads/verifications/{filename}"
        
        electricity_bill_path = None
        if electricity_bill and electricity_bill.filename:
            ext = os.path.splitext(electricity_bill.filename)[1]
            filename = f"{user_type}_{user_id}_electricity_{timestamp}{ext}"
            filepath = os.path.join(upload_dir, filename)
            electricity_bill.save(filepath)
            electricity_bill_path = f"uploads/verifications/{filename}"
        
        # Create verification record
        verification = Verification(
            user_type=user_type,
            user_id=user_id,
            student_id_path=student_id_path,
            college_letter_path=college_letter_path,
            gov_id_path=gov_id_path,
            electricity_bill_path=electricity_bill_path,
            status="pending"
        )
        
        db.session.add(verification)
        
        # Update user verified status to pending
        if user_type == 'student':
            student = Student.query.get(user_id)
            if student:
                student.verified = False
                
                # ============================================================
                # AUTOMATED VERIFICATION (YOLO/OpenCV/EasyOCR)
                # ============================================================
                # If a Student ID was uploaded, try to verify it immediately
                if student_id_path:
                    try:
                        # Get absolute path for the image
                        abs_image_path = os.path.join(app.root_path, 'static', student_id_path)
                        
                        app.logger.info(f"Starting auto-verification for student {user_id}...")
                        app.logger.info(f"Image path: {abs_image_path}")
                        
                        # Run verification logic
                        result = process_verification(abs_image_path, student)
                        
                        app.logger.info(f"Verification result: {result}")
                        
                        if result["verified"]:
                            verification.status = "verified"
                            verification.rejection_reason = "Auto-verified by AI System"
                            verification.reviewed_at = datetime.utcnow()
                            student.verified = True
                            app.logger.info(f"✅ Student {user_id} auto-verified successfully!")
                        else:
                            # Log the failure but keep status as pending for manual review
                            app.logger.warning(f"⚠️ Student {user_id} auto-verification failed: {result['message']}")
                            app.logger.info(f"Extracted data: {result.get('extracted_data', {})}")
                            app.logger.info(f"Checks: {result.get('checks', {})}")
                            verification.rejection_reason = f"AI Check: {result['message']} - Pending manual review"
                            
                    except Exception as e:
                        app.logger.error(f"❌ Auto-verification error for student {user_id}: {str(e)}")
                        import traceback
                        app.logger.error(traceback.format_exc())
                # ============================================================
        
        elif user_type == 'owner':
            owner = Owner.query.get(user_id)
            if owner:
                owner.kyc_verified = False
                
                # ============================================================
                # AUTOMATED VERIFICATION FOR OWNERS
                # ============================================================
                # Check Electricity Bill (preferred for address) or Gov ID
                image_to_verify = None
                if electricity_bill_path:
                    image_to_verify = electricity_bill_path
                elif gov_id_path:
                    image_to_verify = gov_id_path
                
                if image_to_verify:
                    try:
                        abs_image_path = os.path.join(app.root_path, 'static', image_to_verify)
                        result = process_verification(abs_image_path, owner)
                        
                        if result["verified"]:
                            verification.status = "verified"
                            verification.rejection_reason = "Auto-verified by AI System"
                            verification.reviewed_at = datetime.utcnow()
                            owner.kyc_verified = True
                            app.logger.info(f"Owner {user_id} auto-verified successfully.")
                        else:
                            app.logger.info(f"Owner {user_id} auto-verification failed: {result['message']}")
                            verification.rejection_reason = f"AI Check Failed: {result['message']}"
                    except Exception as e:
                        app.logger.error(f"Auto-verification error: {e}")
                # ============================================================
        
        db.session.commit();
        
        return jsonify({
            "success": True,
            "message": "Documents uploaded. AI Verification initiated.",
            "verification_status": verification.status
        }), 200
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Verification upload error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/verification/status", methods=["GET"])
@login_required
def get_verification_status():
    """Get current user's verification status."""
    if not hasattr(current_user, 'role'):
        return jsonify({"error": "Invalid user"}), 400
    
    user_type = current_user.role
    user_id = current_user.id
    
    verification = Verification.query.filter_by(
        user_type=user_type,
        user_id=user_id
    ).order_by(Verification.created_at.desc()).first()
    
    if verification:
        return jsonify({
            "status": verification.status,
            "rejection_reason": verification.rejection_reason,
            "created_at": verification.created_at.isoformat() if verification.created_at else None,
            "reviewed_at": verification.reviewed_at.isoformat() if verification.reviewed_at else None
        }), 200
    else:
        return jsonify({
            "status": "not_submitted",
            "rejection_reason": None
        }), 200


@app.route("/discover")
def discover():
    return render_template("discover.html")


@app.route("/findmate")
def findmate():
    return render_template("findmate.html")


@app.route("/ai-matching")
def ai_matching():
    return render_template("ai_matching.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/faq")
def faq():
    """Frequently Asked Questions page."""
    return render_template("faq.html")


@app.route("/features")
def features_guide():
    """Interactive features guide and navigation."""
    return render_template("features.html")


@app.route("/map-test")
def map_test():
    """Simple map test page."""
    return render_template("map-test.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        try:
            data = request.get_json() if request.is_json else request.form
            name = (data.get("name") or "").strip()
            email = (data.get("email") or "").strip()
            subject = (data.get("subject") or "General Inquiry").strip()
            message = (data.get("message") or "").strip()

            if not all([name, email, message]):
                return jsonify({"error": "Please fill all required fields"}), 400

            contact_msg = ContactMessage(
                name=name,
                email=email,
                subject=subject,
                message=message,
                source="web"
            )
            db.session.add(contact_msg)
            db.session.commit()

            if request.is_json:
                return jsonify({"success": True, "message": "Message sent successfully"})
            flash("Message sent successfully! We'll get back to you soon.", "success")
            return redirect(url_for("contact"))

        except Exception as e:
            app.logger.exception("Contact form error")
            if request.is_json:
                return jsonify({"error": "Failed to send message"}), 500
            flash("Failed to send message. Please try again.", "error")
            return redirect(url_for("contact"))

    return render_template("contact.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        role = (request.form.get("role") or "").strip().lower()

        if role not in {"student", "owner"}:
            flash("Please choose a valid role.", "error")
            return redirect(url_for("login"))

        model = Student if role == "student" else Owner
        user = model.query.filter(func.lower(model.email) == email).first()

        if user is None or not user.verify_password(password):
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))

        login_user(user)
        flash("Welcome back to Roomies!", "success")
        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        college = (request.form.get("college") or "").strip() or "Unknown"
        role = (request.form.get("role") or "student").strip().lower()

        if not all([name, email, password]):
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("signup"))

        email_taken = (
            Owner.query.filter(func.lower(Owner.email) == email).first()
            or Student.query.filter(func.lower(Student.email) == email).first()
        )
        if email_taken:
            flash("An account with that email already exists.", "error")
            return redirect(url_for("signup"))

        if role == "owner":
            owner = Owner(email=email, name=name, kyc_verified=False)
            owner.set_password(password)
            db.session.add(owner)
            db.session.commit()
            flash("Owner account created. Please sign in.", "success")
            return redirect(url_for("login"))

        student = Student(email=email, name=name, college=college, role="student")
        student.set_password(password)
        db.session.add(student)
        db.session.commit()
        login_user(student)
        flash("Account created successfully!", "success")
        return redirect(url_for("home"))

    return render_template("signup.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("home"))


# ---------------------------------------------------------------------------
# OAuth Routes (Supabase)
# ---------------------------------------------------------------------------
@app.route("/auth/google")
def auth_google():
    """Initiate Google OAuth login via Supabase."""
    if not OAUTH_ENABLED:
        flash("Google login is not available at this time.", "error")
        return redirect(url_for("login"))
    
    # Get role from query params (student or owner)
    role = request.args.get("role", "student").lower()
    if role not in {"student", "owner"}:
        role = "student"
    
    # Store role in session for callback
    from flask import session
    session["oauth_role"] = role
    
    # Generate OAuth URL
    redirect_url = url_for("auth_callback", _external=True)
    success, url_or_error = get_google_oauth_url(redirect_url)
    
    if success:
        return redirect(url_or_error)
    else:
        flash(f"Google login error: {url_or_error}", "error")
        return redirect(url_for("login"))


@app.route("/auth/github")
def auth_github():
    """Initiate GitHub OAuth login via Supabase."""
    if not OAUTH_ENABLED:
        flash("GitHub login is not available at this time.", "error")
        return redirect(url_for("login"))
    
    # Get role from query params (student or owner)
    role = request.args.get("role", "student").lower()
    if role not in {"student", "owner"}:
        role = "student"
    
    # Store role in session for callback
    from flask import session
    session["oauth_role"] = role
    
    # Generate OAuth URL
    redirect_url = url_for("auth_callback", _external=True)
    success, url_or_error = get_github_oauth_url(redirect_url)
    
    if success:
        return redirect(url_or_error)
    else:
        flash(f"GitHub login error: {url_or_error}", "error")
        return redirect(url_for("login"))


@app.route("/auth/callback")
def auth_callback():
    """Handle OAuth callback from Supabase."""
    from flask import session
    
    # Get the authorization code or access token from callback
    code = request.args.get("code")
    access_token = request.args.get("access_token")
    error = request.args.get("error")
    error_description = request.args.get("error_description")
    
    if error:
        flash(f"Authentication failed: {error_description or error}", "error")
        return redirect(url_for("login"))
    
    if not code and not access_token:
        flash("Authentication failed: No authorization code received.", "error")
        return redirect(url_for("login"))
    
    # Handle the OAuth callback
    success, user_data = handle_oauth_callback(code=code, access_token=access_token)
    
    if not success:
        error_msg = user_data.get("error", "Unknown error") if isinstance(user_data, dict) else "Unknown error"
        flash(f"Authentication failed: {error_msg}", "error")
        return redirect(url_for("login"))
    
    # Extract user information
    email = user_data.get("email", "").lower()
    name = user_data.get("name", "OAuth User")
    provider = user_data.get("provider", "oauth")
    
    if not email:
        flash("Could not retrieve email from OAuth provider.", "error")
        return redirect(url_for("login"))
    
    # Get role from session (default to student)
    role = session.pop("oauth_role", "student")
    
    # Check if user already exists in either table
    existing_student = Student.query.filter(func.lower(Student.email) == email).first()
    existing_owner = Owner.query.filter(func.lower(Owner.email) == email).first()
    
    if existing_student:
        # Login existing student
        login_user(existing_student)
        flash(f"Welcome back, {existing_student.name}! (via {provider.title()})", "success")
        return redirect(url_for("home"))
    
    if existing_owner:
        # Login existing owner
        login_user(existing_owner)
        flash(f"Welcome back, {existing_owner.name}! (via {provider.title()})", "success")
        return redirect(url_for("home"))
    
    # Create new user based on role
    try:
        if role == "owner":
            owner = Owner(
                email=email,
                name=name,
                kyc_verified=False
            )
            # Set a random secure password (user won't use it with OAuth)
            import secrets
            owner.set_password(secrets.token_urlsafe(32))
            db.session.add(owner)
            db.session.commit()
            
            login_user(owner)
            flash(f"Welcome to Roomies, {name}! Your owner account has been created via {provider.title()}.", "success")
        else:
            student = Student(
                email=email,
                name=name,
                college="Not specified",  # OAuth users can update this later
                role="student",
                verified=True  # OAuth accounts are considered email-verified
            )
            # Set a random secure password (user won't use it with OAuth)
            import secrets
            student.set_password(secrets.token_urlsafe(32))
            db.session.add(student)
            db.session.commit()
            
            login_user(student)
            flash(f"Welcome to Roomies, {name}! Your account has been created via {provider.title()}.", "success")
        
        return redirect(url_for("home"))
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"OAuth user creation failed: {e}")
        flash("Failed to create account. Please try again or use email signup.", "error")
        return redirect(url_for("signup"))


@app.route("/api/oauth/status")
def oauth_status():
    """Check if OAuth providers are available."""
    return jsonify({
        "oauth_enabled": OAUTH_ENABLED,
        "providers": {
            "google": OAUTH_ENABLED,
            "github": OAUTH_ENABLED
        }
    })


@app.route("/settings")
@login_required
def settings():
    """User settings page."""
    return render_template("settings.html")


# ---------------------------------------------------------------------------
# Routes - APIs
# ---------------------------------------------------------------------------
@app.route("/api/rooms")
def api_rooms():
    try:
        include_unverified = request.args.get("include_unverified", "0").lower() in {"1", "true", "yes"}
        college = (request.args.get("college") or "").strip()
        city = (request.args.get("city") or "").strip()
        search = (request.args.get("q") or "").strip()
        property_type = (request.args.get("property_type") or "").strip().lower()
        max_rent = request.args.get("max_rent", type=int)
        min_available = request.args.get("min_available", type=int)
        limit = request.args.get("limit", type=int) or 50
        offset = request.args.get("offset", type=int) or 0
        sort_key = (request.args.get("sort") or "price_asc").lower()

        query = Room.query
        if not include_unverified:
            query = query.filter(Room.verified.is_(True))
        if college:
            query = query.filter(Room.college_nearby.ilike(f"%{college}%"))
        if city:
            query = query.filter(Room.location.ilike(f"%{city}%"))
        if search:
            like = f"%{search}%"
            query = query.filter(
                or_(
                    Room.title.ilike(like),
                    Room.location.ilike(like),
                    Room.college_nearby.ilike(like),
                )
            )
        if property_type:
            query = query.filter(func.lower(Room.property_type) == property_type)
        if max_rent is not None:
            query = query.filter(Room.price <= max_rent)
        if min_available is not None:
            query = query.filter((Room.capacity_total - Room.capacity_occupied) >= min_available)

        sort_map = {
            "price_desc": Room.price.desc(),
            "price_asc": Room.price.asc(),
            "newest": Room.created_at.desc(),
            "slots_desc": (Room.capacity_total - Room.capacity_occupied).desc(),
        }
        order_clause = sort_map.get(sort_key, sort_map["price_asc"])
        query = query.order_by(order_clause, Room.id.asc())

        total = query.count()
        rooms = query.offset(offset).limit(limit).all()

        return jsonify(
            {
                "rooms": [room.to_dict() for room in rooms],
                "meta": {
                    "total": total,
                    "returned": len(rooms),
                    "offset": offset,
                    "limit": limit,
                },
            }
        )
    except SQLAlchemyError:
        app.logger.exception("Room search failed", extra={"args": request.args})
        return jsonify({"error": "Unable to fetch rooms at this time."}), 500

@app.route("/api/room/<int:room_id>")
def api_room_detail(room_id):
    """Get single room details as JSON."""
    try:
        room = Room.query.get_or_404(room_id)
        # Ensure availability status is included
        data = room.to_dict()
        data['availability_status'] = room.availability_status
        data['available_slots'] = room.available_slots
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"API Room Detail Error: {e}")
        return jsonify({"error": "Room not found"}), 404

@app.route("/api/colleges")
def api_colleges():
    """Get list of unique colleges for autocomplete/filter."""
    try:
        colleges = db.session.query(Room.college_nearby).distinct().order_by(Room.college_nearby).all()
        return jsonify([c[0] for c in colleges if c[0]])
    except Exception as e:
        app.logger.error(f"Failed to fetch colleges: {e}")
        return jsonify([]), 500

@app.route("/api/suggestions")
def api_suggestions():
    """Get search suggestions for rooms, locations, and colleges."""
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify([])
    
    try:
        # Search Colleges
        colleges = db.session.query(Room.college_nearby)\
            .filter(Room.college_nearby.ilike(f"%{q}%"))\
            .distinct().limit(3).all()
            
        # Search Locations
        locations = db.session.query(Room.location)\
            .filter(Room.location.ilike(f"%{q}%"))\
            .distinct().limit(3).all()
            
        # Search Room Titles
        titles = db.session.query(Room.title)\
            .filter(Room.title.ilike(f"%{q}%"))\
            .distinct().limit(3).all()
            
        results = []
        for c in colleges:
            if c[0]: results.append({"type": "College", "text": c[0]})
        for l in locations:
            if l[0]: results.append({"type": "Location", "text": l[0]})
        for t in titles:
            if t[0]: results.append({"type": "Room", "text": t[0]})
            
        return jsonify(results)
    except Exception as e:
        app.logger.error(f"Suggestion API error: {e}")
        return jsonify([])

@app.route("/api/owner/listings", methods=["POST"])
@login_required
def create_listing():
    owner = get_current_owner()
    is_student_listing = False
    
    # If not an owner, check if student
    if owner is None:
        student = get_current_student()
        if student:
            # Student is listing a room -> Use System Owner as placeholder
            system_owner = Owner.query.filter_by(email="system@roomies.in").first()
            if not system_owner:
                # Lazy creation of system owner
                try:
                    system_owner = Owner(
                        email="system@roomies.in",
                        name="Roomies System",
                        kyc_verified=True
                    )
                    system_owner.set_password("system123")
                    db.session.add(system_owner)
                    db.session.commit()
                    app.logger.info("Created System Owner for student listing")
                except Exception as e:
                    db.session.rollback()
                    app.logger.error(f"Failed to create system owner: {e}")
                    return jsonify({"error": "System configuration error. Please contact support."}), 500
            
            owner = system_owner
            is_student_listing = True
        else:
            return jsonify({"error": "Only owners or students can publish listings."}), 403

    payload = request.get_json(silent=True) or {}

    required_fields = {
        "title": str,
        "price": int,
        "location": str,
        "college": str,
        "property_type": str,
        "capacity_total": int,
    }

    missing = [field for field in required_fields if payload.get(field) in (None, "")]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    try:
        total_capacity = int(payload["capacity_total"])
        occupied = int(payload.get("capacity_occupied", 0))
        price = int(payload["price"])
    except (TypeError, ValueError):
        return jsonify({"error": "Capacity and price must be numeric."}), 400

    occupied = max(min(occupied, total_capacity), 0)
    images = payload.get("images") or ""
    if isinstance(images, list):
        images = ",".join(images)

    def _to_float(field: str) -> Optional[float]:
        raw = payload.get(field)
        if raw in (None, ""):
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            raise ValueError(f"{field} must be numeric")

    try:
        latitude = _to_float("latitude")
        longitude = _to_float("longitude")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    # Append student info to title if applicable
    title = payload["title"].strip()
    if is_student_listing:
         student = get_current_student() # Re-fetch to be safe or use variable from scope
         if student:
             title = f"{title} (Listed by {student.name})"

    room = Room(
        title=title,
        price=price,
        location=payload["location"].strip(),
        college_nearby=payload["college"].strip(),
        amenities=payload.get("amenities", ""),
        images=images,
        property_type=payload.get("property_type", "shared").strip().lower() or "shared",
        capacity_total=total_capacity,
        capacity_occupied=occupied,
        latitude=latitude,
        longitude=longitude,
        verified=False,
        owner=owner,
    )
    room.capacity_total = max(room.capacity_total, 1)
    room.capacity_occupied = min(max(room.capacity_occupied, 0), room.capacity_total)

    try:
        db.session.add(room)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception("Failed to create listing", extra={"owner": owner.id})
        return jsonify({"error": "We could not publish this listing just yet."}), 500

    return jsonify(room.to_dict()), 201


@app.route("/api/search/autocomplete")
def search_autocomplete():
    """
    DSA-powered Autocomplete Search using Trie.
    Returns rooms that match the prefix.
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"results": []})
    
    # 1. Search Trie for matching Room IDs
    room_ids = search_trie.search(query)
    
    if not room_ids:
        return jsonify({"results": []})
    
    # 2. Fetch full room details from DB
    # Optimization: In a real app, cache these or store minimal data in Trie
    rooms = Room.query.filter(Room.id.in_(room_ids)).limit(20).all()
    
    return jsonify({
        "results": [room.to_dict() for room in rooms],
        "count": len(rooms)
    })


# ---------------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        admin = Admin.query.filter(func.lower(Admin.email) == email).first()

        if admin is None or not admin.verify_password(password):
            flash("Invalid admin credentials.", "error")
            return redirect(url_for("admin_login"))

        login_user(admin)
        flash("Welcome to Roomies Admin Panel!", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin/login.html")


@app.route("/admin")
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    # Analytics queries
    total_users = Student.query.count() + Owner.query.count()
    total_students = Student.query.count()
    total_owners = Owner.query.count()
    total_listings = Room.query.count()
    verified_listings = Room.query.filter_by(verified=True).count()
    pending_listings = Room.query.filter_by(verified=False).count()
    total_messages = ContactMessage.query.count()
    
    # Revenue analytics
    from datetime import date
    from sqlalchemy import extract
    
    today = date.today()
    current_month_revenue = db.session.query(
        Analytics.metric_type,
        func.sum(Analytics.amount).label('total'),
        func.sum(Analytics.count).label('transactions')
    ).filter(
        extract('month', Analytics.date) == today.month,
        extract('year', Analytics.date) == today.year
    ).group_by(Analytics.metric_type).all()
    
    # Calculate total revenue
    total_revenue = sum(row.total for row in current_month_revenue if row.total)
    
    # Active subscriptions
    active_subscriptions = Subscription.query.filter_by(status="active").count()
    
    # Active flash deals
    active_flash_deals = FlashDeal.query.filter(
        FlashDeal.is_active == True,
        FlashDeal.expires_at > datetime.utcnow()
    ).count()
    
    # Total bookings
    total_bookings = Booking.query.count()
    confirmed_bookings = Booking.query.filter_by(booking_status="confirmed").count()
    
    # Wallet balances
    total_wallet_balance = db.session.query(func.sum(Wallet.balance)).scalar() or 0.0
    
    # Listings by city
    listings_by_city = db.session.query(
        Room.location,
        func.count(Room.id).label('count')
    ).group_by(Room.location).order_by(func.count(Room.id).desc()).limit(10).all()
    
    # Top colleges
    top_colleges = db.session.query(
        Room.college_nearby,
        func.count(Room.id).label('count')
    ).group_by(Room.college_nearby).order_by(func.count(Room.id).desc()).limit(10).all()
    
    # Recent listings
    recent_listings = Room.query.order_by(Room.created_at.desc()).limit(10).all()
    
    # Revenue breakdown
    revenue_breakdown = {}
    for row in current_month_revenue:
        revenue_breakdown[row.metric_type] = {
            'amount': row.total,
            'count': row.transactions
        }
    
    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_students=total_students,
        total_owners=total_owners,
        total_listings=total_listings,
        verified_listings=verified_listings,
        pending_listings=pending_listings,
        total_messages=total_messages,
        listings_by_city=listings_by_city,
        top_colleges=top_colleges,
        recent_listings=recent_listings,
        total_revenue=total_revenue,
        revenue_breakdown=revenue_breakdown,
        active_subscriptions=active_subscriptions,
        active_flash_deals=active_flash_deals,
        total_bookings=total_bookings,
        confirmed_bookings=confirmed_bookings,
        total_wallet_balance=total_wallet_balance,
    )


@app.route("/admin/verifications")
@admin_required
def admin_verifications():
    """Admin page to review verification requests."""
    # Get all verifications with user details
    verifications = Verification.query.order_by(
        Verification.created_at.desc()
    ).all()
    
    # Enrich with user details
    enriched_verifications = []
    for verification in verifications:
        if verification.user_type == 'student':
            user = Student.query.get(verification.user_id)
            user_college = user.college if user else None
        else:
            user = Owner.query.get(verification.user_id)
            user_college = None
        
        if user:
            enriched_verifications.append({
                'id': verification.id,
                'user_name': user.name,
                'user_email': user.email,
                'user_type': verification.user_type,
                'user_college': user_college,
                'student_id_path': verification.student_id_path,
                'college_letter_path': verification.college_letter_path,
                'gov_id_path': verification.gov_id_path,
                'electricity_bill_path': verification.electricity_bill_path,
                'status': verification.status,
                'rejection_reason': verification.rejection_reason,
                'created_at': verification.created_at,
                'reviewed_at': verification.reviewed_at
            })
    
    # Calculate stats
    stats = {
        'total': len(verifications),
        'pending': Verification.query.filter_by(status='pending').count(),
        'verified': Verification.query.filter_by(status='verified').count(),
        'rejected': Verification.query.filter_by(status='rejected').count(),
    }
    
    return render_template(
        "admin_verifications.html",
        verifications=enriched_verifications,
        stats=stats
    )


@app.route("/api/admin/verification/<int:verification_id>/approve", methods=["POST"])
@admin_required
def approve_verification(verification_id):
    """Approve a verification request."""
    try:
        verification = Verification.query.get(verification_id)
        if not verification:
            return jsonify({"error": "Verification not found"}), 404
        
        verification.status = 'verified'
        verification.reviewed_by = current_user.id
        verification.reviewed_at = datetime.utcnow()
        
        # Update user verified status
        if verification.user_type == 'student':
            user = Student.query.get(verification.user_id)
            if user:
                user.verified = True
        elif verification.user_type == 'owner':
            user = Owner.query.get(verification.user_id)
            if user:
                user.kyc_verified = True
        
        db.session.commit()
        
        # Send notification email
        email_service.send_verification_approved_email(user, verification.user_type)
        
        return jsonify({
            "success": True,
            "message": "Verification approved successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error approving verification: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/verification/<int:verification_id>/reject", methods=["POST"])
@admin_required
def reject_verification(verification_id):
    """Reject a verification request."""
    try:
        data = request.get_json()
        reason = data.get('reason', 'Documents do not meet requirements')
        
        verification = Verification.query.get(verification_id)
        if not verification:
            return jsonify({"error": "Verification not found"}), 404
        
        verification.status = 'rejected'
        verification.rejection_reason = reason
        verification.reviewed_by = current_user.id
        verification.reviewed_at = datetime.utcnow()
        
        # Update user verified status
        if verification.user_type == 'student':
            user = Student.query.get(verification.user_id)
            if user:
                user.verified = False
        elif verification.user_type == 'owner':
            user = Owner.query.get(verification.user_id)
            if user:
                user.kyc_verified = False
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Verification rejected"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error rejecting verification: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/admin/listings")
@admin_required
def admin_listings():
    page = request.args.get("page", 1, type=int)
    status_filter = request.args.get("status", "all")
    
    query = Room.query
    if status_filter == "pending":
        query = query.filter_by(verified=False)
    elif status_filter == "verified":
        query = query.filter_by(verified=True)
    
    per_page = getattr(config, "ITEMS_PER_PAGE", 50) if config else 50
    pagination = query.order_by(Room.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template(
        "admin/listings.html",
        listings=pagination.items,
        pagination=pagination,
        status_filter=status_filter,
    )


@app.route("/admin/listings/<int:listing_id>/approve", methods=["POST"])
@admin_required
def approve_listing(listing_id):
    room = Room.query.get_or_404(listing_id)
    room.verified = True
    try:
        db.session.commit()
        flash(f"Listing '{room.title}' has been approved.", "success")
    except SQLAlchemyError:
        db.session.rollback()
        flash("Failed to approve listing.", "error")
    return redirect(request.referrer or url_for("admin_listings"))


@app.route("/admin/listings/<int:listing_id>/reject", methods=["POST"])
@admin_required
def reject_listing(listing_id):
    room = Room.query.get_or_404(listing_id)
    room.verified = False
    try:
        db.session.commit()
        flash(f"Listing '{room.title}' has been rejected.", "warning")
    except SQLAlchemyError:
        db.session.rollback()
        flash("Failed to reject listing.", "error")
    return redirect(request.referrer or url_for("admin_listings"))


@app.route("/admin/listings/<int:listing_id>/delete", methods=["POST"])
@admin_required
def delete_listing(listing_id):
    room = Room.query.get_or_404(listing_id)
    title = room.title
    try:
        db.session.delete(room)
        db.session.commit()
        flash(f"Listing '{title}' has been deleted.", "success")
    except SQLAlchemyError:
        db.session.rollback()
        flash("Failed to delete listing.", "error")
    return redirect(request.referrer or url_for("admin_listings"))


@app.route("/admin/users")
@admin_required
def admin_users():
    page = request.args.get("page", 1, type=int)
    role_filter = request.args.get("role", "all")
    
    per_page = getattr(config, "ITEMS_PER_PAGE", 50) if config else 50
    
    if role_filter == "students":
        students = Student.query.order_by(Student.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        owners = None
    elif role_filter == "owners":
        owners = Owner.query.order_by(Owner.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        students = None
    else:
        students = Student.query.order_by(Student.created_at.desc()).limit(25).all()
        owners = Owner.query.order_by(Owner.created_at.desc()).limit(25).all()
    
    return render_template(
        "admin/users.html",
        students=students,
        owners=owners,
        role_filter=role_filter,
    )


@app.route("/admin/users/students/<int:user_id>/verify", methods=["POST"])
@admin_required
def verify_student(user_id):
    student = Student.query.get_or_404(user_id)
    student.verified = True
    try:
        db.session.commit()
        flash(f"Student '{student.name}' has been verified.", "success")
    except SQLAlchemyError:
        db.session.rollback()
        flash("Failed to verify student.", "error")
    return redirect(request.referrer or url_for("admin_users"))


@app.route("/admin/users/owners/<int:user_id>/verify", methods=["POST"])
@admin_required
def verify_owner(user_id):
    owner = Owner.query.get_or_404(user_id)
    owner.kyc_verified = True
    try:
        db.session.commit()
        flash(f"Owner '{owner.name}' has been verified.", "success")
    except SQLAlchemyError:
        db.session.rollback()
        flash("Failed to verify owner.", "error")
    return redirect(request.referrer or url_for("admin_users"))


@app.route("/admin/messages")
@admin_required
def admin_messages():
    page = request.args.get("page", 1, type=int)
    per_page = getattr(config, "ITEMS_PER_PAGE", 50) if config else 50
    
    pagination = ContactMessage.query.order_by(ContactMessage.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template(
        "admin/messages.html",
        messages=pagination.items,
        pagination=pagination,
    )


@app.route("/admin/logout")
@admin_required
def admin_logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("admin_login"))


@app.route("/admin/export/<entity>")
@login_required
@admin_required
def admin_export_entity(entity):
    """Export specific data entity to Excel."""
    try:
        import pandas as pd
        import io
        
        output = io.BytesIO()
        filename = f'roomies_{entity}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if entity == 'hostels':
                rooms = Room.query.all()
                data = [{
                    "id": r.id, "title": r.title, "price": r.price, 
                    "location": r.location, "college": r.college_nearby,
                    "latitude": r.latitude, "longitude": r.longitude,
                    "owner_id": r.owner_id, "verified": r.verified,
                    "property_type": r.property_type, "capacity_total": r.capacity_total
                } for r in rooms]
                pd.DataFrame(data).to_excel(writer, sheet_name='Rooms', index=False)
                
            elif entity == 'owners':
                owners = Owner.query.all()
                data = [{
                    "id": o.id, "name": o.name, "email": o.email, 
                    "kyc_verified": o.kyc_verified
                } for o in owners]
                pd.DataFrame(data).to_excel(writer, sheet_name='Owners', index=False)
                
            elif entity == 'students':
                students = Student.query.all()
                data = [{
                    "id": s.id, "name": s.name, "email": s.email, 
                    "college": s.college, "verified": s.verified
                } for s in students]
                pd.DataFrame(data).to_excel(writer, sheet_name='Students', index=False)
            
            else:
                flash("Invalid entity type", "error")
                return redirect(url_for("admin_dashboard"))

        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        app.logger.error(f"Export failed: {e}")
        flash(f"Export failed: {str(e)}", "danger")
        return redirect(url_for("admin_dashboard"))

@app.route("/admin/import/<entity>", methods=["POST"])
@login_required
@admin_required
def admin_import_entity(entity):
    """Import specific data entity from Excel."""
    try:
        import pandas as pd
        
        if 'file' not in request.files:
            flash("No file part", "error")
            return redirect(url_for("admin_dashboard"))
        
        file = request.files['file']
        if file.filename == '':
            flash("No selected file", "error")
            return redirect(url_for("admin_dashboard"))
            
        if file:
            xls = pd.ExcelFile(file)
            # Default sheet name matches entity, but allow fallback to first sheet
            sheet_name = entity.capitalize()
            if entity == 'hostels': sheet_name = 'Rooms'
            
            if sheet_name not in xls.sheet_names:
                # If specific sheet not found, try the first sheet
                df = pd.read_excel(xls, 0)
            else:
                df = pd.read_excel(xls, sheet_name)
            
            if entity == 'owners':
                count = 0
                for _, row in df.iterrows():
                    email = str(row.get('email', '')).strip()
                    if email and email != 'nan':
                        owner = Owner.query.filter_by(email=email).first()
                        if not owner:
                            owner = Owner(
                                email=email,
                                name=row.get('name', 'Unknown'),
                                kyc_verified=bool(row.get('kyc_verified', False))
                            )
                            owner.set_password("welcome123")
                            db.session.add(owner)
                            count += 1
                flash(f"Imported {count} owners.", "success")

            elif entity == 'students':
                count = 0
                for _, row in df.iterrows():
                    email = str(row.get('email', '')).strip()
                    if email and email != 'nan':
                        student = Student.query.filter_by(email=email).first()
                        if not student:
                            student = Student(
                                email=email,
                                name=row.get('name', 'Unknown'),
                                college=row.get('college', 'Unknown'),
                                verified=bool(row.get('verified', False))
                            )
                            student.set_password("welcome123")
                            db.session.add(student)
                            count += 1
                flash(f"Imported {count} students.", "success")

            elif entity == 'hostels':
                count = 0
                # Ensure system owner exists
                system_owner = Owner.query.filter_by(email="system@roomies.in").first()
                if not system_owner:
                    system_owner = Owner(email="system@roomies.in", name="System", kyc_verified=True)
                    system_owner.set_password("system123")
                    db.session.add(system_owner)
                    db.session.commit()

                for _, row in df.iterrows():
                    title = row.get('title', 'Untitled')
                    location = row.get('location', 'Unknown')
                    
                    # Try to find owner
                    owner_email = str(row.get('owner_email', '')).strip()
                    owner = None
                    if owner_email and owner_email != 'nan':
                        owner = Owner.query.filter_by(email=owner_email).first()
                    
                    if not owner:
                        owner = system_owner

                    existing_room = Room.query.filter_by(title=title, location=location).first()
                    if not existing_room:
                        room = Room(
                            title=title,
                            price=float(row.get('price', 0)),
                            location=location,
                            college_nearby=row.get('college', 'Unknown'),
                            latitude=float(row.get('latitude', 0.0)) if pd.notna(row.get('latitude')) else None,
                            longitude=float(row.get('longitude', 0.0)) if pd.notna(row.get('longitude')) else None,
                            owner_id=owner.id,
                            verified=bool(row.get('verified', False)),
                            property_type=row.get('property_type', 'shared'),
                            capacity_total=int(row.get('capacity_total', 1))
                        )
                        db.session.add(room)
                        count += 1
                flash(f"Imported {count} hostels.", "success")
            
            db.session.commit()
            if entity == 'hostels':
                rebuild_search_index()
            
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Import failed: {e}")
        flash(f"Import failed: {str(e)}", "error")
        
    return redirect(url_for("admin_dashboard"))


# ============= FLASH DEALS API =============

@app.route("/api/flash-deals", methods=["GET"])
def get_flash_deals():
    """Get all active flash deals (not expired)."""
    try:
        now = datetime.utcnow()
        deals = FlashDeal.query.filter(
            FlashDeal.is_active == True,
            FlashDeal.expires_at > now
        ).all()
        
        return jsonify({
            "deals": [deal.to_dict() for deal in deals],
            "count": len(deals),
        })
    except SQLAlchemyError:
        app.logger.exception("Failed to fetch flash deals")
        return jsonify({"error": "Unable to fetch flash deals"}), 500


@app.route("/api/flash-deals/create", methods=["POST"])
@login_required
def create_flash_deal():
    """Create a flash deal (owners only) - ₹29 fee."""
    owner = get_current_owner()
    if owner is None:
        return jsonify({"error": "Only owners can create flash deals."}), 403
    
    try:
        data = request.get_json()
        room_id = data.get("room_id")
        deal_price = data.get("deal_price")
        
        room = Room.query.filter_by(id=room_id, owner_id=owner.id).first()
        if not room:
            return jsonify({"error": "Room not found or not yours."}), 404
        
        # Check if already has active deal
        existing = FlashDeal.query.filter_by(
            room_id=room_id,
            is_active=True
        ).filter(FlashDeal.expires_at > datetime.utcnow()).first()
        
        if existing:
            return jsonify({"error": "Room already has an active flash deal."}), 400
        
        deal = FlashDeal(
            room_id=room_id,
            original_price=room.price,
            deal_price=deal_price,
            expires_at=datetime.utcnow() + timedelta(hours=24),
            is_active=True,
            fee_paid=29.0,
        )
        db.session.add(deal)
        
        # Record revenue in analytics
        analytics = Analytics(
            date=datetime.utcnow().date(),
            metric_type="flash_deal_revenue",
            amount=29.0,
            count=1,
            notes=f"Flash deal created for room {room_id}",
        )
        db.session.add(analytics)
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "deal": deal.to_dict(),
            "message": "Flash deal created! ₹29 fee charged.",
        })
    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception("Failed to create flash deal")
        return jsonify({"error": "Failed to create flash deal"}), 500


@app.route("/api/flash-deals/<int:deal_id>/deactivate", methods=["POST"])
@login_required
def deactivate_flash_deal(deal_id):
    """Deactivate a flash deal early."""
    owner = get_current_owner()
    if owner is None:
        return jsonify({"error": "Only owners can deactivate deals."}), 403
    
    deal = FlashDeal.query.get_or_404(deal_id)
    if deal.room.owner_id != owner.id:
        return jsonify({"error": "Not your deal."}), 403
    
    deal.is_active = False
    try:
        db.session.commit()
        return jsonify({"success": True, "message": "Flash deal deactivated."})
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Failed to deactivate deal"}), 500


# ============= SUBSCRIPTIONS API (Stripe) =============

@app.route("/api/subscriptions/create", methods=["POST"])
@login_required
def create_subscription():
    """Create Owner Pro subscription - ₹199/mo."""
    owner = get_current_owner()
    if owner is None:
        return jsonify({"error": "Only owners can subscribe."}), 403
    
    # Check if already subscribed
    existing = Subscription.query.filter_by(
        owner_id=owner.id,
        status="active"
    ).first()
    
    if existing and existing.is_active:
        return jsonify({"error": "You already have an active subscription."}), 400
    
    # TODO: Integrate with Stripe API
    # For now, create a mock subscription
    subscription = Subscription(
        owner_id=owner.id,
        stripe_subscription_id=f"mock_sub_{owner.id}_{datetime.utcnow().timestamp()}",
        status="active",
        plan_price=199.0,
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=30),
    )
    db.session.add(subscription)
    
    # Record revenue
    analytics = Analytics(
        date=datetime.utcnow().date(),
        metric_type="subscription_revenue",
        amount=199.0,
        count=1,
        notes=f"Owner Pro subscription for owner {owner.id}",
    )
    db.session.add(analytics)
    
    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "subscription": subscription.to_dict(),
            "message": "Subscription activated! You are now Owner Pro.",
        })
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Failed to create subscription"}), 500


@app.route("/api/subscriptions/my", methods=["GET"])
@login_required
def my_subscription():
    """Get current user's subscription status."""
    owner = get_current_owner()
    if owner is None:
        return jsonify({"error": "Only owners have subscriptions."}), 403
    
    subscription = Subscription.query.filter_by(
        owner_id=owner.id,
        status="active"
    ).first()
    
    if subscription:
        return jsonify({
            "has_subscription": True,
            "subscription": subscription.to_dict(),
        })
    else:
        return jsonify({
            "has_subscription": False,
        })


# ============= REFERRAL & WALLET SYSTEM =============

@app.route("/api/referrals/my-code", methods=["GET"])
@login_required
def my_referral_code():
    """Get or create referral code for student."""
    student = get_current_student()
    if student is None:
        return jsonify({"error": "Only students can have referral codes."}), 403
    
    # Check if already has a code
    referral = Referral.query.filter_by(referrer_id=student.id).first()
    if not referral:
        # Generate unique code
        code = f"ROOM{student.id}{datetime.utcnow().timestamp():.0f}"[-10:]
        referral = Referral(
            referrer_id=student.id,
            referral_code=code,
            status="pending",
        )
        db.session.add(referral)
        db.session.commit()
    
    return jsonify({
        "referral_code": referral.referral_code,
        "total_referrals": Referral.query.filter_by(
            referrer_id=student.id,
            status="completed"
        ).count(),
    })


@app.route("/api/referrals/apply", methods=["POST"])
@login_required
def apply_referral():
    """Apply referral code during signup - gives ₹200 to both parties."""
    student = get_current_student()
    if student is None:
        return jsonify({"error": "Only students can use referrals."}), 403
    
    data = request.get_json()
    code = data.get("referral_code", "").strip()
    
    if not code:
        return jsonify({"error": "Referral code required."}), 400
    
    # Find referral
    referral = Referral.query.filter_by(referral_code=code).first()
    if not referral:
        return jsonify({"error": "Invalid referral code."}), 404
    
    if referral.referrer_id == student.id:
        return jsonify({"error": "Cannot use your own referral code."}), 400
    
    # Check if already used a referral
    existing = Referral.query.filter_by(referred_id=student.id).first()
    if existing:
        return jsonify({"error": "You have already used a referral code."}), 400
    
    # Mark as completed and credit wallets
    referral.referred_id = student.id
    referral.status = "completed"
    
    # Credit ₹200 to both parties
    referrer_wallet = Wallet.query.filter_by(student_id=referral.referrer_id).first()
    if not referrer_wallet:
        referrer_wallet = Wallet(student_id=referral.referrer_id, balance=0.0)
        db.session.add(referrer_wallet)
    
    referred_wallet = Wallet.query.filter_by(student_id=student.id).first()
    if not referred_wallet:
        referred_wallet = Wallet(student_id=student.id, balance=0.0)
        db.session.add(referred_wallet)
    
    referrer_wallet.balance += 200.0
    referred_wallet.balance += 200.0
    
    # Record transactions
    db.session.add(WalletTransaction(
        wallet_id=referrer_wallet.id,
        transaction_type="credit",
        amount=200.0,
        description="Referral reward",
        reference_id=f"ref_{referral.id}",
    ))
    
    db.session.add(WalletTransaction(
        wallet_id=referred_wallet.id,
        transaction_type="credit",
        amount=200.0,
        description="Referral signup bonus",
        reference_id=f"ref_{referral.id}",
    ))
    
    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "₹200 credited to your wallet!",
            "wallet_balance": referred_wallet.balance,
        })
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Failed to apply referral"}), 500


@app.route("/api/wallet/balance", methods=["GET"])
@login_required
def wallet_balance():
    """Get wallet balance for student."""
    student = get_current_student()
    if student is None:
        return jsonify({"error": "Only students can have wallets."}), 403
    
    wallet = Wallet.query.filter_by(student_id=student.id).first()
    if not wallet:
        wallet = Wallet(student_id=student.id, balance=0.0)
        db.session.add(wallet)
        db.session.commit()
    
    return jsonify({
        "balance": wallet.balance,
        "student_id": student.id,
    })


@app.route("/api/wallet/transactions", methods=["GET"])
@login_required
def wallet_transactions():
    """Get wallet transaction history."""
    student = get_current_student()
    if student is None:
        return jsonify({"error": "Only students can have wallets."}), 403
    
    wallet = Wallet.query.filter_by(student_id=student.id).first()
    if not wallet:
        return jsonify({"transactions": []})
    
    transactions = WalletTransaction.query.filter_by(
        wallet_id=wallet.id
    ).order_by(WalletTransaction.created_at.desc()).limit(50).all()
    
    return jsonify({
        "transactions": [{
            "id": t.id,
            "type": t.transaction_type,
            "amount": t.amount,
            "description": t.description,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        } for t in transactions]
    })


# ============= SUBSCRIPTION & REVENUE SYSTEM =============

@app.route("/api/subscription-plans", methods=["GET"])
def get_subscription_plans():
    """Get all active subscription plans."""
    user_type = request.args.get("user_type")  # 'student' or 'owner'
    
    query = SubscriptionPlan.query.filter_by(is_active=True)
    if user_type:
        query = query.filter_by(user_type=user_type)
    
    plans = query.order_by(SubscriptionPlan.display_order).all()
    
    return jsonify({
        "plans": [plan.to_dict() for plan in plans]
    })


@app.route("/api/subscriptions/subscribe", methods=["POST"])
@login_required
def subscribe_to_plan():
    """Subscribe to a plan."""
    data = request.get_json()
    plan_id = data.get("plan_id")
    billing_cycle = data.get("billing_cycle", "monthly")  # monthly or yearly
    
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    
    # Determine user type and ID
    user_type = getattr(current_user, 'role', None)
    user_id = current_user.id
    
    if not user_type or user_type not in ['student', 'owner']:
        return jsonify({"error": "Invalid user type"}), 400
    
    # Check if already subscribed
    existing = UserSubscription.query.filter_by(
        user_id=user_id,
        user_type=user_type,
        status="active"
    ).filter(UserSubscription.end_date > datetime.utcnow()).first()
    
    if existing:
        return jsonify({"error": "You already have an active subscription"}), 400
    
    # Calculate amount and dates
    if billing_cycle == "yearly":
        amount = plan.price_yearly
        end_date = datetime.utcnow() + timedelta(days=365)
    else:
        amount = plan.price_monthly
        end_date = datetime.utcnow() + timedelta(days=30)
    
    # Create subscription (pending payment)
    subscription = UserSubscription(
        user_id=user_id,
        user_type=user_type,
        plan_id=plan_id,
        status="pending",
        billing_cycle=billing_cycle,
        amount_paid=amount,
        end_date=end_date,
        next_billing_date=end_date if subscription.auto_renew else None
    )
    
    db.session.add(subscription)
    
    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "subscription": subscription.to_dict(),
            "message": f"Subscription created! Pay ₹{amount:,.0f} to activate.",
            "amount": amount
        })
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Failed to create subscription"}), 500


@app.route("/api/subscriptions/activate/<int:subscription_id>", methods=["POST"])
@login_required
def activate_subscription(subscription_id):
    """Activate subscription after payment."""
    subscription = UserSubscription.query.get_or_404(subscription_id)
    
    # Verify ownership
    if subscription.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json()
    transaction_id = data.get("transaction_id")
    
    # TODO: Verify payment with payment gateway
    
    subscription.status = "active"
    subscription.transaction_id = transaction_id
    subscription.payment_method = "razorpay"
    
    # Record revenue
    analytics = RevenueAnalytics.query.filter_by(date=datetime.utcnow().date()).first()
    if not analytics:
        analytics = RevenueAnalytics(date=datetime.utcnow().date())
        db.session.add(analytics)
    
    analytics.subscription_revenue += subscription.amount_paid
    analytics.new_subscriptions += 1
    analytics.calculate_total()
    
    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Subscription activated successfully!",
            "subscription": subscription.to_dict()
        })
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Failed to activate subscription"}), 500


@app.route("/api/subscriptions/my", methods=["GET"])
@login_required
def get_my_subscription():
    """Get current user's subscription."""
    user_type = getattr(current_user, 'role', None)
    
    subscription = UserSubscription.query.filter_by(
        user_id=current_user.id,
        user_type=user_type
    ).filter(UserSubscription.end_date > datetime.utcnow()).first()
    
    if subscription:
        return jsonify({"subscription": subscription.to_dict()})
    else:
        return jsonify({"subscription": None})


@app.route("/api/subscriptions/cancel/<int:subscription_id>", methods=["POST"])
@login_required
def cancel_subscription(subscription_id):
    """Cancel subscription (will not renew)."""
    subscription = UserSubscription.query.get_or_404(subscription_id)
    
    if subscription.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    subscription.auto_renew = False
    subscription.cancelled_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Subscription will not renew. Access continues until " + subscription.end_date.strftime('%d %B, %Y')
        })
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Failed to cancel subscription"}), 500


# ============= LISTING FEES =============

@app.route("/api/listing-fees/purchase", methods=["POST"])
@login_required
def purchase_listing_fee():
    """Owner purchases listing fee for a property."""
    owner = get_current_owner()
    if not owner:
        return jsonify({"error": "Only owners can purchase listing fees"}), 403
    
    data = request.get_json()
    room_id = data.get("room_id")
    fee_type = data.get("fee_type", "basic")  # basic, featured, premium
    
    room = Room.query.filter_by(id=room_id, owner_id=owner.id).first()
    if not room:
        return jsonify({"error": "Room not found or not yours"}), 404
    
    # Check if owner has active subscription
    if owner.is_premium:
        return jsonify({"message": "Premium members get free listings!"}), 200
    
    # Define fee structure
    fees = {
        "basic": {"amount": 500, "days": 30},
        "featured": {"amount": 1000, "days": 60},
        "premium": {"amount": 1500, "days": 90}
    }
    
    fee_info = fees.get(fee_type, fees["basic"])
    
    listing_fee = ListingFee(
        room_id=room_id,
        owner_id=owner.id,
        fee_type=fee_type,
        amount=fee_info["amount"],
        validity_days=fee_info["days"],
        expires_at=datetime.utcnow() + timedelta(days=fee_info["days"]),
        payment_status="pending"
    )
    
    db.session.add(listing_fee)
    
    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "listing_fee_id": listing_fee.id,
            "amount": fee_info["amount"],
            "message": f"Pay ₹{fee_info['amount']} for {fee_info['days']} days listing"
        })
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Failed to create listing fee"}), 500


@app.route("/api/listing-fees/confirm/<int:fee_id>", methods=["POST"])
@login_required
def confirm_listing_fee(fee_id):
    """Confirm payment of listing fee."""
    listing_fee = ListingFee.query.get_or_404(fee_id)
    
    owner = get_current_owner()
    if not owner or listing_fee.owner_id != owner.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json()
    transaction_id = data.get("transaction_id")
    
    listing_fee.payment_status = "completed"
    listing_fee.transaction_id = transaction_id
    
    # Mark room as featured/premium if applicable
    room = listing_fee.room
    if listing_fee.fee_type == "featured":
        room.is_featured = True
    elif listing_fee.fee_type == "premium":
        room.is_premium_listing = True
    
    # Record revenue
    analytics = RevenueAnalytics.query.filter_by(date=datetime.utcnow().date()).first()
    if not analytics:
        analytics = RevenueAnalytics(date=datetime.utcnow().date())
        db.session.add(analytics)
    
    analytics.listing_fee_revenue += listing_fee.amount
    analytics.calculate_total()
    
    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": f"Listing activated for {listing_fee.validity_days} days!"
        })
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Failed to confirm payment"}), 500


# ============= VALUE-ADDED SERVICES =============

@app.route("/api/services", methods=["GET"])
def get_services():
    """Get all available services."""
    target_user = request.args.get("target_user")  # 'student', 'owner', 'both'
    service_type = request.args.get("service_type")
    
    query = ValueAddedService.query.filter_by(is_active=True)
    
    if target_user:
        query = query.filter((ValueAddedService.target_user == target_user) | 
                           (ValueAddedService.target_user == "both"))
    
    if service_type:
        query = query.filter_by(service_type=service_type)
    
    services = query.all()
    
    return jsonify({
        "services": [service.to_dict() for service in services]
    })


@app.route("/api/services/purchase", methods=["POST"])
@login_required
def purchase_service():
    """Purchase a value-added service."""
    data = request.get_json()
    service_id = data.get("service_id")
    room_id = data.get("room_id")  # Optional, for property-related services
    scheduled_date_str = data.get("scheduled_date")
    
    service = ValueAddedService.query.get_or_404(service_id)
    
    user_type = getattr(current_user, 'role', None)
    user_id = current_user.id
    
    # Parse scheduled date
    scheduled_date = None
    if scheduled_date_str:
        try:
            scheduled_date = datetime.strptime(scheduled_date_str, "%Y-%m-%d %H:%M")
        except:
            pass
    
    purchase = ServicePurchase(
        service_id=service_id,
        user_id=user_id,
        user_type=user_type,
        room_id=room_id,
        amount=service.price,
        payment_status="pending",
        scheduled_date=scheduled_date
    )
    
    db.session.add(purchase)
    
    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "purchase_id": purchase.id,
            "amount": service.price,
            "message": f"Pay ₹{service.price:,.0f} for {service.service_name}"
        })
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Failed to create purchase"}), 500


@app.route("/api/services/confirm/<int:purchase_id>", methods=["POST"])
@login_required
def confirm_service_purchase(purchase_id):
    """Confirm service payment and schedule."""
    purchase = ServicePurchase.query.get_or_404(purchase_id)
    
    if purchase.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json()
    transaction_id = data.get("transaction_id")
    
    purchase.payment_status = "completed"
    purchase.transaction_id = transaction_id
    purchase.service_status = "in_progress"
    
    # Record revenue
    analytics = RevenueAnalytics.query.filter_by(date=datetime.utcnow().date()).first()
    if not analytics:
        analytics = RevenueAnalytics(date=datetime.utcnow().date())
        db.session.add(analytics)
    
    analytics.service_revenue += purchase.amount
    analytics.services_sold += 1
    analytics.calculate_total()
    
    try:
        db.session.commit()
        
        # TODO: Send email to service provider/team
        
        return jsonify({
            "success": True,
            "message": "Service booked successfully! Our team will contact you soon."
        })
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Failed to confirm payment"}), 500


# ============= REVENUE ANALYTICS =============

@app.route("/api/admin/revenue/summary", methods=["GET"])
@admin_required
def revenue_summary():
    """Get revenue summary."""
    period = request.args.get("period", "today")  # today, week, month, year
    
    if period == "today":
        start_date = datetime.utcnow().date()
        end_date = start_date
    elif period == "week":
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=7)
    elif period == "month":
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)
    elif period == "year":
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=365)
    else:
        start_date = datetime.utcnow().date()
        end_date = start_date
    
    analytics = RevenueAnalytics.query.filter(
        RevenueAnalytics.date.between(start_date, end_date)
    ).all()
    
    # Aggregate totals
    totals = {
        "subscription_revenue": sum(a.subscription_revenue for a in analytics),
        "commission_revenue": sum(a.commission_revenue for a in analytics),
        "listing_fee_revenue": sum(a.listing_fee_revenue for a in analytics),
        "service_revenue": sum(a.service_revenue for a in analytics),
        "transaction_fee_revenue": sum(a.transaction_fee_revenue for a in analytics),
        "advertising_revenue": sum(a.advertising_revenue for a in analytics),
        "total_revenue": sum(a.total_revenue for a in analytics),
        "new_subscriptions": sum(a.new_subscriptions for a in analytics),
        "total_bookings": sum(a.total_bookings for a in analytics),
        "services_sold": sum(a.services_sold for a in analytics),
    }
    
    return jsonify({
        "period": period,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "summary": totals,
        "daily_data": [{
            "date": a.date.isoformat(),
            "total_revenue": a.total_revenue,
            "breakdown": {
                "subscriptions": a.subscription_revenue,
                "commissions": a.commission_revenue,
                "listing_fees": a.listing_fee_revenue,
                "services": a.service_revenue,
                "transaction_fees": a.transaction_fee_revenue,
                "advertising": a.advertising_revenue,
            }
        } for a in analytics]
    })


# ============= BOOKING SYSTEM (Complete Flow) =============

try:
    from utils.email_service import email_service
    from utils.contract_generator import contract_generator
except ImportError as e:
    print(f"Warning: Could not import utils: {e}")
    
    class MockService:
        def __getattr__(self, name):
            def method(*args, **kwargs):
                print(f"MockService.{name} called")
                return True
            return method
            
    email_service = MockService()
    contract_generator = MockService()


# ---------------------------------------------------------------------------
# Payment Gateway APIs (Razorpay)
# ---------------------------------------------------------------------------

@app.route("/api/payment/create-order", methods=["POST"])
@login_required
def create_razorpay_order():
    """Create a Razorpay order for payment."""
    data = request.get_json()
    amount = data.get("amount")  # Amount in paise (₹999 = 99900 paise)
    booking_id = data.get("booking_id")
    
    if not amount:
        return jsonify({"error": "Amount is required"}), 400
    
    # Demo mode: If Razorpay is not configured, return a mock order for testing
    if razorpay_client is None:
        app.logger.info("Razorpay not configured - using DEMO mode for payment")
        demo_order_id = f"demo_order_{booking_id}_{datetime.utcnow().timestamp()}"
        return jsonify({
            "success": True,
            "demo_mode": True,
            "order_id": demo_order_id,
            "amount": int(amount),
            "currency": "INR",
            "key": "demo_key",
            "message": "Demo mode: Razorpay not configured. Payment will be simulated."
        })
    
    try:
        # Create Razorpay order
        order_data = {
            "amount": int(amount),  # Amount in paise
            "currency": "INR",
            "receipt": f"booking_{booking_id}_{datetime.utcnow().timestamp()}",
            "notes": {
                "booking_id": str(booking_id) if booking_id else "",
                "user_id": str(current_user.id),
                "user_type": current_user.role
            }
        }
        
        order = razorpay_client.order.create(data=order_data)
        
        return jsonify({
            "success": True,
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key": os.environ.get("RAZORPAY_KEY_ID", "")
        })
    except Exception as e:
        app.logger.error(f"Razorpay order creation error: {e}")
        # Fallback to Demo Mode on failure (e.g. auth error, connection reset)
        app.logger.info("Fallback to DEMO mode due to Razorpay error")
        demo_order_id = f"demo_fallback_{booking_id}_{datetime.utcnow().timestamp()}"
        return jsonify({
            "success": True,
            "demo_mode": True,
            "order_id": demo_order_id,
            "amount": int(amount),
            "currency": "INR",
            "key": "demo_key",
            "message": "Payment system unavailable. Using demo mode."
        })


@app.route("/api/payment/verify", methods=["POST"])
@login_required
def verify_razorpay_payment():
    """Verify Razorpay payment signature."""
    if razorpay_client is None:
        return jsonify({"error": "Payment gateway not configured"}), 503
    
    data = request.get_json()
    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_signature = data.get("razorpay_signature")
    booking_id = data.get("booking_id")
    
    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return jsonify({"error": "Missing payment details"}), 400
    
    try:
        # Verify payment signature
        params = {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        }
        
        razorpay_client.utility.verify_payment_signature(params)
        
        # Update booking if booking_id provided
        if booking_id:
            booking = Booking.query.get(booking_id)
            if booking:
                booking.razorpay_payment_id = razorpay_payment_id
                booking.razorpay_signature = razorpay_signature
                booking.payment_status = "completed"
                booking.booking_status = "confirmed"
                booking.total_paid = booking.calculate_total_due()
                booking.confirmed_at = datetime.utcnow()
                db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Payment verified successfully"
        })
    except razorpay.errors.SignatureVerificationError:
        return jsonify({"error": "Payment verification failed"}), 400
    except Exception as e:
        app.logger.error(f"Payment verification error: {e}")
        return jsonify({"error": "Payment verification failed"}), 500


@app.route("/api/bookings/create", methods=["POST"])
@login_required
def create_booking():
    """Step 1: Student initiates booking with ₹999 booking fee."""
    student = get_current_student()
    if student is None:
        return jsonify({"error": "Only students can book rooms."}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    room_id = data.get("room_id")
    if not room_id:
        return jsonify({"error": "Room ID is required"}), 400
        
    try:
        room_id = int(room_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid Room ID format"}), 400

    move_in_date_str = data.get("move_in_date")  # Format: YYYY-MM-DD
    contract_duration = data.get("contract_duration_months", 11)
    
    room = Room.query.get(room_id)
    if not room:
        return jsonify({"error": "Room not found."}), 404
    
    if room.available_slots <= 0:
        return jsonify({"error": "No slots available."}), 400
    
    # Check if already booked this room
    existing = Booking.query.filter_by(
        student_id=student.id,
        room_id=room_id
    ).filter(Booking.booking_status.in_(["pending", "payment_initiated", "confirmed", "active"])).first()
    
    if existing:
        return jsonify({"error": "You already have an active booking for this room."}), 400
    
    # Parse move-in date
    try:
        move_in_date = datetime.strptime(move_in_date_str, "%Y-%m-%d").date() if move_in_date_str else None
    except:
        move_in_date = None
    
    # Calculate contract dates
    if move_in_date:
        contract_start = move_in_date
        contract_end = contract_start + timedelta(days=contract_duration * 30)
    else:
        contract_start = None
        contract_end = None
    
    # Create booking
    booking = Booking(
        student_id=student.id,
        room_id=room_id,
        booking_amount=999.0,
        monthly_rent=room.price,
        payment_status="pending",
        booking_status="pending",
        contract_duration_months=contract_duration,
        contract_start_date=contract_start,
        contract_end_date=contract_end,
        move_in_date=move_in_date,
    )
    
    # Calculate financial terms
    booking.calculate_security_deposit()
    booking.calculate_platform_fee()
    
    # Create Razorpay order for booking fee (₹999)
    booking.razorpay_order_id = f"order_booking_{booking.id}_{datetime.utcnow().timestamp()}"
    
    db.session.add(booking)
    
    try:
        db.session.commit()
        
        return jsonify({
            "success": True,
            "booking": {
                "id": booking.id,
                "booking_amount": booking.booking_amount,
                "monthly_rent": booking.monthly_rent,
                "security_deposit": booking.security_deposit,
                "platform_fee": booking.platform_fee,
                "total_due": booking.calculate_total_due(),
                "razorpay_order_id": booking.razorpay_order_id,
            },
            "message": "Booking initiated! Pay ₹999 to send request to owner.",
        })
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Booking creation error: {e}")
        return jsonify({"error": "Failed to create booking"}), 500


@app.route("/api/bookings/<int:booking_id>/pay-booking-fee", methods=["POST"])
@login_required
def pay_booking_fee(booking_id):
    """Step 2: Student pays ₹999 booking fee and request is sent to owner."""
    student = get_current_student()
    if student is None:
        return jsonify({"error": "Unauthorized"}), 403
    
    booking = Booking.query.get_or_404(booking_id)
    if booking.student_id != student.id:
        return jsonify({"error": "Not your booking"}), 403
    
    data = request.get_json() or {}
    payment_id = data.get("razorpay_payment_id")
    signature = data.get("razorpay_signature")
    
    # Bypass/Skip Payment Logic
    # If no payment info provided, generate dummy info to progress the flow
    if not payment_id:
        app.logger.info("No payment ID provided - Using SKIP/BYPASS payment mode")
        payment_id = f"skip_pay_{datetime.utcnow().timestamp()}"
        signature = "skip_signature_bypass"
    
    # TODO: Verify Razorpay payment signature
    # For now, mark as paid
    booking.razorpay_payment_id = payment_id
    booking.razorpay_signature = signature
    booking.total_paid = booking.booking_amount
    booking.payment_status = "partial"  # Only booking fee paid
    booking.booking_status = "payment_initiated"
    
    # Send notification to owner
    room = booking.room
    owner = room.owner
    
    if owner:
        try:
            app.logger.info(f"Attempting to send booking notification to owner: {owner.email}")
            result = email_service.send_booking_request_to_owner(booking, room, student, owner)
            if result:
                app.logger.info(f"Successfully sent notification to owner: {owner.email}")
                booking.owner_notified = True
                booking.owner_notification_sent_at = datetime.utcnow()
            else:
                app.logger.warning(f"Email service returned False for owner notification")
        except Exception as e:
            app.logger.error(f"Failed to send owner notification: {e}")
    else:
        app.logger.warning(f"No owner found for room {room.id}, skipping owner notification")
    
    # Send confirmation to student
    try:
        app.logger.info(f"Attempting to send booking confirmation to student: {student.email}")
        subject = f"Booking Request Sent: {room.title}"
        html_content = f"""
        <h2>Booking Request Submitted! 🎉</h2>
        <p>Hi {student.name},</p>
        <p>Your booking request for <strong>{room.title}</strong> has been sent to the owner.</p>
        <p><strong>What's next?</strong></p>
        <ol>
            <li>Owner will review your request within 24 hours</li>
            <li>You'll receive email notification of their decision</li>
            <li>If approved, complete remaining payment to confirm booking</li>
        </ol>
        <p>Booking Fee Paid: ₹{booking.booking_amount:,.2f}</p>
        <p>Track your booking status at: <a href="{os.getenv('APP_URL')}/my-bookings">My Bookings</a></p>
        """
        result = email_service.send_email(student.email, subject, html_content)
        if result:
            app.logger.info(f"Successfully sent confirmation to student: {student.email}")
            booking.student_notified = True
            booking.student_notification_sent_at = datetime.utcnow()
        else:
            app.logger.warning(f"Email service returned False for student notification")
    except Exception as e:
        app.logger.error(f"Failed to send student notification: {e}")
    
    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Booking fee paid! Request sent to owner. You'll be notified within 24 hours.",
        })
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Failed to process payment"}), 500


@app.route("/api/bookings/<int:booking_id>/owner-approve", methods=["POST"])
@login_required
def owner_approve_booking(booking_id):
    """Step 3: Owner approves/rejects booking request."""
    owner = get_current_owner()
    if owner is None:
        return jsonify({"error": "Only owners can approve bookings."}), 403
    
    booking = Booking.query.get_or_404(booking_id)
    room = booking.room
    
    if room.owner_id != owner.id:
        return jsonify({"error": "This is not your property."}), 403
    
    data = request.get_json()
    approved = data.get("approved", False)
    rejection_reason = data.get("rejection_reason")
    
    student = booking.student
    
    if approved:
        # Owner approved
        booking.owner_approved = True
        booking.owner_approved_at = datetime.utcnow()
        booking.booking_status = "confirmed"  # Waiting for full payment
        
        # Send notification to student to complete payment
        try:
            email_service.send_owner_approval_notification(booking, room, student, owner)
        except Exception as e:
            app.logger.error(f"Failed to send approval notification: {e}")
        
        message = "Booking approved! Student will be notified to complete payment."
        
    else:
        # Owner rejected
        booking.owner_approved = False
        booking.owner_approved_at = datetime.utcnow()
        booking.owner_rejection_reason = rejection_reason
        booking.booking_status = "cancelled"
        booking.cancelled_by = "owner"
        booking.cancelled_at = datetime.utcnow()
        
        # Process refund of booking fee
        booking.refund_amount = booking.booking_amount
        booking.refund_processed = True  # TODO: Implement actual refund via Razorpay
        booking.refund_processed_at = datetime.utcnow()
        
        # Send rejection notification to student
        try:
            email_service.send_booking_rejection_to_student(
                booking, room, student, owner, rejection_reason
            )
        except Exception as e:
            app.logger.error(f"Failed to send rejection notification: {e}")
        
        message = "Booking rejected. Student will be notified and refunded."
    
    try:
        db.session.commit()
        return jsonify({"success": True, "message": message})
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Failed to process request"}), 500


@app.route("/api/bookings/<int:booking_id>/complete-payment", methods=["POST"])
@login_required
def complete_booking_payment(booking_id):
    """Step 4: Student completes remaining payment (deposit + rent + fee)."""
    student = get_current_student()
    if student is None:
        return jsonify({"error": "Unauthorized"}), 403
    
    booking = Booking.query.get_or_404(booking_id)
    if booking.student_id != student.id:
        return jsonify({"error": "Not your booking"}), 403
    
    if booking.booking_status != "confirmed":
        return jsonify({"error": "Booking not confirmed by owner yet."}), 400
    
    data = request.get_json() or {}
    payment_id = data.get("razorpay_payment_id")
    signature = data.get("razorpay_signature")
    
    # Bypass/Skip Payment Logic
    if not payment_id:
        app.logger.info("No payment ID provided provided - Using SKIP/BYPASS payment mode")
        payment_id = f"skip_pay_complete_{datetime.utcnow().timestamp()}"
        signature = "skip_signature_complete_bypass"
    
    # Calculate remaining amount
    remaining_amount = booking.calculate_total_due() - booking.total_paid
    
    # TODO: Verify Razorpay payment
    # Mark payment as complete
    booking.payment_status = "completed"
    booking.total_paid = booking.calculate_total_due()
    booking.booking_status = "active"
    booking.confirmed_at = datetime.utcnow()
    
    # Update room occupancy
    room = booking.room
    room.capacity_occupied += 1
    
    # Calculate and record platform commission
    owner = room.owner
    commission_rate = owner.commission_rate  # 15% if premium, 25% if free tier
    base_commission = booking.monthly_rent * (commission_rate / 100)
    
    # Apply subscription discount
    discount = 0
    if owner.is_premium:
        # Premium owners get 10% discount on commission (25% -> 15%)
        discount = booking.monthly_rent * 0.10
    
    final_commission = base_commission - discount
    
    commission_record = Commission(
        booking_id=booking.id,
        owner_id=owner.id,
        student_id=student.id,
        base_amount=booking.monthly_rent,
        commission_rate=commission_rate,
        commission_amount=base_commission,
        discount_amount=discount,
        final_amount=final_commission,
        payment_status="pending"
    )
    db.session.add(commission_record)
    
    # Record transaction fee (2% of total transaction)
    total_transaction = booking.calculate_total_due()
    transaction_fee_rate = 0.02  # 2%
    transaction_fee = TransactionFee(
        booking_id=booking.id,
        student_id=student.id,
        transaction_amount=total_transaction,
        fee_rate=transaction_fee_rate,
        fee_amount=total_transaction * transaction_fee_rate,
        payment_method="razorpay",
        payment_status="completed"
    )
    db.session.add(transaction_fee)
    
    # Record revenue analytics
    analytics_record = RevenueAnalytics.query.filter_by(date=datetime.utcnow().date()).first()
    if not analytics_record:
        analytics_record = RevenueAnalytics(date=datetime.utcnow().date())
        db.session.add(analytics_record)
    
    analytics_record.commission_revenue += final_commission
    analytics_record.transaction_fee_revenue += transaction_fee.fee_amount
    analytics_record.total_bookings += 1
    analytics_record.calculate_total()
    
    # Old analytics for backward compatibility
    analytics = Analytics(
        date=datetime.utcnow().date(),
        metric_type="booking_revenue",
        amount=booking.platform_fee,
        count=1,
    )
    db.session.add(analytics)
    
    # Generate rental contract
    owner = room.owner
    try:
        contract_path = contract_generator.generate_rental_agreement(
            booking, room, student, owner
        )
        booking.contract_pdf_path = contract_path
        
        # Send contract for signature
        email_service.send_contract_for_signature(
            booking, room, student, owner, contract_path
        )
    except Exception as e:
        app.logger.error(f"Contract generation error: {e}")
    
    # Send final confirmation emails
    try:
        email_service.send_booking_confirmation_to_student(booking, room, student, owner)
    except Exception as e:
        app.logger.error(f"Confirmation email error: {e}")
    
    try:
        # Notify owner of payment completion
        subject = f"Payment Received: {room.title} - {student.name}"
        html_content = f"""
        <h2>💰 Payment Received Successfully</h2>
        <p>Hi {owner.name},</p>
        <p>Good news! The tenant <strong>{student.name}</strong> has completed the full payment for your property <strong>{room.title}</strong>.</p>
        <p><strong>Payment Details:</strong></p>
        <ul>
            <li>Security Deposit: ₹{booking.security_deposit:,.2f}</li>
            <li>First Month Rent: ₹{booking.monthly_rent:,.2f}</li>
            <li>Total Received: ₹{booking.total_paid:,.2f}</li>
        </ul>
        <p><strong>Next Steps:</strong></p>
        <ol>
            <li>Review and sign the rental agreement (sent separately)</li>
            <li>Coordinate move-in date with tenant: {booking.move_in_date.strftime('%d %B, %Y') if booking.move_in_date else 'TBD'}</li>
            <li>Prepare property for tenant arrival</li>
            <li>Conduct move-in inspection together</li>
        </ol>
        <p>Tenant Contact: {student.email}</p>
        <p>View booking details: <a href="{os.getenv('APP_URL')}/owner/bookings/{booking.id}">Click here</a></p>
        """
        email_service.send_email(owner.email, subject, html_content)
    except Exception as e:
        app.logger.error(f"Owner payment notification error: {e}")
    
    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Payment completed! Rental agreement sent to your email. Welcome to your new home!",
            "booking": booking.to_dict(),
        })
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Failed to complete payment"}), 500


@app.route("/api/bookings/<int:booking_id>/sign-contract", methods=["POST"])
@login_required
def sign_contract(booking_id):
    """Step 5: Student signs the contract digitally."""
    student = get_current_student()
    if student is None:
        return jsonify({"error": "Unauthorized"}), 403
    
    booking = Booking.query.get_or_404(booking_id)
    if booking.student_id != student.id:
        return jsonify({"error": "Not your booking"}), 403
    
    data = request.get_json()
    signature = data.get("signature")  # Digital signature or checkbox confirmation
    
    booking.contract_signed = True
    booking.contract_signed_at = datetime.utcnow()
    
    room = booking.room
    owner = room.owner
    
    # Notify owner of contract signing
    try:
        subject = f"Contract Signed: {room.title}"
        html_content = f"""
        <h2>📝 Rental Agreement Signed</h2>
        <p>Hi {owner.name},</p>
        <p>The tenant <strong>{student.name}</strong> has signed the rental agreement for <strong>{room.title}</strong>.</p>
        <p>The booking is now fully confirmed. Please sign the agreement as well to complete the process.</p>
        <p><strong>Move-in Date:</strong> {booking.move_in_date.strftime('%d %B, %Y') if booking.move_in_date else 'To be confirmed'}</p>
        """
        email_service.send_email(owner.email, subject, html_content)
    except Exception as e:
        app.logger.error(f"Contract signing notification error: {e}")
    
    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Contract signed successfully! Owner will be notified.",
        })
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Failed to sign contract"}), 500


@app.route("/api/bookings/my", methods=["GET"])
@login_required
def my_bookings():
    """Get current student's bookings."""
    student = get_current_student()
    if student is None:
        return jsonify({"error": "Only students can have bookings."}), 403
    
    bookings = Booking.query.filter_by(student_id=student.id).order_by(
        Booking.created_at.desc()
    ).all()
    
    return jsonify({
        "bookings": [b.to_dict() for b in bookings]
    })


@app.route("/api/owner/bookings", methods=["GET"])
@login_required
def owner_bookings():
    """Get owner's property bookings."""
    owner = get_current_owner()
    if owner is None:
        return jsonify({"error": "Only owners can view this."}), 403
    
    # Get all rooms owned by this owner
    room_ids = [room.id for room in owner.rooms]
    
    bookings = Booking.query.filter(Booking.room_id.in_(room_ids)).order_by(
        Booking.created_at.desc()
    ).all()
    
    return jsonify({
        "bookings": [{
            **b.to_dict(),
            "student": {
                "name": b.student.name,
                "email": b.student.email,
                "college": b.student.college,
                "verified": b.student.verified,
            }
        } for b in bookings]
    })


@app.route("/api/bookings/<int:booking_id>/cancel", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    """Cancel booking (with refund policy)."""
    user = current_user
    booking = Booking.query.get_or_404(booking_id)
    
    data = request.get_json()
    reason = data.get("cancellation_reason", "User requested cancellation")
    
    # Check authorization
    is_student = booking.student_id == user.id
    is_owner = booking.room.owner_id == user.id if hasattr(user, 'rooms') else False
    
    if not (is_student or is_owner):
        return jsonify({"error": "Unauthorized"}), 403
    
    # Cancellation policy
    if booking.booking_status == "active":
        # Active contract - apply penalties
        booking.refund_amount = booking.security_deposit  # Return deposit
        # Forfeit one month rent if cancelled early
        booking.cancellation_reason = reason
    elif booking.booking_status in ["pending", "payment_initiated"]:
        # Not yet confirmed - full refund of booking fee
        booking.refund_amount = booking.total_paid
    elif booking.booking_status == "confirmed":
        # Owner approved but payment not completed
        booking.refund_amount = booking.total_paid
    
    booking.booking_status = "cancelled"
    booking.cancelled_at = datetime.utcnow()
    booking.cancelled_by = "student" if is_student else "owner"
    booking.refund_processed = True  # TODO: Process actual refund
    booking.refund_processed_at = datetime.utcnow()
    
    # Free up room slot if was occupied
    if booking.move_in_completed:
        room = booking.room
        room.capacity_occupied = max(0, room.capacity_occupied - 1)
    
    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": f"Booking cancelled. Refund of ₹{booking.refund_amount:,.2f} will be processed within 5-7 days.",
        })
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Failed to cancel booking"}), 500


# ============= MESS MENU CALENDAR =============

@app.route("/api/mess-menu/<int:room_id>", methods=["GET"])
def get_mess_menu(room_id):
    """Get weekly mess menu for a room."""
    menus = MessMenu.query.filter_by(room_id=room_id).all()
    
    menu_by_day = {}
    for menu in menus:
        if menu.day_of_week not in menu_by_day:
            menu_by_day[menu.day_of_week] = {}
        menu_by_day[menu.day_of_week][menu.meal_type] = {
            "text": menu.menu_text,
            "image": url_for("static", filename=f"uploads/{menu.menu_image}") if menu.menu_image else None,
        }
    
    return jsonify({"menu": menu_by_day})


@app.route("/api/mess-menu/add", methods=["POST"])
@login_required
def add_mess_menu():
    """Add mess menu item (owners only)."""
    owner = get_current_owner()
    if owner is None:
        return jsonify({"error": "Only owners can add mess menus."}), 403
    
    data = request.form
    room_id = data.get("room_id")
    

    
    room = Room.query.filter_by(id=room_id, owner_id=owner.id).first()
    if not room:
        return jsonify({"error": "Room not found or not yours."}), 404
    
    # Handle image upload
    image_filename = None
    if "menu_image" in request.files:
        file = request.files["menu_image"]
        if file.filename:
            # Save to uploads folder
            filename = f"menu_{room_id}_{datetime.utcnow().timestamp()}.jpg"
            file.save(os.path.join(app.static_folder, "uploads", filename))
            image_filename = filename
    
    menu = MessMenu(
        room_id=room_id,
        day_of_week=data.get("day_of_week"),
        meal_type=data.get("meal_type"),
        menu_text=data.get("menu_text"),
        menu_image=image_filename,
    )
    db.session.add(menu)
    
    try:
        db.session.commit()
        return jsonify({"success": True, "message": "Menu added!"})
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Failed to add menu"}), 500


# ============= SAFETY AUDIT SCORING =============

@app.route("/api/safety-audit/<int:room_id>", methods=["GET"])
def get_safety_audit(room_id):
    """Get safety audit score for a room."""
    audit = SafetyAudit.query.filter_by(room_id=room_id).first()
    
    if not audit:
        return jsonify({"score": 0, "details": {}})
    
    return jsonify({
        "score": audit.total_score,
        "details": {
            "fire_extinguisher": audit.fire_extinguisher,
            "emergency_exit": audit.emergency_exit,
            "first_aid_kit": audit.first_aid_kit,
            "cctv_coverage": audit.cctv_coverage,
            "security_guard": audit.security_guard,
            "smoke_detector": audit.smoke_detector,
            "well_lit_area": audit.well_lit_area,
            "gated_community": audit.gated_community,
            "women_friendly": audit.women_friendly,
            "police_verification": audit.police_verification,
        }
    })


@app.route("/api/safety-audit/update", methods=["POST"])
@login_required
def update_safety_audit():
    """Update safety audit for room (owners only)."""
    owner = get_current_owner()
    if owner is None:
        return jsonify({"error": "Only owners can update safety audits."}), 403
    
    data = request.get_json()
    room_id = data.get("room_id")
    
    room = Room.query.filter_by(id=room_id, owner_id=owner.id).first()
    if not room:
        return jsonify({"error": "Room not found or not yours."}), 404
    
    audit = SafetyAudit.query.filter_by(room_id=room_id).first()
    if not audit:
        audit = SafetyAudit(room_id=room_id)
        db.session.add(audit)
    
    # Update all fields
    audit.fire_extinguisher = data.get("fire_extinguisher", False)
    audit.emergency_exit = data.get("emergency_exit", False)
    audit.first_aid_kit = data.get("first_aid_kit", False)
    audit.cctv_coverage = data.get("cctv_coverage", False)
    audit.security_guard = data.get("security_guard", False)
    audit.smoke_detector = data.get("smoke_detector", False)
    audit.well_lit_area = data.get("well_lit_area", False)
    audit.gated_community = data.get("gated_community", False)
    audit.women_friendly = data.get("women_friendly", False)
    audit.police_verification = data.get("police_verification", False)
    
    audit.calculate_score()
    
    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "score": audit.total_score,
            "message": f"Safety score: {audit.total_score}/10",
        })
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Failed to update safety audit"}), 500


# ============= ROOMMATE MATCHING =============

@app.route("/api/profile-tags/my", methods=["GET"])
@login_required
def my_profile_tags():
    """Get current student's profile tags."""

    student = get_current_student()
    if student is None:
        return jsonify({"error": "Only students can have profile tags."}), 403
    
    tags = ProfileTag.query.filter_by(student_id=student.id).all()

    return jsonify({"tags": [t.tag for t in tags]})


@app.route("/api/profile-tags/update", methods=["POST"])
@login_required
def update_profile_tags():
    """Update profile tags for roommate matching."""
    student = get_current_student()
    if student is None:
        return jsonify({"error": "Only students can update tags."}), 403
    
    data = request.get_json()
    new_tags = data.get("tags", [])
    
    # Delete existing tags
    ProfileTag.query.filter_by(student_id=student.id).delete()
    
    # Add new tags
    for tag in new_tags:
        db.session.add(ProfileTag(student_id=student.id, tag=tag))
    
    try:
        db.session.commit()
        return jsonify({"success": True, "message": "Profile updated!"})

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Failed to update tags"}), 500


@app.route("/api/roommate-match", methods=["GET"])
@login_required
def roommate_match():
    """Find compatible roommates based on profile tags."""
    student = get_current_student()
    if student is None:
        return jsonify({"error": "Only students can find roommates."}), 403
    
    # Get current student's tags
    my_tags = [t.tag for t in ProfileTag.query.filter_by(student_id=student.id).all()]
    
    if not my_tags:
        return jsonify({
            "matches": [],
            "message": "Update your profile tags to find compatible roommates!",
        })
    
    # Find other students with matching tags
    matches = db.session.query(
        Student,
        func.count(ProfileTag.tag).label("match_count")
    ).join(
        ProfileTag, Student.id == ProfileTag.student_id
    ).filter(
        ProfileTag.tag.in_(my_tags),
        Student.id != student.id
    ).group_by(
        Student.id
    ).order_by(
        func.count(ProfileTag.tag).desc()
    ).limit(10).all()
    
    return jsonify({
        "matches": [{
            "id": s.id,
            "name": s.name,
            "college": s.college,
            "budget": s.budget,
            "lifestyle": s.lifestyle,
            "compatibility_score": round((match_count / len(my_tags)) * 100),
            "matching_tags": match_count,
        } for s, match_count in matches]
    })


@app.route("/healthz")
def healthcheck():
    status = {
        "authenticated": current_user.is_authenticated,
        "rooms": Room.query.count(),
    }
    return jsonify(status)


@app.route("/api/chat", methods=["POST"])
def chat_api():
    """AI Chatbot API endpoint."""
    data = request.get_json()
    user_message = data.get("message", "")
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
        
    response = chatbot.get_response(user_message)
    return jsonify({"response": response})

# ---------------------------------------------------------------------------
# AI Agent Data Providers
# ---------------------------------------------------------------------------
def get_rooms_for_chat(query_text):
    """
    Retrieves relevant rooms for the chatbot context based on user query.
    This is a simple heuristic search to feed the RAG system.
    """
    try:
        query_text = query_text.lower()
        base_query = Room.query.filter(Room.verified == True)
        
        # 1. Location Filter
        # Get all unique locations to check against query
        # In production, use a proper NER or search engine
        locations = db.session.query(Room.location).distinct().all()
        found_location = False
        for (loc,) in locations:
            if loc and loc.lower() in query_text:
                base_query = base_query.filter(Room.location.ilike(f"%{loc}%"))
                found_location = True
                break
        
        # 2. Price Filter (Basic regex)
        import re
        # Look for "under 5000", "below 10000", "< 8000"
        price_match = re.search(r'(under|below|less than|<)\s?(\d+)', query_text)
        if price_match:
            try:
                max_price = int(price_match.group(2))
                base_query = base_query.filter(Room.price <= max_price)
            except:
                pass
                
        # 3. Property Type
        if 'hostel' in query_text:
            base_query = base_query.filter(Room.property_type == 'hostel')
        elif 'flat' in query_text or 'apartment' in query_text:
            base_query = base_query.filter(Room.property_type == 'flat')
        elif 'pg' in query_text:
            base_query = base_query.filter(Room.property_type == 'pg')

        # Limit results for context window
        rooms = base_query.limit(5).all()
        return [r.to_dict() for r in rooms]
    except Exception as e:
        app.logger.error(f"Chatbot room provider error: {e}")
        return []

# Register the provider
chatbot.set_room_provider(get_rooms_for_chat)


@app.route("/api/news")
def get_news():
    """Get latest college/education news."""
    try:
        limit = request.args.get('limit', 5, type=int)
        news = news_service.get_latest_news(limit=limit)
        return jsonify({"success": True, "news": news})
    except Exception as e:
        app.logger.error(f"News API error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Database Initialization (Auto-create tables on startup)
# ---------------------------------------------------------------------------
def init_database():
    """Create all tables and seed initial data if needed."""
    import json
    import random
    
    with app.app_context():
        try:
            # Show connection info (hide password)
            db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
            if "postgresql" in db_uri:
                # Parse and hide password for logging
                import re
                safe_uri = re.sub(r':[^:@]+@', ':****@', db_uri)
                print(f"🗄️ Connecting to PostgreSQL: {safe_uri[:80]}...")
            else:
                print(f"🗄️ Using SQLite database")
            
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Create admin if not exists
            admin = Admin.query.filter_by(email="admin@roomies.in").first()
            if not admin:
                admin = Admin(
                    email="admin@roomies.in",
                    name="System Admin",
                    role="admin"
                )
                admin.set_password("admin123")
                db.session.add(admin)
                db.session.commit()
                print("✅ Admin user created: admin@roomies.in / admin123")
            
            # Create system owner if not exists
            owner = Owner.query.filter_by(email="system@roomies.in").first()
            if not owner:
                owner = Owner(
                    email="system@roomies.in",
                    name="Roomies System",
                    kyc_verified=True
                )
                owner.set_password("system123")
                db.session.add(owner)
                db.session.commit()
                print("✅ System owner created")
            else:
                owner = Owner.query.filter_by(email="system@roomies.in").first()
            
            # Check if rooms exist, if not load from real_data_dump.json
            room_count = Room.query.count()
            if room_count == 0:
                print("📦 No rooms found. Loading data from real_data_dump.json...")
                
                # Room images for variety
                # Room images for variety
                room_images = [
                    "/static/images/room1.png",
                    "/static/images/room2.png",
                    "/static/images/room3.png",
                    "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=600",
                    "https://images.unsplash.com/photo-1595526114035-0d45ed16cfbf?w=600",
                    "https://images.unsplash.com/photo-1522771753035-4a50354b6063?w=600",
                    "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=600",
                    "https://images.unsplash.com/photo-1505693416388-b0346efee539?w=600",
                ]
                
                try:
                    # Load data from JSON file
                    json_path = os.path.join(app.root_path, 'data', 'real_data_dump.json')
                    with open(json_path, 'r', encoding='utf-8') as f:
                        colleges_data = json.load(f)
                    
                    count = 0
                    for college_entry in colleges_data:
                        college_name = college_entry['college']
                        hostels = college_entry.get('nearby_hostels', [])
                        
                        for hostel in hostels:
                            # Skip hostels with "Unknown" in name
                            if "Unknown" in hostel['name']:
                                continue
                            
                            # Generate random attributes
                            price = random.choice([7000, 8000, 9000, 10000, 12000, 14000, 15000, 18000])
                            capacity = random.choice([2, 3, 4, 6])
                            occupied = random.randint(0, capacity - 1)
                            
                            # Pick random images
                            selected_images = random.sample(room_images, min(3, len(room_images)))
                            image_string = ",".join(selected_images)
                            
                            room = Room(
                                title=hostel['name'],
                                price=price,
                                location=f"Near {college_name}",
                                college_nearby=college_name,
                                amenities="WiFi,AC,Laundry,Security",
                                property_type="Hostel" if hostel.get('type') == 'hostel' else "PG",
                                capacity_total=capacity,
                                capacity_occupied=occupied,
                                latitude=hostel['lat'],
                                longitude=hostel['lon'],
                                owner_id=owner.id,
                                verified=True,
                                images=image_string
                            )
                            db.session.add(room)
                            count += 1
                    
                    db.session.commit()
                    print(f"✅ Added {count} hostels/rooms from {len(colleges_data)} colleges!")
                    
                except FileNotFoundError:
                    print("⚠️ real_data_dump.json not found. Adding sample data instead...")
                    # Fallback sample rooms
                    sample_rooms = [
                        Room(
                            title="Student Hostel Near DJ Sanghvi",
                            price=12000,
                            location="Vile Parle West, Mumbai",
                            college_nearby="DJ Sanghvi College of Engineering",
                            amenities="WiFi,AC,Laundry,Security",
                            property_type="Hostel",
                            capacity_total=4,
                            capacity_occupied=2,
                            latitude=19.1075,
                            longitude=72.8365,
                            owner_id=owner.id,
                            verified=True,
                            images="https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=600"
                        ),
                        Room(
                            title="PG Near IIT Bombay",
                            price=15000,
                            location="Powai, Mumbai",
                            college_nearby="IIT Bombay",
                            amenities="WiFi,Meals,AC,Gym",
                            property_type="PG",
                            capacity_total=2,
                            capacity_occupied=1,
                            latitude=19.1334,
                            longitude=72.9133,
                            owner_id=owner.id,
                            verified=True,
                            images="https://images.unsplash.com/photo-1522771753035-4a50354b6063?w=600"
                        ),
                    ]
                    for room in sample_rooms:
                        db.session.add(room)
                    db.session.commit()
                    print(f"✅ Added {len(sample_rooms)} sample rooms!")
            else:
                print(f"📦 Found {room_count} existing rooms.")
            
            # Create subscription plans if they don't exist
            plan_count = SubscriptionPlan.query.count()
            if plan_count == 0:
                print("💰 Creating subscription plans...")
                
                # Student Plans
                student_plans = [
                    SubscriptionPlan(
                        name="Free",
                        user_type="student",
                        price_monthly=0,
                        price_yearly=0,
                        features=json.dumps({
                            "property_inquiries": "5 per month",
                            "saved_properties": "10",
                            "chat_support": True,
                            "verified_listings": False,
                            "priority_responses": False,
                            "virtual_tours": False
                        }),
                        display_order=1,
                        commission_discount=0,
                        is_active=True
                    ),
                    SubscriptionPlan(
                        name="Basic",
                        user_type="student",
                        price_monthly=299,
                        price_yearly=2999,
                        features=json.dumps({
                            "property_inquiries": "20 per month",
                            "saved_properties": "50",
                            "chat_support": True,
                            "verified_listings": True,
                            "priority_responses": True,
                            "virtual_tours": False
                        }),
                        display_order=2,
                        commission_discount=5,
                        is_active=True
                    ),
                    SubscriptionPlan(
                        name="Premium",
                        user_type="student",
                        price_monthly=599,
                        price_yearly=5999,
                        features=json.dumps({
                            "property_inquiries": "Unlimited",
                            "saved_properties": "Unlimited",
                            "chat_support": True,
                            "verified_listings": True,
                            "priority_responses": True,
                            "virtual_tours": True,
                            "dedicated_support": True,
                            "move_in_assistance": True
                        }),
                        display_order=3,
                        commission_discount=10,
                        is_active=True
                    ),
                ]
                
                # Owner Plans
                owner_plans = [
                    SubscriptionPlan(
                        name="Free",
                        user_type="owner",
                        price_monthly=0,
                        price_yearly=0,
                        features=json.dumps({
                            "active_listings": "2",
                            "commission_rate": 15,
                            "listing_fee_required": True,
                            "featured_listings": False,
                            "analytics_dashboard": False
                        }),
                        display_order=1,
                        commission_discount=0,
                        is_active=True
                    ),
                    SubscriptionPlan(
                        name="Standard",
                        user_type="owner",
                        price_monthly=999,
                        price_yearly=9999,
                        features=json.dumps({
                            "active_listings": "10",
                            "commission_rate": 10,
                            "listing_fee_required": False,
                            "featured_listings": True,
                            "analytics_dashboard": True,
                            "priority_support": True
                        }),
                        display_order=2,
                        commission_discount=0,
                        is_active=True
                    ),
                    SubscriptionPlan(
                        name="Professional",
                        user_type="owner",
                        price_monthly=1999,
                        price_yearly=19999,
                        features=json.dumps({
                            "active_listings": "Unlimited",
                            "commission_rate": 5,
                            "listing_fee_required": False,
                            "featured_listings": True,
                            "analytics_dashboard": True,
                            "priority_support": True,
                            "auto_promotion": True,
                            "dedicated_account_manager": True,
                            "advanced_analytics": True,
                            "bulk_operations": True
                        }),
                        display_order=3,
                        commission_discount=0,
                        is_active=True
                    ),
                ]
                
                for plan in student_plans + owner_plans:
                    db.session.add(plan)
                
                db.session.commit()
                print(f"✅ Created {len(student_plans)} student plans and {len(owner_plans)} owner plans!")
            else:
                print(f"💰 Found {plan_count} existing subscription plans.")
                
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            import traceback
            traceback.print_exc()

# Auto-initialize on startup
init_database()


if __name__ == "__main__":
    app.run(debug=True)
