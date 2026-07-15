"""Репозиторий для работы с наградами."""

import json
import logging
from datetime import datetime
from typing import Any, Mapping, Sequence

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError

from stp_database.models.Achievements import Awards
from stp_database.repo.base import BaseRepo

logger = logging.getLogger(__name__)

ALLOWED_ACTIVATION_FIELD_TYPES = {
    "date",
    "text",
    "int",
    "time",
    "datetime",
}


class AwardsRepo(BaseRepo):
    """Репозиторий для работы с наградами."""

    async def get_awards(self) -> Sequence[Awards]:
        """Получить список всех наград."""
        stmt = select(Awards).order_by(Awards.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_award_by_uuid(self, award_uuid: str) -> Awards | None:
        """Получить награду по UUID."""
        stmt = select(Awards).where(Awards.uuid == award_uuid)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_award(
        self,
        *,
        uuid: str,
        created_by: int,
        name: str = "Новая награда",
        description: str | None = "Новая награда",
        divisions: list[Any] | None = None,
        positions: list[Any] | None = None,
        cost: int = 1,
        count: int = 1,
        activations_rules: Mapping[str, Any] | None = None,
        activation_form_example: list[Mapping[str, Any]] | None = None,
        manager_role: int = 0,
        status: str = "unactive",
    ) -> Awards:
        """Создать награду."""
        self._validate_non_negative_int(cost, "cost")
        self._validate_positive_int(count, "count")
        self._validate_status(status)

        award = Awards(
            uuid=uuid,
            name=name,
            description=description,
            divisions=self._serialize_list(divisions or [], "divisions"),
            positions=self._serialize_list(positions or [], "positions"),
            cost=cost,
            count=count,
            activations_rules=self._serialize_activations_rules(
                activations_rules or {}
            ),
            activation_form_example=self._serialize_activation_form_example(
                activation_form_example or []
            ),
            manager_role=manager_role,
            status=status,
            created_by=created_by,
        )

        try:
            self.session.add(award)
            await self.session.commit()
            await self.session.refresh(award)
            return award
        except SQLAlchemyError:
            await self.session.rollback()
            logger.exception("[БД] Ошибка создания награды %s", uuid)
            raise

    async def update_award(
        self,
        award_uuid: str,
        **changes: Any,
    ) -> Awards | None:
        """Обновить награду по UUID."""
        if not changes:
            raise ValueError("Необходимо передать минимум одно поле")

        allowed_fields = {
            "name",
            "description",
            "divisions",
            "positions",
            "cost",
            "count",
            "activations_rules",
            "activation_form_example",
            "manager_role",
            "status",
            "updated_by",
        }
        invalid_fields = set(changes) - allowed_fields
        if invalid_fields:
            raise ValueError(
                "Недопустимые поля: " + ", ".join(sorted(invalid_fields))
            )

        result = await self.session.execute(
            select(Awards).where(Awards.uuid == award_uuid)
        )
        award = result.scalar_one_or_none()
        if award is None:
            return None

        if "cost" in changes:
            self._validate_non_negative_int(changes["cost"], "cost")
        if "count" in changes:
            self._validate_positive_int(changes["count"], "count")
        if "status" in changes:
            self._validate_status(changes["status"])
        if "divisions" in changes:
            changes["divisions"] = self._serialize_list(
                changes["divisions"] or [], "divisions"
            )
        if "positions" in changes:
            changes["positions"] = self._serialize_list(
                changes["positions"] or [], "positions"
            )
        if "activations_rules" in changes:
            changes["activations_rules"] = self._serialize_activations_rules(
                changes["activations_rules"] or {}
            )
        if "activation_form_example" in changes:
            changes["activation_form_example"] = (
                self._serialize_activation_form_example(
                    changes["activation_form_example"] or []
                )
            )

        for field, value in changes.items():
            setattr(award, field, value)
        award.updated_at = datetime.now()

        try:
            await self.session.commit()
            await self.session.refresh(award)
            return award
        except SQLAlchemyError:
            await self.session.rollback()
            logger.exception("[БД] Ошибка обновления награды %s", award_uuid)
            raise

    async def delete_award(self, award_uuid: str) -> bool:
        """Удалить награду по UUID."""
        try:
            result = await self.session.execute(
                delete(Awards).where(Awards.uuid == award_uuid)
            )
            if result.rowcount == 0:
                await self.session.rollback()
                return False
            await self.session.commit()
            return True
        except SQLAlchemyError:
            await self.session.rollback()
            logger.exception("[БД] Ошибка удаления награды %s", award_uuid)
            raise

    @staticmethod
    def deserialize_activations_rules(award: Awards) -> dict[str, Any]:
        value = json.loads(award.activations_rules or "{}")
        if not isinstance(value, dict):
            raise TypeError("activations_rules должен содержать JSON-объект")
        return value

    @staticmethod
    def deserialize_activation_form_example(
        award: Awards,
    ) -> list[dict[str, Any]]:
        value = json.loads(award.activation_form_example or "[]")
        if not isinstance(value, list):
            raise TypeError(
                "activation_form_example должен содержать JSON-массив"
            )
        return value

    @staticmethod
    def _serialize_activations_rules(rules: Mapping[str, Any]) -> str:
        if not isinstance(rules, Mapping):
            raise TypeError("activations_rules должен быть объектом")
        return json.dumps(
            dict(rules),
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )

    @staticmethod
    def _serialize_activation_form_example(
        fields: list[Mapping[str, Any]],
    ) -> str:
        if not isinstance(fields, list):
            raise TypeError("activation_form_example должен быть списком")

        normalized: list[dict[str, Any]] = []
        for index, field in enumerate(fields):
            if not isinstance(field, Mapping):
                raise TypeError(f"Поле формы {index} должно быть объектом")

            label = field.get("label")
            field_type = field.get("type")
            if not isinstance(label, str) or not label.strip():
                raise ValueError(f"У поля формы {index} отсутствует label")
            if field_type not in ALLOWED_ACTIVATION_FIELD_TYPES:
                raise ValueError(
                    f"Недопустимый тип {field_type!r}. Допустимо: "
                    + ", ".join(sorted(ALLOWED_ACTIVATION_FIELD_TYPES))
                )
            normalized.append(dict(field))

        return json.dumps(
            normalized,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )

    @staticmethod
    def _serialize_list(value: list[Any], field_name: str) -> str:
        if not isinstance(value, list):
            raise TypeError(f"{field_name} должен быть списком")
        return json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )

    @staticmethod
    def _validate_positive_int(value: Any, field_name: str) -> None:
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(f"{field_name} должен иметь тип int")
        if value <= 0:
            raise ValueError(f"{field_name} должен быть больше нуля")

    @staticmethod
    def _validate_non_negative_int(value: Any, field_name: str) -> None:
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(f"{field_name} должен иметь тип int")
        if value < 0:
            raise ValueError(f"{field_name} не может быть отрицательным")

    @staticmethod
    def _validate_status(status: str) -> None:
        if status not in {"unactive", "active"}:
            raise ValueError("status должен быть unactive или active")
