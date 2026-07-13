"""Модель лога просчета достижения."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from stp_database.models.base import Base


class LogAchievements(Base):
    """Предмет лога просчета достижения."""

    __tablename__ = "log_achievements"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "achievement_uuid",
            name="uq_log_achievements_user_achievement",
        ),
        {
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    uuid: Mapped[str] = mapped_column(
        String(250),
        unique=True,
        primary_key=True,
        comment="Уникальный идентификатор записи лога",
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="ID пользователя",
    )

    achievement_uuid: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
        comment="Идентификатор достижения",
    )

    check_result: Mapped[str] = mapped_column(
        LONGTEXT,
        nullable=False,
        default="{}",
        comment="Результат проверки достижения по критериям",
    )

    checked_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment="Когда было просчитано",
    )
