from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String, Boolean, JSON
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import event

from app.database import Base


class BaseModel(Base):
    """
    Abstract base model with common fields for all models.
    All models should inherit from this class.
    Note: Models must define their own primary key (e.g., user_id, profile_id).
    """
    __abstract__ = True

    date_created = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    date_updated = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    meta = Column(JSON, nullable=True, default=lambda: {})

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def update_timestamp(self):
        """Update the date_updated timestamp."""
        self.date_updated = datetime.now(timezone.utc)


@event.listens_for(BaseModel, 'before_update', propagate=True)
def receive_before_update(mapper, connection, target):
    """Event listener to auto-update date_updated on record changes."""
    target.update_timestamp()
