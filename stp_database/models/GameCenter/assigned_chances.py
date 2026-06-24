"""Модель индивидуальных шансов GameCenter."""

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from stp_database.models.base import Base

class AssignedChances(Base):
    __tablename__ = "assigned_chances"

    uuid: Mapped[str] = mapped_column(
        String(250),
        primary_key=True,
        comment="UUID записи",
    )

    game_uuid: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
        index=True,
        comment="UUID игры",
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="ID сотрудника",
    )

    chance: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.1,
        comment="Индивидуальный шанс на победу"
    )