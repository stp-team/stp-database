"""Агрегатор репозиториев БД достижений."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from stp_database.repo.Achievements.achievements import AchievementsRepo
from stp_database.repo.Achievements.log_achievements import (
    LogAchievementsRepo,
)


@dataclass
class AchievementsRequestsRepo:
    """Репозитории базы данных достижений."""

    session: AsyncSession

    @property
    def achievements(self) -> AchievementsRepo:
        """Работа со списком достижений."""
        return AchievementsRepo(self.session)

    @property
    def achievement_logs(self) -> LogAchievementsRepo:
        """Работа с логами расчёта достижений."""
        return LogAchievementsRepo(self.session)