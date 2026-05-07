"""Репозиторий функций для работы с нерабочими сменами."""

import uuid
from datetime import datetime, timedelta, date, time
from typing import Any, Sequence

from sqlalchemy import and_, extract, func, or_, select, delete

from stp_database import DbConfig
from stp_database.models.Shedule import Shift, ShiftOut, ShiftHigh
from stp_database.models.STP.employee import Employee
from stp_database.repo.base import BaseRepo


class ShiftsOutRepo(BaseRepo):
    """Репозиторий с функциями для работы с нерабочими сменами."""

    async def add_outshift(
        self,
        user_id: int,
        date: date,
        type: str | None = "other",
        comment: str | None = None,
    ) -> ShiftOut:
        """Добавление новой смены.

        Args:
            user_id: Уникальный ID пользователя которому принадлежит смена
            date: дата
            type: тип смены: основная, доп.смена, отработка
            comment: дополнительный комментарий

        Returns:
             Объект созданной ShiftOut
        """
        outshift_uuid = str(uuid.uuid4())

        outshift = ShiftOut(
            uuid=outshift_uuid,
            user_id=user_id,
            date=date,
            type=type,
            comment=comment,
        )

        self.session.add(outshift)
        await self.session.commit()
        await self.session.refresh(outshift)
        return outshift

    async def add_outshifts_batch(
        self,
        outshifts_list: Sequence[dict],
    ) -> list[ShiftOut]:
        """
        Добавление пачки смен.

        outshifts_list пример:
        [
            {
                "user_id": 1,
                "date": datetime(...),
                "type": "base",
                "comment": "..."
            }
        ]
        """

        outshifts = [
            ShiftOut(
                user_id=item["user_id"],
                date=item["date"],
                type=item.get("type", "other"),
                comment=item.get("comment"),
            )
            for item in outshifts_list
        ]

        self.session.add_all(outshifts)
        await self.session.commit()

        for outshift in outshifts:
            await self.session.refresh(outshift)

        return outshifts

    async def get_outshifts_by_period(
        self,
        date_start: datetime,
        date_end: datetime,
        user_id: int | None = None,
    ) -> list[ShiftOut]:
        """
        Получить смены, у которых outshift.date попадает в период.
        """

        stmt = select(ShiftOut).where(
            ShiftOut.date >= date_start,
            ShiftOut.date <= date_end,
        )

        if user_id is not None:
            stmt = stmt.where(ShiftOut.user_id == user_id)

        stmt = stmt.order_by(ShiftOut.date.asc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def clear_outshifts_by_period(
        self,
        date_start: datetime,
        date_end: datetime,
        user_id: int | None = None,
    ) -> int:
        """
        Удалить смены, у которых outshift.date попадает в период.
        Возвращает количество удалённых строк.
        """

        stmt = delete(ShiftOut).where(
            ShiftOut.date >= date_start,
            ShiftOut.date <= date_end,
        )

        if user_id is not None:
            stmt = stmt.where(ShiftOut.user_id == user_id)

        result = await self.session.execute(stmt)
        await self.session.commit()

        return result.rowcount or 0

    async def delete_outshift_by_uuid(
        self,
        outshift_uuid: str
    ) -> bool:
        """
        Удаление смены по uuid.

        Returns:
            True если удалено, False если не найдено
        """

        stmt = delete(ShiftOut).where(ShiftOut.uuid == outshift_uuid)

        result = await self.session.execute(stmt)
        await self.session.commit()

        return (result.rowcount or 0) > 0

    async def get_outshift_by_uuid(
        self,
        outshift_uuid: str,
    ) -> ShiftOut | None:
        """
        Получить смену по uuid.
        """

        stmt = select(ShiftOut).where(ShiftOut.uuid == outshift_uuid)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_outshifts_by_date(
        self,
        outshift_date: date,
        user_id: int | None = None,
    ) -> list[ShiftOut]:
        """
        Получить смены за конкретный день по outshift.date.
        """

        day = datetime.combine(outshift_date, time.min)

        stmt = select(ShiftOut).where(
            ShiftOut.date >= day
        )

        if user_id is not None:
            stmt = stmt.where(ShiftOut.user_id == user_id)

        stmt = stmt.order_by(ShiftOut.date.asc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_outshift_by_params(
        self,
        outshift_uuid: str | None = None,
        outshift_date: date | None = None,
        user_id: int | None = None,
    ) -> list[ShiftOut]:
        """
        Универсальный поиск смен по разным параметрам.
        """

        stmt = select(ShiftOut)

        if outshift_uuid is not None:
            stmt = stmt.where(ShiftOut.uuid == outshift_uuid)

        if outshift_date is not None:
            day = datetime.combine(outshift_date, time.min)

            stmt = stmt.where(
                ShiftOut.date >= day
            )

        if user_id is not None:
            stmt = stmt.where(ShiftOut.user_id == user_id)

        stmt = stmt.order_by(ShiftOut.date.asc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())