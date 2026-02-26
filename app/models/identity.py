"""Identity governance database models."""

from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped

from app.core.database import Base


class IdentitySnapshot(Base):
    """Identity statistics snapshot per tenant."""

    __tablename__ = "identity_snapshots"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    snapshot_date: Mapped[date] = Column(Date, nullable=False)
    total_users: Mapped[int] = Column(Integer, default=0)
    active_users: Mapped[int] = Column(Integer, default=0)
    guest_users: Mapped[int] = Column(Integer, default=0)
    mfa_enabled_users: Mapped[int] = Column(Integer, default=0)
    mfa_disabled_users: Mapped[int] = Column(Integer, default=0)
    privileged_users: Mapped[int] = Column(Integer, default=0)
    stale_accounts_30d: Mapped[int] = Column(Integer, default=0)
    stale_accounts_90d: Mapped[int] = Column(Integer, default=0)
    service_principals: Mapped[int] = Column(Integer, default=0)
    synced_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<IdentitySnapshot {self.snapshot_date}: {self.total_users} users>"


class PrivilegedUser(Base):
    """Privileged user tracking."""

    __tablename__ = "privileged_users"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    user_principal_name: Mapped[str] = Column(String(255), nullable=False)
    display_name: Mapped[str] = Column(String(255))
    user_type: Mapped[str] = Column(String(50))  # Member, Guest
    role_name: Mapped[str] = Column(String(255), nullable=False)
    role_scope: Mapped[str] = Column(String(500))  # subscription, resource group, etc.
    is_permanent: Mapped[int] = Column(Integer, default=1)  # vs PIM eligible
    mfa_enabled: Mapped[int] = Column(Integer, default=0)
    last_sign_in: Mapped[datetime | None] = Column(DateTime)
    synced_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<PrivilegedUser {self.user_principal_name}: {self.role_name}>"
