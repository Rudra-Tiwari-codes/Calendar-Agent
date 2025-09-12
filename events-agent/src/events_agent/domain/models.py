from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Integer, String, UniqueConstraint, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    discord_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    tz: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    google_sub: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    token_ciphertext: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class GuildSettings(Base):
    __tablename__ = "guild_settings"
    __table_args__ = (UniqueConstraint("guild_id", name="uq_guild_settings_guild"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    default_channel_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    default_tz: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class Reminder(Base):
    __tablename__ = "reminders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    event_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    channel_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent: Mapped[bool] = mapped_column(Boolean, default=False)
    retries: Mapped[int] = mapped_column(Integer, default=0)
    __table_args__ = (UniqueConstraint("event_id", "remind_at", name="uq_reminder_event_at"),)


class EventTemplate(Base):
    __tablename__ = "event_templates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    location: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    default_attendees: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    reminder_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_pattern: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_user_template_name"),)


