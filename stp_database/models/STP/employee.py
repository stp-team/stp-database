"""Модели, связанные с сущностями сотрудников."""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import BIGINT, BOOLEAN, INTEGER, Computed, Date, Unicode, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stp_database.models.base import Base

if TYPE_CHECKING:
    from stp_database.models.STP.event_log import EventLog
    from stp_database.models.STP.exchange import Exchange, ExchangeSubscription


class Employee(Base):
    """Модель, представляющий сущность сотрудника в БД.

    Args:
        id: Уникальный идентификатор пользователя
        user_id: Идентификатор сотрудника в Telegram
        username: Username сотрудника в Telegram
        division: Направление сотрудника (НТП/НЦК)
        position: Позиция/должность сотрудника
        fullname: ФИО сотрудника
        head: ФИО руководителя сотрудника
        email: Email сотрудника
        role: Уровень доступа сотрудника в БД
        is_trainee: Является ли сотрудник стажером
        is_casino_allowed: Разрешено ли казино сотруднику
        is_exchange_banned: Забанен ли сотрудник на бирже смен

    Methods:
        __repr__(): Возвращает строковое представление объекта Employee.
    """

    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(
        BIGINT, primary_key=True, comment="Уникальный идентификатор пользователя"
    )
    employee_id: Mapped[int] = mapped_column(
        BIGINT, nullable=True, comment="Идентификатор сотрудника в OKC"
    )
    user_id: Mapped[int] = mapped_column(
        BIGINT, nullable=True, comment="Идентификатор сотрудника в Telegram"
    )
    username: Mapped[str] = mapped_column(
        Unicode, nullable=True, comment="Username сотрудника в Telegram"
    )
    division: Mapped[str] = mapped_column(
        Unicode, nullable=True, comment="Направление сотрудника (НТП/НЦК)"
    )
    position: Mapped[str] = mapped_column(
        Unicode, nullable=True, comment="Позиция/должность сотрудника"
    )
    fullname: Mapped[str] = mapped_column(
        Unicode, nullable=False, comment="ФИО сотрудника"
    )
    fullname_hash: Mapped[str] = mapped_column(
        Unicode(64),
        Computed(func.sha2("fullname", 256), persisted=True),
        nullable=False,
        comment="Хеш ФИО сотрудника",
    )
    head: Mapped[str] = mapped_column(
        Unicode, nullable=True, comment="ФИО руководителя сотрудника"
    )
    email: Mapped[str] = mapped_column(
        Unicode, nullable=True, comment="Email сотрудника"
    )
    birthday: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="День рождения",
    )
    employment_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Дата трудоустройства",
    )
    role: Mapped[int] = mapped_column(
        BIGINT, nullable=False, comment="Уровень доступа сотрудника в БД"
    )

    is_trainee: Mapped[bool] = mapped_column(
        BOOLEAN, nullable=False, default=True, comment="Является ли сотрудник стажером"
    )
    is_tutor: Mapped[bool] = mapped_column(
        BOOLEAN,
        nullable=False,
        default=False,
        comment="Является ли сотрудник наставником",
    )
    tutor_type: Mapped[int] = mapped_column(
        INTEGER, nullable=True, comment="Тип наставника"
    )
    tutor_subtype: Mapped[int] = mapped_column(
        INTEGER, nullable=True, comment="Подтип наставника"
    )

    is_casino_allowed: Mapped[bool] = mapped_column(
        BOOLEAN, nullable=False, comment="Разрешено ли казино сотруднику"
    )
    is_exchange_banned: Mapped[bool] = mapped_column(
        BOOLEAN,
        nullable=False,
        default=False,
        comment="Забанен ли сотрудник на бирже подмен",
    )
    access: Mapped[bool] = mapped_column(
        BOOLEAN,
        nullable=False,
        default=True,
        comment="Есть ли у сотрудника доступ к системам",
    )
    on_vacation: Mapped[bool] = mapped_column(
        BOOLEAN,
        nullable=False,
        default=False,
        comment="Находится ли сотрудник в отпуске",
    )

    # Отношения
    event_logs: Mapped[list["EventLog"]] = relationship(
        "EventLog", back_populates="employee", lazy="select"
    )
    owned_exchanges: Mapped[list["Exchange"]] = relationship(
        "Exchange",
        primaryjoin="Employee.user_id == foreign(Exchange.owner_id)",
        back_populates="owner",
        lazy="select",
    )
    counterpart_exchanges: Mapped[list["Exchange"]] = relationship(
        "Exchange",
        primaryjoin="Employee.user_id == foreign(Exchange.counterpart_id)",
        back_populates="counterpart",
        lazy="select",
    )
    exchange_subscriptions: Mapped[list["ExchangeSubscription"]] = relationship(
        "ExchangeSubscription",
        primaryjoin="Employee.user_id == foreign(ExchangeSubscription.subscriber_id)",
        back_populates="subscriber",
        lazy="select",
    )
    target_subscriptions: Mapped[list["ExchangeSubscription"]] = relationship(
        "ExchangeSubscription",
        primaryjoin="Employee.user_id == foreign(ExchangeSubscription.target_seller_id)",
        back_populates="target_seller",
        lazy="select",
    )

    def __repr__(self):
        """Возвращает строковое представление объекта Employee."""
        return f"<Employee {self.id} {self.user_id} {self.username} {self.fullname} {self.head} {self.email} {self.role}>"
