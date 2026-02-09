"""Модели, связанные с сущностями показателей специалистов."""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from stp_database.models.base import Base


class SpecKPI(Base):
    """Универсальная модель, представляющая сущность показателей специалиста день, неделю или месяц.

    Может работать с разными таблицами: KpiDay, KpiWeek, KpiMonth.
    Таблица указывается динамически через __table_args__ или при создании мапера.

    Args:
        fullname: ФИО специалиста
        contacts_count: Кол-во контактов специалиста

        csat: Значение показателя CSAT за период
        aht: Значение показателя AHT за период
        flr: Значение показателя FLR за период
        csi: Значение показателя оценки за период
        pok: Значение показателя отклика за период
        delay: Значение показателя задержки за период (только НТП)

        sales_count: Кол-во реальных продаж за период
        sales_potential: Кол-во потенциальных продаж за период
        sales_conversion: Конверсия продаж

        paid_service_count: Платный сервис реальный
        paid_service_conversion: Конверсия платного сервиса

        extraction_period: Дата, с которой производилась выгрузка показателей
        updated_at: Дата выгрузки показателей в БД

    Methods:
        __repr__(): Возвращает строковое представление объекта SpecKPI.
    """

    __tablename__ = None  # Будет установлено динамически
    __abstract__ = True  # Абстрактная модель

    employee_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        primary_key=True,
        comment="Идентификатор сотрудника на OKC",
    )
    contacts_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Кол-во контактов специалиста за период"
    )

    # Колонки, связанные с CSAT
    csat: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Значение показатели CSAT за период"
    )
    csat_rated: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Количество оцененных чатов в Генезис"
    )
    csat_high_rated: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Количество высоко оцененных чатов в Генезис"
    )

    # Колонки, связанные с AHT
    aht: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Значение показателя AHT за период"
    )
    aht_chats_mobile: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Кол-во контактов из приложения за период"
    )
    aht_chats_web: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Кол-во контактов из сайта за период"
    )
    aht_chats_smartdom: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Кол-во контактов из МП УДР за период"
    )
    aht_chats_dhcp: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Кол-во контактов из портала за период"
    )
    aht_chats_telegram: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Кол-во контактов из Telegram за период"
    )
    aht_chats_viber: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Кол-во контактов из Viber за период"
    )

    # Колонки, связанные с FLR
    flr: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Значение показателя FLR за период"
    )
    flr_services: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Кол-во сервисных заявок за период"
    )
    flr_services_cross: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Кол-во сквозных обращений за период"
    )
    flr_services_transfer: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Кол-во переведенных обращений за период"
    )

    # Колонки, связанные с CSI
    csi: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Значение показателя оценки за период"
    )

    # Колонки, связанные с POK
    pok: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Значение показателя отклика за период",
    )
    pok_rated_contacts: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Кол-во оцененных чатов за период"
    )

    # Колонки, связанные с Delay
    delay: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Значение показателя задержки за период",
    )

    # Колонки, связанные с реальными продажами
    sales: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Кол-во реальных продаж за период",
    )
    sales_videos: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Кол-во реальных продаж видеокамер за период",
    )
    sales_routers: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Кол-во реальных продаж роутеров за период",
    )
    sales_tvs: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Кол-во реальных продаж приставок за период",
    )
    sales_intercoms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Кол-во реальных продаж домофонов за период",
    )
    sales_conversion: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Конверсия реальных продаж за период",
    )

    # Колонки, связанные с потенциальными продажами
    sales_potential: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Кол-во потенциальных продаж за период",
    )
    sales_potential_video: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Кол-во потенциальных продаж видеокамер за период",
    )
    sales_potential_routers: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Кол-во потенциальных продаж роутеров за период",
    )
    sales_potential_tvs: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Кол-во потенциальных продаж приставок за период",
    )
    sales_potential_intercoms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Кол-во потенциальных продаж домофонов за период",
    )
    sales_potential_conversion: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Конверсия потенциальных продаж за период",
    )

    # Колонки, связанные с платным сервисом
    services: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Кол-во заявок на платный сервис за период",
    )
    services_remote: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Кол-во заявок на удаленный платный сервис за период",
    )
    services_onsite: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Кол-во заявок на выездной платный сервис за период",
    )
    services_conversion: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Конверсия платного сервиса за период",
    )

    thanks: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=0, comment="Кол-во благодарностей за период"
    )

    # Колонки, связанные с Q&A метриками
    q_answered: Mapped[int | None] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Кол-во ответов на вопросы за период",
    )
    q_asked: Mapped[int | None] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Кол-во заданных вопросов за период",
    )
    q_asked_conversion: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Конверсия заданных вопросов (вычисляемое поле)",
    )

    extraction_period: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        primary_key=True,
        comment="Дата, с которой производилась выгрузка отчета",
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="Дата выгрузки показателей в БД",
        default=datetime.now,
    )

    def __repr__(self) -> str:
        """Возвращает строковое представление объекта SpecKPI."""
        table = self.__tablename__
        return f"<SpecKPI[{table}] employee_id={self.employee_id} contacts_count={self.contacts_count} extraction_period={self.extraction_period} updated_at={self.updated_at}>"


# Конкретные модели для каждой таблицы
class SpecDayKPI(SpecKPI):
    """Модель показателей специалиста за день."""

    __tablename__ = "KpiDay"


class SpecWeekKPI(SpecKPI):
    """Модель показателей специалиста за неделю."""

    __tablename__ = "KpiWeek"


class SpecMonthKPI(SpecKPI):
    """Модель показателей специалиста за месяц."""

    __tablename__ = "KpiMonth"
