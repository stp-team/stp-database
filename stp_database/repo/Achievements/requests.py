"""Агрегатор репозиториев AchievementsRepo."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from stp_database.repo.Achievements import AchievementsRepo
from stp_database.repo.Achievements import LogAchievementsRepo


@dataclass
class AchievementsRequestsRepo:
    """Репозиторий для обработки операций с БД Achievements."""

    session: AsyncSession

    @property
    def space(self) -> AchievementsRepo:
        return AchievementsRepo(self.session)

    @property
    def space(self) -> LogAchievementsRepo:
        return LogAchievementsRepo(self.session)