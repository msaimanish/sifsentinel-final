from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PrecursorFeature(Base):

    __tablename__ = "precursor_features"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    report_id: Mapped[int] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"),
        index=True,
    )

    activity: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )

    hazard: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    exposure: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    barrier: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    barrier_failure: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    life_saving_rules: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )