"""Модель, связанная с сущностью ShiftOut."""
import uuid

from datetime import datetime

from sqlalchemy import BIGINT, BOOLEAN, DateTime, Integer, Unicode
from sqlalchemy.orm import Mapped, mapped_column

from stp_database.models.base import Base

def generate_uuid():
    return str(uuid.uuid4())

class ShiftOut(Base):
    """Модель, представляющая сущность ShiftOut в БД.

    Args:
        uuid: Уникальный ID смены
        user_id: Уникальный ID сотрудника
        type: тип: base - основная, add - допка, out - отработка, other - другое
        date: Дата
        comment: комментарий

    Methods:
        __repr__(): Возвращает строковое представление объекта shift.
    """

    __tablename__ = "shifts_out"

    uuid: Mapped[str] = mapped_column(
        Unicode(36),
        unique=True,
        primary_key=True,
        nullable=False,
        default=generate_uuid,
        comment="Уникальный ID смены"
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Уникальный ID сотрудника"
    )

    type: Mapped[str] = mapped_column(
        Unicode(5000),
        nullable=False,
        default="other",
        comment="Тип смены"
    )

    date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="Дата"
    )

    comment: Mapped[str] = mapped_column(
        Unicode(5000),
        nullable=True,
        default=None,
        comment="Комментарий"
    )


    def __repr__(self):
        """Возвращает строковое представление объекта ShiftOut."""
        return f"<ShiftOut {self.uuid} {self.user_id} {self.type} {self.date} {self.comment}>"