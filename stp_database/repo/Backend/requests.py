"""Репозиторий для работы с моделями БД STP."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from stp_database.repo.STP.api_token import ApiTokenRepo


@dataclass
class BackendRequestsRepo:
    """Репозиторий для обработки операций с БД. Этот класс содержит все репозитории для моделей базы данных Бекенда.

    Ты можешь добавить дополнительные репозитории в качестве свойств к этому классу, чтобы они были легко доступны.
    """

    session: AsyncSession

    def api_token(self) -> ApiTokenRepo:
        """Инициализация репозитория ApiTokenRepo с сессией для работы с API токенами."""
        return ApiTokenRepo(self.session)
