from datetime import date

from sqlalchemy import Date, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Report(Base):

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    report_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
    )

    data_source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    report_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    event_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    employer: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        index=True,
    )

    city: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    state: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    naics: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,
    )

    candidate_oil_gas: Mapped[int] = mapped_column(
        Integer,
        default=0,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    nature: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    event: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    secondary_source: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    federal_state: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    hospitalized: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    amputation: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    loss_of_eye: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )