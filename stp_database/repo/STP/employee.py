"""Репозиторий функций для взаимодействия с сотрудниками."""

import logging
from typing import Any, Sequence

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import SQLAlchemyError

from stp_database.models.STP import Employee
from stp_database.repo.base import BaseRepo

logger = logging.getLogger(__name__)


class EmployeeRepo(BaseRepo):
    """Репозиторий для работы с сотрудниками."""

    async def add_user(
        self,
        division: str,
        position: str,
        fullname: str,
        head: str,
        role: int = 0,
        user_id: int | None = None,
    ) -> Employee | None:
        """Добавление нового сотрудника.

        Args:
            user_id: Идентификатор Telegram сотрудника
            division: Подразделение
            position: Должность
            fullname: ФИО сотрудника
            head: ФИО руководителя
            role: Роль пользователя (по умолчанию 0)

        Returns:
            Созданный объект Employee или None в случае ошибки
        """
        new_user = Employee(
            user_id=user_id,
            division=division,
            position=position,
            fullname=fullname,
            head=head,
            role=role,
            is_casino_allowed=True,
        )

        try:
            self.session.add(new_user)
            await self.session.commit()
            await self.session.refresh(new_user)
            logger.info(f"[БД] Создан новый пользователь: {fullname}")
            return new_user
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка добавления пользователя {fullname}: {e}")
            await self.session.rollback()
            return None

    async def get_users(
        self,
        main_id: int | list[int] | None = None,
        user_id: int | list[int] | None = None,
        username: str | None = None,
        fullname: str | None = None,
        email: str | None = None,
        head: str | None = None,
        roles: int | list[int] | None = None,
    ) -> Employee | None | Sequence[Employee]:
        """Поиск пользователя или списка пользователей.

        Args:
            main_id: Primary Key (int - возвращает одного пользователя, list[int] - возвращает список)
            user_id: Уникальный идентификатор пользователя Telegram (int - возвращает одного пользователя, list[int] - возвращает список)
            username: Никнейм пользователя Telegram (если указан, возвращает одного пользователя)
            fullname: ФИО пользователя в БД (если указан, возвращает одного пользователя)
            email: Почта пользователя в БД (если указан, возвращает одного пользователя)
            head: ФИО руководителя (если указан, возвращает участников группы руководителя)
            roles: Роль (int) или список ролей (list[int]) для фильтрации списка пользователей

        Returns:
            Объект Employee или None (если указан одиночный main_id, user_id, username, fullname или email)
            Последовательность Employee (если указаны списки или другие параметры)
        """
        # Определяем, одиночный запрос или множественный
        is_single = (
            (isinstance(main_id, int))
            or (isinstance(user_id, int))
            or (username is not None)
            or (fullname is not None)
            or (email is not None)
        )

        if is_single:
            # Запрос одного пользователя
            filters = []

            if isinstance(main_id, int):
                filters.append(Employee.id == main_id)
            if isinstance(user_id, int):
                filters.append(Employee.user_id == user_id)
            if username:
                filters.append(Employee.username == username)
            if fullname:
                filters.append(Employee.fullname == fullname)
            if email:
                filters.append(Employee.email == email)

            query = select(Employee).where(*filters).order_by(Employee.fullname.desc())

            try:
                result = await self.session.execute(query)
                return result.scalar_one_or_none()
            except SQLAlchemyError as e:
                logger.error(f"[БД] Ошибка получения пользователя: {e}")
                return None
        else:
            # Запрос списка пользователей
            filters = []

            # Фильтр по main_id (список)
            if isinstance(main_id, list) and main_id:
                filters.append(Employee.id.in_(main_id))

            # Фильтр по user_id (список)
            if isinstance(user_id, list) and user_id:
                filters.append(Employee.user_id.in_(user_id))

            # Фильтр по руководителю
            if head is not None:
                filters.append(Employee.head == head)

            # Фильтр по ролям
            if roles is not None:
                if isinstance(roles, int):
                    # Одна роль
                    filters.append(Employee.role == roles)
                elif isinstance(roles, list) and roles:
                    # Список ролей
                    filters.append(Employee.role.in_(roles))

            # Формируем запрос
            if filters:
                query = (
                    select(Employee).where(*filters).order_by(Employee.fullname.desc())
                )
            else:
                # Все пользователи
                query = select(Employee).order_by(Employee.fullname.desc())

            try:
                result = await self.session.execute(query)
                return result.scalars().all()
            except SQLAlchemyError as e:
                logger.error(f"[БД] Ошибка получения списка пользователей: {e}")
                return []

    async def get_unauthorized_users(self, head_name: str = None) -> Sequence[Employee]:
        """Получает список неавторизованных пользователей.

        Неавторизованные пользователи - те, у которых отсутствует user_id (не связан с Telegram).

        Args:
            head_name: Фильтр по имени руководителя (опционально)

        Returns:
            Список неавторизованных пользователей
        """
        # Основное условие - отсутствие user_id означает что пользователь не авторизован в Telegram
        base_conditions = [Employee.user_id.is_(None)]

        # Добавляем фильтр по руководителю если указан
        if head_name:
            base_conditions.append(Employee.head == head_name)

        query = select(Employee).where(*base_conditions).order_by(Employee.fullname)

        try:
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(
                f"[БД] Ошибка получения списка неавторизованных пользователей: {e}"
            )
            return []

    async def update_user(
        self,
        main_id: int = None,
        user_id: int = None,
        **kwargs: Any,
    ) -> Employee | None:
        """Обновление сотрудника.

        Args:
            main_id: Идентификатор сотрудника в БД
            user_id: Идентификатор Telegram сотрудника
            **kwargs: Параметры для обновления

        Returns:
            Обновленный объект Employee или None
        """
        conditions = []
        if main_id:
            conditions.append(Employee.id == main_id)
        if user_id:
            conditions.append(Employee.user_id == user_id)

        select_stmt = select(Employee).where(*conditions)

        result = await self.session.execute(select_stmt)
        user: Employee | None = result.scalar_one_or_none()

        # Если пользователь существует - обновляем его
        if user:
            for key, value in kwargs.items():
                setattr(user, key, value)
            await self.session.commit()

        return user

    async def get_users_by_fio_parts(
        self, fullname: str, limit: int = 10
    ) -> Sequence[Employee] | None:
        """Поиск пользователей по частичному совпадению ФИО.

        Возвращает список пользователей для случаев, когда найдено несколько совпадений.

        Args:
            fullname: Частичное или полное ФИО для поиска
            limit: Максимальное количество результатов

        Returns:
            Список объектов User или None
        """
        name_parts = fullname.strip().split()
        if not name_parts:
            return []

        # Создаём условия для каждой части имени
        like_conditions = []
        for part in name_parts:
            like_conditions.append(Employee.fullname.ilike(f"%{part}%"))

        # Все части должны присутствовать в ФИО (AND)
        query = select(Employee).where(and_(*like_conditions)).limit(limit)

        try:
            result = await self.session.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка получения пользователей по ФИО: {e}")
            return []

    async def search_users(
        self, search_query: str, limit: int = 50
    ) -> Sequence[Employee] | None:
        """Универсальный поиск пользователей.

         Поиск по различным критериям:
        - User ID (число)
        - Username Telegram (начинается с @)
        - Частичное/полное ФИО

        Args:
            search_query: Поисковый запрос
            limit: Максимальное количество результатов

        Returns:
            Список объектов Employee или None
        """
        search_query = search_query.strip()
        if not search_query:
            return []

        conditions = []

        # Проверяем, является ли запрос числом (User ID)
        if search_query.isdigit():
            user_id = int(search_query)
            conditions.append(Employee.user_id == user_id)

        # Поиск по username (с @ и без @)
        if search_query.startswith("@"):
            # Если начинается с @, ищем без @
            username = search_query[1:]
            if username:  # Проверяем, что после @ что-то есть
                conditions.append(Employee.username.ilike(f"%{username}%"))
        else:
            # Всегда добавляем поиск по username
            conditions.append(Employee.username.ilike(f"%{search_query}%"))

        # Поиск по частичному ФИО
        name_parts = search_query.split()
        if name_parts:
            # Создаём условия для каждой части имени
            name_conditions = []
            for part in name_parts:
                name_conditions.append(Employee.fullname.ilike(f"%{part}%"))

            # Все части должны присутствовать в ФИО (AND)
            if len(name_conditions) == 1:
                conditions.append(name_conditions[0])
            else:
                conditions.append(and_(*name_conditions))

        # Объединяем все условия через OR
        if not conditions:
            return []

        query = select(Employee).where(or_(*conditions)).limit(limit)

        try:
            result = await self.session.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"[БД] Ошибка универсального поиска пользователей: {e}")
            return []

    async def delete_user(
        self, main_id: int = None, fullname: str = None, user_id: int = None
    ) -> int:
        """Удаление сотрудников.

        Args:
            main_id: Идентификатор сотрудника в БД
            fullname: ФИО сотрудника
            user_id: Идентификатор Telegram сотрудника

        Returns:
            Кол-во удаленных пользователей
        """
        if not fullname and not user_id:
            raise ValueError(
                "Как минимум один параметр (fullname или user_id) должен быть предоставлен"
            )

        try:
            # Строим условие для поиска
            conditions = []
            if main_id:
                conditions.append(Employee.id == main_id)
            if fullname:
                conditions.append(Employee.fullname == fullname)
            if user_id:
                conditions.append(Employee.user_id == user_id)

            # Находим пользователей по условиям
            query = select(Employee).where(*conditions)
            result = await self.session.execute(query)
            users = result.scalars().all()

            deleted_count = 0
            for user in users:
                await self.session.delete(user)
                deleted_count += 1
                logger.info(
                    f"[БД] Пользователь {user.fullname} (ID: {user.user_id}) удален из базы"
                )

            if deleted_count > 0:
                await self.session.commit()
                identifier = f"ФИО {fullname}" if fullname else f"user_id {user_id}"
                logger.info(
                    f"[БД] Всего удалено {deleted_count} пользователей по {identifier}"
                )

            return deleted_count
        except SQLAlchemyError as e:
            identifier = f"ФИО {fullname}" if fullname else f"user_id {user_id}"
            logger.error(f"[БД] Ошибка удаления пользователей по {identifier}: {e}")
            await self.session.rollback()
            return 0
