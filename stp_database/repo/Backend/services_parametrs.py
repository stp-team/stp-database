from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.exc import SQLAlchemyError

from stp_database.models.Backend.services_parametrs import ServicesParametrs
from stp_database.repo.base import BaseRepo

class ServicesParametrsRepo(BaseRepo):
    async def get_param(
            self,
            service: str,
            name: str,
    ) -> ServicesParametrs:
        """ Получить параметр по service + name """
        return await self.session.get(
            ServicesParametrs, (service, name)
        )

    async def get_service_params(
            self,
            service: str,
    ) -> list[ServicesParametrs]:
        """ Получить все параметры сервиса. """
        stmt = select(ServicesParametrs).where(ServicesParametrs.service == service).order_by(ServicesParametrs.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert_param(
            self,
            service: str,
            name: str,
            type: str,
            value: str | None,
    ) -> ServicesParametrs:
        """ Создать или обновить параметр. """
        if type not in {"int", "float", "string", "text", "json"}:
            raise ValueError(f"Недопустимый тип параметра: {type}")
        stmt = insert(ServicesParametrs).values(
            service=service,
            name=name,
            type=type,
            value=value,
        )

        stmt = stmt.on_duplicate_key_update(
            type=type,
            value=value,
        )

        try:
            await self.session.execute(stmt)
            await self.session.commit()
            return await self.session.get(ServicesParametrs, (service, name), populate_existing=True)
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def delete_param(
        self,
        service: str,
        name: str,
    ) -> bool:
        """ Удаление параметра. """
        param = await self.get_param(service, name)

        if param is None:
            return False

        try:
            await self.session.delete(param)
            await self.session.commit()
            return True
        except SQLAlchemyError:
            await self.session.rollback()
            raise
