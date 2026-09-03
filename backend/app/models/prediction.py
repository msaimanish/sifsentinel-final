from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ModelPrediction(Base):

    __tablename__ = "model_predictions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    report_id: Mapped[int] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"),
        index=True,
    )

    model_version: Mapped[str] = mapped_column(
        String(100),
        index=True,
    )

    sif_probability: Mapped[float] = mapped_column(
        Float,
    )

    sif_label: Mapped[str] = mapped_column(
        String(20),
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    prediction_timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )