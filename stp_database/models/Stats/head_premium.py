"""Модели, связанные с сущностями премии руководителей."""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from stp_database.models.base import Base


class HeadPremium(Base):
    """Модель, представляющая сущность премии руководителя за месяц в БД.

    Args:
        employee_id: Идентификатор сотрудника на OKC

        gok: Значение показателя ГОК
        gok_normative: Норматив показателя ГОК
        gok_pers_normative: Персональный норматив показателя ГОК
        gok_normative_rate: Процент выполнения норматива ГОК

        flr: Значение показателя FLR
        flr_normative: Норматив показателя FLR
        flr_pers_normative: Персональный норматив показателя FLR
        flr_normative_rate: Процент выполнения норматива FLR

        aht: Значение показателя AHT
        aht_normative: Норматив показателя AHT
        aht_pers_normative: Персональный норматив показателя AHT
        aht_normative_rate: Процент выполнения норматива AHT

        raw_premium: Общий процент выполнения
        total_premium: Общий процент премии
        updated_at: Дата обновления показателей премии
        extraction_period: Дата, с которой производилась выгрузка премии

    Methods:
        __repr__(): Возвращает строковое представление объекта HeadPremium.
    """

    __tablename__ = "HeadPremium"

    employee_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        primary_key=True,
        comment="Идентификатор сотрудника на OKC",
    )

    gok: Mapped[float | None] = mapped_column(Float, nullable=True)
    gok_normative: Mapped[float | None] = mapped_column(Float, nullable=True)
    gok_pers_normative: Mapped[float | None] = mapped_column(Float, nullable=True)
    gok_normative_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    flr: Mapped[float | None] = mapped_column(Float, nullable=True)
    flr_normative: Mapped[float | None] = mapped_column(Float, nullable=True)
    flr_pers_normative: Mapped[float | None] = mapped_column(Float, nullable=True)
    flr_normative_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    aht: Mapped[float | None] = mapped_column(Float, nullable=True)
    aht_normative: Mapped[float | None] = mapped_column(Float, nullable=True)
    aht_pers_normative: Mapped[float | None] = mapped_column(Float, nullable=True)
    aht_normative_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    raw_premium: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Общий процент выполнения"
    )
    total_premium: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Общий процент премии"
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="Дата обновления показателей премии",
        default=datetime.now,
    )
    extraction_period: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        primary_key=True,
        comment="Дата, с которой производилась выгрузка премии",
    )

    def __repr__(self):
        """Возвращает строковое представление объекта HeadPremium."""
        return f"<HeadPremium employee_id={self.employee_id} total_premium={self.total_premium} updated_at={self.updated_at}>"
