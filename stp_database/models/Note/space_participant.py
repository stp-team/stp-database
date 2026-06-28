"""Модель участника пространств."""

from datetime import datetime
from enum import Enum

from sqlalchemy import BIGINT, Boolean, DateTime, Enum as SqlEnum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from stp_database.models.base import Base

class SpaceParticipantRole(str, Enum):
    """Роль участника пространства."""

    viewer = "viewer"
    editor = "editor"
    admin = "admin"
    owner = "owner"

class SpaceParticipant(Base):
    """Участник пространства."""

    __tablename__ = "spaces_participants"

    __table_args__ = (
        UniqueConstraint('user_id', 'space_uuid', name='uq_space_participant'),
        {
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    user_id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    space_uuid: Mapped[str] = mapped_column(
        String(250),
        ForeignKey("spaces.uuid", ondelete="CASCADE"),
        primary_key=True,
    )

    role: Mapped[SpaceParticipantRole] = mapped_column(
        SqlEnum(SpaceParticipantRole),
        nullable=False,
        default=SpaceParticipantRole.viewer,
    )

    can_notificate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    accession_by: Mapped[int] = mapped_column(BIGINT, nullable=True)

    accession_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )