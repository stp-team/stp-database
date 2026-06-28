"""Репозиторий пространств блокнота."""

import logging
from typing import Sequence

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import SQLAlchemyError

from stp_database.models.Note.space import Space, SpaceType, SpaceVisibility
from stp_database.models.Note.space_participant import SpaceParticipant, SpaceParticipantRole
from stp_database.repo.base import BaseRepo

logger = logging.getLogger(__name__)

class SpaceRepo(BaseRepo):
    """Репозиторий для работы с пространствами."""

    async def create_space(
            self,
            uuid: str,
            short_name: str,
            text_name: str,
            space_type: SpaceType,
            visibility: SpaceVisibility,
            user_id: int,
    ) -> Space | None:
        """Создать пространство и добавить создателя как owner."""

        space = Space(
            uuid=uuid,
            short_name=short_name,
            text_name=text_name,
            type=space_type,
            visibility=visibility,
            owned_by=user_id,
            created_by=user_id,
        )

        participant = SpaceParticipant(
            user_id=user_id,
            space_uuid=uuid,
            role=SpaceParticipantRole.owner,
            can_notify=True,
            accession_by=user_id,
        )

        try:
            self.session.add(space)
            self.session.add(participant)
            await self.session.commit()
            await self.session.refresh(space)
            return space
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка создания пространства {short_name}: {e}")
            await self.session.rollback()
            return None

    async def get_space(
            self,
            uuid: str | None = None,
            short_name: str | None = None,
    ) -> Space | None:
        """Получить пространство по uuid или short_name."""

        filters = []

        if uuid:
            filters.append(Space.uuid == uuid)

        if short_name:
            filters.append(Space.short_name == short_name)

        if not filters:
            return None

        query = select(Space).where(or_(*filters))

        try:
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка получения пространства: {e}")
            return None

    async def search_spaces(
            self,
            query_text: str,
            user_id: int | None = None,
            limit: int = 50,
    ) -> Sequence[Space]:
        """Поиск пространств по short_name или text_name."""

        query_text = query_text.strip()

        if not query_text:
            return []

        filters = [
            or_(
                Space.short_name.ilike(f"%{query_text}%"),
                Space.text_name.ilike(f"%{query_text}%"),
            )
        ]

        # Public - Доступно всем
        # Private - Доступно не всем
        query = select(Space).where(*filters).limit(limit)

        try:
            result = await self.session.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка поиска пространств: {e}")
            return []

    async def update_space(
        self,
        space_uuid: str,
        **kwargs,
    ) -> Space | None:
        """Обновить пространство по uuid."""

        space = await self.get_space(uuid=space_uuid)

        if not space:
            return None

        allowed_fields = {
            "short_name",
            "text_name",
            "visibility",
            "type",
            "owned_by",
        }

        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(space, key, value)

        try:
            await self.session.commit()
            await self.session.refresh(space)
            return space
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка обновления пространства {space_uuid}: {e}")
            await self.session.rollback()
            return None

    async def delete_space(self, space_uuid: str) -> bool:
        """Удалить пространство.

        Связанные notes и spaces_participants удалятся через ON DELETE CASCADE.
        """

        space = await self.get_space(uuid=space_uuid)

        if not space:
            return False

        try:
            await self.session.delete(space)
            await self.session.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка удаления пространства {space_uuid}: {e}")
            await self.session.rollback()
            return False

    async def get_participant(
        self,
        space_uuid: str,
        user_id: int,
    ) -> SpaceParticipant | None:
        """Получить участника пространства."""

        query = select(SpaceParticipant).where(
            and_(
                SpaceParticipant.space_uuid == space_uuid,
                SpaceParticipant.user_id == user_id,
            )
        )

        try:
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка получения участника пространства: {e}")
            return None

    async def join_space(
        self,
        space_uuid: str,
        user_id: int,
        accession_by: int | None = None,
        role: SpaceParticipantRole = SpaceParticipantRole.viewer,
    ) -> SpaceParticipant | None:
        """Присоединиться к пространству."""

        current = await self.get_participant(space_uuid=space_uuid, user_id=user_id)

        if current:
            return current

        real_accession_by = accession_by if accession_by is not None else user_id

        participant = SpaceParticipant(
            user_id=user_id,
            space_uuid=space_uuid,
            role=role,
            can_notify=False,
            accession_by=real_accession_by,
        )

        try:
            self.session.add(participant)
            await self.session.commit()
            await self.session.refresh(participant)
            return participant
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка присоединения к пространству {space_uuid}: {e}")
            await self.session.rollback()
            return None

    async def leave_space(
        self,
        space_uuid: str,
        user_id: int,
    ) -> bool:
        """Отсоединиться от пространства."""

        participant = await self.get_participant(space_uuid=space_uuid, user_id=user_id)

        if not participant:
            return False

        try:
            await self.session.delete(participant)
            await self.session.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка выхода из пространства {space_uuid}: {e}")
            await self.session.rollback()
            return False

    async def set_notifications(
        self,
        space_uuid: str,
        user_id: int,
        can_notify: bool,
    ) -> SpaceParticipant | None:
        """Включить или выключить уведомления."""

        participant = await self.get_participant(space_uuid=space_uuid, user_id=user_id)

        if not participant:
            return None

        participant.can_notify = can_notify

        try:
            await self.session.commit()
            await self.session.refresh(participant)
            return participant
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка изменения уведомлений {space_uuid}: {e}")
            await self.session.rollback()
            return None

    async def get_spaces_admin(
        self,
        short_name: str | None = None,
        text_name: str | None = None,
        visibility: SpaceVisibility | None = None,
        space_type: SpaceType | None = None,
        owned_by: int | None = None,
        limit: int = 100,
    ) -> Sequence[Space]:
        """Получить список пространств для админки."""

        filters = []

        if short_name:
            filters.append(Space.short_name.ilike(f"%{short_name}%"))

        if text_name:
            filters.append(Space.text_name.ilike(f"%{text_name}%"))

        if visibility:
            filters.append(Space.visibility == visibility)

        if space_type:
            filters.append(Space.type == space_type)

        if owned_by:
            filters.append(Space.owned_by == owned_by)

        query = select(Space).where(*filters).limit(limit)

        try:
            result = await self.session.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка получения списка пространств: {e}")
            return []