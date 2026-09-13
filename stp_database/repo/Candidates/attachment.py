"""Репозиторий вложений кандидатов."""

import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from stp_database.models.Candidates import (
    CandidateAttachment,
)

from stp_database.repo.base import BaseRepo


logger = logging.getLogger(
    __name__
)


class CandidateAttachmentRepo(
    BaseRepo
):
    async def create_attachment(
        self,
        *,
        uuid: str,
        candidate_uuid: str,
        name: str | None,
        content_type: str,
        size: int,
        content: bytes,
    ) -> CandidateAttachment | None:
        attachment = CandidateAttachment(
            uuid=uuid,
            candidate_uuid=candidate_uuid,
            name=name,
            content_type=content_type,
            size=size,
            content=content,
        )

        try:
            self.session.add(
                attachment
            )

            await self.session.commit()

            await self.session.refresh(
                attachment
            )

            return attachment

        except SQLAlchemyError as exc:
            logger.error(
                "[БД] Ошибка создания "
                "вложения %s: %s",
                uuid,
                exc,
            )

            await self.session.rollback()

            return None

    async def get_attachment(
        self,
        *,
        uuid: str,
        candidate_uuid: str,
    ) -> CandidateAttachment | None:
        query = (
            select(
                CandidateAttachment
            )
            .where(
                CandidateAttachment.uuid
                == uuid,
                CandidateAttachment.candidate_uuid
                == candidate_uuid,
            )
        )

        try:
            result = (
                await self.session.execute(
                    query
                )
            )

            return (
                result.scalar_one_or_none()
            )

        except SQLAlchemyError as exc:
            logger.error(
                "[БД] Ошибка получения "
                "вложения %s: %s",
                uuid,
                exc,
            )

            return None