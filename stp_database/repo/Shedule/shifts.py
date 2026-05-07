"""Репозиторий функций для работы со сменами."""

import uuid
from datetime import datetime, timedelta, date, time
from typing import Any, Sequence

from sqlalchemy import and_, extract, func, or_, select, delete

from stp_database import DbConfig
from stp_database.models.Shedule import Shift, ShiftOut, ShiftHigh
from stp_database.models.STP.employee import Employee
from stp_database.repo.base import BaseRepo


class ShiftsRepo(BaseRepo):
    """Репозиторий с функциями для работы со сменами."""

    async def add_shift(
        self,
        user_id: int,
        date_start: datetime,
        date_end: datetime,
        type: str | None = "other",
        comment: str | None = None,
    ) -> Shift:
        """Добавление новой смены.

        Args:
            user_id: Уникальный ID пользователя которому принадлежит смена
            date_start: дата начала
            date_end: дата окончания
            type: тип смены: основная, доп.смена, отработка
            comment: дополнительный комментарий

        Returns:
             Объект созданной Shift
        """
        shift_uuid = str(uuid.uuid4())

        shift = Shift(
            uuid=shift_uuid,
            user_id=user_id,
            date_start=date_start,
            date_end=date_end,
            type=type,
            comment=comment,
        )

        self.session.add(shift)
        await self.session.commit()
        await self.session.refresh(shift)
        return shift

    async def add_shifts_batch(
        self,
        shifts_list: Sequence[dict],
    ) -> list[Shift]:
        """
        Добавление пачки смен.

        shifts_list пример:
        [
            {
                "user_id": 1,
                "date_start": datetime(...),
                "date_end": datetime(...),
                "type": "base",
                "comment": "..."
            }
        ]
        """

        shifts = [
            Shift(
                user_id=item["user_id"],
                date_start=item["date_start"],
                date_end=item["date_end"],
                type=item.get("type", "other"),
                comment=item.get("comment"),
            )
            for item in shifts_list
        ]

        self.session.add_all(shifts)
        await self.session.commit()

        for shift in shifts:
            await self.session.refresh(shift)

        return shifts

    async def get_shifts_by_period(
        self,
        date_start: datetime,
        date_end: datetime,
        user_id: int | None = None,
    ) -> list[Shift]:
        """
        Получить смены, у которых shift.date_start попадает в период.
        """

        stmt = select(Shift).where(
            Shift.date_start >= date_start,
            Shift.date_start <= date_end,
        )

        if user_id is not None:
            stmt = stmt.where(Shift.user_id == user_id)

        stmt = stmt.order_by(Shift.date_start.asc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def clear_shifts_by_period(
        self,
        date_start: datetime,
        date_end: datetime,
        user_id: int | None = None,
    ) -> int:
        """
        Удалить смены, у которых shift.date_start попадает в период.
        Возвращает количество удалённых строк.
        """

        stmt = delete(Shift).where(
            Shift.date_start >= date_start,
            Shift.date_start <= date_end,
        )

        if user_id is not None:
            stmt = stmt.where(Shift.user_id == user_id)

        result = await self.session.execute(stmt)
        await self.session.commit()

        return result.rowcount or 0

    async def delete_shift_by_uuid(
        self,
        shift_uuid: str
    ) -> bool:
        """
        Удаление смены по uuid.

        Returns:
            True если удалено, False если не найдено
        """

        stmt = delete(Shift).where(Shift.uuid == shift_uuid)

        result = await self.session.execute(stmt)
        await self.session.commit()

        return (result.rowcount or 0) > 0

    async def get_shift_by_uuid(
        self,
        shift_uuid: str,
    ) -> Shift | None:
        """
        Получить смену по uuid.
        """

        stmt = select(Shift).where(Shift.uuid == shift_uuid)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_shifts_by_date(
        self,
        shift_date: date,
        user_id: int | None = None,
    ) -> list[Shift]:
        """
        Получить смены за конкретный день по shift.date_start.
        """

        day_start = datetime.combine(shift_date, time.min)
        day_end = datetime.combine(shift_date, time.max)

        stmt = select(Shift).where(
            Shift.date_start >= day_start,
            Shift.date_start <= day_end,
        )

        if user_id is not None:
            stmt = stmt.where(Shift.user_id == user_id)

        stmt = stmt.order_by(Shift.date_start.asc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_shift_by_params(
        self,
        shift_uuid: str | None = None,
        shift_date: date | None = None,
        user_id: int | None = None,
    ) -> list[Shift]:
        """
        Универсальный поиск смен по разным параметрам.
        """

        stmt = select(Shift)

        if shift_uuid is not None:
            stmt = stmt.where(Shift.uuid == shift_uuid)

        if shift_date is not None:
            day_start = datetime.combine(shift_date, time.min)
            day_end = datetime.combine(shift_date, time.max)

            stmt = stmt.where(
                Shift.date_start >= day_start,
                Shift.date_start <= day_end,
            )

        if user_id is not None:
            stmt = stmt.where(Shift.user_id == user_id)

        stmt = stmt.order_by(Shift.date_start.asc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())