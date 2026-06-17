"""Репозиторий функций для работы со сменами дежурных."""

import uuid
from datetime import date, datetime, time
from typing import Sequence

from sqlalchemy import delete, select

from stp_database.models.Shedule import ShiftHigh
from stp_database.repo.base import BaseRepo


class ShiftsHighRepo(BaseRepo):
    """Репозиторий с функциями для работы со сменами дежурных."""

    @staticmethod
    def _highshift_type(item: dict) -> str:
        return item.get("type") or "other"

    @classmethod
    def _highshift_key_from_values(
        cls,
        user_id: int,
        date_start: datetime,
        date_end: datetime,
        highshift_type: str | None,
    ) -> tuple[int, datetime, datetime, str]:
        return user_id, date_start, date_end, highshift_type or "other"

    @classmethod
    def _highshift_key_from_item(cls, item: dict) -> tuple[int, datetime, datetime, str]:
        return cls._highshift_key_from_values(
            item["user_id"],
            item["date_start"],
            item["date_end"],
            cls._highshift_type(item),
        )

    @classmethod
    def _highshift_key(cls, highshift: ShiftHigh) -> tuple[int, datetime, datetime, str]:
        return cls._highshift_key_from_values(
            highshift.user_id,
            highshift.date_start,
            highshift.date_end,
            highshift.type,
        )

    @staticmethod
    def _deduplicate_items(highshifts_list: Sequence[dict]) -> dict[tuple[int, datetime, datetime, str], dict]:
        items_by_key: dict[tuple[int, datetime, datetime, str], dict] = {}

        for item in highshifts_list:
            items_by_key[ShiftsHighRepo._highshift_key_from_item(item)] = item

        return items_by_key

    @staticmethod
    def _index_existing(
        highshifts: Sequence[ShiftHigh],
    ) -> tuple[dict[tuple[int, datetime, datetime, str], ShiftHigh], list[ShiftHigh]]:
        highshifts_by_key: dict[tuple[int, datetime, datetime, str], ShiftHigh] = {}
        duplicates: list[ShiftHigh] = []

        for highshift in highshifts:
            key = ShiftsHighRepo._highshift_key(highshift)
            if key in highshifts_by_key:
                duplicates.append(highshift)
                continue

            highshifts_by_key[key] = highshift

        return highshifts_by_key, duplicates

    async def _get_existing_by_period(
        self,
        date_start: datetime,
        date_end: datetime,
        user_ids: set[int],
    ) -> list[ShiftHigh]:
        stmt = select(ShiftHigh).where(
            ShiftHigh.date_start >= date_start,
            ShiftHigh.date_start <= date_end,
        )

        if user_ids:
            stmt = stmt.where(ShiftHigh.user_id.in_(user_ids))

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_highshift(
        self,
        user_id: int,
        date_start: datetime,
        date_end: datetime,
        type: str | None = "other",
        comment: str | None = None,
    ) -> ShiftHigh:
        """Добавление или обновление смены дежурного."""

        highshift_type = type or "other"
        stmt = select(ShiftHigh).where(
            ShiftHigh.user_id == user_id,
            ShiftHigh.date_start == date_start,
            ShiftHigh.date_end == date_end,
            ShiftHigh.type == highshift_type,
        )

        result = await self.session.execute(stmt)
        existing_highshifts = list(result.scalars().all())

        if existing_highshifts:
            highshift = existing_highshifts[0]
            highshift.comment = comment

            for duplicate in existing_highshifts[1:]:
                await self.session.delete(duplicate)

            await self.session.commit()
            await self.session.refresh(highshift)
            return highshift

        highshift = ShiftHigh(
            uuid=str(uuid.uuid4()),
            user_id=user_id,
            date_start=date_start,
            date_end=date_end,
            type=highshift_type,
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
        """Добавление пачки смен дежурных без создания дублей."""

        items_by_key = self._deduplicate_items(highshifts_list)
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

        highshifts: list[ShiftHigh] = []
        for key, item in items_by_key.items():
            highshift = existing_by_key.get(key)

            if highshift is None:
                highshift = ShiftHigh(
                    user_id=item["user_id"],
                    date_start=item["date_start"],
                    date_end=item["date_end"],
                    type=self._highshift_type(item),
                    comment=item.get("comment"),
                )
                self.session.add(highshift)
            else:
                highshift.comment = item.get("comment")

            highshifts.append(highshift)

        await self.session.commit()

        for highshift in highshifts:
            await self.session.refresh(highshift)

        return highshifts

    async def sync_highshifts_by_period(
        self,
        highshifts_list: Sequence[dict],
        date_start: datetime | None = None,
        date_end: datetime | None = None,
        user_ids: Sequence[int] | None = None,
    ) -> dict[str, int]:
        """Синхронизировать старшинство/дежурство за период с новым графиком."""

        stats = {"created": 0, "updated": 0, "deleted": 0, "unchanged": 0}
        items_by_key = self._deduplicate_items(highshifts_list)
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

            highshift = existing_by_key.get(key)
            if highshift is None:
                highshift = ShiftHigh(
                    user_id=item["user_id"],
                    date_start=item["date_start"],
                    date_end=item["date_end"],
                    type=self._highshift_type(item),
                    comment=item.get("comment"),
                )
                self.session.add(highshift)
                stats["created"] += 1
                continue

            new_comment = item.get("comment")
            if highshift.comment != new_comment:
                highshift.comment = new_comment
                stats["updated"] += 1
            else:
                stats["unchanged"] += 1

        incoming_keys = {key for key in items_by_key if key[0] in target_user_ids}
        for key, highshift in existing_by_key.items():
            if key not in incoming_keys:
                await self.session.delete(highshift)
                stats["deleted"] += 1

        await self.session.commit()
        return stats

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