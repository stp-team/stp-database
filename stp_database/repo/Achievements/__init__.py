"""Репозитории Achievements."""

from stp_database.repo.Achievements.achievements import AchievementsRepo
from stp_database.repo.Achievements.log_achievements import LogAchievementsRepo

__all__ = [
    "AchievementsRepo",
    "LogAchievementsRepo",
]