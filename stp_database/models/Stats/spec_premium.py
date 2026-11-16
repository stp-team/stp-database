"""Модели, связанные с сущностями премии специалистов."""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from stp_database.models.base import Base


class SpecPremium(Base):
    """Модель, представляющая сущность премии специалиста за месяц в БД.

    Args:
        employee_id: Идентификатор сотрудника на OKC
        contacts_count: Кол-во контактов специалиста

        aht: Значение показателя AHT
        aht_normative: Норматив показателя AHT
        aht_pers_normative: Персональный норматив показателя AHT
        aht_normative_rate: Процент выполнения норматива AHT

        csat: Значение показателя CSAT
        csat_normative: Норматив показателя CSAT
        csat_pers_normative: Персональный норматив показателя CSAT
        csat_normative_rate: Процент выполнения норматива CSAT

        csi: Значение показателя Отклик
        csi_normative: Норматив показателя Отклик
        csi_normative_rate: Процент выполнения норматива Отклик

        gok: Значение показателя ГОК
        gok_normative: Норматив показателя ГОК
        gok_pers_normative: Персональный норматив показателя ГОК
        gok_normative_rate: Процент выполнения норматива ГОК

        revenue: Фактическая выручка от продажи оборудования
        revenue_normative: План выручки от продажи оборудования
        revenue_normative_rate: Процент выполнения плана выручки

        raw_premium: Общий процент выполнения
        total_premium: Общий процент премии
        updated_at: Дата обновления показателей премии
        extraction_period: Дата, с которой производилась выгрузка премии

    Methods:
        __repr__(): Возвращает строковое представление объекта SpecPremium.
    """

    __tablename__ = "SpecPremium"

    employee_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        primary_key=True,
        comment="Идентификатор сотрудника на OKC",
    )
    contacts_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Кол-во контактов специалиста"
    )

    aht: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Значение показателя AHT"
    )
    aht_normative: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Норматив показателя AHT"
    )
    aht_pers_normative: Mapped[float | None] = mapped_column(Float, nullable=True)
    aht_normative_rate: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Процент выполнения норматива AHT"
    )

    csat: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Значение показателя CSAT"
    )
    csat_normative: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Норматив показателя CSAT"
    )
    csat_pers_normative: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Личный норматив показателя CSAT"
    )
    csat_normative_rate: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Процент выполнения норматива CSAT"
    )

    csi: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Значение показателя Отклик"
    )
    csi_normative: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Норматив показателя Отклик"
    )
    csi_normative_rate: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Процент выполнения норматива Отклик"
    )

    gok: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Значение показателя ГОК"
    )
    gok_normative: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Норматив показателя ГОК"
    )
    gok_pers_normative: Mapped[float | None] = mapped_column(Float, nullable=True)
    gok_normative_rate: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Процент выполнения норматива ГОК"
    )

    revenue: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Фактическая выручка от продажи оборудования"
    )
    revenue_normative: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="План выручки от продажи оборудования"
    )
    revenue_normative_rate: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Процент выполнения плана выручки"
    )

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
        """Возвращает строковое представление объекта SpecPremium."""
        return f"<SpecPremium employee_id={self.employee_id} contacts_count={self.contacts_count} total_premium={self.total_premium} updated_at={self.updated_at}>"
