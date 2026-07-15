"""Репозитории Achievements."""

from stp_database.repo.Achievements.achievements import AchievementsRepo
from stp_database.repo.Achievements.activations import ActivationsRepo
from stp_database.repo.Achievements.awards import AwardsRepo
from stp_database.repo.Achievements.inventory import InventoryRepo
from stp_database.repo.Achievements.log_achievements import LogAchievementsRepo

__all__ = [
    "AchievementsRepo",
    "ActivationsRepo",
    "AwardsRepo",
    "InventoryRepo",
    "LogAchievementsRepo",
]
