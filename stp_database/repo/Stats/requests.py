"""Репозиторий для работы с моделями БД Stats."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from stp_database.models.Stats.spec_kpi import SpecDayKPI, SpecMonthKPI, SpecWeekKPI
from .questioner import (
    QuestionerMonthRepo,
    QuestionerChatsRepo,
)
from stp_database.repo.Stats.head_premium import HeadPremiumRepo
from stp_database.repo.Stats.spec_kpi import SpecKPIRepo
from stp_database.repo.Stats.spec_premium import SpecPremiumRepo


@dataclass
class StatsRequestsRepo:
    """Репозиторий для обработки операций с БД. Этот класс содержит все репозитории для моделей базы данных Stats.

    Ты можешь добавить дополнительные репозитории в качестве свойств к этому классу, чтобы они были легко доступны.
    """

    session: AsyncSession

    @property
    def head_premium(self) -> HeadPremiumRepo:
        """Инициализация репозитория HeadPremiumRepo с сессией для работы с премией руководителей."""
        return HeadPremiumRepo(self.session)

    @property
    def questioner_month(self) -> QuestionerMonthRepo:
        """Инициализация репозитория QuestionerMonth с сессией для работы с ежемесячной статистикой вопросника."""
        return QuestionerMonthRepo(self.session)

    @property
    def questioner_chats(self) -> QuestionerChatsRepo:
        """Инициализация репозитория QuestionerChats с сессией для работы с ежедневной статистикой вопросника."""
        return QuestionerChatsRepo(self.session)

    @property
    def spec_premium(self) -> SpecPremiumRepo:
        """Инициализация репозитория SpecPremiumRepo с сессией для работы с премией специалистов."""
        return SpecPremiumRepo(self.session)

    @property
    def spec_day_kpi(self) -> SpecKPIRepo:
        """Инициализация репозитория SpecKPIRepo с сессией для работы с дневными показателями специалистов."""
        return SpecKPIRepo(self.session, SpecDayKPI)

    @property
    def spec_week_kpi(self) -> SpecKPIRepo:
        """Инициализация репозитория SpecKPIRepo с сессией для работы с недельными показателями специалистов."""
        return SpecKPIRepo(self.session, SpecWeekKPI)

    @property
    def spec_month_kpi(self) -> SpecKPIRepo:
        """Инициализация репозитория SpecKPIRepo с сессией для работы с месячными показателями специалистов."""
        return SpecKPIRepo(self.session, SpecMonthKPI)
