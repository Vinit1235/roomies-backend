"""
Database models for Roomies application.
Organized by domain for better maintainability.
"""

from .base import db, TimestampMixin, PasswordMixin
from .user import Student, Owner, Admin
from .property import Room, MessMenu, SafetyAudit
from .verification import Verification
from .transaction import Booking, Wallet, WalletTransaction
from .marketing import FlashDeal, Subscription, Referral
from .engagement import ProfileTag, ContactMessage
from .analytics import Analytics

__all__ = [
    'db',
    'TimestampMixin',
    'PasswordMixin',
    'Student',
    'Owner',
    'Admin',
    'Room',
    'MessMenu',
    'SafetyAudit',
    'Verification',
    'Booking',
    'Wallet',
    'WalletTransaction',
    'FlashDeal',
    'Subscription',
    'Referral',
    'ProfileTag',
    'ContactMessage',
    'Analytics',
]
