"""Репозиторий функций для взаимодействия с покупками."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, List

from sqlalchemy import desc, func, select
from sqlalchemy.exc import SQLAlchemyError

from stp_database.models.STP import Employee, Product
from stp_database.models.STP.purchase import Purchase
from stp_database.repo.base import BaseRepo

logger = logging.getLogger(__name__)


@dataclass
class PurchaseDetailedParams:
    """Класс с детальными данными о покупке."""

    user_purchase: Purchase
    product_info: Product

    @property
    def max_usages(self) -> int:
        """Возвращает кол-во максимальных использований предмета."""
        return self.product_info.count

    @property
    def current_usages(self) -> int:
        """Возвращает кол-во текущих использований предмета."""
        return self.user_purchase.usage_count


class PurchaseRepo(BaseRepo):
    """Репозиторий для работы с покупками."""

    async def add_purchase(
        self, user_id: int, product_id: int, status: str = "stored"
    ) -> Purchase:
        """Создание новой покупки для пользователя.

        Args:
            user_id: ID пользователя Telegram
            product_id: ID предмета из таблицы products
            status: Статус покупки (по умолчанию "stored")

        Returns:
            Созданная покупка пользователя
        """
        from datetime import datetime

        user_purchase = Purchase(
            user_id=user_id,
            product_id=product_id,
            usage_count=0,
            bought_at=datetime.now(),
            status=status,
        )

        self.session.add(user_purchase)
        await self.session.commit()
        await self.session.refresh(user_purchase)

        return user_purchase

    async def get_purchases(
        self,
        user_id: int | None = None,
        manager_role: int | None = None,
        division: str | list[str] | None = None,
        status: str | None = None,
        updated_by_user_id: int | None = None,
        updated_by_user_id__isnull: bool | None = None,
        order_by: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> List[Purchase]:
        """Получение списка покупок с фильтрацией.

        Args:
            user_id: ID пользователя-покупателя
            manager_role: Роль менеджера для фильтрации
            division: Подразделение(я) для фильтрации
            status: Статус покупки ('pending', 'approved', 'rejected')
            updated_by_user_id: ID пользователя, который обновил запись
            updated_by_user_id__isnull: Фильтр по наличию/отсутствию updated_by_user_id
                - True: только где updated_by_user_id IS NULL
                - False: только где updated_by_user_id IS NOT NULL
            order_by: Поле для сортировки (например, "-updated_at", "bought_at")
            limit: Максимальное количество записей
            offset: Смещение для пагинации

        Returns:
            Список объектов UserPurchase
        """
        query = select(Purchase)

        # Джойн с Employee для фильтрации по division и manager_role
        if manager_role is not None or division is not None:
            query = query.join(Employee, Purchase.user_id == Employee.id)

        # Фильтрация по пользователю
        if user_id is not None:
            query = query.filter(Purchase.user_id == user_id)

        # Фильтрация по роли менеджера
        if manager_role is not None:
            query = query.filter(Employee.role == manager_role)

        # Фильтрация по подразделению
        if division is not None:
            if isinstance(division, list):
                query = query.filter(Employee.division.in_(division))
            else:
                query = query.filter(Employee.division == division)

        # Фильтрация по статусу
        if status is not None:
            query = query.filter(Purchase.status == status)

        # Фильтрация по updated_by_user_id
        if updated_by_user_id is not None:
            query = query.filter(Purchase.updated_by_user_id == updated_by_user_id)

        # Фильтрация по наличию/отсутствию updated_by_user_id
        if updated_by_user_id__isnull is not None:
            if updated_by_user_id__isnull:
                query = query.filter(Purchase.updated_by_user_id.is_(None))
            else:
                query = query.filter(Purchase.updated_by_user_id.is_not(None))

        # Сортировка
        if order_by is not None:
            if order_by.startswith("-"):
                # Сортировка по убыванию
                field_name = order_by[1:]
                if hasattr(Purchase, field_name):
                    query = query.order_by(desc(getattr(Purchase, field_name)))
            else:
                # Сортировка по возрастанию
                if hasattr(Purchase, order_by):
                    query = query.order_by(getattr(Purchase, order_by))

        # Пагинация
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_user_purchases(self, user_id: int) -> list[Purchase]:
        """Получение полного списка покупок пользователя.

        Args:
            user_id: ID пользователя Telegram

        Returns:
            Список покупок пользователя
        """
        select_stmt = select(Purchase).where(Purchase.user_id == user_id)
        result = await self.session.execute(select_stmt)
        purchases = result.scalars().all()
        return list(purchases)

    async def get_user_purchases_with_details(
        self, user_id: int
    ) -> list[PurchaseDetailedParams]:
        """Получение полного списка покупок пользователя с детальной информацией.

        Args:
            user_id: ID пользователя Telegram

        Returns:
            Список покупок с информацией о предметах
        """
        select_stmt = (
            select(Purchase, Product)
            .join(Product, Purchase.product_id == Product.id)
            .where(Purchase.user_id == user_id)
            .order_by(Purchase.bought_at.desc())
        )

        result = await self.session.execute(select_stmt)
        purchases_with_details = result.all()

        return [
            PurchaseDetailedParams(user_purchase=purchase, product_info=product)
            for purchase, product in purchases_with_details
        ]

    async def get_purchase_details(
        self, user_purchase_id: int
    ) -> PurchaseDetailedParams | None:
        """Получение детальной информации о конкретной покупке пользователя.

        Args:
            user_purchase_id: ID покупки в таблице purchases

        Returns:
            Детальная информация о покупке или None если не найдена
        """
        select_stmt = (
            select(Purchase, Product)
            .join(Product, Purchase.product_id == Product.id)
            .where(Purchase.id == user_purchase_id)
        )

        result = await self.session.execute(select_stmt)
        purchase_details = result.first()

        if not purchase_details:
            return None

        purchase, product = purchase_details
        return PurchaseDetailedParams(user_purchase=purchase, product_info=product)

    async def get_user_purchases_sum(self, user_id: int) -> int:
        """Получение суммы стоимости покупок пользователя.

        Args:
            user_id: ID пользователя Telegram

        Returns:
            Общая сумма стоимости всех покупок
        """
        select_stmt = (
            select(func.sum(Product.cost))
            .select_from(Purchase)
            .join(Product, Product.id == Purchase.product_id)
            .where(Purchase.user_id == user_id)
        )

        result = await self.session.execute(select_stmt)
        total = result.scalar()

        return total or 0  # Если покупка не найдена - возвращаем 0

    async def get_review_purchases_for_activation(
        self, manager_role: int, division: str | list[str] = None
    ) -> list[PurchaseDetailedParams]:
        """Получение списка покупок, ожидающих активации.

        Фильтрует по статусу "review" и роли менеджера.
        Опционально фильтрует по подразделению пользователей.

        Args:
            manager_role: Роль менеджера для фильтрации
            division: Подразделение для фильтрации (может быть строкой или списком строк)

        Returns:
            Список покупок с детальной информацией
        """
        select_stmt = (
            select(Purchase, Product, Employee)
            .join(Product, Purchase.product_id == Product.id)
            .join(Employee, Purchase.user_id == Employee.id)
            .where(Purchase.status == "review", Product.manager_role == manager_role)
        )

        # Добавляем фильтр по division если указан
        if division:
            if isinstance(division, list):
                select_stmt = select_stmt.where(Employee.division.in_(division))
            else:
                select_stmt = select_stmt.where(Employee.division == division)

        select_stmt = select_stmt.order_by(
            Purchase.bought_at.asc()
        )  # Сортируем по дате покупки (сначала старые)

        result = await self.session.execute(select_stmt)
        purchases_with_details = result.all()

        return [
            PurchaseDetailedParams(user_purchase=purchase, product_info=product)
            for purchase, product, user in purchases_with_details
        ]

    async def update_purchase(
        self,
        purchase_id: int = None,
        **kwargs: Any,
    ) -> Purchase | None:
        """Обновление информации о покупке.

        Args:
            purchase_id: ID покупки в таблице purchases
            **kwargs: Параметры для обновления

        Returns:
            Обновленный объект Purchase или None
        """
        select_stmt = select(Purchase).where(Purchase.id == purchase_id)

        result = await self.session.execute(select_stmt)
        purchase: Purchase | None = result.scalar_one_or_none()

        # Если покупка существует - обновляем её
        if purchase:
            for key, value in kwargs.items():
                setattr(purchase, key, value)
            await self.session.commit()

        return purchase

    async def use_purchase(self, purchase_id: int) -> bool:
        """Использование покупки пользователем.

        Изменяет статус покупки с 'stored' на 'review'.

        Args:
            purchase_id: ID покупки в таблице purchases

        Returns:
            True если успешно, False если недоступно для использования
        """
        select_stmt = select(Purchase).where(Purchase.id == purchase_id)
        result = await self.session.execute(select_stmt)
        purchase = result.scalar_one_or_none()

        if not purchase or purchase.status != "stored":
            return False

        # Get product info to check usage limits
        product_info = await self.session.get(Product, purchase.product_id)
        if purchase.usage_count >= product_info.count:
            return False

        purchase.status = "review"
        purchase.updated_at = datetime.now()

        await self.session.commit()
        return True

    async def approve_purchase_usage(
        self, purchase_id: int, updated_by_user_id: int
    ) -> bool:
        """Одобрение использования покупки менеджером.

        Увеличивает счетчик использований и устанавливает статус 'stored' или 'used_up'.

        Args:
            purchase_id: ID покупки в таблице purchases
            updated_by_user_id: ID пользователя, который одобрил

        Returns:
            True если успешно, False если покупка не найдена
        """
        # Get the user purchase first
        purchase = await self.session.get(Purchase, purchase_id)
        if not purchase:
            return False

        # Get the product info
        product_info = await self.session.get(Product, purchase.product_id)
        if not product_info:
            return False

        # Increment usage count
        purchase.usage_count += 1
        purchase.updated_at = datetime.now()
        purchase.updated_by_user_id = updated_by_user_id

        # Set status based on remaining uses
        if purchase.usage_count >= product_info.count:
            purchase.status = "used_up"
        else:
            purchase.status = "stored"

        await self.session.commit()
        return True

    async def reject_purchase_usage(
        self, purchase_id: int, updated_by_user_id: int
    ) -> bool:
        """Отклонение использования покупки.

        Возвращает статус покупки на 'stored' или 'used_up'.

        Args:
            purchase_id: ID покупки в таблице purchases
            updated_by_user_id: ID пользователя, который отклонил

        Returns:
            True если успешно, False если покупка не найдена
        """
        # Get the user purchase first
        purchase = await self.session.get(Purchase, purchase_id)
        if not purchase:
            return False

        # Get the product info
        product_info = await self.session.get(Product, purchase.product_id)
        if not product_info:
            return False

        purchase.updated_at = datetime.now()
        purchase.updated_by_user_id = updated_by_user_id

        # Set status based on remaining uses
        if purchase.usage_count >= product_info.count:
            purchase.status = "used_up"
        else:
            purchase.status = "stored"

        await self.session.commit()
        return True

    async def delete_user_purchase(self, purchase_id: int) -> bool:
        """Удаление записи о покупке пользователя из БД.

        Используется для возврата покупки.

        Args:
            purchase_id: ID записи в таблице purchases

        Returns:
            True если успешно, False если покупка не найдена
        """
        select_stmt = select(Purchase).where(Purchase.id == purchase_id)
        result = await self.session.execute(select_stmt)
        purchase = result.scalar_one_or_none()

        if not purchase:
            return False

        # Проверяем, что покупку можно удалить (только со статусом "stored" и usage_count = 0)
        if purchase.status != "stored" or purchase.usage_count > 0:
            return False

        await self.session.delete(purchase)
        await self.session.commit()

        return True

    async def get_most_bought_product(self, user_id: int) -> tuple[str, int] | None:
        """Получение самого используемого предмета пользователя.

        Args:
            user_id: ID пользователя Telegram

        Returns:
            Кортеж (название предмета, количество использований) или None если нет покупок
        """
        select_stmt = (
            select(Product.name, Purchase.usage_count)
            .select_from(Purchase)
            .join(Product, Purchase.product_id == Product.id)
            .where(Purchase.user_id == user_id)
            .order_by(Purchase.usage_count.desc())
            .limit(1)
        )

        result = await self.session.execute(select_stmt)
        most_used = result.first()

        if not most_used:
            return None

        return most_used.name, most_used.usage_count

    async def get_group_purchases_stats(self, head_name: str) -> dict:
        """Получение статистики покупок для группы руководителя.

        Args:
            head_name: Имя руководителя

        Returns:
            Словарь со статистикой покупок группы
        """
        try:
            # Получаем все покупки сотрудников группы
            query = (
                select(
                    Product.name,
                    func.sum(Purchase.usage_count).label("total_usage"),
                    func.count(Purchase.product_id).label("purchase_count"),
                )
                .select_from(Employee)
                .join(Purchase, Employee.id == Purchase.user_id)
                .join(Product, Purchase.product_id == Product.id)
                .where(Employee.head == head_name)
                .group_by(Product.name)
                .order_by(func.sum(Purchase.usage_count).desc())
            )

            result = await self.session.execute(query)
            purchases_stats = result.all()

            total_usage = sum(stat.total_usage for stat in purchases_stats)
            total_purchases = sum(stat.purchase_count for stat in purchases_stats)
            most_popular = purchases_stats[0] if purchases_stats else None

            return {
                "total_usage": total_usage,
                "total_purchases": total_purchases,
                "most_popular": most_popular,
                "details": purchases_stats,
            }

        except SQLAlchemyError as e:
            logger.error(
                f"[БД] Ошибка получения статистики покупок для группы {head_name}: {e}"
            )
            return {
                "total_usage": 0,
                "total_purchases": 0,
                "most_popular": None,
                "details": [],
            }
