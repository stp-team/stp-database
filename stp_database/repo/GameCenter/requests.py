"""Агрегатор репозиториев GameCenter."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from stp_database.repo.GameCenter.games import GameCenterGamesRepo


@dataclass
class GameCenterRequestsRepo:
    """Репозиторий для обработки операций с БД GameCenter."""

    session: AsyncSession

    @property
    def games(self) -> GameCenterGamesRepo:
        """Инициализация GameCenterGamesRepo."""
        return GameCenterGamesRepo(self.session)