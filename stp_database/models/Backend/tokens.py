"""Модели, связанные с API токенами."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BIGINT, BOOLEAN, JSON, ForeignKey, Index, Text, Unicode, func
from sqlalchemy.dialects.mysql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stp_database.models.base import Base

if TYPE_CHECKING:
    from stp_database.models.STP.employee import Employee


class ApiToken(Base):
    """Модель, представляющий API токен в БД.

    Токен может находиться в трех состояниях:
    - Активен (is_active=True, is_revoked=False): токен можно использовать
    - Деактивирован (is_active=False, is_revoked=False): токен временно отключен, можно активировать
    - Отозван (is_revoked=True): токен безвозвратно отключен, восстановление невозможно

    Args:
        id: Уникальный идентификатор токена
        token_hash: Хеш токена
        employee_id: Идентификатор сотрудника-владельца
        name: Название токена
        description: Описание токена
        is_active: Активен ли токен
        is_revoked: Отозван ли токен (безвозвратно)
        expires_at: Дата истечения токена
        last_used_at: Дата последнего использования
        permissions: JSON с разрешениями токена
        created_by: Идентификатор сотрудника, создавшего токен
        created_at: Дата создания токена

    Methods:
        __repr__(): Возвращает строковое представление объекта ApiToken.
    """

    __tablename__ = "tokens"
    __table_args__ = (
        Index("idx_token_hash", "token_hash"),
        Index("idx_employee_id", "employee_id"),
        Index("idx_expires_at", "expires_at"),
        Index("idx_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(
        BIGINT, primary_key=True, comment="Уникальный идентификатор токена"
    )
    token_hash: Mapped[str] = mapped_column(
        Unicode(64), nullable=False, unique=True, comment="Хеш токена"
    )
    employee_id: Mapped[int] = mapped_column(
        BIGINT, nullable=False, comment="Идентификатор сотрудника-владельца"
    )
    name: Mapped[str] = mapped_column(
        Unicode(100), nullable=False, comment="Название токена"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Описание токена"
    )
    is_active: Mapped[bool] = mapped_column(
        BOOLEAN,
        nullable=False,
        default=True,
        comment="Активен ли токен",
    )
    is_revoked: Mapped[bool] = mapped_column(
        BOOLEAN,
        nullable=False,
        default=False,
        comment="Отозван ли токен (безвозвратно)",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP, nullable=True, comment="Дата истечения токена"
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP, nullable=True, comment="Дата последнего использования"
    )
    permissions: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=lambda: {}, comment="JSON с разрешениями токена"
    )
    created_by: Mapped[int | None] = mapped_column(
        BIGINT, nullable=True, comment="Идентификатор сотрудника, создавшего токен"
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), comment="Дата создания токена"
    )

    # Отношения
    employee: Mapped["Employee"] = relationship(
        "Employee",
        primaryjoin="ApiToken.employee_id == foreign(Employee.user_id)",
        lazy="select",
    )
    creator: Mapped["Employee | None"] = relationship(
        "Employee",
        primaryjoin="ApiToken.created_by == foreign(Employee.user_id)",
        overlaps="employee",
        lazy="select",
    )
    audit_logs: Mapped[list["ApiTokenAuditLog"]] = relationship(
        "ApiTokenAuditLog", back_populates="token", lazy="select"
    )

    def __repr__(self):
        """Возвращает строковое представление объекта ApiToken."""
        return f"<ApiToken {self.id} {self.name} {self.employee_id}>"


class ApiTokenAuditLog(Base):
    """Модель, представляющая аудит-лог API токена в БД.

    Args:
        id: Уникальный идентификатор записи
        token_id: Идентификатор токена
        action: Выполненное действие
        ip_address: IP-адрес запроса
        user_agent: User-Agent запроса
        endpoint: Эндпоинт запроса
        success: Успешность запроса
        error_message: Сообщение об ошибке
        metadata: Дополнительные метаданные
        created_at: Дата создания записи

    Methods:
        __repr__(): Возвращает строковое представление объекта ApiTokenAuditLog.
    """

    __tablename__ = "token_audit_logs"
    __table_args__ = (
        Index("idx_token_id", "token_id"),
        Index("idx_action", "action"),
        Index("idx_created_at", "created_at"),
        Index("idx_token_time", "token_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(
        BIGINT, primary_key=True, comment="Уникальный идентификатор записи"
    )
    token_id: Mapped[int] = mapped_column(
        BIGINT,
        ForeignKey("tokens.id", ondelete="CASCADE"),
        nullable=False,
        comment="Идентификатор токена",
    )
    action: Mapped[str] = mapped_column(
        Unicode(50), nullable=False, comment="Выполненное действие"
    )
    ip_address: Mapped[str | None] = mapped_column(
        Unicode(45), nullable=True, comment="IP-адрес запроса"
    )
    user_agent: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="User-Agent запроса"
    )
    endpoint: Mapped[str | None] = mapped_column(
        Unicode(255), nullable=True, comment="Эндпоинт запроса"
    )
    success: Mapped[bool] = mapped_column(
        BOOLEAN,
        nullable=False,
        default=True,
        comment="Успешность запроса",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Сообщение об ошибке"
    )
    extra_metadata: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="Дополнительные метаданные"
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), comment="Дата создания записи"
    )

    # Отношения
    token: Mapped["ApiToken"] = relationship(
        "ApiToken", back_populates="audit_logs", lazy="select"
    )

    def __repr__(self):
        """Возвращает строковое представление объекта ApiTokenAuditLog."""
        return f"<ApiTokenAuditLog {self.id} {self.token_id} {self.action}>"
