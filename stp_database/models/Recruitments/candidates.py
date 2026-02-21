"""Модели, связанные с сущностями кандидатов."""

from sqlalchemy import BIGINT, Enum, Integer
from sqlalchemy.dialects.mysql import LONGTEXT, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from stp_database.models.base import Base


class Candidate(Base):
    """Класс, представляющий сущность кандидата в БД.

    Args:
        user_id: Идентификатор Telegram кандидата
        fullname: ФИО кандидата
        position: Название позиции, на которую подается кандидат
        age: Возраст кандидата
        topic_id: Идентификатор Telegram топика, которому принадлежит кандидат
        status: Статус кандидата
        city: Город кандидата
        citizenship: Гражданство кандидата
        username: Имя пользователя Telegram кандидата
        shift_type: Тип смены (полная/частичная)
        shift_time: Время смены (день/ночь/любое)
        experience: Опыт работы
        workplace: Рабочее место кандидата
        internet_speed: Скорость интернета кандидата
        typing_speed: Скорость печати кандидата
        resume_link: Ссылка на резюме кандидата
        rejection_reason: Причина отказа

    Methods:
        __repr__(): Возвращает строковое представление объекта Candidate.
    """

    __tablename__ = "candidates"

    user_id: Mapped[int] = mapped_column(
        BIGINT,
        primary_key=True,
        nullable=False,
        comment="Идентификатор Telegram кандидата",
    )
    fullname: Mapped[str | None] = mapped_column(
        VARCHAR(255), nullable=True, comment="ФИО кандидата"
    )
    position: Mapped[str] = mapped_column(
        VARCHAR(255),
        nullable=True,
        comment="Название позиции, на которую подается кандидат",
    )
    age: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Возраст кандидата"
    )
    topic_id: Mapped[int | None] = mapped_column(
        BIGINT,
        nullable=True,
        comment="Идентификатор Telegram топика, которому принадлежит кандидат",
    )
    status: Mapped[str] = mapped_column(
        Enum("interview", "waiting", "review", "decline", "accept", "reject"),
        nullable=False,
        comment="Статус кандидата",
        default="interview",
    )
    city: Mapped[str | None] = mapped_column(
        VARCHAR(255), nullable=True, comment="Город кандидата"
    )
    citizenship: Mapped[str | None] = mapped_column(
        VARCHAR(255), nullable=True, comment="Гражданство кандидата"
    )
    username: Mapped[str | None] = mapped_column(
        VARCHAR(255), nullable=True, comment="Имя пользователя Telegram кандидата"
    )
    shift_type: Mapped[str | None] = mapped_column(
        Enum("full", "part"), nullable=True, comment="Тип смены (полная/частичная)"
    )
    shift_time: Mapped[str | None] = mapped_column(
        Enum("day", "night", "any"),
        nullable=True,
        comment="Время смены (день/ночь/любое)",
    )
    experience: Mapped[str | None] = mapped_column(
        Enum("chats", "calls", "in-person", "no"), nullable=True, comment="Опыт работы"
    )
    workplace: Mapped[str | None] = mapped_column(
        LONGTEXT, nullable=True, comment="Рабочее место кандидата"
    )
    internet_speed: Mapped[str | None] = mapped_column(
        Enum("<20", "<30", "50<>20", "30<>100", "100<>50", ">100"),
        nullable=True,
        comment="Скорость интернета кандидата",
    )
    typing_speed: Mapped[str | None] = mapped_column(
        VARCHAR(255), nullable=True, comment="Скорость печати кандидата"
    )
    resume_link: Mapped[str | None] = mapped_column(
        VARCHAR(255), nullable=True, comment="Ссылка на резюме кандидата"
    )
    manager_user_id: Mapped[int | None] = mapped_column(
        BIGINT, nullable=True, comment="Менеджер, принявший решение по кандидату"
    )
    rejection_reason: Mapped[str | None] = mapped_column(
        Enum("found_job", "not_interested", "requirements", "other"),
        nullable=True,
        comment="Причина отказа",
    )

    def __repr__(self):
        """Возвращает строковое представление объекта Candidate."""
        return f"<Candidate {self.user_id} {self.position} {self.status}>"
