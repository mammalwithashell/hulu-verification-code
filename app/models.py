import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> uuid.UUID:
    return uuid.uuid4()


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    email_connections: Mapped[list["EmailConnection"]] = relationship(back_populates="user")
    streaming_accounts: Mapped[list["StreamingAccount"]] = relationship(back_populates="user")


class EmailConnection(Base):
    __tablename__ = "email_connections"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    email_address: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_secret_ref: Mapped[str] = mapped_column(Text, nullable=False)
    imap_server: Mapped[str] = mapped_column(String(255), nullable=False)
    imap_port: Mapped[int] = mapped_column(Integer, default=993)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user: Mapped["User"] = relationship(back_populates="email_connections")
    streaming_accounts: Mapped[list["StreamingAccount"]] = relationship(back_populates="email_connection")


class StreamingAccount(Base):
    __tablename__ = "streaming_accounts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    email_connection_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("email_connections.id"), nullable=False)
    service_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_label: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user: Mapped["User"] = relationship(back_populates="streaming_accounts")
    email_connection: Mapped["EmailConnection"] = relationship(back_populates="streaming_accounts")


class SharedAccess(Base):
    __tablename__ = "shared_access"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    grantee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    streaming_account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("streaming_accounts.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    owner: Mapped["User"] = relationship(foreign_keys=[owner_id])
    grantee: Mapped["User"] = relationship(foreign_keys=[grantee_id])
    streaming_account: Mapped["StreamingAccount"] = relationship()


class VerificationRequest(Base):
    __tablename__ = "verification_requests"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    requester_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    streaming_account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("streaming_accounts.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    code: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)
    confidence: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)
    error: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    requester: Mapped["User"] = relationship()
    streaming_account: Mapped["StreamingAccount"] = relationship()
    events: Mapped[list["VerificationEvent"]] = relationship(back_populates="verification_request")


class VerificationEvent(Base):
    __tablename__ = "verification_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    verification_request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("verification_requests.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    verification_request: Mapped["VerificationRequest"] = relationship(back_populates="events")
