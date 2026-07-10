"""Агрегатор репозиториев AchievementsRepo."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from stp_database.repo.Achievements import AchievementsRepo


@dataclass
class AchievementsRequestsRepo:
    """Репозиторий для обработки операций с БД Achievements."""

    session: AsyncSession

    @property
    def space(self) -> AchievementsRepo:
        return AchievementsRepo(self.session)