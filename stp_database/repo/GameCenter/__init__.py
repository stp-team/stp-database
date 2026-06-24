"""Репозиториий GameCenter."""

from stp_database.repo.GameCenter.games import GameCenterGamesRepo
from stp_database.repo.GameCenter.requests import GameCenterRequestRepo

__all__ = ["GameCenterGamesRepo", "GameCenterRequestRepo"]