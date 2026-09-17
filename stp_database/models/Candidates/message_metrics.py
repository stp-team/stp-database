"""Модель метрик сообщения кандидата."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.mysql import (
    BIGINT,
    INTEGER,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from stp_database.models.base import Base


class MessageMetrics(Base):
    """Метрики набора сообщения кандидата."""

    __tablename__ = "message_metrics"

    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_general_ci",
    }

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    message_uuid: Mapped[str] = mapped_column(
        String(
            250,
            collation="utf8mb4_general_ci",
        ),
        ForeignKey(
            "messages.uuid",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
    )

    reaction_time_ms: Mapped[
        int | None
    ] = mapped_column(
        BIGINT(unsigned=True),
        nullable=True,
    )

    total_response_time_ms: Mapped[
        int | None
    ] = mapped_column(
        BIGINT(unsigned=True),
        nullable=True,
    )

    typing_duration_ms: Mapped[
        int | None
    ] = mapped_column(
        BIGINT(unsigned=True),
        nullable=True,
    )

    active_typing_time_ms: Mapped[
        int | None
    ] = mapped_column(
        BIGINT(unsigned=True),
        nullable=True,
    )

    final_chars: Mapped[
        int | None
    ] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )

    inserted_chars: Mapped[
        int | None
    ] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )

    deleted_chars: Mapped[
        int | None
    ] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )

    speed_total_cpm: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(12, 4),
        nullable=True,
    )

    speed_active_cpm: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(12, 4),
        nullable=True,
    )

    correction_ratio: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(10, 6),
        nullable=True,
    )

    paste_events: Mapped[
        int | None
    ] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )

    pasted_chars: Mapped[
        int | None
    ] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )

    largest_paste_chars: Mapped[
        int | None
    ] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )

    paste_ratio: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(10, 6),
        nullable=True,
    )

    pause_count: Mapped[
        int | None
    ] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )

    pause_total_ms: Mapped[
        int | None
    ] = mapped_column(
        BIGINT(unsigned=True),
        nullable=True,
    )

    pause_max_ms: Mapped[
        int | None
    ] = mapped_column(
        BIGINT(unsigned=True),
        nullable=True,
    )

    pause_avg_ms: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(12, 4),
        nullable=True,
    )

    typing_bursts: Mapped[
        int | None
    ] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )

    typing_speed_peak_cpm: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(12, 4),
        nullable=True,
    )

    typing_speed_stddev: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(12, 4),
        nullable=True,
    )

    focus_lost_count: Mapped[
        int | None
    ] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )

    focus_lost_time_ms: Mapped[
        int | None
    ] = mapped_column(
        BIGINT(unsigned=True),
        nullable=True,
    )

    final_words: Mapped[
        int | None
    ] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )

    sentence_count: Mapped[
        int | None
    ] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )

    paragraph_count: Mapped[
        int | None
    ] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )

    avg_word_length: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(10, 4),
        nullable=True,
    )

    avg_sentence_words: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(10, 4),
        nullable=True,
    )

    uppercase_ratio: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(10, 6),
        nullable=True,
    )

    created_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )