"""Репозиторий форм кандидатов."""

import logging
from datetime import datetime
from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from stp_database.models.Candidates import Form
from stp_database.repo.base import BaseRepo


logger = logging.getLogger(__name__)


class FormRepo(BaseRepo):
    """Репозиторий для работы с формами."""

    async def create_form(
        self,
        uuid: str,
        name: str | None,
        content: str | None,
        created_by: int | None = None,
    ) -> Form | None:
        form = Form(
            uuid=uuid,
            name=name,
            content=content,
            created_by=created_by,
            updated_by=created_by,
        )

        try:
            self.session.add(form)
            await self.session.commit()
            await self.session.refresh(form)

            return form

        except SQLAlchemyError as e:
            logger.error(
                f"[БД] Ошибка создания формы {uuid}: {e}"
            )
            await self.session.rollback()
            return None

    async def set_default_form(
            self,
            form_uuid: str,
            updated_by: int | None = None,
    ) -> Form | None:
        form = await self.get_form(
            form_uuid
        )

        if form is None:
            return None

        try:
            # -------------------------------------------------
            # Все остальные формы перестают
            # быть формой по умолчанию.
            # -------------------------------------------------

            await self.session.execute(
                update(Form)
                .where(
                    Form.uuid != form_uuid
                )
                .values(
                    is_default=False
                )
            )

            # -------------------------------------------------
            # Выбранная становится default.
            # -------------------------------------------------

            form.is_default = True

            if updated_by is not None:
                form.updated_by = (
                    updated_by
                )

            form.updated_at = (
                datetime.now()
            )

            # -------------------------------------------------
            # Всё фиксируем одним commit.
            # -------------------------------------------------

            await self.session.commit()

            await self.session.refresh(
                form
            )

            return form

        except SQLAlchemyError as e:
            logger.error(
                "[БД] Ошибка назначения "
                "формы по умолчанию "
                f"{form_uuid}: {e}"
            )

            await self.session.rollback()

            return None

    async def get_form(
        self,
        uuid: str,
    ) -> Form | None:
        query = select(Form).where(Form.uuid == uuid)

        try:
            result = await self.session.execute(query)
            return result.scalar_one_or_none()

        except SQLAlchemyError as e:
            logger.error(
                f"[БД] Ошибка получения формы {uuid}: {e}"
            )
            return None

    async def get_default_form(
            self,
    ) -> Form | None:
        query = (
            select(Form)
            .where(
                Form.is_default.is_(True)
            )
            .order_by(
                Form.updated_at.desc()
            )
            .limit(1)
        )

        try:
            result = (
                await self.session.execute(
                    query
                )
            )

            return (
                result.scalars().first()
            )

        except SQLAlchemyError as e:
            logger.error(
                "[БД] Ошибка получения "
                f"формы по умолчанию: {e}"
            )

            return None

    async def get_forms(
        self,
        created_by: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Form]:
        filters = []

        if created_by is not None:
            filters.append(Form.created_by == created_by)

        query = (
            select(Form)
            .where(*filters)
            .order_by(Form.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        try:
            result = await self.session.execute(query)
            return result.scalars().all()

        except SQLAlchemyError as e:
            logger.error(
                f"[БД] Ошибка получения списка форм: {e}"
            )
            return []

    async def update_form(
        self,
        form_uuid: str,
        updated_by: int | None = None,
        **kwargs,
    ) -> Form | None:
        form = await self.get_form(form_uuid)

        if form is None:
            return None

        allowed_fields = {
            "name",
            "content",
        }

        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(form, key, value)

        form.updated_by = updated_by
        form.updated_at = datetime.now()

        try:
            await self.session.commit()
            await self.session.refresh(form)

            return form

        except SQLAlchemyError as e:
            logger.error(
                f"[БД] Ошибка обновления формы "
                f"{form_uuid}: {e}"
            )
            await self.session.rollback()
            return None

    async def delete_form(
        self,
        form_uuid: str,
    ) -> bool:
        form = await self.get_form(form_uuid)

        if form is None:
            return False

        try:
            await self.session.delete(form)
            await self.session.commit()

            return True

        except SQLAlchemyError as e:
            logger.error(
                f"[БД] Ошибка удаления формы "
                f"{form_uuid}: {e}"
            )
            await self.session.rollback()
            return False