"""Агрегатор репозиториев БД достижений."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from stp_database.repo.Achievements.achievements import AchievementsRepo
from stp_database.repo.Achievements.inventory import InventoryRepo
from stp_database.repo.Achievements.awards import AwardsRepo
from stp_database.repo.Achievements.activations import ActivationsRepo
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

    @property
    def activations(self) -> ActivationsRepo:
        """Работа с активациями."""
        return ActivationsRepo(self.session)

    @property
    def awards(self) -> AwardsRepo:
        """Работа с наградами."""
        return AwardsRepo(self.session)

    @property
    def inventory(self) -> InventoryRepo:
        """Работа с инвентарем."""
        return InventoryRepo(self.session)