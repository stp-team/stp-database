"""Репозиторий для работы с Stats специалистов."""

import logging
from typing import Generic, Sequence, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from stp_database.models.Stats.spec_kpi import SpecKPI
from stp_database.repo.base import BaseRepo

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=SpecKPI)


class SpecKPIRepo(BaseRepo, Generic[T]):
    """Универсальный репозиторий для работы с Stats специалистов.

    Работает с любой таблицей Stats (KpiDay, KpiWeek, KpiMonth) через один интерфейс.

    Attributes:
        model: Класс модели Stats (SpecDayKPI, SpecWeekKPI или SpecMonthKPI)
    """

    def __init__(self, session, model: Type[T]):
        """Инициализация репозитория.

        Args:
            session: Сессия SQLAlchemy
            model: Класс модели Stats (SpecDayKPI/SpecWeekKPI/SpecMonthKPI)
        """
        super().__init__(session)
        self.model = model

    async def get_kpi(self, employee_ids: int | list[int]) -> T | None | Sequence[T]:
        """Поиск показателей специалистов в БД по ID сотрудника.

        Args:
            employee_ids: ID сотрудника или список ID сотрудников в БД

        Returns:
            Показатели Stats специалиста или None (если передано одно число)
            Последовательность объектов SpecKPI (если передан список)
        """
        # Определяем, одиночный запрос или множественный
        is_single = isinstance(employee_ids, int)

        if is_single:
            query = select(self.model).where(self.model.employee_id == employee_ids)
        else:
            if not employee_ids:
                return []
            query = select(self.model).where(self.model.employee_id.in_(employee_ids))

        try:
            result = await self.session.execute(query)
            if is_single:
                return result.scalar_one_or_none()
            else:
                return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(
                f"[БД] Ошибка получения показателей специалиста(-ов) из {self.model.__tablename__}: {e}"
            )
            raise
            #return None if is_single else []
