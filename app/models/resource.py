"""Resource inventory database models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped

from app.core.database import Base


class Resource(Base):
    """Azure resource inventory item."""

    __tablename__ = "resources"

    id: Mapped[str] = Column(String(500), primary_key=True)  # Azure resource ID
    tenant_id: Mapped[str] = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    subscription_id: Mapped[str] = Column(String(36), nullable=False)
    resource_group: Mapped[str] = Column(String(255), nullable=False)
    resource_type: Mapped[str] = Column(String(255), nullable=False)
    name: Mapped[str] = Column(String(255), nullable=False)
    location: Mapped[str] = Column(String(100))
    provisioning_state: Mapped[Optional[str]] = Column(String(50))
    sku: Mapped[Optional[str]] = Column(String(100))
    kind: Mapped[Optional[str]] = Column(String(100))
    tags_json: Mapped[Optional[str]] = Column(Text)  # JSON blob
    is_orphaned: Mapped[int] = Column(Integer, default=0)  # SQLite bool
    estimated_monthly_cost: Mapped[Optional[float]] = Column(Integer)
    synced_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Resource {self.resource_type}/{self.name}>"


class ResourceTag(Base):
    """Tag compliance tracking."""

    __tablename__ = "resource_tags"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    resource_id: Mapped[str] = Column(String(500), ForeignKey("resources.id"), nullable=False)
    tag_name: Mapped[str] = Column(String(255), nullable=False)
    tag_value: Mapped[Optional[str]] = Column(String(500))
    is_required: Mapped[int] = Column(Integer, default=0)  # SQLite bool
    synced_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<ResourceTag {self.tag_name}={self.tag_value}>"
