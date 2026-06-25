"""Репозиториий GameCenter."""

from stp_database.repo.GameCenter.games import GameCenterGamesRepo
from stp_database.repo.GameCenter.requests import GameCenterRequestsRepo

__all__ = ["GameCenterGamesRepo", "GameCenterRequestsRepo"]