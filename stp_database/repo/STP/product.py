"""Репозиторий функций для взаимодействия с предметами."""

from typing import List

from sqlalchemy import func, or_, select

from stp_database.models.STP import Product
from stp_database.repo.base import BaseRepo


class ProductsRepo(BaseRepo):
    """Репозиторий для работы с предметами."""

    @staticmethod
    def _normalize_division(division: str | None) -> str | None:
        """Нормализация подразделения.

        Если подразделение начинается с 'НТП', возвращает 'НТП'.

        Args:
            division: Подразделение для нормализации

        Returns:
            Нормализованное подразделение
        """
        if division and division.startswith("НТП"):
            return "НТП"
        return division

    async def get_products(
        self,
        division: str | None = None,
        role: int | None = None,
        only_active: bool = True,
    ):
        """Получение полного списка предметов.

        Args:
            division: Фильтр по подразделению (опционально)
            role: ID роли для фильтрации по buyer_roles (опционально)
            only_active: Фильтр только активных предметов

        Returns:
            Список предметов
        """
        conditions = [Product.active == only_active]

        # Нормализуем подразделение (НТП1, НТП2 -> НТП)
        normalized_division = self._normalize_division(division)

        if normalized_division:
            conditions.append(Product.division == normalized_division)

        # Если указана роль, добавляем фильтрацию по buyer_roles
        if role is not None:
            conditions.append(
                or_(
                    Product.buyer_roles.is_(None),
                    Product.buyer_roles == [],
                    func.json_contains(Product.buyer_roles, role),
                )
            )

        select_stmt = select(Product).where(*conditions)
        result = await self.session.execute(select_stmt)
        products = result.scalars().all()

        return list(products)

    async def get_product(self, product_id: int) -> Product | None:
        """Получение информации о предмете по его идентификатору.

        Args:
            product_id: Уникальный идентификатор предмета в таблице products

        Returns:
            Объект Product
        """
        select_stmt = select(Product).where(Product.id == product_id)
        result = await self.session.execute(select_stmt)

        return result.scalar_one()

    async def get_available_products(
        self, user_balance: int, division: str, user_role: int | None = None
    ) -> List[Product]:
        """Получение списка доступных предметов для пользователя.

        Возвращает предметы, стоимость которых меньше или равна балансу пользователя,
        и которые доступны для роли пользователя.

        Args:
            user_balance: Количество баллов пользователя
            division: Подразделение для фильтрации
            user_role: ID роли пользователя для фильтрации по buyer_roles

        Returns:
            Список доступных предметов
        """
        # Нормализуем подразделение (НТП1, НТП2 -> НТП)
        normalized_division = self._normalize_division(division)

        # Базовые условия: стоимость и подразделение
        conditions = [
            Product.cost <= user_balance,
            Product.division == normalized_division,
        ]

        # Если указана роль пользователя, добавляем фильтрацию по buyer_roles
        if user_role is not None:
            # Товар доступен, если buyer_roles пустой/None ИЛИ содержит роль пользователя
            conditions.append(
                or_(
                    Product.buyer_roles.is_(None),
                    Product.buyer_roles == [],
                    func.json_contains(Product.buyer_roles, user_role),
                )
            )

        select_stmt = select(Product).where(*conditions)

        result = await self.session.execute(select_stmt)
        products = result.scalars().all()

        return list(products)
