import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Category(str, enum.Enum):
    movie = "movie"
    tv = "tv"
    actor = "actor"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    onboarding_variant: Mapped[str] = mapped_column(String, default="control")
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    games: Mapped[list["GameAttempt"]] = relationship(back_populates="user")
    events: Mapped[list["Event"]] = relationship(back_populates="user")


class DailyWord(Base):
    __tablename__ = "daily_words"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    word_date: Mapped[date] = mapped_column(Date, unique=True, index=True, nullable=False)
    answer: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[Category] = mapped_column(Enum(Category), nullable=False)
    clue: Mapped[str] = mapped_column(String, nullable=True)
    source_id: Mapped[str] = mapped_column(String, nullable=True)


class GameAttempt(Base):
    __tablename__ = "game_attempts"
    __table_args__ = (UniqueConstraint("user_id", "daily_word_id", name="uq_user_word"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    daily_word_id: Mapped[str] = mapped_column(ForeignKey("daily_words.id"), nullable=False)
    guesses: Mapped[str] = mapped_column(String, default="")  # comma-separated guess words
    won: Mapped[bool] = mapped_column(Boolean, default=False)
    attempts_used: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="games")


class Event(Base):
    """Funnel/activation tracking: signup, game_started, game_won, paywall_viewed, upgraded, etc."""

    __tablename__ = "events"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    properties: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    user: Mapped["User"] = relationship(back_populates="events")


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    variants: Mapped[str] = mapped_column(String, nullable=False)  # comma-separated
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Assignment(Base):
    __tablename__ = "assignments"
    __table_args__ = (UniqueConstraint("user_id", "experiment_key", name="uq_user_experiment"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    experiment_key: Mapped[str] = mapped_column(String, nullable=False)
    variant: Mapped[str] = mapped_column(String, nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    stripe_customer_id: Mapped[str] = mapped_column(String, nullable=True)
    stripe_subscription_id: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="inactive")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
