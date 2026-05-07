"""Модель, связанная с сущностью обычной смены."""
import uuid

from datetime import datetime

from sqlalchemy import BIGINT, BOOLEAN, DateTime, Integer, Unicode
from sqlalchemy.orm import Mapped, mapped_column

from stp_database.models.base import Base

def generate_uuid():
    return str(uuid.uuid4())

class Shift(Base):
    """Модель, представляющая сущность смены в БД.

    Args:
        uuid: Уникальный ID смены
        user_id: Уникальный ID сотрудника
        date_start: Дата начала
        date_end: Дата окончания
        type: тип: base - основная, add - допка, out - отработка, other - другое
        comment: комментарий

    Methods:
        __repr__(): Возвращает строковое представление объекта shift.
    """

    __tablename__ = "shifts"

    uuid: Mapped[str] = mapped_column(
        Unicode(36),
        unique=True,
        nullable=False,
        default=generate_uuid,
        comment="Уникальный ID смены"
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Уникальный ID сотрудника"
    )

    date_start: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="Время начала"
    )

    date_end: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="Время окончания"
    )

    type: Mapped[str] = mapped_column(
        Unicode(5000),
        nullable=False,
        default="other",
        comment="Тип смены"
    )

    comment: Mapped[str] = mapped_column(
        Unicode(5000),
        nullable=True,
        default=None,
        comment="Комментарий"
    )


    def __repr__(self):
        """Возвращает строковое представление объекта Shift."""
        return f"<Shift {self.uuid} {self.user_id} {self.date_start} {self.date_end} {self.type} {self.comment}>"