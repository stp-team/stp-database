"""Репозиторий функций для работы со сменами."""

import uuid
from datetime import date, datetime, time
from typing import Sequence

from sqlalchemy import delete, select

from stp_database.models.Shedule import Shift
from stp_database.repo.base import BaseRepo


class ShiftsRepo(BaseRepo):
    """Репозиторий с функциями для работы со сменами."""

    @staticmethod
    def _shift_type(item: dict) -> str:
        return item.get("type") or "other"

    @classmethod
    def _shift_key_from_values(
        cls,
        user_id: int,
        date_start: datetime,
        shift_type: str | None,
    ) -> tuple[int, date, str]:
        return user_id, date_start.date(), shift_type or "other"

    @classmethod
    def _shift_key_from_item(cls, item: dict) -> tuple[int, date, str]:
        return cls._shift_key_from_values(
            item["user_id"],
            item["date_start"],
            cls._shift_type(item),
        )

    @classmethod
    def _shift_key(cls, shift: Shift) -> tuple[int, date, str]:
        return cls._shift_key_from_values(
            shift.user_id,
            shift.date_start,
            shift.type,
        )

    @staticmethod
    def _deduplicate_items(shifts_list: Sequence[dict]) -> dict[tuple[int, datetime, datetime, str], dict]:
        items_by_key: dict[tuple[int, datetime, datetime, str], dict] = {}

        for item in shifts_list:
            items_by_key[ShiftsRepo._shift_key_from_item(item)] = item

        return items_by_key

    @staticmethod
    def _index_existing(
        shifts: Sequence[Shift],
    ) -> tuple[dict[tuple[int, datetime, datetime, str], Shift], list[Shift]]:
        shifts_by_key: dict[tuple[int, datetime, datetime, str], Shift] = {}
        duplicates: list[Shift] = []

        for shift in shifts:
            key = ShiftsRepo._shift_key(shift)
            if key in shifts_by_key:
                duplicates.append(shift)
                continue

            shifts_by_key[key] = shift

        return shifts_by_key, duplicates

    async def _get_existing_by_period(
        self,
        date_start: datetime,
        date_end: datetime,
        user_ids: set[int],
    ) -> list[Shift]:
        stmt = select(Shift).where(
            Shift.date_start >= date_start,
            Shift.date_start <= date_end,
        )

        if user_ids:
            stmt = stmt.where(Shift.user_id.in_(user_ids))

        result = await self.session.execute(stmt)
        return list(result.scalars().all())


    # В начале ищет есть ли смена (поиск только по дате из date_start без времени) если смена есть то обновить время, если оно отличается. Если смены нет то добавить
    async def add_shift(
        self,
        user_id: int,
        date_start: datetime,
        date_end: datetime,
        type: str | None = "other",
        comment: str | None = None,
    ) -> Shift:
        """Добавление или обновление смены."""

        shift_type = type or "other"
        stmt = select(Shift).where(
            Shift.user_id == user_id,
            Shift.date_start == date_start,
            Shift.date_end == date_end,
            Shift.type == shift_type,
        )

        result = await self.session.execute(stmt)
        existing_shifts = list(result.scalars().all())

        if existing_shifts:
            shift = existing_shifts[0]
            shift.comment = comment

            for duplicate in existing_shifts[1:]:
                await self.session.delete(duplicate)

            await self.session.commit()
            await self.session.refresh(shift)
            return shift

        shift = Shift(
            uuid=str(uuid.uuid4()),
            user_id=user_id,
            date_start=date_start,
            date_end=date_end,
            type=shift_type,
            comment=comment,
        )

        self.session.add(shift)
        await self.session.commit()
        await self.session.refresh(shift)
        return shift

    # В начале ищет есть ли смена (поиск только по дате из date_start без времени) если смена есть то обновить время, если оно отличается. Если смены нет то добавить
    async def add_shifts_batch(
        self,
        shifts_list: Sequence[dict],
    ) -> list[Shift]:
        """Добавление пачки смен без создания дублей."""

        items_by_key = self._deduplicate_items(shifts_list)
        if not items_by_key:
            return []

        items = list(items_by_key.values())
        user_ids = {item["user_id"] for item in items}
        period_start = min(item["date_start"] for item in items)
        period_end = max(item["date_start"] for item in items)

        existing = await self._get_existing_by_period(period_start, period_end, user_ids)
        existing_by_key, duplicates = self._index_existing(existing)

        for duplicate in duplicates:
            await self.session.delete(duplicate)

        shifts: list[Shift] = []
        for key, item in items_by_key.items():
            shift = existing_by_key.get(key)

            if shift is None:
                shift = Shift(
                    user_id=item["user_id"],
                    date_start=item["date_start"],
                    date_end=item["date_end"],
                    type=self._shift_type(item),
                    comment=item.get("comment"),
                )
                self.session.add(shift)
            else:
                shift.comment = item.get("comment")

            shifts.append(shift)

        await self.session.commit()

        for shift in shifts:
            await self.session.refresh(shift)

        return shifts

    async def sync_shifts_by_period(
        self,
        shifts_list: Sequence[dict],
        date_start: datetime | None = None,
        date_end: datetime | None = None,
        user_ids: Sequence[int] | None = None,
    ) -> dict[str, int]:
        """Синхронизировать смены за период с новым графиком.

        Метод создаёт новые смены, обновляет найденные по естественному ключу
        и удаляет старые записи за этот же период/сотрудников, которых нет в новой загрузке.
        """

        stats = {"created": 0, "updated": 0, "deleted": 0, "unchanged": 0}
        items_by_key = self._deduplicate_items(shifts_list)
        items = list(items_by_key.values())

        target_user_ids = set(user_ids or [item["user_id"] for item in items])
        if not target_user_ids:
            return stats

        if date_start is None:
            if not items:
                return stats
            date_start = min(item["date_start"] for item in items)

        if date_end is None:
            if not items:
                return stats
            date_end = max(item["date_start"] for item in items)

        existing = await self._get_existing_by_period(date_start, date_end, target_user_ids)
        existing_by_key, duplicates = self._index_existing(existing)

        for duplicate in duplicates:
            await self.session.delete(duplicate)
            stats["deleted"] += 1

        for key, item in items_by_key.items():
            if key[0] not in target_user_ids:
                continue

            shift = existing_by_key.get(key)
            if shift is None:
                shift = Shift(
                    user_id=item["user_id"],
                    date_start=item["date_start"],
                    date_end=item["date_end"],
                    type=self._shift_type(item),
                    comment=item.get("comment"),
                )
                self.session.add(shift)
                stats["created"] += 1
                continue

            new_date_start = item["date_start"]
            new_date_end = item.get("date_end")
            new_comment = item.get("comment")

            if (shift.date_start != new_date_start
                or shift.date_end != new_date_end
                or shift.comment != new_comment
            ):
                shift.date_start = new_date_start
                shift.date_end = new_date_end
                shift.comment = new_comment
                stats["updated"] += 1
            else:
                stats["unchanged"] += 1

        incoming_keys = {key for key in items_by_key if key[0] in target_user_ids}
        for key, shift in existing_by_key.items():
            if key not in incoming_keys:
                await self.session.delete(shift)
                stats["deleted"] += 1

        await self.session.commit()
        return stats

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