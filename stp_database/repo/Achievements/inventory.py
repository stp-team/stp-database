"""Репозиторий для работы с инвентарём наград."""

import logging
from typing import Sequence
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from stp_database.models.Achievements import Inventory
from stp_database.repo.base import BaseRepo

logger = logging.getLogger(__name__)


class InventoryRepo(BaseRepo):
    """Репозиторий для работы с инвентарём пользователей."""

    async def get_inventory(
        self,
        *,
        user_id: int | None = None,
        award_uuid: str | None = None,
        status: str | None = None,
        manager_role: int | None = None,
    ) -> Sequence[Inventory]:
        """Получить инвентарь по необязательным фильтрам."""
        stmt = select(Inventory)
        if user_id is not None:
            stmt = stmt.where(Inventory.user_id == user_id)
        if award_uuid is not None:
            stmt = stmt.where(Inventory.award_uuid == award_uuid)
        if status is not None:
            self._validate_status(status)
            stmt = stmt.where(Inventory.status == status)
        if manager_role is not None:
            stmt = stmt.where(Inventory.manager_role == manager_role)
        stmt = stmt.order_by(Inventory.bought_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_inventory_item_by_uuid(
        self,
        item_uuid: str,
    ) -> Inventory | None:
        """Получить предмет инвентаря по UUID."""
        result = await self.session.execute(
            select(Inventory).where(Inventory.uuid == item_uuid)
        )
        return result.scalar_one_or_none()

    async def create_inventory_item(
        self,
        *,
        user_id: int,
        award_uuid: str,
        remaining_uses: int,
        item_uuid: str | None = None,
        status: str = "stored",
        manager_role: int,
    ) -> Inventory:
        """Добавить предмет в инвентарь."""
        self._validate_non_negative_amount(remaining_uses)
        self._validate_status(status)
        if remaining_uses == 0 and status == "stored":
            status = "used_up"

        item = Inventory(
            uuid=item_uuid or str(uuid4()),
            user_id=user_id,
            award_uuid=award_uuid,
            remaining_uses=remaining_uses,
            status=status,
            manager_role=manager_role,
        )

        try:
            self.session.add(item)
            await self.session.commit()
            await self.session.refresh(item)
            return item
        except SQLAlchemyError:
            await self.session.rollback()
            logger.exception(
                "[БД] Ошибка добавления награды %s пользователю %s",
                award_uuid,
                user_id,
            )
            raise

    async def add_remaining_uses(
        self,
        item_uuid: str,
        amount: int,
    ) -> Inventory | None:
        """Прибавить заданное количество использований."""
        self._validate_positive_amount(amount)
        return await self._change_remaining_uses(item_uuid, amount)

    async def subtract_remaining_uses(
        self,
        item_uuid: str,
        amount: int,
    ) -> Inventory | None:
        """Убавить заданное количество использований."""
        self._validate_positive_amount(amount)
        return await self._change_remaining_uses(item_uuid, -amount)

    async def _change_remaining_uses(
        self,
        item_uuid: str,
        delta: int,
    ) -> Inventory | None:
        """Атомарно изменить остаток с блокировкой строки."""
        stmt = (
            select(Inventory)
            .where(Inventory.uuid == item_uuid)
            .with_for_update()
        )

        try:
            result = await self.session.execute(stmt)
            item = result.scalar_one_or_none()
            if item is None:
                await self.session.rollback()
                return None

            new_value = item.remaining_uses + delta
            if new_value < 0:
                raise ValueError(
                    "Недостаточно активаций: "
                    f"остаток={item.remaining_uses}, требуется={abs(delta)}"
                )

            item.remaining_uses = new_value
            item.status = "used_up" if new_value == 0 else "stored"

            await self.session.commit()
            await self.session.refresh(item)
            return item
        except SQLAlchemyError:
            await self.session.rollback()
            logger.exception(
                "[БД] Ошибка изменения remaining_uses %s на %s",
                item_uuid,
                delta,
            )
            raise
        except Exception:
            await self.session.rollback()
            raise

    @staticmethod
    def _validate_positive_amount(amount: int) -> None:
        if not isinstance(amount, int) or isinstance(amount, bool):
            raise TypeError("amount должен иметь тип int")
        if amount <= 0:
            raise ValueError("amount должен быть больше нуля")

    @staticmethod
    def _validate_non_negative_amount(amount: int) -> None:
        if not isinstance(amount, int) or isinstance(amount, bool):
            raise TypeError("remaining_uses должен иметь тип int")
        if amount < 0:
            raise ValueError("remaining_uses не может быть отрицательным")

    @staticmethod
    def _validate_status(status: str) -> None:
        if status not in {"stored", "used_up", "rollback"}:
            raise ValueError("Недопустимый status инвентаря")
