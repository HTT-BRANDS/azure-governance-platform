"""Resource inventory database models."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
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
    provisioning_state: Mapped[str | None] = Column(String(50))
    sku: Mapped[str | None] = Column(String(100))
    kind: Mapped[str | None] = Column(String(100))
    tags_json: Mapped[str | None] = Column(Text)  # JSON blob
    is_orphaned: Mapped[int] = Column(Integer, default=0)  # SQLite bool
    estimated_monthly_cost: Mapped[float | None] = Column(Integer)
    synced_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Resource {self.resource_type}/{self.name}>"


class ResourceTag(Base):
    """Tag compliance tracking."""

    __tablename__ = "resource_tags"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    resource_id: Mapped[str] = Column(String(500), ForeignKey("resources.id"), nullable=False)
    tag_name: Mapped[str] = Column(String(255), nullable=False)
    tag_value: Mapped[str | None] = Column(String(500))
    is_required: Mapped[int] = Column(Integer, default=0)  # SQLite bool
    synced_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<ResourceTag {self.tag_name}={self.tag_value}>"


class IdleResource(Base):
    """Detected idle resources for optimization."""

    __tablename__ = "idle_resources"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    resource_id: Mapped[str] = Column(String(500), ForeignKey("resources.id"), nullable=False)
    tenant_id: Mapped[str] = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    subscription_id: Mapped[str] = Column(String(36), nullable=False)
    detected_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    idle_type: Mapped[str] = Column(String(50), nullable=False)  # low_cpu, no_connections, etc.
    description: Mapped[str] = Column(Text, nullable=False)
    estimated_monthly_savings: Mapped[float | None] = Column(Float)
    idle_days: Mapped[int] = Column(Integer, default=0)
    is_reviewed: Mapped[int] = Column(Integer, default=0)  # SQLite bool
    reviewed_by: Mapped[str | None] = Column(String(255))
    reviewed_at: Mapped[datetime | None] = Column(DateTime)
    review_notes: Mapped[str | None] = Column(Text)

    def __repr__(self) -> str:
        return f"<IdleResource {self.idle_type}: ${self.estimated_monthly_savings:.2f}/mo>"
