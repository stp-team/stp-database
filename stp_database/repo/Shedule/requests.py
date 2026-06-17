"""Репозиторий для работы с моделями БД Shedule."""

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from stp_database.repo.Shedule.shifts import ShiftsRepo
from stp_database.repo.Shedule.shifts_high import ShiftsHighRepo
from stp_database.repo.Shedule.shifts_out import ShiftsOutRepo


@dataclass
class SheduleRequestsRepo:
    """Репозиторий для обработки операций с БД. Этот класс содержит все репозитории для моделей базы данных Shedule.

    Ты можешь добавить дополнительные репозитории в качестве свойств к этому классу, чтобы они были легко доступны.
    """

    session: AsyncSession

    @property
    def shifts(self) -> ShiftsRepo:
        """Инициализация репозитория ShiftsRepo с сессией для работы со сменами."""
        return ShiftsRepo(self.session)

    @property
    def highshifts(self) -> ShiftsHighRepo:
        """Инициализация репозитория ShiftsHighRepo с сессией для работы со сменами дежурных."""
        return ShiftsHighRepo(self.session)

    @property
    def outshifts(self) -> ShiftsOutRepo:
        """Инициализация репозитория ShiftsOutRepo с нерабочими сменами."""
        return ShiftsOutRepo(self.session)

    async def sync_shedule_by_period(
        self,
        shifts: Sequence[dict] | None = None,
        highshifts: Sequence[dict] | None = None,
        outshifts: Sequence[dict] | None = None,
        date_start: datetime | None = None,
        date_end: datetime | None = None,
        user_ids: Sequence[int] | None = None,
    ) -> dict[str, dict[str, int]]:
        """Синхронизировать весь график за период по трём таблицам."""

        return {
            "shifts": await self.shifts.sync_shifts_by_period(
                shifts or [],
                date_start=date_start,
                date_end=date_end,
                user_ids=user_ids,
            ),
            "shifts_high": await self.highshifts.sync_highshifts_by_period(
                highshifts or [],
                date_start=date_start,
                date_end=date_end,
                user_ids=user_ids,
            ),
            "shifts_out": await self.outshifts.sync_outshifts_by_period(
                outshifts or [],
                date_start=date_start,
                date_end=date_end,
                user_ids=user_ids,
            ),
        }

    async def sync_schedule_by_period(
        self,
        shifts: Sequence[dict] | None = None,
        highshifts: Sequence[dict] | None = None,
        outshifts: Sequence[dict] | None = None,
        date_start: datetime | None = None,
        date_end: datetime | None = None,
        user_ids: Sequence[int] | None = None,
    ) -> dict[str, dict[str, int]]:
        """Alias для sync_shedule_by_period с правильным английским написанием."""

        return await self.sync_shedule_by_period(
            shifts=shifts,
            highshifts=highshifts,
            outshifts=outshifts,
            date_start=date_start,
            date_end=date_end,
            user_ids=user_ids,
        )
