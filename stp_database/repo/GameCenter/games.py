"""Репозиторий GameCenter."""

import logging
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from stp_database.models.GameCenter.assigned_chances import AssignedChances
from stp_database.models.GameCenter.games_list import GameList
from stp_database.models.Teaching import result
from stp_database.repo.base import BaseRepo

logger = logging.getLogger(__name__)

class GameCenterGamesRepo(BaseRepo):
    """Репозиторий для игр GameCenter."""

    async def get_game_by_uuid(
            self,
            game_uuid: str,
    ) -> GameList | None:
        """Получение игры по UUID."""
        try:
            result = await self.session.execute(
                select(GameList).where(
                    GameList.uuid == game_uuid
                )
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"[GameCenter] Ошибка получения игры {game_uuid}: {e}")

        return None

    async def get_active_games(
            self,
    ) -> Sequence[GameList]:
        """Получение списка активных игр."""
        try:
            result = await self.session.execute(
                select(GameList).where(
                    GameList.is_active == True
                )
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"[GameCenter] Ошибка получения активных игр: {e}")
            return []

    async def get_assigned_chance(
            self,
            game_uuid: str,
            user_id: int,
    ) -> AssignedChances | None:
        """Получение индивидуального шанса пользователя для игры."""
        try:
            result = await self.session.execute(
                select(AssignedChances).where(
                    AssignedChances.game_uuid == game_uuid,
                    AssignedChances.user_id == user_id,
                )
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"[GameCenter] Ошибка получения индивидуального шанса {game_uuid}: {e}"
                         f"game_uuid={game_uuid}, user_id={user_id}: {e}")
            return None