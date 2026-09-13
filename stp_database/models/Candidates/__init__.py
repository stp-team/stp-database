"""Инициализация моделей базы Candidates."""

from .attachment import CandidateAttachment
from .candidate import Candidate
from .form import Form
from .message import Message


__all__ = [
    "CandidateAttachment",
    "Candidate",
    "Form",
    "Message",
]