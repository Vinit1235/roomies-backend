"""Base database configuration and mixins."""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


class TimestampMixin:
    """Adds created_at and updated_at to models."""
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class PasswordMixin:
    """Password hashing helpers."""
    password = db.Column(db.String(255), nullable=False)

    def set_password(self, raw_password: str) -> None:
        """Hash and set password."""
        self.password = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def verify_password(self, raw_password: str) -> bool:
        """Verify password against hash."""
        if not self.password:
            return False
        try:
            return bcrypt.check_password_hash(self.password, raw_password)
        except ValueError:
            return self.password == raw_password
