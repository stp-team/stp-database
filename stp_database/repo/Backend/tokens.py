"""Репозиторий для работы с API токенами."""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError

from stp_database.models.Backend.tokens import ApiToken, ApiTokenAuditLog
from stp_database.repo.base import BaseRepo

logger = logging.getLogger(__name__)


class ApiTokenRepo(BaseRepo):
    """Репозиторий для работы с API токенами."""

    async def create_token(
        self,
        employee_id: int,
        name: str,
        description: str | None = None,
        expires_in_days: int | None = None,
        permissions: dict | None = None,
        created_by: int | None = None,
    ) -> tuple[str, ApiToken] | None:
        """Создание нового API токена.

        Генерирует токен в формате 'stp_' + 64 hex символов,
        хеширует его через SHA-256 и сохраняет в БД.

        Args:
            employee_id: Идентификатор сотрудника-владельца
            name: Название токена
            description: Описание токена
            expires_in_days: Срок действия в днях (None = бессрочный)
            permissions: Разрешения токена
            created_by: Кто создал токен

        Returns:
            Кортеж (raw_token, ApiToken) или None в случае ошибки
        """
        raw_token = self._generate_token()
        token_hash = self._hash_token(raw_token)

        # Вычисляем дату истечения
        expires_at = None
        if expires_in_days is not None:
            expires_at = datetime.now() + timedelta(days=expires_in_days)

        # Устанавливаем разрешения по умолчанию
        if permissions is None:
            permissions = {}

        new_token = ApiToken(
            token_hash=token_hash,
            employee_id=employee_id,
            name=name,
            description=description,
            expires_at=expires_at,
            permissions=permissions,
            created_by=created_by,
        )

        try:
            self.session.add(new_token)
            await self.session.commit()
            await self.session.refresh(new_token)
            logger.info(
                f"[БД] Создан новый API токен: {name} для сотрудника {employee_id}"
            )

            # Создаем запись аудита
            await self._create_audit_log(
                token_id=new_token.id,
                action="token_created",
                success=True,
            )

            return raw_token, new_token
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка создания API токена {name}: {e}")
            await self.session.rollback()
            return None

    async def validate_token(
        self,
        raw_token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        endpoint: str | None = None,
    ) -> ApiToken | None:
        """Валидация API токена.

        Args:
            raw_token: RAW токен
            ip_address: IP адрес клиента
            user_agent: User Agent клиента
            endpoint: Эндпоинт

        Returns:
            Объект ApiToken или None если токен невалиден
        """
        token_hash = self._hash_token(raw_token)

        query = select(ApiToken).where(
            and_(
                ApiToken.token_hash == token_hash,
                ApiToken.is_active,
            )
        )

        try:
            result = await self.session.execute(query)
            token: ApiToken | None = result.scalar_one_or_none()

            if token is None:
                # Создаем запись аудита о неудачной попытке (без token_id)
                await self._create_audit_log(
                    token_id=None,
                    action="token_validation_failed",
                    success=False,
                    error_message="Токен не найден или неактивен",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    endpoint=endpoint,
                )
                return None

            # Проверяем срок действия
            if token.expires_at and token.expires_at < datetime.now():
                # Токен истек
                await self._create_audit_log(
                    token_id=token.id,
                    action="token_validation_failed",
                    success=False,
                    error_message="Токен истек",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    endpoint=endpoint,
                )
                return None

            # Обновляем время последнего использования
            token.last_used_at = datetime.now()
            await self.session.commit()

            # Создаем запись аудита об успешном использовании
            await self._create_audit_log(
                token_id=token.id,
                action="token_used",
                success=True,
                ip_address=ip_address,
                user_agent=user_agent,
                endpoint=endpoint,
            )

            return token
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка валидации API токена: {e}")
            return None

    async def revoke_token(self, token_id: int) -> bool:
        """Отзыв API токена.

        Args:
            token_id: Идентификатор токена

        Returns:
            True если успешно, иначе False
        """
        query = select(ApiToken).where(ApiToken.id == token_id)

        try:
            result = await self.session.execute(query)
            token: ApiToken | None = result.scalar_one_or_none()

            if token is None:
                logger.warning(f"[БД] Токен с ID {token_id} не найден")
                return False

            token.is_active = False
            await self.session.commit()

            logger.info(f"[БД] Токен {token_id} отозван")

            # Создаем запись аудита
            await self._create_audit_log(
                token_id=token.id,
                action="token_revoked",
                success=True,
            )

            return True
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка отзыва токена {token_id}: {e}")
            await self.session.rollback()
            return False

    async def extend_token(self, token_id: int, days: int) -> ApiToken | None:
        """Продление срока действия API токена.

        Args:
            token_id: Идентификатор токена
            days: Количество дней для продления

        Returns:
            Обновленный объект ApiToken или None
        """
        query = select(ApiToken).where(ApiToken.id == token_id)

        try:
            result = await self.session.execute(query)
            token: ApiToken | None = result.scalar_one_or_none()

            if token is None:
                logger.warning(f"[БД] Токен с ID {token_id} не найден")
                return None

            # Если expires_at был None, устанавливаем от текущей даты
            if token.expires_at is None:
                token.expires_at = datetime.now() + timedelta(days=days)
            else:
                # Добавляем дни к существующей дате
                token.expires_at = token.expires_at + timedelta(days=days)

            await self.session.commit()
            await self.session.refresh(token)

            logger.info(f"[БД] Срок действия токена {token_id} продлен на {days} дней")

            # Создаем запись аудита
            await self._create_audit_log(
                token_id=token.id,
                action="token_extended",
                success=True,
                metadata={"days": days},
            )

            return token
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка продления токена {token_id}: {e}")
            await self.session.rollback()
            return None

    async def get_user_tokens(self, employee_id: int) -> list[ApiToken]:
        """Получение списка токенов сотрудника.

        Args:
            employee_id: Идентификатор сотрудника

        Returns:
            Список токенов, отсортированный по created_at DESC
        """
        query = (
            select(ApiToken)
            .where(ApiToken.employee_id == employee_id)
            .order_by(ApiToken.created_at.desc())
        )

        try:
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка получения токенов сотрудника {employee_id}: {e}")
            return []

    async def check_permission(
        self,
        token: ApiToken,
        resource: str,
        action: str,
    ) -> bool:
        """Проверка разрешения токена.

        Args:
            token: Объект токена
            resource: Ресурс (например, "employees")
            action: Действие (например, "read")

        Returns:
            True если разрешено, иначе False
        """
        permissions = token.permissions

        # Проверяем admin права
        if permissions.get("admin") is True:
            return True

        # Проверяем разрешения для конкретного ресурса
        resources = permissions.get("resources", {})
        resource_perm = resources.get(resource)

        if resource_perm is None or resource_perm is False:
            return False
        elif resource_perm is True:
            # Все действия разрешены для этого ресурса
            return True
        elif isinstance(resource_perm, str):
            # Проверяем точное совпадение действия
            return resource_perm == action
        elif isinstance(resource_perm, list):
            # Проверяем наличие действия в списке
            return action in resource_perm

        return False

    async def get_token_audit_logs(
        self,
        token_id: int,
        limit: int = 100,
    ) -> list[ApiTokenAuditLog]:
        """Получение логов аудита токена.

        Args:
            token_id: Идентификатор токена
            limit: Максимальное количество записей

        Returns:
            Список записей аудита, отсортированный по created_at DESC
        """
        query = (
            select(ApiTokenAuditLog)
            .where(ApiTokenAuditLog.token_id == token_id)
            .order_by(ApiTokenAuditLog.created_at.desc())
            .limit(limit)
        )

        try:
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка получения логов аудита токена {token_id}: {e}")
            return []

    async def cleanup_expired_tokens(
        self,
        days_inactive: int = 30,
    ) -> int:
        """Очистка неактивных истекших токенов.

        Args:
            days_inactive: Количество дней неактивности

        Returns:
            Количество удаленных токенов
        """
        cutoff_date = datetime.now() - timedelta(days=days_inactive)

        # Находим токены для удаления
        query = select(ApiToken).where(
            and_(
                not ApiToken.is_active,
                ApiToken.expires_at < cutoff_date,
            )
        )

        try:
            result = await self.session.execute(query)
            tokens = result.scalars().all()

            deleted_count = 0
            for token in tokens:
                await self.session.delete(token)
                deleted_count += 1

            if deleted_count > 0:
                await self.session.commit()
                logger.info(f"[БД] Удалено {deleted_count} неактивных токенов")

            return deleted_count
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка очистки неактивных токенов: {e}")
            await self.session.rollback()
            return 0

    def _generate_token(self) -> str:
        """Генерация нового токена.

        Returns:
            Строка токена в формате 'stp_' + 64 символа hex
        """
        random_bytes = secrets.token_bytes(32)
        hex_part = random_bytes.hex()
        return f"stp_{hex_part}"

    def _hash_token(self, raw_token: str) -> str:
        """Хеширование токена.

        Args:
            raw_token: RAW токен

        Returns:
            SHA-256 хеш токена
        """
        return hashlib.sha256(raw_token.encode()).hexdigest()

    async def _create_audit_log(
        self,
        token_id: int | None,
        action: str,
        success: bool = True,
        error_message: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        endpoint: str | None = None,
        metadata: dict | None = None,
    ) -> ApiTokenAuditLog | None:
        """Создание записи аудита.

        Args:
            token_id: Идентификатор токена
            action: Действие
            success: Успешность операции
            error_message: Сообщение об ошибке
            ip_address: IP адрес
            user_agent: User Agent
            endpoint: Эндпоинт
            metadata: Дополнительные данные

        Returns:
            Объект ApiTokenAuditLog или None
        """
        if token_id is None:
            # Не можем создать запись аудита без токена
            return None

        audit_log = ApiTokenAuditLog(
            token_id=token_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            success=success,
            error_message=error_message,
            metadata=metadata,
        )

        try:
            self.session.add(audit_log)
            await self.session.commit()
            return audit_log
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка создания записи аудита: {e}")
            await self.session.rollback()
            return None
