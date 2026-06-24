"""Модель списка игр GameCenter."""

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from stp_database.models.base import Base

class GameList(Base):
    """Модель игры из таблицы games_list"""
    __tablename__ = 'games_list'

    uuid: Mapped[str] = mapped_column(
        String(250),
        primary_key=True,
        comment="UUID игры",
    )

    title: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
        comment="Название игры",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="Описание игры",
    )

    url_game: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="URL игры"
    )

    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        comment="Работоспособность игры",
    )

    val_min_bet: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Минимальная ставка",
    )

    val_max_bet: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Максимальная ставка",
    )

    val_max_daily_used: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Максимальное кол-во использований в день",
    )

    val_chance_winning: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        default=None,
        comment="Общий шанс победы",
    )