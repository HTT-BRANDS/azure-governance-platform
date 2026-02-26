"""Tenant and subscription models."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base


class Tenant(Base):
    """Azure tenant configuration."""

    __tablename__ = "tenants"

    id: Mapped[str] = Column(String(36), primary_key=True)
    name: Mapped[str] = Column(String(255), nullable=False)
    tenant_id: Mapped[str] = Column(String(36), unique=True, nullable=False)
    client_id: Mapped[str | None] = Column(String(36))
    client_secret_ref: Mapped[str | None] = Column(String(500))  # Key Vault URI
    description: Mapped[str | None] = Column(Text)
    is_active: Mapped[bool] = Column(Boolean, default=True)
    use_lighthouse: Mapped[bool] = Column(Boolean, default=False)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription", back_populates="tenant", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Tenant {self.name} ({self.tenant_id})>"


class Subscription(Base):
    """Azure subscription within a tenant."""

    __tablename__ = "subscriptions"

    id: Mapped[str] = Column(String(36), primary_key=True)
    tenant_ref: Mapped[str] = Column(
        String(36), ForeignKey("tenants.id"), nullable=False
    )
    subscription_id: Mapped[str] = Column(String(36), nullable=False)
    display_name: Mapped[str] = Column(String(255), nullable=False)
    state: Mapped[str] = Column(String(50), default="Enabled")
    synced_at: Mapped[datetime | None] = Column(DateTime)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="subscriptions")

    def __repr__(self) -> str:
        return f"<Subscription {self.display_name} ({self.subscription_id})>"
