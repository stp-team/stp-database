"""Общий репозиторий базы Candidates."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from stp_database.repo.Candidates.candidate import CandidateRepo
from stp_database.repo.Candidates.form import FormRepo
from stp_database.repo.Candidates.message import MessageRepo
from stp_database.repo.Candidates.attachment import (
    CandidateAttachmentRepo,
)


@dataclass
class CandidatesRequestsRepo:
    """Репозитории базы Candidates."""

    session: AsyncSession

    @property
    def candidates(self) -> CandidateRepo:
        return CandidateRepo(self.session)

    @property
    def forms(self) -> FormRepo:
        return FormRepo(self.session)

    @property
    def messages(self) -> MessageRepo:
        return MessageRepo(self.session)

    @property
    def attachments(
            self,
    ) -> CandidateAttachmentRepo:
        return CandidateAttachmentRepo(
            self.session
        )