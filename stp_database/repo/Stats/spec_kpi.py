"""Репозиторий для работы с Stats специалистов."""

import logging
from datetime import datetime
from typing import Generic, Sequence, Type, TypeVar

from sqlalchemy import func, select
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

    async def get_kpi_for_period(
            self,
            employee_id: int,
            extraction_period: datetime,
    ) -> T | None:
        stmt = select(self.model).where(
            self.model.employee_id == employee_id,
            self.model.extraction_period == extraction_period,
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

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

    async def get_selected_kpi(
            self,
            employee_ids: list[int],
            columns: list[str],
    ) -> tuple[datetime | None, list[dict[str, object]]]:
        """
        Получить выбранные показатели последнего доступного месяца.

        Args:
            employee_ids: employee_id сотрудников из таблицы employees.
            columns: Разрешённые названия показателей KpiMonth.

        Returns:
            Дата выгрузки и строки с выбранными показателями.
        """
        if not employee_ids:
            return None, []

        requested_columns = list(dict.fromkeys(columns))

        available_columns = {
            column.name
            for column in self.model.__table__.columns
        }

        invalid_columns = set(requested_columns) - available_columns

        if invalid_columns:
            raise ValueError(
                "Неизвестные колонки KPI: "
                + ", ".join(sorted(invalid_columns))
            )

        try:
            # Находим последний общий доступный период среди сотрудников группы.
            period_query = (
                select(func.max(self.model.extraction_period))
                .where(self.model.employee_id.in_(employee_ids))
            )

            period_result = await self.session.execute(period_query)
            extraction_period = period_result.scalar_one_or_none()

            if extraction_period is None:
                return None, []

            selected_columns = [
                self.model.employee_id,
                self.model.extraction_period,
                *[
                    getattr(self.model, column_name)
                    for column_name in requested_columns
                ],
            ]

            query = (
                select(*selected_columns)
                .where(
                    self.model.employee_id.in_(employee_ids),
                    self.model.extraction_period == extraction_period,
                )
                .order_by(self.model.employee_id)
            )

            result = await self.session.execute(query)

            rows = [
                dict(row)
                for row in result.mappings().all()
            ]

            return extraction_period, rows

        except SQLAlchemyError as error:
            logger.error(
                "[БД] Ошибка получения выбранных KPI "
                f"из {self.model.__tablename__}: {error}"
            )
            raise
