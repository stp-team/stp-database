"""Репозиторий для работы с моделями БД Shedule."""

from dataclasses import dataclass

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
