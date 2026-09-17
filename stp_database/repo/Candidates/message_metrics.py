"""Репозиторий метрик сообщений кандидатов."""

import logging

from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_HALF_UP,
)

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from stp_database.models.Candidates import (
    MessageMetrics,
)
from stp_database.repo.base import BaseRepo


logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# UNSIGNED INTEGER / BIGINT
# ---------------------------------------------------------

INTEGER_FIELDS = {
    "reaction_time_ms",
    "total_response_time_ms",
    "typing_duration_ms",
    "active_typing_time_ms",

    "final_chars",
    "inserted_chars",
    "deleted_chars",

    "paste_events",
    "pasted_chars",
    "largest_paste_chars",

    "pause_count",
    "pause_total_ms",
    "pause_max_ms",

    "typing_bursts",

    "focus_lost_count",
    "focus_lost_time_ms",

    "final_words",
    "sentence_count",
    "paragraph_count",
}


# ---------------------------------------------------------
# DECIMAL(..., 4)
# ---------------------------------------------------------

DECIMAL_4_FIELDS = {
    "speed_total_cpm",
    "speed_active_cpm",

    "pause_avg_ms",

    "typing_speed_peak_cpm",
    "typing_speed_stddev",

    "avg_word_length",
    "avg_sentence_words",
}


# ---------------------------------------------------------
# DECIMAL(..., 6)
# ---------------------------------------------------------

DECIMAL_6_FIELDS = {
    "correction_ratio",
    "paste_ratio",
    "uppercase_ratio",
}


METRIC_FIELDS = (
    INTEGER_FIELDS
    | DECIMAL_4_FIELDS
    | DECIMAL_6_FIELDS
)


# ---------------------------------------------------------
# Приведение в UNSIGNED INT
# ---------------------------------------------------------

def _to_unsigned_int(
    value,
) -> int | None:
    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return None

    try:
        decimal_value = Decimal(
            str(value)
        )

    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ):
        return None

    if not decimal_value.is_finite():
        return None

    int_value = int(
        decimal_value
    )

    if int_value < 0:
        return None

    return int_value


# ---------------------------------------------------------
# Приведение в DECIMAL
# ---------------------------------------------------------

def _to_decimal(
    value,
    quantizer: str,
) -> Decimal | None:
    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return None

    try:
        decimal_value = Decimal(
            str(value)
        )

        if not decimal_value.is_finite():
            return None

        return decimal_value.quantize(
            Decimal(
                quantizer
            ),
            rounding=ROUND_HALF_UP,
        )

    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ):
        return None


# ---------------------------------------------------------
# Полная нормализация JSON -> SQL
# ---------------------------------------------------------

def normalize_metrics_for_db(
    metrics: dict,
) -> dict:
    normalized = {}

    for key, value in metrics.items():
        #
        # metrics в API может содержать любой JSON.
        #
        # Но в SQL кладём только существующие
        # колонки таблицы message_metrics.
        #
        if key not in METRIC_FIELDS:
            continue

        if key in INTEGER_FIELDS:
            normalized[key] = (
                _to_unsigned_int(
                    value
                )
            )

            continue

        if key in DECIMAL_4_FIELDS:
            normalized[key] = (
                _to_decimal(
                    value,
                    "0.0001",
                )
            )

            continue

        if key in DECIMAL_6_FIELDS:
            normalized[key] = (
                _to_decimal(
                    value,
                    "0.000001",
                )
            )

    return normalized


class MessageMetricsRepo(BaseRepo):
    """Работа с метриками сообщений."""

    async def create_metrics(
        self,
        message_uuid: str,
        metrics: dict,
    ) -> MessageMetrics | None:
        data = (
            normalize_metrics_for_db(
                metrics
            )
        )

        row = MessageMetrics(
            message_uuid=message_uuid,
            **data,
        )

        try:
            self.session.add(
                row
            )

            await self.session.commit()

            await self.session.refresh(
                row
            )

            return row

        except SQLAlchemyError as e:
            logger.error(
                "[БД] Ошибка создания "
                "метрик сообщения "
                f"{message_uuid}: {e}"
            )

            await self.session.rollback()

            return None

    async def get_metrics(
        self,
        message_uuid: str,
    ) -> MessageMetrics | None:
        query = (
            select(
                MessageMetrics
            )
            .where(
                MessageMetrics.message_uuid
                == message_uuid
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

        except SQLAlchemyError as e:
            logger.error(
                "[БД] Ошибка получения "
                "метрик сообщения "
                f"{message_uuid}: {e}"
            )

            return None

    async def get_metrics_for_messages(
        self,
        message_uuids: list[str],
    ):
        if not message_uuids:
            return []

        query = (
            select(
                MessageMetrics
            )
            .where(
                MessageMetrics.message_uuid
                .in_(
                    message_uuids
                )
            )
        )

        try:
            result = (
                await self.session.execute(
                    query
                )
            )

            return (
                result.scalars().all()
            )

        except SQLAlchemyError as e:
            logger.error(
                "[БД] Ошибка получения "
                f"метрик сообщений: {e}"
            )

            return []