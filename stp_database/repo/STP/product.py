"""Репозиторий функций для взаимодействия с предметами."""

from typing import List

from sqlalchemy import func, or_, select

from stp_database.models.STP import Product
from stp_database.repo.base import BaseRepo


class ProductsRepo(BaseRepo):
    """Репозиторий для работы с предметами."""

    async def get_products(self, division: str = None, only_active: bool = True):
        """Получение полного списка предметов.

        Args:
            division: Фильтр по подразделению (опционально)

        Returns:
            Список предметов
        """
        if division:
            select_stmt = select(Product).where(
                Product.division == division, Product.active == only_active
            )
        else:
            select_stmt = select(Product).where(Product.active == only_active)

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
        self, user_balance: int, division: str, user_role: int = None
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
        # Базовые условия: стоимость и подразделение
        conditions = [
            Product.cost <= user_balance,
            Product.division == division,
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
