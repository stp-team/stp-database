"""Вложения сообщений кандидатов."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    String,
    func,
)

from sqlalchemy.dialects.mysql import (
    MEDIUMBLOB,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from stp_database.models.base import Base


class CandidateAttachment(Base):
    """Файл, загруженный в чат кандидата."""

    __tablename__ = (
        "attachments"
    )

    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    uuid: Mapped[str] = mapped_column(
        String(250),
        primary_key=True,
        nullable=False,
    )

    candidate_uuid: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
        index=True,
    )

    name: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    content_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    content: Mapped[bytes] = mapped_column(
        MEDIUMBLOB,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )