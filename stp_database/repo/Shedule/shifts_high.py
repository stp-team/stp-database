"""Репозиторий функций для работы со сменами дежурных."""

import uuid
from datetime import datetime, timedelta, date, time
from typing import Any, Sequence

from sqlalchemy import and_, extract, func, or_, select, delete

from stp_database import DbConfig
from stp_database.models.Shedule import Shift, ShiftOut, ShiftHigh
from stp_database.models.STP.employee import Employee
from stp_database.repo.base import BaseRepo


class ShiftsHighRepo(BaseRepo):
    """Репозиторий с функциями для работы со сменами дежурных."""

    async def add_highshift(
        self,
        user_id: int,
        date_start: datetime,
        date_end: datetime,
        type: str | None = "other",
        comment: str | None = None,
    ) -> ShiftHigh:
        """Добавление новой смены.

        Args:
            user_id: Уникальный ID пользователя которому принадлежит смена
            date_start: дата начала
            date_end: дата окончания
            type: тип смены: старший, помощник
            comment: дополнительный комментарий

        Returns:
             Объект созданной ShiftOut
        """
        highshift_uuid = str(uuid.uuid4())

        highshift = ShiftHigh(
            uuid=highshift_uuid,
            user_id=user_id,
            date_start=date_start,
            date_end=date_end,
            type=type,
            comment=comment,
        )

        self.session.add(highshift)
        await self.session.commit()
        await self.session.refresh(highshift)
        return highshift

    async def add_highshifts_batch(
        self,
        highshifts_list: Sequence[dict],
    ) -> list[ShiftHigh]:
        """
        Добавление пачки смен.

        highshifts_list пример:
        [
            {
                "user_id": 1,
                "date_start": datetime(...),
                "date_time": datetime(...),
                "type": "base",
                "comment": "..."
            }
        ]
        """

        highshifts = [
            ShiftHigh(
                user_id=item["user_id"],
                date_start=item["date_start"],
                date_end=item["date_end"],
                type=item.get("type", "other"),
                comment=item.get("comment"),
            )
            for item in highshifts_list
        ]

        self.session.add_all(highshifts)
        await self.session.commit()

        for outshift in highshifts:
            await self.session.refresh(outshift)

        return highshifts

    async def get_highshifts_by_period(
        self,
        date_start: datetime,
        date_end: datetime,
        user_id: int | None = None,
    ) -> list[ShiftHigh]:
        """
        Получить смены, у которых highshift.date попадает в период.
        """

        stmt = select(ShiftHigh).where(
            ShiftHigh.date_start >= date_start,
            ShiftHigh.date_start <= date_end,
        )

        if user_id is not None:
            stmt = stmt.where(ShiftHigh.user_id == user_id)

        stmt = stmt.order_by(ShiftHigh.date_start.asc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def clear_highshifts_by_period(
        self,
        date_start: datetime,
        date_end: datetime,
        user_id: int | None = None,
    ) -> int:
        """
        Удалить смены, у которых highshift.date попадает в период.
        Возвращает количество удалённых строк.
        """

        stmt = delete(ShiftHigh).where(
            ShiftHigh.date_start >= date_start,
            ShiftHigh.date_start <= date_end,
        )

        if user_id is not None:
            stmt = stmt.where(ShiftHigh.user_id == user_id)

        result = await self.session.execute(stmt)
        await self.session.commit()

        return result.rowcount or 0

    async def delete_highshift_by_uuid(
        self,
        highshift_uuid: str
    ) -> bool:
        """
        Удаление смены по uuid.

        Returns:
            True если удалено, False если не найдено
        """

        stmt = delete(ShiftHigh).where(ShiftHigh.uuid == highshift_uuid)

        result = await self.session.execute(stmt)
        await self.session.commit()

        return (result.rowcount or 0) > 0

    async def get_highshift_by_uuid(
        self,
        highshift_uuid: str,
    ) -> ShiftHigh | None:
        """
        Получить смену по uuid.
        """

        stmt = select(ShiftHigh).where(ShiftHigh.uuid == highshift_uuid)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_highshifts_by_date(
        self,
        highshift_date: date,
        user_id: int | None = None,
    ) -> list[ShiftHigh]:
        """
        Получить смены за конкретный день по highshift.date.
        """

        day = datetime.combine(highshift_date, time.min)

        stmt = select(ShiftHigh).where(
            ShiftHigh.date_start >= day
        )

        if user_id is not None:
            stmt = stmt.where(ShiftHigh.user_id == user_id)

        stmt = stmt.order_by(ShiftHigh.date_start.asc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_highshift_by_params(
        self,
        highshift_uuid: str | None = None,
        highshift_date: date | None = None,
        user_id: int | None = None,
    ) -> list[ShiftHigh]:
        """
        Универсальный поиск смен по разным параметрам.
        """

        stmt = select(ShiftHigh)

        if highshift_uuid is not None:
            stmt = stmt.where(ShiftHigh.uuid == highshift_uuid)

        if highshift_date is not None:
            day = datetime.combine(highshift_date, time.min)

            stmt = stmt.where(
                ShiftHigh.date_start >= day
            )

        if user_id is not None:
            stmt = stmt.where(ShiftHigh.user_id == user_id)

        stmt = stmt.order_by(ShiftHigh.date_start.asc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())