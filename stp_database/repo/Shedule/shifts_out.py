"""Репозиторий функций для работы с нерабочими сменами."""

import uuid
from datetime import date, datetime, time
from typing import Sequence

from sqlalchemy import delete, select

from stp_database.models.Shedule import ShiftOut
from stp_database.repo.base import BaseRepo


class ShiftsOutRepo(BaseRepo):
    """Репозиторий с функциями для работы с нерабочими сменами."""

    @staticmethod
    def _outshift_type(item: dict) -> str:
        return item.get("type") or "other"

    @classmethod
    def _outshift_key_from_values(
        cls,
        user_id: int,
        outshift_date: date | datetime,
        outshift_type: str | None,
    ) -> tuple[int, date | datetime, str]:
        return user_id, outshift_date, outshift_type or "other"

    @classmethod
    def _outshift_key_from_item(cls, item: dict) -> tuple[int, date | datetime, str]:
        return cls._outshift_key_from_values(
            item["user_id"],
            item["date"],
            cls._outshift_type(item),
        )

    @classmethod
    def _outshift_key(cls, outshift: ShiftOut) -> tuple[int, date | datetime, str]:
        return cls._outshift_key_from_values(
            outshift.user_id,
            outshift.date,
            outshift.type,
        )

    @staticmethod
    def _deduplicate_items(outshifts_list: Sequence[dict]) -> dict[tuple[int, date | datetime, str], dict]:
        items_by_key: dict[tuple[int, date | datetime, str], dict] = {}

        for item in outshifts_list:
            items_by_key[ShiftsOutRepo._outshift_key_from_item(item)] = item

        return items_by_key

    @staticmethod
    def _index_existing(
        outshifts: Sequence[ShiftOut],
    ) -> tuple[dict[tuple[int, date | datetime, str], ShiftOut], list[ShiftOut]]:
        outshifts_by_key: dict[tuple[int, date | datetime, str], ShiftOut] = {}
        duplicates: list[ShiftOut] = []

        for outshift in outshifts:
            key = ShiftsOutRepo._outshift_key(outshift)
            if key in outshifts_by_key:
                duplicates.append(outshift)
                continue

            outshifts_by_key[key] = outshift

        return outshifts_by_key, duplicates

    async def _get_existing_by_period(
        self,
        date_start: date | datetime,
        date_end: date | datetime,
        user_ids: set[int],
    ) -> list[ShiftOut]:
        stmt = select(ShiftOut).where(
            ShiftOut.date >= date_start,
            ShiftOut.date <= date_end,
        )

        if user_ids:
            stmt = stmt.where(ShiftOut.user_id.in_(user_ids))

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_outshift(
        self,
        user_id: int,
        date: date,
        type: str | None = "other",
        comment: str | None = None,
    ) -> ShiftOut:
        """Добавление или обновление нерабочей смены."""

        outshift_type = type or "other"
        stmt = select(ShiftOut).where(
            ShiftOut.user_id == user_id,
            ShiftOut.date == date,
            ShiftOut.type == outshift_type,
        )

        result = await self.session.execute(stmt)
        existing_outshifts = list(result.scalars().all())

        if existing_outshifts:
            outshift = existing_outshifts[0]
            outshift.comment = comment

            for duplicate in existing_outshifts[1:]:
                await self.session.delete(duplicate)

            await self.session.commit()
            await self.session.refresh(outshift)
            return outshift

        outshift = ShiftOut(
            uuid=str(uuid.uuid4()),
            user_id=user_id,
            date=date,
            type=outshift_type,
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
        """Добавление пачки нерабочих смен без создания дублей."""

        items_by_key = self._deduplicate_items(outshifts_list)
        if not items_by_key:
            return []

        items = list(items_by_key.values())
        user_ids = {item["user_id"] for item in items}
        period_start = min(item["date"] for item in items)
        period_end = max(item["date"] for item in items)

        existing = await self._get_existing_by_period(period_start, period_end, user_ids)
        existing_by_key, duplicates = self._index_existing(existing)

        for duplicate in duplicates:
            await self.session.delete(duplicate)

        outshifts: list[ShiftOut] = []
        for key, item in items_by_key.items():
            outshift = existing_by_key.get(key)

            if outshift is None:
                outshift = ShiftOut(
                    user_id=item["user_id"],
                    date=item["date"],
                    type=self._outshift_type(item),
                    comment=item.get("comment"),
                )
                self.session.add(outshift)
            else:
                outshift.comment = item.get("comment")

            outshifts.append(outshift)

        await self.session.commit()

        for outshift in outshifts:
            await self.session.refresh(outshift)

        return outshifts

    async def sync_outshifts_by_period(
        self,
        outshifts_list: Sequence[dict],
        date_start: date | datetime | None = None,
        date_end: date | datetime | None = None,
        user_ids: Sequence[int] | None = None,
    ) -> dict[str, int]:
        """Синхронизировать отпуска/больничные/прогулы за период с новым графиком."""

        stats = {"created": 0, "updated": 0, "deleted": 0, "unchanged": 0}
        items_by_key = self._deduplicate_items(outshifts_list)
        items = list(items_by_key.values())

        target_user_ids = set(user_ids or [item["user_id"] for item in items])
        if not target_user_ids:
            return stats

        if date_start is None:
            if not items:
                return stats
            date_start = min(item["date"] for item in items)

        if date_end is None:
            if not items:
                return stats
            date_end = max(item["date"] for item in items)

        existing = await self._get_existing_by_period(date_start, date_end, target_user_ids)
        existing_by_key, duplicates = self._index_existing(existing)

        for duplicate in duplicates:
            await self.session.delete(duplicate)
            stats["deleted"] += 1

        for key, item in items_by_key.items():
            if key[0] not in target_user_ids:
                continue

            outshift = existing_by_key.get(key)
            if outshift is None:
                outshift = ShiftOut(
                    user_id=item["user_id"],
                    date=item["date"],
                    type=self._outshift_type(item),
                    comment=item.get("comment"),
                )
                self.session.add(outshift)
                stats["created"] += 1
                continue

            new_comment = item.get("comment")
            if outshift.comment != new_comment:
                outshift.comment = new_comment
                stats["updated"] += 1
            else:
                stats["unchanged"] += 1

        incoming_keys = {key for key in items_by_key if key[0] in target_user_ids}
        for key, outshift in existing_by_key.items():
            if key not in incoming_keys:
                await self.session.delete(outshift)
                stats["deleted"] += 1

        await self.session.commit()
        return stats

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