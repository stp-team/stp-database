"""Репозиторий статей/заметок."""

import logging
from datetime import datetime
from typing import Sequence

from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError

from stp_database.models.STP.note import Note
from stp_database.repo.base import BaseRepo

logger = logging.getLogger(__name__)


class NoteRepo(BaseRepo):
    """Репозиторий для работы со статьями."""

    async def create_note(
        self,
        uuid: str,
        space_uuid: str,
        short_link: str,
        content: str,
        created_by: int,
        title: str | None = None,
        disclaimer: str | None = None,
    ) -> Note | None:
        """Создать статью."""

        note = Note(
            uuid=uuid,
            space_uuid=space_uuid,
            short_link=short_link,
            title=title,
            disclaimer=disclaimer,
            content=content,
            created_by=created_by,
        )

        try:
            self.session.add(note)
            await self.session.commit()
            await self.session.refresh(note)
            return note
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка создания статьи {uuid}: {e}")
            await self.session.rollback()
            return None

    async def get_note(
        self,
        uuid: str | None = None,
        short_link: str | None = None,
    ) -> Note | None:
        """Получить статью по uuid или short_link."""

        filters = []

        if uuid:
            filters.append(Note.uuid == uuid)

        if short_link:
            filters.append(Note.short_link == short_link)

        if not filters:
            return None

        query = select(Note).where(or_(*filters))

        try:
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка получения статьи: {e}")
            return None

    async def update_note(
        self,
        note_uuid: str,
        updated_by: int,
        **kwargs,
    ) -> Note | None:
        """Обновить статью."""

        note = await self.get_note(uuid=note_uuid)

        if not note:
            return None

        allowed_fields = {
            "title",
            "disclaimer",
            "content",
        }

        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(note, key, value)

        note.updated_by = updated_by
        note.updated_at = datetime.now()

        try:
            await self.session.commit()
            await self.session.refresh(note)
            return note
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка обновления статьи {note_uuid}: {e}")
            await self.session.rollback()
            return None

    async def delete_note(self, note_uuid: str) -> bool:
        """Удалить статью."""

        note = await self.get_note(uuid=note_uuid)

        if not note:
            return False

        try:
            await self.session.delete(note)
            await self.session.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка удаления статьи {note_uuid}: {e}")
            await self.session.rollback()
            return False

    async def get_notes_admin(
        self,
        space_uuid: str | None = None,
        created_by: int | None = None,
        uuid: str | None = None,
        short_link: str | None = None,
        limit: int = 100,
    ) -> Sequence[Note]:
        """Получить список статей для админки."""

        filters = []

        if space_uuid:
            filters.append(Note.space_uuid == space_uuid)

        if created_by:
            filters.append(Note.created_by == created_by)

        if uuid:
            filters.append(Note.uuid == uuid)

        if short_link:
            filters.append(Note.short_link == short_link)

        query = select(Note).where(*filters).limit(limit)

        try:
            result = await self.session.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка получения списка статей: {e}")
            return []