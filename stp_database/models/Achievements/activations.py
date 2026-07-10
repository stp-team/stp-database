"""Модель очереди активаций."""

from datetime import datetime

from sqlalchemy.dialects.mysql import LONGTEXT, VARCHAR
from sqlalchemy import JSON, Enum, Boolean, Integer
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

    item_uuid: Mapped[str] = mapped_column(
        String(250),
        comment="Идентификатор купленного предмета в инвентаре"
    )

    item_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Количество которое подано на активацию"
    )

    comment_user: Mapped[str] = mapped_column(
        LONGTEXT,
        nullable=True,
        comment="Комментарий пользователя",
    )

    status: Mapped[str] = mapped_column(
        Enum("ready", "inprogress", "approved", "rejected"),
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
        server_default=func.now(),
        nullable=False,
    )

    review_by: Mapped[int] = mapped_column(
        BIGINT,
        nullable=False
    )