"""Репозиторий по работе со списком достижений."""

import logging
from typing import Any, Sequence
from datetime import datetime
from typing import Sequence

from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError

from stp_database.models.Achievements import Achievements
from stp_database.repo.base import BaseRepo

logger = logging.getLogger(__name__)


class AchievementsRepo(BaseRepo):
    """Репозиторий для работы со списком достижений."""

    async def create_achievement(
            self,
            uuid: str,
            name: str | None = "Новое достижение",
            description: str | None = "Новое достижение",
            divisions: list[str] | None = None,
            positions: list[str] | None = None,
            period: str | None = None,
            reward: int | None = None,
            rule_expression: str | None = None,
            created_by: int | None = None,
    ) -> None:
        achievement = Achievements(
            uuid=uuid,
            name=name,
            description=description,
            divisions=divisions,
            positions=positions,
            period=period,
            reward=reward,
            rule_expression=rule_expression,
            created_by=created_by,
        )

        try:
            self.session.add(achievement)
            await self.session.commit()
            await self.session.refresh(achievement)
            return achievement
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка создания достижения: {e}")
            await self.session.rollback()
            return None

    async def update_achievement(
            self,
            achievement_uuid: int,
            **kwargs: Any,
    ) -> Achievements | None:
        """Обновление достижения.

        Args:
            achievement_uuid: Идентификатор достижения

        Returns:
            Обновленный объект Achievements или None
        """
        select_stmt = select(Achievements).where(Achievements.uuid == achievement_uuid)

        result = await self.session.execute(select_stmt)
        achievement: Achievements | None = result.scalar_one_or_none()

        # Если достижение существует - обновляем его
        if achievement:
            for key, value in kwargs.items():
                setattr(achievement, key, value)
            await self.session.commit()

        return achievement