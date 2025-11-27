"""Property-related models: Room, MessMenu, SafetyAudit."""

from datetime import datetime
from typing import Optional
from .base import db, TimestampMixin


class Room(TimestampMixin, db.Model):
    """Room/Property listings."""
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    price = db.Column(db.Integer, nullable=False, index=True)
    location = db.Column(db.String(255), nullable=False, index=True)
    college_nearby = db.Column(db.String(255), nullable=False, index=True)
    amenities = db.Column(db.Text)  # Consider JSONB for PostgreSQL
    images = db.Column(db.Text)  # Consider JSONB for PostgreSQL
    property_type = db.Column(db.String(50), default="shared", nullable=False, index=True)
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
    verified = db.Column(db.Boolean, default=False, nullable=False, index=True)
    
    # Relationships
    owner = db.relationship("Owner", back_populates="rooms", lazy="joined")
    mess_menus = db.relationship("MessMenu", back_populates="room", cascade="all, delete-orphan", lazy="dynamic")
    safety_audit = db.relationship("SafetyAudit", back_populates="room", uselist=False, cascade="all, delete-orphan")

    @property
    def available_slots(self) -> int:
        """Calculate available capacity."""
        return max((self.capacity_total or 0) - (self.capacity_occupied or 0), 0)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        amenities_list = []
        if self.amenities:
            amenities_list = [item.strip() for item in self.amenities.split(",") if item.strip()]
        
        images_list = []
        if self.images:
            images_list = [item.strip() for item in self.images.split(",") if item.strip()]
        
        return {
            "id": self.id,
            "title": self.title,
            "price": self.price,
            "location": self.location,
            "college": self.college_nearby,
            "property_type": self.property_type,
            "amenities": amenities_list,
            "images": images_list,
            "verified": bool(self.verified),
            "owner": {
                "id": self.owner.id,
                "name": self.owner.name,
            } if self.owner else None,
            "capacity_total": self.capacity_total,
            "capacity_occupied": self.capacity_occupied,
            "available_slots": self.available_slots,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "has_mess": bool(self.mess_menus.count() > 0) if hasattr(self, 'mess_menus') else False,
            "safety_score": self.safety_audit.audit_score if self.safety_audit else 0,
        }


class MessMenu(TimestampMixin, db.Model):
    """Weekly mess/meal schedules for properties."""
    __tablename__ = "mess_menus"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week = db.Column(db.String(20), nullable=False, index=True)  # Monday, Tuesday, etc.
    breakfast = db.Column(db.Text)  # Can store JSON or comma-separated items
    lunch = db.Column(db.Text)
    dinner = db.Column(db.Text)
    snacks = db.Column(db.Text)  # Optional evening snacks
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # Enable/disable specific days
    
    # Relationships
    room = db.relationship("Room", back_populates="mess_menus")
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('room_id', 'day_of_week', name='unique_room_day'),
        db.CheckConstraint(
            "day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')",
            name='valid_day_of_week'
        ),
    )

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "room_id": self.room_id,
            "day_of_week": self.day_of_week,
            "breakfast": self.breakfast,
            "lunch": self.lunch,
            "dinner": self.dinner,
            "snacks": self.snacks,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SafetyAudit(TimestampMixin, db.Model):
    """Safety and security compliance audits for properties."""
    __tablename__ = "safety_audits"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    # Safety Features (Boolean flags)
    fire_extinguisher = db.Column(db.Boolean, default=False, nullable=False)
    smoke_detector = db.Column(db.Boolean, default=False, nullable=False)
    first_aid_kit = db.Column(db.Boolean, default=False, nullable=False)
    emergency_exit = db.Column(db.Boolean, default=False, nullable=False)
    
    # Security Features
    cctv = db.Column(db.Boolean, default=False, nullable=False)
    security_guard = db.Column(db.Boolean, default=False, nullable=False)
    biometric_access = db.Column(db.Boolean, default=False, nullable=False)
    intercom = db.Column(db.Boolean, default=False, nullable=False)
    
    # Audit Metadata
    last_audit_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    next_audit_date = db.Column(db.DateTime)  # Scheduled next audit
    audit_score = db.Column(db.Integer, default=0, nullable=False)  # 0-100 score
    auditor_name = db.Column(db.String(255))  # Who conducted the audit
    audit_notes = db.Column(db.Text)  # Additional observations
    compliance_status = db.Column(db.String(50), default="pending")  # pending, approved, failed
    
    # Relationships
    room = db.relationship("Room", back_populates="safety_audit")

    def calculate_score(self) -> int:
        """Calculate safety score based on features (0-100)."""
        features = [
            self.fire_extinguisher,
            self.smoke_detector,
            self.first_aid_kit,
            self.emergency_exit,
            self.cctv,
            self.security_guard,
            self.biometric_access,
            self.intercom,
        ]
        return int((sum(features) / len(features)) * 100)

    def update_score(self):
        """Recalculate and update audit score."""
        self.audit_score = self.calculate_score()

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "room_id": self.room_id,
            "fire_extinguisher": self.fire_extinguisher,
            "smoke_detector": self.smoke_detector,
            "first_aid_kit": self.first_aid_kit,
            "emergency_exit": self.emergency_exit,
            "cctv": self.cctv,
            "security_guard": self.security_guard,
            "biometric_access": self.biometric_access,
            "intercom": self.intercom,
            "last_audit_date": self.last_audit_date.isoformat() if self.last_audit_date else None,
            "next_audit_date": self.next_audit_date.isoformat() if self.next_audit_date else None,
            "audit_score": self.audit_score,
            "auditor_name": self.auditor_name,
            "audit_notes": self.audit_notes,
            "compliance_status": self.compliance_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
