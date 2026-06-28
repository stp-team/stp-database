"""Модель пространств для блокнота."""

from datetime import datetime
from enum import Enum

from sqlalchemy import BIGINT, DateTime, Enum as SqlEnum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from stp_database.models.base import Base

class SpaceVisibility(str, Enum):
    """Видимость пространства."""

    private = "private"
    public = "public"

class SpaceType(str, Enum):
    """Тип пространства."""

    personal = "personal"
    group = "group"

class Space(Base):
    """Пространство для заметок/статей."""

    __tablename__ = "spaces"

    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    uuid: Mapped[str] = mapped_column(String(250), primary_key=True)
    short_name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    text_name: Mapped[str] = mapped_column(String(250), nullable=False)

    visibility: Mapped[SpaceVisibility] = mapped_column(
        SqlEnum(SpaceVisibility),
        nullable=False,
        default=SpaceVisibility.private,
    )

    type: Mapped[SpaceType] = mapped_column(
        SqlEnum(SpaceType),
        nullable=False,
        default=SpaceType.personal,
    )

    owned_by: Mapped[int] = mapped_column(BIGINT, nullable=False)
    created_by: Mapped[int] = mapped_column(BIGINT, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )