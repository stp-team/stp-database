"""Модель очереди активаций."""

from datetime import datetime

from sqlalchemy.dialects.mysql import LONGTEXT, VARCHAR
from sqlalchemy import JSON, Enum, Boolean, Integer, null
from sqlalchemy import BIGINT, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from stp_database.models.base import Base

class Activations(Base):
    """Предмет активации."""

    __tablename__ = "activations"

    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    uuid: Mapped[str] = mapped_column(
        String(250),
        unique=True,
        primary_key=True,
        comment="Уникальный идентификатор заявки"
    )

    award_uuid: Mapped[str] = mapped_column(
        String(250),
        comment="Идентификатор награды которая подана на активацию"
    )

    manager_role: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Роль сотрудника, ответственного за обработку заявки",
    )

    item_uuid: Mapped[str] = mapped_column(
        String(250),
        comment="Идентификатор купленного предмета в инвентаре"
    )

    item_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Количество которое подано на активацию"
    )

    form_data: Mapped[str] = mapped_column(
        LONGTEXT,
        nullable=False,
        default='[]',
        comment="JSON список заполненных полей формы активации",
    )

    status: Mapped[str] = mapped_column(
        Enum("ready", "inprogress", "approved", "rejected", "rollback"),
        nullable=False,
        comment="Статус заявки: в очереди, в работе, подтвержден, отклонен",
        default="ready",
    )

    review_comment: Mapped[str] = mapped_column(
        LONGTEXT,
        nullable=True,
        comment="Комментарий ответственного",
    )

    review_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
    )

    review_by: Mapped[int] = mapped_column(
        BIGINT,
        nullable=True,
        default=None,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment="Когда создана заявка",
    )

    created_by: Mapped[int] = mapped_column(
        BIGINT,
        nullable=False,
        comment="Кем создана заявка",
    )