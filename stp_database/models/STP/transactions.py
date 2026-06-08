"""Модели, связанные с сущностями транзакций."""

from datetime import datetime

from sqlalchemy import TIMESTAMP, Enum, Integer, String
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from stp_database.models.base import Base


class Transaction(Base):
    """Класс, представляющий сущность транзакции пользователя в БД.

    Args:
        id: Уникальный идентификатор транзакции
        user_id: Идентификатор Telegram сотрудника
        type: Тип операции: начисление или списание
        source_id: Идентификатор достижения или предмета. Для manual или casino — None
        source_type: Источник транзакции: achievement, product, casino, manual
        amount: Количество баллов
        comment: Комментарий к транзакции
        kpi_extracted_at: Дата выгрузки показателей. Указывается в случае награды за достижения
        created_by: ID администратора, создавшего транзакцию. None если создана автоматически
        created_at: Дата создания транзакции

    Methods:
        __repr__(): Возвращает строковое представление объекта Transaction.
    """

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="Уникальный идентификатор транзакции",
    )
    user_id: Mapped[int] = mapped_column(
        BIGINT, nullable=False, comment="Идентификатор Telegram сотрудника"
    )
    type: Mapped[str] = mapped_column(
        Enum("earn", "spend"),
        nullable=False,
        comment="Тип операции: начисление или списание",
    )
    source_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Идентификатор достижения или предмета. Для manual или casino — None",
    )
    source_type: Mapped[str] = mapped_column(
        Enum("achievement", "achievement_new", "product", "manual", "casino"),
        nullable=False,
        comment="Источник транзакции: achievement, product, casino, manual",
    )
    amount: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Количество баллов"
    )
    comment: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Комментарий к транзакции"
    )
    kpi_extracted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        nullable=True,
        comment="Дата выгрузки показателей. Указывается в случае награды за достижения",
    )
    created_by: Mapped[int | None] = mapped_column(
        BIGINT,
        nullable=True,
        comment="ID администратора, создавшего транзакцию. None если создана автоматически",
    )
    created_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        nullable=True,
        default=func.current_timestamp(),
        comment="Дата создания транзакции",
    )

    def __repr__(self):
        """Возвращает строковое представление объекта Transaction."""
        return f"<Transaction {self.id} {self.user_id} {self.type} {self.source_id} {self.source_type} {self.amount} {self.created_at}>"
