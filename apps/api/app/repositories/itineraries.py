"""Small SQLAlchemy repository for saved itinerary snapshots.

Local development defaults to SQLite. Set DATABASE_URL to a PostgreSQL URL for
shared deployments; PostgreSQL URLs use the psycopg 3 driver.
"""

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from sqlalchemy import Index, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.domain.schemas import Itinerary


class ItineraryRepository(Protocol):
    def save(self, itinerary: Itinerary) -> Itinerary:
        """Store an immutable snapshot and return its new opaque ID."""

    def get(self, itinerary_id: str) -> Itinerary | None:
        """Fetch one saved itinerary by its opaque ID."""

    def list_recent(self, limit: int = 20) -> list[Itinerary]:
        """Return most recently generated saved itineraries."""


class _Base(DeclarativeBase):
    pass


class _ItineraryRow(_Base):
    __tablename__ = "itineraries"
    __table_args__ = (Index("ix_itineraries_saved_at", "saved_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    destination: Mapped[str] = mapped_column(String(160), nullable=False)
    saved_at: Mapped[str] = mapped_column(String(40), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)


def default_database_url() -> str:
    return os.environ.get("DATABASE_URL", "sqlite:///./data/itineraries.db")


class SqlAlchemyItineraryRepository:
    """Persist Pydantic itinerary snapshots with SQLite/PostgreSQL."""

    def __init__(self, database_url: str | None = None) -> None:
        url = database_url or default_database_url()
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url.removeprefix("postgres://")
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
        elif url.startswith("sqlite:///./"):
            local_path = Path(url.removeprefix("sqlite:///./"))
            local_path.parent.mkdir(parents=True, exist_ok=True)

        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        self._engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)
        _Base.metadata.create_all(self._engine)

    def save(self, itinerary: Itinerary) -> Itinerary:
        itinerary_id = str(uuid4())
        saved = itinerary.model_copy(update={"id": itinerary_id})
        payload = saved.model_dump_json()
        with Session(self._engine) as session, session.begin():
            row = _ItineraryRow(
                id=itinerary_id,
                destination=saved.destination,
                saved_at=datetime.now(UTC).isoformat(timespec="microseconds"),
                payload=payload,
            )
            session.add(row)
        return saved

    def get(self, itinerary_id: str) -> Itinerary | None:
        with Session(self._engine) as session:
            row = session.get(_ItineraryRow, itinerary_id)
            return Itinerary.model_validate_json(row.payload) if row else None

    def list_recent(self, limit: int = 20) -> list[Itinerary]:
        safe_limit = max(1, min(limit, 50))
        with Session(self._engine) as session:
            rows = session.scalars(
                select(_ItineraryRow)
                .order_by(_ItineraryRow.saved_at.desc(), _ItineraryRow.id)
                .limit(safe_limit)
            )
            return [Itinerary.model_validate_json(row.payload) for row in rows]
