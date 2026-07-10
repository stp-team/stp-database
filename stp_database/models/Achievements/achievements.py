"""Модель достижения."""

from datetime import datetime

from sqlalchemy.dialects.mysql import LONGTEXT, VARCHAR
from sqlalchemy import JSON, Enum, Boolean, Integer
from sqlalchemy import BIGINT, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from stp_database.models.base import Base

class Achievements(Base):
    """Предмет достижения."""

    __tablename__ = "achievements"

    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    uuid: Mapped[str] = mapped_column(
        String(250),
        unique=True,
        primary_key=True,
        comment="Уникальный идентификатор достижения"
    )

    name: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
        comment="Название достижения"
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Описание достижения"
    )
    divisions: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        comment="Список направлений которые могут получить достижение"
    )
    positions: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        comment="Список должностей которые могут получить это достижение"
    )
    rule_expression: Mapped[str] = mapped_column(
        LONGTEXT,
        nullable=False,
        default='{"type": "constant", "kpi": {}}',
        comment="Требования для получения достижения",
    )
    period: Mapped[str] = mapped_column(
        Enum("daily", "weekly", "monthly", "manual"),
        nullable=False,
        comment="Частота возможного получения достижения: день, неделя, месяц и ручная",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment="Кем создано"
    )
    created_by: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Когда создано"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=True,
        comment="Кем обновлено"
    )
    updated_by: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        comment="Когда обновлено"
    )