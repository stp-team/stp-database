"""Модели, связанные с сущностями достижений."""

import json
from typing import Any

from sqlalchemy import Enum, Integer, Text
from sqlalchemy.dialects.mysql import LONGTEXT, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from stp_database.models.base import Base


class Achievement(Base):
    """Класс, представляющий сущность достижения в БД.

    Args:
        id: Уникальный идентификатор достижения
        name: Название достижения
        description: Описание достижения
        division: Направление сотрудника (НТП/НЦК) для получения достижения
        kpi: Показатели Stats для получения достижения
        reward: Награда за получение достижение в баллах
        position: Позиция/должность сотрудника для получения достижения
        period: Частота возможного получения достижения: день, неделя, месяц и ручная

    Methods:
        __repr__(): Возвращает строковое представление объекта Achievement.
    """

    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Уникальный идентификатор достижения",
    )
    name: Mapped[str] = mapped_column(
        VARCHAR(30), nullable=False, comment="Название достижения"
    )
    description: Mapped[str] = mapped_column(
        VARCHAR(255), nullable=False, comment="Описание достижения"
    )
    division: Mapped[str] = mapped_column(
        VARCHAR(3),
        nullable=False,
        comment="Направление сотрудника (НТП/НЦК) для получения достижения",
    )
    kpi: Mapped[str] = mapped_column(
        VARCHAR(3), nullable=False, comment="Показатели Stats для получения достижения"
    )
    reward: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Награда за получение достижение в баллах"
    )
    position: Mapped[str] = mapped_column(
        VARCHAR(31),
        nullable=False,
        comment="Позиция/должность сотрудника для получения достижения",
    )
    period: Mapped[str] = mapped_column(
        Enum("d", "w", "m", "A"),
        nullable=False,
        comment="Частота возможного получения достижения: день, неделя, месяц и ручная",
    )

    def __repr__(self):
        """Возвращает строковое представление объекта Achievement."""
        return f"<Achievement {self.id} {self.name} {self.description} {self.division} {self.kpi} {self.reward} {self.position} {self.period}>"


class AchievementNew(Base):
    """Класс, представляющий сущность достижения в БД (achievements_new).

    Args:
        id: Уникальный идентификатор достижения
        name: Название достижения
        description: Описание достижения
        division: Направление сотрудника (НТП/НЦК) для получения достижения
        requirements: Требования для получения достижения (JSON)
        reward: Награда за получение достижение в баллах
        position: Позиция/должность сотрудника для получения достижения
        period: Частота возможного получения достижения (daily, weekly, monthly, once, manual)

    Methods:
        __repr__(): Возвращает строковое представление объекта AchievementNew.
    """

    __tablename__ = "achievements_new"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Идентификатор",
    )
    name: Mapped[str] = mapped_column(VARCHAR(30), nullable=False, comment="Название")
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Описание"
    )
    division: Mapped[str] = mapped_column(
        VARCHAR(3),
        nullable=False,
        comment="Направление",
    )
    position: Mapped[str] = mapped_column(
        VARCHAR(31),
        nullable=False,
        comment="Должности, способные получить достижения",
    )
    requirements: Mapped[str] = mapped_column(
        LONGTEXT,
        nullable=False,
        default='{"type": "constant", "kpi": {}}',
        comment="Требования для получения достижения",
    )
    reward: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Награда в баллах"
    )
    period: Mapped[str] = mapped_column(
        Enum("daily", "weekly", "monthly", "once", "manual", name="achievement_period"),
        nullable=False,
        comment="Период получения достижения",
    )

    @property
    def requirements_dict(self) -> str | Any:
        """Get requirements as a dictionary."""
        if isinstance(self.requirements, str):
            return json.loads(self.requirements)
        return self.requirements

    @requirements_dict.setter
    def requirements_dict(self, value: dict) -> None:
        """Set requirements from a dictionary."""
        self.requirements = json.dumps(value)

    def __repr__(self):
        """Возвращает строковое представление объекта AchievementNew."""
        return f"<AchievementNew {self.id} {self.name} {self.description} {self.division} {self.requirements} {self.reward} {self.position} {self.period}>"
