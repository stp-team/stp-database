"""Репозиторий по работе со списком достижений."""

import logging
from typing import Any, Sequence
from datetime import datetime
from typing import Sequence

from sqlalchemy import or_, delete, select
from sqlalchemy.exc import SQLAlchemyError

from stp_database.models.Achievements import Achievements
from stp_database.repo.base import BaseRepo

logger = logging.getLogger(__name__)


class AchievementsRepo(BaseRepo):
    """Репозиторий для работы со списком достижений."""

    async def get_achievements_by_period(
        self,
        period: str,
    ) -> Sequence[Achievements]:
        """Получить достижения для заданного периода."""
        stmt = (
            select(Achievements)
            .where(Achievements.period == period)
            .order_by(Achievements.created_at.desc())
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_achievements(self) -> Sequence[Achievements]:
        """Получить список всех достижений."""

        stmt = (
            select(Achievements)
            .order_by(Achievements.created_at.desc())
        )

        result = await self.session.execute(stmt)

        return result.scalars().all()

    async def get_achievement_by_uuid(
            self,
            achievement_uuid: str,
    ) -> Achievements | None:
        """
        Получить достижение по UUID.

        Args:
            achievement_uuid: UUID достижения.

        Returns:
            Достижение или None, если запись не найдена.
        """

        stmt = select(Achievements).where(
            Achievements.uuid == achievement_uuid
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

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
            achievement_uuid: str,
            **changes: Any,
    ) -> Achievements | None:
        """
        Обновить достижение по UUID.

        Необходимо передать минимум одно изменяемое поле.

        Returns:
            Обновлённое достижение или None, если запись не найдена.

        Raises:
            ValueError: Если поля обновления не переданы или передано
                недопустимое поле.
        """

        if not changes:
            raise ValueError(
                "Необходимо передать минимум одно поле для обновления"
            )

        allowed_fields = {
            "name",
            "description",
            "divisions",
            "positions",
            "period",
            "reward",
            "rule_expression",
            "updated_by",
        }

        invalid_fields = set(changes) - allowed_fields

        if invalid_fields:
            raise ValueError(
                "Недопустимые поля для обновления: "
                + ", ".join(sorted(invalid_fields))
            )

        stmt = select(Achievements).where(
            Achievements.uuid == achievement_uuid
        )

        result = await self.session.execute(stmt)
        achievement = result.scalar_one_or_none()

        if achievement is None:
            return None

        for field, value in changes.items():
            setattr(achievement, field, value)

        achievement.updated_at = datetime.now()

        try:
            await self.session.commit()
            await self.session.refresh(achievement)
            return achievement

        except SQLAlchemyError:
            await self.session.rollback()
            logger.exception(
                "[БД] Ошибка обновления достижения %s",
                achievement_uuid,
            )
            raise

    async def delete_achievement(
            self,
            achievement_uuid: str,
    ) -> bool:
        """
        Удалить достижение по UUID.

        Returns:
            True, если достижение удалено.
            False, если достижение не найдено.
        """

        stmt = (
            delete(Achievements)
            .where(Achievements.uuid == achievement_uuid)
        )

        try:
            result = await self.session.execute(stmt)

            if result.rowcount == 0:
                await self.session.rollback()
                return False

            await self.session.commit()
            return True

        except SQLAlchemyError:
            await self.session.rollback()
            logger.exception(
                "[БД] Ошибка удаления достижения %s",
                achievement_uuid,
            )
            raise