"""Текущие месячные показатели наставников."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from stp_database.models.base import Base


class Tutors(Base):
    __tablename__ = "Tutors"

    employee_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        nullable=False,
    )

    shifts_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    trainee_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    extraction_period: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=func.now(),
        onupdate=func.now(),
    )
