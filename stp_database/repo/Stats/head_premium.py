"""Репозиторий функций для работы с премией руководителей."""

import logging
from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from stp_database.models.Stats.head_premium import HeadPremium
from stp_database.repo.base import BaseRepo

logger = logging.getLogger(__name__)


class HeadPremiumRepo(BaseRepo):
    """Репозиторий с функциями для работы с премией руководителей."""

    async def get_premium(
        self, employee_ids: int | list[int], extraction_period: datetime
    ) -> HeadPremium | None | Sequence[HeadPremium]:
        """Поиск показателей премии руководителей в БД по ID сотрудника.

        Args:
            employee_ids: ID сотрудника или список ID сотрудников в БД
            extraction_period: Дата выгрузки премиума

        Returns:
            HeadPremium или ничего (если передано одно число)
            Список объектов HeadPremium (если передан список)
        """
        # Определяем, одиночный запрос или множественный
        is_single = isinstance(employee_ids, int)

        if is_single:
            query = select(HeadPremium).where(
                HeadPremium.employee_id == employee_ids,
                HeadPremium.extraction_period == extraction_period,
            )
        else:
            if not employee_ids:
                return []
            query = select(HeadPremium).where(
                HeadPremium.employee_id.in_(employee_ids),
                HeadPremium.extraction_period == extraction_period,
            )

        try:
            result = await self.session.execute(query)
            if is_single:
                return result.scalar_one_or_none()
            else:
                return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(
                f"[БД] Ошибка получения показателей премиума руководителя(-ей): {e}"
            )
            raise
            #return None if is_single else []

    async def update_premium(
        self,
        extraction_period: datetime,
        employee_id: int,
        **kwargs: Any,
    ) -> HeadPremium | None:
        """Обновление премиума.

        Args:
            employee_id: ID сотрудника
            extraction_period: Дата выгрузки премиума
            **kwargs: Параметры для обновления

        Returns:
            Обновленный объект HeadPremium или None
        """
        select_stmt = select(HeadPremium).where(
            HeadPremium.employee_id == employee_id,
            HeadPremium.extraction_period == extraction_period,
        )

        result = await self.session.execute(select_stmt)
        premium: HeadPremium | None = result.scalar_one_or_none()

        # Если строка существует - обновляем ее
        if premium:
            for key, value in kwargs.items():
                setattr(premium, key, value)
            await self.session.commit()

        return premium
