"""Репозиторий для работы с активациями наград."""

import json
import logging
from datetime import datetime
from typing import Any, Mapping, Sequence
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from stp_database.models.Achievements import Activations
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
        stmt = stmt.order_by(Activations.review_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_activation_by_uuid(
        self,
        activation_uuid: str,
    ) -> Activations | None:
        """Получить активацию по UUID."""
        result = await self.session.execute(
            select(Activations).where(Activations.uuid == activation_uuid)
        )
        return result.scalar_one_or_none()

    async def create_activation(
        self,
        *,
        award_uuid: str,
        item_uuid: str,
        item_count: int,
        form_data: Mapping[str, Any] | list[Any],
        review_by: int,
        activation_uuid: str | None = None,
        status: str = "ready",
        review_comment: str | None = None,
        review_at: datetime | None = None,
    ) -> Activations:
        """Добавить заявку на активацию награды."""
        self._validate_positive_count(item_count)
        self._validate_status(status)

        activation = Activations(
            uuid=activation_uuid or str(uuid4()),
            award_uuid=award_uuid,
            item_uuid=item_uuid,
            item_count=item_count,
            form_data=self._serialize_form_data(form_data),
            status=status,
            review_comment=review_comment,
            review_by=review_by,
        )
        if review_at is not None:
            activation.review_at = review_at

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
            raise ValueError("Необходимо передать минимум одно поле")

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
                "Недопустимые поля: " + ", ".join(sorted(invalid_fields))
            )

        result = await self.session.execute(
            select(Activations).where(Activations.uuid == activation_uuid)
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
        value = json.loads(activation.form_data or "[]")
        if not isinstance(value, (dict, list)):
            raise TypeError("form_data должен быть JSON-объектом или массивом")
        return value

    @staticmethod
    def _serialize_form_data(
        form_data: Mapping[str, Any] | list[Any],
    ) -> str:
        if not isinstance(form_data, (Mapping, list)):
            raise TypeError("form_data должен быть объектом или списком")
        value = dict(form_data) if isinstance(form_data, Mapping) else form_data
        return json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )

    @staticmethod
    def _validate_positive_count(item_count: int) -> None:
        if not isinstance(item_count, int) or isinstance(item_count, bool):
            raise TypeError("item_count должен иметь тип int")
        if item_count <= 0:
            raise ValueError("item_count должен быть больше нуля")

    @staticmethod
    def _validate_status(status: str) -> None:
        if status not in {"ready", "inprogress", "approved", "rejected"}:
            raise ValueError("Недопустимый status активации")
