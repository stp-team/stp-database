"""Репозиторий для работы с транзакциями."""

import datetime
import logging
from typing import Sequence, TypedDict, Unpack

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from stp_database.models.STP.transactions import Transaction
from stp_database.repo.base import BaseRepo

logger = logging.getLogger(__name__)


class TransactionParams(TypedDict, total=False):
    """Доступные параметры для обновления транзакции."""

    user_id: int
    type: str
    source_id: int | None
    source_type: str
    amount: int
    comment: str | None
    created_by: int | None
    kpi_extracted_at: datetime.datetime | None


class TransactionRepo(BaseRepo):
    """Репозиторий для работы с транзакциями."""

    async def add_transaction(
        self,
        user_id: int,
        transaction_type: str,
        source_type: str,
        amount: int,
        source_id: int | None = None,
        comment: str | None = None,
        created_by: int | None = None,
        kpi_extracted_at: datetime.datetime | None = None,
    ) -> tuple[Transaction, int] | None:
        """Добавление новой транзакции в БД.

        Args:
            user_id: Идентификатор пользователя
            transaction_type: Тип операции: 'earn' или 'spend'
            source_type: Источник транзакции: 'achievement', 'product', 'casino', 'manual'
            amount: Количество баллов
            source_id: Идентификатор достижения или предмета (опционально)
            comment: Комментарий (опционально)
            created_by: ID администратора, создавшего транзакцию (опционально)
            kpi_extracted_at: Дата выгрузки Stats

        Returns:
            Кортеж (объект Transaction, новый баланс) или None в случае ошибки
        """
        try:
            transaction = Transaction(
                user_id=user_id,
                type=transaction_type,
                source_type=source_type,
                amount=amount,
                source_id=source_id,
                comment=comment,
                created_by=created_by,
                kpi_extracted_at=kpi_extracted_at,
            )

            self.session.add(transaction)
            await self.session.commit()
            await self.session.refresh(transaction)

            logger.info(
                f"[БД] Создана транзакция ID: {transaction.id} для пользователя {user_id}"
            )

            new_balance = await self.get_user_balance(transaction.user_id)
            return transaction, new_balance

        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка создания транзакции: {e}")
            await self.session.rollback()
            return None

    async def get_transaction(self, transaction_id: int) -> Transaction | None:
        """Получение транзакции по ID.

        Args:
            transaction_id: Уникальный идентификатор транзакции

        Returns:
            Объект Transaction или None
        """
        try:
            result = await self.session.execute(
                select(Transaction).where(Transaction.id == transaction_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка получения транзакции {transaction_id}: {e}")
            return None

    async def get_user_transactions(
        self, user_id: int, only_achievements: bool = False
    ) -> Sequence[Transaction]:
        """Получение всех транзакций пользователя.

        Args:
            user_id: Идентификатор пользователя
            only_achievements: Если True, возвращать только транзакции-достижения

        Returns:
            Список транзакций пользователя
        """
        try:
            query = select(Transaction).where(Transaction.user_id == user_id)

            if only_achievements:
                query = query.where(Transaction.source_type.in_(["achievement", "achievement_new"]))

            query = query.order_by(Transaction.created_at.desc())
            result = await self.session.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(
                f"[БД] Ошибка получения транзакций пользователя {user_id}: {e}"
            )
            return []

    async def get_transactions(self) -> Sequence[Transaction]:
        """Получение всех транзакций.

        Returns:
            Список всех транзакций
        """
        try:
            result = await self.session.execute(
                select(Transaction).order_by(Transaction.created_at.desc())
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка получения списка транзакций: {e}")
            return []

    async def update_transaction(
        self,
        transaction_id: int,
        **kwargs: Unpack[TransactionParams],
    ) -> Transaction | None:
        """Обновление транзакции.

        Args:
            transaction_id: ID транзакции для обновления
            **kwargs: Параметры для обновления

        Returns:
            Обновленная транзакция или None
        """
        try:
            select_stmt = select(Transaction).where(Transaction.id == transaction_id)
            result = await self.session.execute(select_stmt)
            transaction: Transaction | None = result.scalar_one_or_none()

            if transaction:
                for key, value in kwargs.items():
                    setattr(transaction, key, value)
                await self.session.commit()
                logger.info(f"[БД] Транзакция {transaction_id} обновлена")

            return transaction
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка обновления транзакции {transaction_id}: {e}")
            await self.session.rollback()
            return None

    async def delete_transaction(self, transaction_id: int) -> bool:
        """Удаление транзакции из БД.

        Args:
            transaction_id: ID транзакции для удаления

        Returns:
            True если транзакция удалена, False в случае ошибки
        """
        try:
            result = await self.session.execute(
                select(Transaction).where(Transaction.id == transaction_id)
            )
            transaction = result.scalar_one_or_none()

            if transaction:
                await self.session.delete(transaction)
                await self.session.commit()
                logger.info(f"[БД] Транзакция {transaction_id} удалена")
                return True
            else:
                logger.warning(f"[БД] Транзакция {transaction_id} не найдена")
                return False

        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка удаления транзакции {transaction_id}: {e}")
            await self.session.rollback()
            return False

    async def get_user_balance(self, user_id: int) -> int:
        """Вычисление баланса пользователя.

        Баланс рассчитывается как сумма всех транзакций.

        Args:
            user_id: Идентификатор пользователя

        Returns:
            Баланс пользователя
        """
        try:
            transactions = await self.get_user_transactions(user_id)
            balance = 0

            for transaction in transactions:
                if transaction.type == "earn":
                    balance += transaction.amount
                elif transaction.type == "spend":
                    balance -= transaction.amount

            return balance
        except Exception as e:
            logger.error(f"[БД] Ошибка вычисления баланса пользователя {user_id}: {e}")
            return 0

    async def get_user_achievements_sum(self, user_id: int) -> int:
        """Вычисление суммы баллов за достижения пользователя.

        Включает достижения и ручные транзакции.

        Args:
            user_id: Идентификатор пользователя

        Returns:
            Сумма баллов за достижения и ручные транзакции
        """
        try:
            query = select(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.source_type.in_(["achievement", "achievement_new", "manual"]),
                Transaction.type == "earn",
            )
            result = await self.session.execute(query)
            transactions = result.scalars().all()

            achievements_sum = sum(transaction.amount for transaction in transactions)
            return achievements_sum
        except Exception as e:
            logger.error(
                f"[БД] Ошибка вычисления суммы достижений пользователя {user_id}: {e}"
            )
            return 0

    async def get_group_transactions(self, head_name: str) -> Sequence[Transaction]:
        """Получение всех транзакций группы по имени руководителя.

        Args:
            head_name: ФИО руководителя

        Returns:
            Список транзакций всех участников группы
        """
        try:
            from stp_database.models import Employee

            # Получаем всех участников группы
            group_members = await self.session.execute(
                select(Employee).where(Employee.head == head_name)
            )
            members = group_members.scalars().all()

            if not members:
                return []

            # Получаем user_id всех участников группы
            member_user_ids = [member.user_id for member in members if member.user_id]

            if not member_user_ids:
                return []

            # Получаем все транзакции участников группы
            query = select(Transaction).where(Transaction.user_id.in_(member_user_ids))
            query = query.order_by(Transaction.created_at.desc())
            result = await self.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(
                f"[БД] Ошибка получения транзакций группы для {head_name}: {e}"
            )
            return []

    async def get_heads_ranking_by_division(self, division: str) -> list[dict]:
        """Получение рейтинга руководителей по дивизиону.

        Рейтинг основан на очках группы за текущий месяц с 1-го числа.

        Args:
            division: Название дивизиона

        Returns:
            Список словарей с информацией о руководителях и их местах
        """
        try:
            from datetime import date, datetime

            from sqlalchemy import and_, func

            from stp_database.models import Employee

            # Получаем начало текущего месяца (1-е число)
            current_date = datetime.now()
            month_start = date(current_date.year, current_date.month, 1)

            # Получаем всех руководителей указанного дивизиона
            heads_query = select(Employee).where(
                and_(
                    Employee.division == division,
                    Employee.role == 2,  # Роль руководителя
                )
            )
            heads_result = await self.session.execute(heads_query)
            heads = heads_result.scalars().all()

            if not heads:
                return []

            ranking = []

            for head in heads:
                # Получаем участников группы этого руководителя
                group_members = await self.session.execute(
                    select(Employee).where(Employee.head == head.fullname)
                )
                members = group_members.scalars().all()
                member_user_ids = [
                    member.user_id for member in members if member.user_id
                ]

                # Подсчитываем очки группы за текущий месяц с 1-го числа
                if member_user_ids:
                    points_query = select(func.sum(Transaction.amount)).where(
                        Transaction.user_id.in_(member_user_ids),
                        Transaction.type == "earn",
                        func.date(Transaction.created_at) >= month_start,
                    )
                    points_result = await self.session.execute(points_query)
                    points = points_result.scalar() or 0
                else:
                    points = 0

                ranking.append({
                    "head_name": head.fullname,
                    "username": head.username,
                    "points": points,
                    "group_size": len(members),
                })

            # Сортируем по убыванию очков
            ranking.sort(key=lambda x: x["points"], reverse=True)

            # Добавляем места
            for i, head_data in enumerate(ranking, 1):
                head_data["place"] = i

            return ranking

        except Exception as e:
            logger.error(
                f"[БД] Ошибка получения рейтинга руководителей для дивизиона {division}: {e}"
            )
            return []

    async def get_group_all_time_top_3(self, head_name: str) -> list[dict]:
        """Получение ТОП-3 участников группы по всем баллам за все время.

        Args:
            head_name: ФИО руководителя

        Returns:
            Список словарей с информацией о топ-3 участниках группы за все время
        """
        try:
            from sqlalchemy import func

            from stp_database.models import Employee

            # Получаем всех участников группы
            group_members = await self.session.execute(
                select(Employee).where(Employee.head == head_name)
            )
            members = group_members.scalars().all()

            if not members:
                return []

            # Получаем user_id всех участников группы
            member_user_ids = [member.user_id for member in members if member.user_id]

            if not member_user_ids:
                return []

            # Запрос для получения суммы очков каждого участника за все время
            all_time_stats_query = (
                select(
                    Transaction.user_id,
                    func.sum(Transaction.amount).label("all_time_points"),
                )
                .where(
                    Transaction.user_id.in_(member_user_ids), Transaction.type == "earn"
                )
                .group_by(Transaction.user_id)
            )

            all_time_stats_result = await self.session.execute(all_time_stats_query)
            all_time_stats = all_time_stats_result.all()

            # Сортируем по убыванию и берем ТОП-3
            top_3_all_time = sorted(
                all_time_stats, key=lambda x: x.all_time_points, reverse=True
            )[:3]

            # Формируем список ТОП-3 с именами
            top_3_list = []
            for user_stats in top_3_all_time:
                member = next(
                    (m for m in members if m.user_id == user_stats.user_id), None
                )
                if member:
                    top_3_list.append({
                        "name": member.fullname,
                        "username": member.username,
                        "points": user_stats.all_time_points,
                    })

            return top_3_list

        except Exception as e:
            logger.error(
                f"[БД] Ошибка получения ТОП-3 за все время для группы {head_name}: {e}"
            )
            return []
