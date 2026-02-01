"""Репозиторий функций для взаимодействия с таблицей достижений."""

import logging
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from stp_database.models.STP.achievement import Achievement
from stp_database.repo.base import BaseRepo

logger = logging.getLogger(__name__)


class AchievementsRepo(BaseRepo):
    """Класс репозитория достижений."""

    async def get_achievements(
        self,
        achievement_id: int | None = None,
        division: str | None = None,
    ) -> Achievement | None | Sequence[Achievement]:
        """Получает достижение(я) по идентификатору или список достижений.

        Args:
            achievement_id: Уникальный идентификатор достижения (если указан, возвращает одно достижение)
            division: Фильтр по направлению (НЦК, НТП и т.д.) - используется только если achievement_id не указан

        Returns:
            Achievement или None (если указан achievement_id)
            Последовательность Achievement (если achievement_id не указан)
        """
        if achievement_id is not None:
            # Запрос одного достижения по ID
            select_stmt = select(Achievement).where(Achievement.id == achievement_id)
            result = await self.session.execute(select_stmt)
            return result.scalar_one_or_none()
        else:
            # Запрос списка достижений с опциональной фильтрацией по division
            if division:
                select_stmt = select(Achievement).where(
                    Achievement.division == division
                )
            else:
                select_stmt = select(Achievement)

            result = await self.session.execute(select_stmt)
            achievements = result.scalars().all()

            return list(achievements)

    async def add_achievement(
        self,
        name: str,
        description: str,
        division: str,
        kpi: str,
        reward: int,
        position: str,
        period: str,
    ) -> Achievement | None:
        """Добавление нового достижения.

        Args:
            name: Название достижения
            description: Описание достижения
            division: Направление сотрудника (НТП/НЦК) для получения достижения
            kpi: Показатели Stats для получения достижения
            reward: Награда за получение достижение в баллах
            position: Позиция/должность сотрудника для получения достижения
            period: Частота возможного получения достижения: день, неделя, месяц и ручная

        Returns:
            Созданный объект Achievement или None в случае ошибки
        """
        new_achievement = Achievement(
            name=name,
            description=description,
            division=division,
            kpi=kpi,
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
        period_type: str,  # "d", "w", "m" or "daily", "weekly", "monthly"
    ) -> Sequence[Achievement]:
        """Получает достижения по периоду (день/неделя/месяц).

        Args:
            period_type: Тип периода:
                - "d" - ежедневные достижения
                - "w" - еженедельные достижения
                - "m" - ежемесячные достижения

        Returns:
            Список достижений указанного периода
        """
        try:
            # Filter achievements where the period field is True
            select_stmt = select(Achievement).where(Achievement.period == period_type)
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
    ) -> Achievement | None:
        """Обновление достижения.

        Args:
            achievement_id: Идентификатор достижения

        Returns:
            Обновленный объект Achievement или None
        """
        select_stmt = select(Achievement).where(Achievement.id == achievement_id)

        result = await self.session.execute(select_stmt)
        achievement: Achievement | None = result.scalar_one_or_none()

        # Если достижение существует - обновляем его
        if achievement:
            for key, value in kwargs.items():
                setattr(achievement, key, value)
            await self.session.commit()

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
            select_stmt = select(Achievement).where(Achievement.id == achievement_id)
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
