"""Репозиторий кандидатов."""

import logging
from datetime import datetime
from typing import Sequence

from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError

from stp_database.models.Candidates import Candidate
from stp_database.repo.base import BaseRepo


logger = logging.getLogger(__name__)


class CandidateRepo(BaseRepo):
    """Репозиторий для работы с кандидатами."""

    async def create_candidate(
            self,
            uuid: str,
            fullname: str | None = None,
            short_link: str | None = None,
            use_password: str | None = None,
            form_data: dict | None = None,
            created_by: int | None = None,
            status: str = "new",
    ) -> Candidate | None:
        candidate = Candidate(
            uuid=uuid,
            status=status,
            fullname=fullname,
            short_link=short_link,
            use_password=use_password,
            form_data=form_data or {},
            created_by=created_by,
            updated_by=created_by,
        )

        try:
            self.session.add(candidate)
            await self.session.commit()
            await self.session.refresh(candidate)
            return candidate

        except SQLAlchemyError as e:
            logger.error(
                f"[БД] Ошибка создания кандидата {uuid}: {e}"
            )
            await self.session.rollback()
            return None

    async def get_candidate(
        self,
        uuid: str | None = None,
        short_link: str | None = None,
    ) -> Candidate | None:
        filters = []

        if uuid:
            filters.append(Candidate.uuid == uuid)

        if short_link:
            filters.append(Candidate.short_link == short_link)

        if not filters:
            return None

        query = select(Candidate).where(or_(*filters))

        try:
            result = await self.session.execute(query)
            return result.scalar_one_or_none()

        except SQLAlchemyError as e:
            logger.error(
                f"[БД] Ошибка получения кандидата: {e}"
            )
            return None

    async def get_candidates(
        self,
        form_uuid: str | None = None,
        created_by: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Candidate]:
        filters = []

        if form_uuid:
            filters.append(Candidate.form_uuid == form_uuid)

        if created_by is not None:
            filters.append(Candidate.created_by == created_by)

        query = (
            select(Candidate)
            .where(*filters)
            .order_by(Candidate.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        try:
            result = await self.session.execute(query)
            return result.scalars().all()

        except SQLAlchemyError as e:
            logger.error(
                f"[БД] Ошибка получения списка кандидатов: {e}"
            )
            return []

    async def update_candidate(
        self,
        candidate_uuid: str,
        updated_by: int | None = None,
        **kwargs,
    ) -> Candidate | None:
        candidate = await self.get_candidate(uuid=candidate_uuid)

        if candidate is None:
            return None

        allowed_fields = {
            "status",
            "fullname",
            "short_link",
            "use_password",
            "form_uuid",
            "form_data",
            "readed_message_user_uuid",
            "readed_message_candidate_uuid",
            "assigned_hr_id",
            "assigned_rg_id",
        }

        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(candidate, key, value)

        if updated_by is not None:
            candidate.updated_by = updated_by

        candidate.updated_at = datetime.now()

        try:
            await self.session.commit()
            await self.session.refresh(candidate)

            return candidate

        except SQLAlchemyError as e:
            logger.error(
                f"[БД] Ошибка обновления кандидата "
                f"{candidate_uuid}: {e}"
            )
            await self.session.rollback()
            return None

    async def delete_candidate(
        self,
        candidate_uuid: str,
    ) -> bool:
        candidate = await self.get_candidate(
            uuid=candidate_uuid,
        )

        if candidate is None:
            return False

        try:
            await self.session.delete(candidate)
            await self.session.commit()

            return True

        except SQLAlchemyError as e:
            logger.error(
                f"[БД] Ошибка удаления кандидата "
                f"{candidate_uuid}: {e}"
            )
            await self.session.rollback()
            return False