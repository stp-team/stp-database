"""Модель наград."""

from datetime import datetime

from sqlalchemy.dialects.mysql import LONGTEXT, VARCHAR
from sqlalchemy import JSON, Enum, Boolean, Integer
from sqlalchemy import BIGINT, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from stp_database.models.base import Base

class Awards(Base):
    """Предмет активации."""

    __tablename__ = "awards"

    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    uuid: Mapped[str] = mapped_column(
        String(250),
        unique=True,
        primary_key=True,
        comment="Уникальный идентификатор награды"
    )

    name: Mapped[str] = mapped_column(
        String(250),
        comment="Название награды",
        default="Новая награда",
    )

    description: Mapped[str] = mapped_column(
        LONGTEXT,
        nullable=True,
        comment="Описание награды",
        default="Новая награда",
    )

    divisions: Mapped[str] = mapped_column(
        LONGTEXT,
        nullable=False,
        default='[]',
        comment="Направления сотрудники которого могут получать награду",
    )

    positions: Mapped[str] = mapped_column(
        LONGTEXT,
        nullable=False,
        default='[]',
        comment="Должности сотрудники которых могут получать награду",
    )

    cost: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Стоимость",
        default=1,
    )

    count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Количество активаций которые приобретает пользователь",
        default=1,
    )

    activations_rules: Mapped[str] = mapped_column(
        LONGTEXT,
        nullable=False,
        default='{}',
        comment="Правила активации наград",
    )

    activation_form_example: Mapped[str] = mapped_column(
        LONGTEXT,
        nullable=False,
        default='[]',
        comment="JSON список полей формы активации",
    )

    manager_role: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Роль ответственного пользователя",
        default=0,
    )

    status: Mapped[str] = mapped_column(
        Enum("unactive", "active"),
        nullable=False,
        comment="Статус активности",
        default="unactive",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    created_by: Mapped[int] = mapped_column(
        BIGINT,
        nullable=False
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    updated_by: Mapped[int | None] = mapped_column(
        BIGINT,
        nullable=True
    )