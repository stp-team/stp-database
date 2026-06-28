"""Репозитории Note."""

from stp_database.repo.Note.note import NoteRepo
from stp_database.repo.Note.space import SpaceRepo
from stp_database.repo.Note.requests import NoteRequestsRepo

__all__ = [
    "NoteRepo",
    "SpaceRepo",
    "NoteRequestsRepo",
]