"""Репозиторий для работы с активациями наград."""

import json
import logging
from datetime import datetime
from typing import Any, Mapping, Sequence
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from stp_database.models.Achievements import Activations, Inventory
from stp_database.repo.base import BaseRepo

logger = logging.getLogger(__name__)


class ActivationsRepo(BaseRepo):
    """Репозиторий для работы с заявками на активацию."""

    async def get_activations(
        self,
        *,
        award_uuid: str | None = None,
        item_uuid: str | None = None,
        status: str | None = None,
        review_by: int | None = None,
        created_by: int | list[int] | None = None,
        limit: int | None = None,
    ) -> Sequence[Activations]:
        """Получить активации по необязательным фильтрам."""
        stmt = select(Activations)

        if award_uuid is not None:
            stmt = stmt.where(Activations.award_uuid == award_uuid)
        if item_uuid is not None:
            stmt = stmt.where(Activations.item_uuid == item_uuid)
        if status is not None:
            self._validate_status(status)
            stmt = stmt.where(Activations.status == status)
        if review_by is not None:
            stmt = stmt.where(Activations.review_by == review_by)
        if isinstance(created_by, int):
            stmt = stmt.where(
                Activations.created_by == created_by
            )
        elif created_by:
            stmt = stmt.where(
                Activations.created_by.in_(created_by)
            )

        stmt = stmt.order_by(Activations.created_at.desc())

        if limit is not None:
            if limit <= 0:
                raise ValueError("Limit должен быть больше 0")

            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)

        return result.scalars().all()

    async def get_queue_activations(
            self,
            *,
            manager_role: int | None = None,
            status: str | None = None,
    ) -> Sequence[Activations]:
        """Получить очередь заявок по роли ответственного."""

        stmt = select(Activations)

        if manager_role is not None:
            stmt = stmt.where(
                Activations.manager_role == manager_role
            )

        if status is not None:
            self._validate_status(status)
            stmt = stmt.where(
                Activations.status == status
            )

        stmt = stmt.order_by(
            Activations.created_at.asc()
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_history_activations(
            self,
            *,
            review_at_from: datetime,
            manager_role: int | None = None,
            award_uuid: str | None = None,
    ) -> Sequence[Activations]:
        """Получить историю заявок за последние 30 дней. Статусы approved, rejected, rollback, inprogress"""
        stmt = select(Activations).where(
            Activations.status.in_(("approved", "rejected", "rollback", "inprogress")),
            Activations.review_at.is_not(None),
            Activations.review_at >= review_at_from,
        )

        if manager_role is not None:
            stmt = stmt.where(Activations.manager_role == manager_role)

        if award_uuid is not None:
            stmt = stmt.where(Activations.award_uuid == award_uuid)

        stmt = stmt.order_by(
            Activations.review_at.desc(),
            Activations.created_at.desc(),
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_activation_by_uuid(
        self,
        activation_uuid: str,
    ) -> Activations | None:
        """Получить активацию по UUID."""
        result = await self.session.execute(
            select(Activations).where(
                Activations.uuid == activation_uuid
            )
        )
        return result.scalar_one_or_none()

    async def create_activation_from_inventory(
        self,
        *,
        user_id: int,
        item_uuid: str,
        item_count: int,
        manager_role: int,
        form_data: list[Mapping[str, Any]],
        created_by: int,
        activation_uuid: str | None = None,
    ) -> Activations:
        """
        Создать активацию и списать uses в одной транзакции.

        Строка inventory блокируется через SELECT FOR UPDATE, поэтому две
        параллельные заявки не смогут списать один и тот же остаток.
        """
        self._validate_positive_count(item_count)

        inventory_stmt = (
            select(Inventory)
            .where(
                Inventory.uuid == item_uuid,
                Inventory.user_id == user_id,
            )
            .with_for_update()
        )

        try:
            inventory_result = await self.session.execute(
                inventory_stmt
            )
            item = inventory_result.scalar_one_or_none()

            if item is None:
                raise LookupError("Inventory item not found")

            if item.status == "rollback":
                raise ValueError(
                    "Inventory item is unavailable for activation"
                )

            if item.remaining_uses < item_count:
                raise ValueError(
                    "Недостаточно доступных активаций: "
                    f"остаток={item.remaining_uses}, "
                    f"запрошено={item_count}"
                )

            item.remaining_uses -= item_count
            item.status = (
                "used_up"
                if item.remaining_uses == 0
                else "stored"
            )

            activation = Activations(
                uuid=activation_uuid or str(uuid4()),
                award_uuid=item.award_uuid,
                manager_role=manager_role,
                item_uuid=item.uuid,
                item_count=item_count,
                form_data=self._serialize_form_data(form_data),
                status="ready",
                review_comment=None,
                created_by=created_by,
            )

            self.session.add(activation)
            await self.session.commit()
            await self.session.refresh(activation)

            return activation

        except Exception:
            await self.session.rollback()
            logger.exception(
                "[БД] Ошибка создания активации из inventory %s",
                item_uuid,
            )
            raise

    async def rollback_activation(
        self,
        *,
        activation_uuid: str,
        user_id: int,
    ) -> tuple[Activations, Inventory]:
        """
        Отозвать ready-активацию и вернуть uses в inventory.

        Активация и строка inventory блокируются и изменяются в одной
        транзакции.
        """
        activation_stmt = (
            select(Activations)
            .where(Activations.uuid == activation_uuid)
            .with_for_update()
        )

        try:
            activation_result = await self.session.execute(
                activation_stmt
            )
            activation = activation_result.scalar_one_or_none()

            if activation is None:
                raise LookupError("Activation not found")

            if activation.status != "ready":
                raise ValueError(
                    "Отозвать можно только активацию со статусом ready"
                )

            inventory_stmt = (
                select(Inventory)
                .where(
                    Inventory.uuid == activation.item_uuid,
                    Inventory.user_id == user_id,
                )
                .with_for_update()
            )
            inventory_result = await self.session.execute(
                inventory_stmt
            )
            item = inventory_result.scalar_one_or_none()

            if item is None:
                raise LookupError("Inventory item not found")

            item.remaining_uses += activation.item_count
            item.status = "stored"
            activation.status = "rollback"
            activation.review_at = datetime.now()

            await self.session.commit()
            await self.session.refresh(activation)
            await self.session.refresh(item)

            return activation, item

        except Exception:
            await self.session.rollback()
            logger.exception(
                "[БД] Ошибка отзыва активации %s",
                activation_uuid,
            )
            raise

    async def reject_activation(
            self,
            *,
            activation_uuid: str,
            review_by: int,
            review_comment: str,
    ) -> tuple[Activations, Inventory]:
        """
        Отклонить активацию и вернуть uses в inventory.

        Активация и строка inventory блокируются и изменяются
        в одной транзакции.
        """
        normalized_comment = review_comment.strip()

        if not normalized_comment:
            raise ValueError(
                "При отклонении заявки необходимо указать комментарий"
            )

        activation_stmt = (
            select(Activations)
            .where(
                Activations.uuid == activation_uuid
            )
            .with_for_update()
        )

        try:
            activation_result = await self.session.execute(
                activation_stmt
            )
            activation = activation_result.scalar_one_or_none()

            if activation is None:
                raise LookupError("Activation not found")

            if activation.status not in {
                "ready",
                "inprogress",
            }:
                raise ValueError(
                    "Отклонить можно только заявку "
                    "со статусом ready или inprogress"
                )

            inventory_stmt = (
                select(Inventory)
                .where(
                    Inventory.uuid == activation.item_uuid,
                    Inventory.user_id == activation.created_by,
                )
                .with_for_update()
            )

            inventory_result = await self.session.execute(
                inventory_stmt
            )
            item = inventory_result.scalar_one_or_none()

            if item is None:
                raise LookupError("Inventory item not found")

            item.remaining_uses += activation.item_count
            item.status = "stored"

            activation.status = "rejected"
            activation.review_comment = normalized_comment
            activation.review_at = datetime.now()
            activation.review_by = review_by

            await self.session.commit()
            await self.session.refresh(activation)
            await self.session.refresh(item)

            return activation, item

        except Exception:
            await self.session.rollback()
            logger.exception(
                "[БД] Ошибка отклонения активации %s",
                activation_uuid,
            )
            raise

    async def create_activation(
        self,
        *,
        award_uuid: str,
        item_uuid: str,
        item_count: int,
        manager_role: int,
        form_data: Mapping[str, Any] | list[Any],
        activation_uuid: str | None = None,
        status: str = "ready",
        created_by: int,
    ) -> Activations:
        """Добавить заявку на активацию награды."""
        self._validate_positive_count(item_count)
        self._validate_status(status)

        activation = Activations(
            uuid=activation_uuid or str(uuid4()),
            award_uuid=award_uuid,
            manager_role=manager_role,
            item_uuid=item_uuid,
            item_count=item_count,
            form_data=self._serialize_form_data(form_data),
            status=status,
            created_by=created_by,
        )

        # if review_at is not None:
        #     activation.review_at = review_at

        try:
            self.session.add(activation)
            await self.session.commit()
            await self.session.refresh(activation)
            return activation
        except SQLAlchemyError:
            await self.session.rollback()
            logger.exception(
                "[БД] Ошибка создания активации %s для %s",
                award_uuid,
                item_uuid,
            )
            raise

    async def update_activation(
        self,
        activation_uuid: str,
        **changes: Any,
    ) -> Activations | None:
        """Обновить заявку на активацию по UUID."""
        if not changes:
            raise ValueError(
                "Необходимо передать минимум одно поле"
            )

        allowed_fields = {
            "item_count",
            "form_data",
            "status",
            "review_comment",
            "review_at",
            "review_by",
        }
        invalid_fields = set(changes) - allowed_fields

        if invalid_fields:
            raise ValueError(
                "Недопустимые поля: "
                + ", ".join(sorted(invalid_fields))
            )

        result = await self.session.execute(
            select(Activations).where(
                Activations.uuid == activation_uuid
            )
        )
        activation = result.scalar_one_or_none()

        if activation is None:
            return None

        if "item_count" in changes:
            self._validate_positive_count(changes["item_count"])
        if "status" in changes:
            self._validate_status(changes["status"])
        if "form_data" in changes:
            changes["form_data"] = self._serialize_form_data(
                changes["form_data"]
            )

        for field, value in changes.items():
            setattr(activation, field, value)

        try:
            await self.session.commit()
            await self.session.refresh(activation)
            return activation
        except SQLAlchemyError:
            await self.session.rollback()
            logger.exception(
                "[БД] Ошибка обновления активации %s",
                activation_uuid,
            )
            raise

    @staticmethod
    def deserialize_form_data(
        activation: Activations,
    ) -> Mapping[str, Any] | list[Any]:
        """Десериализовать form_data."""
        value = json.loads(activation.form_data or "[]")

        if not isinstance(value, (dict, list)):
            raise TypeError(
                "form_data должен быть JSON-объектом или массивом"
            )

        return value

    @staticmethod
    def _serialize_form_data(
        form_data: Mapping[str, Any] | list[Any],
    ) -> str:
        """Сериализовать form_data."""
        if not isinstance(form_data, (Mapping, list)):
            raise TypeError(
                "form_data должен быть объектом или списком"
            )

        value = (
            dict(form_data)
            if isinstance(form_data, Mapping)
            else form_data
        )

        return json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )

    @staticmethod
    def _validate_positive_count(item_count: int) -> None:
        if (
            not isinstance(item_count, int)
            or isinstance(item_count, bool)
        ):
            raise TypeError("item_count должен иметь тип int")

        if item_count <= 0:
            raise ValueError(
                "item_count должен быть больше нуля"
            )

    @staticmethod
    def _validate_status(status: str) -> None:
        if status not in {
            "ready",
            "inprogress",
            "approved",
            "rejected",
            "rollback",
        }:
            raise ValueError(
                "Недопустимый status активации"
            )