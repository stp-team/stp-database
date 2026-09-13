"""Репозитории базы Candidates."""

from .candidate import CandidateRepo
from .form import FormRepo
from .message import MessageRepo
from .requests import CandidatesRequestsRepo
from .attachment import (
    CandidateAttachmentRepo,
)

__all__ = [
    "CandidateRepo",
    "FormRepo",
    "MessageRepo",
    "CandidatesRequestsRepo",
    "CandidateAttachmentRepo",
]