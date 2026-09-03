from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.database import Base


class ReportEmbedding(Base):

    __tablename__ = "report_embeddings"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    report_id: Mapped[int] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"),
        index=True,
    )

    model_name: Mapped[str] = mapped_column(
        String(200),
    )

    embedding: Mapped[list[float]] = mapped_column(
        Vector(768),
    )