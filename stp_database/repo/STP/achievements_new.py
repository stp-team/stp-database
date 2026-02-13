"""Репозиторий функций для взаимодействия с таблицей достижений (новая версия)."""

import json
import logging
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from stp_database.models.STP.achievement import AchievementNew
from stp_database.repo.base import BaseRepo

logger = logging.getLogger(__name__)


class AchievementsNewRepo(BaseRepo):
    """Класс репозитория достижений (новая версия)."""

    async def get_achievements(
        self,
        achievement_id: int | None = None,
        division: str | None = None,
    ) -> AchievementNew | None | Sequence[AchievementNew]:
        """Получает достижение(я) по идентификатору или список достижений.

        Args:
            achievement_id: Уникальный идентификатор достижения (если указан, возвращает одно достижение)
            division: Фильтр по направлению (НЦК, НТП и т.д.) - используется только если achievement_id не указан

        Returns:
            AchievementNew или None (если указан achievement_id)
            Последовательность AchievementNew (если achievement_id не указан)
        """
        if achievement_id is not None:
            select_stmt = select(AchievementNew).where(
                AchievementNew.id == achievement_id
            )
            result = await self.session.execute(select_stmt)
            return result.scalar_one_or_none()
        else:
            if division:
                select_stmt = select(AchievementNew).where(
                    AchievementNew.division == division
                )
            else:
                select_stmt = select(AchievementNew)

            result = await self.session.execute(select_stmt)
            achievements = result.scalars().all()

            return list(achievements)

    async def add_achievement(
        self,
        name: str,
        description: str | None,
        division: str,
        requirements: dict,
        reward: int,
        position: str,
        period: str,
    ) -> AchievementNew | None:
        """Добавление нового достижения.

        Args:
            name: Название достижения
            description: Описание достижения
            division: Направление сотрудника (НТП/НЦК) для получения достижения
            requirements: Требования для получения достижения (JSON)
            reward: Награда за получение достижение в баллах
            position: Должности, способные получить достижения
            period: Частота возможного получения достижения (daily, weekly, monthly, once, manual)

        Returns:
            Созданный объект AchievementNew или None в случае ошибки
        """
        # Serialize requirements to JSON string for database storage
        requirements_json = (
            json.dumps(requirements) if isinstance(requirements, dict) else requirements
        )

        new_achievement = AchievementNew(
            name=name,
            description=description,
            division=division,
            requirements=requirements_json,
            reward=reward,
            position=position,
            period=period,
        )

        try:
            self.session.add(new_achievement)
            await self.session.commit()
            await self.session.refresh(new_achievement)
            logger.info(f"[БД] Создано новое достижение: {name}")
            return new_achievement
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка добавления достижения {name}: {e}")
            await self.session.rollback()
            return None

    async def get_achievements_by_period(
        self,
        period_type: str,  # "daily", "weekly", "monthly", "once", "manual"
    ) -> Sequence[AchievementNew]:
        """Получает достижения по периоду (день/неделя/месяц/единижды/ручная).

        Args:
            period_type: Тип периода:
                - "daily" - ежедневные достижения
                - "weekly" - еженедельные достижения
                - "monthly" - ежемесячные достижения
                - "once" - единоразовые достижения
                - "manual" - ручные достижения

        Returns:
            Список достижений указанного периода
        """
        try:
            select_stmt = select(AchievementNew).where(
                AchievementNew.period == period_type
            )
            result = await self.session.execute(select_stmt)
            achievements = result.scalars().all()

            logger.info(
                f"[БД] Получено {len(achievements)} достижений для периода '{period_type}'"
            )
            return list(achievements)

        except SQLAlchemyError as e:
            logger.error(
                f"[БД] Ошибка получения достижений для периода {period_type}: {e}"
            )
            return []

    async def update_achievement(
        self,
        achievement_id: int,
        **kwargs: Any,
    ) -> AchievementNew | None:
        """Обновление достижения.

        Args:
            achievement_id: Идентификатор достижения
            **kwargs: Поля для обновления (name, description, division, requirements, reward, position, period)

        Returns:
            Обновленный объект AchievementNew или None
        """
        select_stmt = select(AchievementNew).where(AchievementNew.id == achievement_id)

        result = await self.session.execute(select_stmt)
        achievement: AchievementNew | None = result.scalar_one_or_none()

        if achievement:
            for key, value in kwargs.items():
                # Serialize requirements to JSON string for database storage
                if key == "requirements" and isinstance(value, dict):
                    value = json.dumps(value)
                setattr(achievement, key, value)
            await self.session.commit()
            logger.info(f"[БД] Обновлено достижение с ID {achievement_id}")

        return achievement

    async def delete_achievement(
        self,
        achievement_id: int,
    ) -> bool:
        """Удаление достижения.

        Args:
            achievement_id: Идентификатор достижения

        Returns:
            True если успешно, иначе False
        """
        try:
            select_stmt = select(AchievementNew).where(
                AchievementNew.id == achievement_id
            )
            result = await self.session.execute(select_stmt)
            achievement = result.scalar_one_or_none()

            if achievement is None:
                logger.warning(f"[БД] Достижение с ID {achievement_id} не найдено")
                return False

            await self.session.delete(achievement)
            await self.session.commit()
            logger.info(f"[БД] Достижение с ID {achievement_id} успешно удалено")
            return True

        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка удаления достижения с ID {achievement_id}: {e}")
            await self.session.rollback()
            return False
