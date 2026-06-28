"""Агрегатор репозиториев Note."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from stp_database.repo.Note.note import NoteRepo
from stp_database.repo.Note.space import SpaceRepo


@dataclass
class NoteRequestsRepo:
    """Репозиторий для обработки операций с БД Note."""

    session: AsyncSession

    @property
    def space(self) -> SpaceRepo:
        return SpaceRepo(self.session)

    @property
    def note(self) -> NoteRepo:
        return NoteRepo(self.session)