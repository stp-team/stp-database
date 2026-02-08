"""Модели, связанные с сущностями предметов."""

from sqlalchemy import JSON, Boolean, Integer
from sqlalchemy.dialects.mysql import VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from stp_database.models.base import Base


class Product(Base):
    """Класс, представляющий сущность предмета в БД.

    Args:
        id: Уникальный идентификатор предмета
        name: Название предмета
        description: Описание предмета
        division: Направление (НТП/НЦК) доступности приобретения предмета
        cost: Стоимость предмета в магазине
        count: Кол-во использований предмета
        activate_days: Дни доступности активации предмета
        manager_role: Роль для подтверждения активации предмета

    Methods:
        __repr__(): Возвращает строковое представление объекта Product.
    """

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Уникальный идентификатор предмета",
    )
    name: Mapped[str] = mapped_column(
        VARCHAR(255), nullable=False, comment="Название предмета"
    )
    description: Mapped[str] = mapped_column(
        VARCHAR(255), nullable=False, comment="Описание предмета"
    )
    division: Mapped[str] = mapped_column(
        VARCHAR(3),
        nullable=False,
        comment="Направление (НТП/НЦК) доступности приобретения предмета",
    )
    cost: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Стоимость предмета в магазине"
    )
    count: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Кол-во использований предмета"
    )
    activate_days: Mapped[list] = mapped_column(
        JSON, nullable=True, comment="Дни доступности активации предмета"
    )
    manager_role: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Роль для подтверждения активации предмета"
    )
    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="Доступен ли предмет пользователям",
        default=1,
    )

    def __repr__(self):
        """Возвращает строковое представление объекта Product."""
        return f"<Product {self.id} {self.name} {self.description} {self.division} {self.cost} {self.count} {self.manager_role}>"
