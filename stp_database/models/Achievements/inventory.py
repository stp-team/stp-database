"""Модель инвентаря."""

from datetime import datetime

from sqlalchemy.dialects.mysql import LONGTEXT, VARCHAR
from sqlalchemy import JSON, Enum, Boolean, Integer
from sqlalchemy import BIGINT, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from stp_database.models.base import Base

class Inventory(Base):
    """Предмет инвентаря."""

    __tablename__ = "inventory"

    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    uuid: Mapped[str] = mapped_column(
        String(250),
        unique=True,
        primary_key=True,
        comment="Уникальный идентификатор предмета в инвентаре"
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="ID пользователя",
    )

    award_uuid: Mapped[str] = mapped_column(
        String(250),
        comment="Идентификатор награды которая была куплена в инвентарь"
    )

    remaining_uses: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Остаток доступных активаций",
    )

    bought_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment="Когда было куплено",
    )

    status: Mapped[str] = mapped_column(
        Enum("stored", "used_up", "rollback"),
        nullable=False,
        comment="Статус",
        default="stored",
    )