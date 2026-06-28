"""Модель статьи/заметки."""

from datetime import datetime

from sqlalchemy import BIGINT, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from stp_database.models.base import Base

class Note(Base):
    """Статья внутри пространства."""

    __tablename__ = "notes"

    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    uuid: Mapped[str] = mapped_column(String(250), primary_key=True)

    space_uuid: Mapped[str] = mapped_column(
        String(250),
        ForeignKey("spaces.uuid", ondelete="CASCADE"),
        nullable=False,
    )

    short_link: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)

    title: Mapped[str| None] = mapped_column(String(250), nullable=True)
    disclaimer: Mapped[str | None] = mapped_column(String(250), nullable=True)

    # Здесь будет храниться уже зашифрованный content.
    content: Mapped[str] = mapped_column(Text, nullable=False)

    created_by: Mapped[int] = mapped_column(BIGINT, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    updated_by: Mapped[int | None] = mapped_column(BIGINT, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)