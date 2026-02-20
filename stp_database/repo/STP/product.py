"""Репозиторий функций для взаимодействия с предметами."""

from typing import List

from sqlalchemy import and_, select

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
            Объект Product или None, если предмет не найден
        """
        select_stmt = select(Product).where(Product.id == product_id)
        result = await self.session.execute(select_stmt)

        return result.scalar_one_or_none()

    async def get_available_products(
        self, user_balance: int, division: str
    ) -> List[Product]:
        """Получение списка доступных предметов для пользователя.

        Возвращает предметы, стоимость которых меньше или равна балансу пользователя.

        Args:
            user_balance: Количество баллов пользователя
            division: Подразделение для фильтрации

        Returns:
            Список доступных предметов
        """
        # Получаем список предметов, подходящих под критерии
        select_stmt = select(Product).where(
            and_(Product.cost <= user_balance), Product.division == division
        )

        result = await self.session.execute(select_stmt)
        products = result.scalars().all()

        return list(products)

    async def create_product(
        self,
        name: str,
        description: str,
        division: str,
        cost: int,
        count: int,
        manager_role: int,
        activate_days: list = None,
        active: bool = True,
    ) -> Product:
        """Создание нового предмета.

        Args:
            name: Название предмета
            description: Описание предмета
            division: Подразделение (НТП/НЦК)
            cost: Стоимость предмета
            count: Количество использований
            manager_role: Роль менеджера для подтверждения
            activate_days: Дни доступности активации
            active: Доступен ли предмет

        Returns:
            Созданный объект Product
        """
        product = Product(
            name=name,
            description=description,
            division=division,
            cost=cost,
            count=count,
            manager_role=manager_role,
            activate_days=activate_days,
            active=active,
        )
        self.session.add(product)
        await self.session.flush()
        await self.session.commit()
        return product

    async def update_product(
        self,
        product_id: int,
        name: str = None,
        description: str = None,
        division: str = None,
        cost: int = None,
        count: int = None,
        manager_role: int = None,
        activate_days: list = None,
        active: bool = None,
    ) -> Product | None:
        """Обновление информации о предмете.

        Args:
            product_id: Уникальный идентификатор предмета
            name: Новое название (опционально)
            description: Новое описание (опционально)
            division: Новое подразделение (опционально)
            cost: Новая стоимость (опционально)
            count: Новое количество использований (опционально)
            manager_role: Новая роль менеджера (опционально)
            activate_days: Новые дни активации (опционально)
            active: Новый статус активности (опционально)

        Returns:
            Обновленный объект Product или None, если предмет не найден
        """
        product = await self.get_product(product_id)
        if not product:
            return None

        if name is not None:
            product.name = name
        if description is not None:
            product.description = description
        if division is not None:
            product.division = division
        if cost is not None:
            product.cost = cost
        if count is not None:
            product.count = count
        if manager_role is not None:
            product.manager_role = manager_role
        if activate_days is not None:
            product.activate_days = activate_days
        if active is not None:
            product.active = active

        await self.session.flush()
        await self.session.commit()
        return product

    async def delete_product(self, product_id: int) -> bool:
        """Удаление предмета.

        Args:
            product_id: Уникальный идентификатор предмета

        Returns:
            True, если предмет был удален, False если не найден
        """
        product = await self.get_product(product_id)
        if not product:
            return False

        await self.session.delete(product)
        await self.session.flush()
        await self.session.commit()
        return True
