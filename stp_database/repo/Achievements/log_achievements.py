"""Репозиторий для работы с логами проверки достижений."""

import copy
import json
import logging
from datetime import datetime
from typing import Any, Mapping, Sequence
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import delete

from stp_database.models.Achievements import LogAchievements
from stp_database.repo.base import BaseRepo

logger = logging.getLogger(__name__)


class LogAchievementsRepo(BaseRepo):
    """Репозиторий для работы с логами проверки достижений."""

    async def create_log(
            self,
            user_id: int,
            achievement_uuid: str,
            rule_expression: str | Mapping[str, Any],
            condition_results: Mapping[str, Any],
            *,
            log_uuid: str | None = None,
            checked_at: datetime | None = None,
    ) -> LogAchievements:
        """
        Создать запись лога проверки достижения.

        Если для пары user_id + achievement_uuid уже существуют записи,
        они удаляются перед созданием новой.

        Удаление старых записей и добавление новой выполняются в рамках
        одной транзакции.

        Args:
            user_id:
                ID проверяемого пользователя.

            achievement_uuid:
                UUID достижения.

            rule_expression:
                Исходное дерево правил достижения. Можно передать JSON-строкой
                либо уже десериализованным словарём.

            condition_results:
                Дерево результатов проверки, соответствующее структуре
                rule_expression.

                Для каждого конечного условия ожидаются поля:

                {
                    "checked_value": фактическое_значение,
                    "result": true | false
                }

                Вложенность должна повторять структуру rule_expression.

            log_uuid:
                UUID новой записи лога. Если не передан, генерируется
                автоматически.

            checked_at:
                Время проверки. Если не передано, используется серверное
                значение checked_at из модели.

        Returns:
            Созданная запись LogAchievements.
        """
        parsed_rule_expression = self._parse_rule_expression(
            rule_expression
        )

        check_result = self.build_check_result(
            rule_expression=parsed_rule_expression,
            condition_results=condition_results,
        )

        log = LogAchievements(
            uuid=log_uuid or str(uuid4()),
            user_id=user_id,
            achievement_uuid=achievement_uuid,
            check_result=json.dumps(
                check_result,
                ensure_ascii=False,
                separators=(",", ":"),
                default=self._json_default,
            ),
        )

        if checked_at is not None:
            log.checked_at = checked_at

        try:
            delete_stmt = delete(LogAchievements).where(
                LogAchievements.user_id == user_id,
                LogAchievements.achievement_uuid == achievement_uuid,
            )

            await self.session.execute(delete_stmt)

            self.session.add(log)

            await self.session.commit()
            await self.session.refresh(log)

            return log

        except SQLAlchemyError:
            await self.session.rollback()

            logger.exception(
                "[БД] Ошибка создания лога проверки достижения. "
                "user_id=%s, achievement_uuid=%s",
                user_id,
                achievement_uuid,
            )

            raise

    async def get_logs(
        self,
        *,
        user_id: int | None = None,
        achievement_uuid: str | None = None,
        checked_at_from: datetime | None = None,
        checked_at_to: datetime | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> Sequence[LogAchievements]:
        """
        Получить логи проверок достижений по фильтрам.

        Все фильтры необязательные и могут комбинироваться.

        Период задаётся включительно:

        checked_at_from <= checked_at <= checked_at_to

        Args:
            user_id:
                ID пользователя.

            achievement_uuid:
                UUID достижения.

            checked_at_from:
                Начало периода проверки включительно.

            checked_at_to:
                Конец периода проверки включительно.

            limit:
                Максимальное количество записей.

            offset:
                Количество пропускаемых записей.

        Returns:
            Последовательность логов, отсортированных от новых к старым.
        """
        if checked_at_from is not None and checked_at_to is not None:
            if checked_at_from > checked_at_to:
                raise ValueError(
                    "checked_at_from не может быть больше checked_at_to"
                )

        if limit is not None and limit <= 0:
            raise ValueError("limit должен быть больше нуля")

        if offset < 0:
            raise ValueError("offset не может быть отрицательным")

        stmt = select(LogAchievements)

        if user_id is not None:
            stmt = stmt.where(LogAchievements.user_id == user_id)

        if achievement_uuid is not None:
            stmt = stmt.where(
                LogAchievements.achievement_uuid == achievement_uuid
            )

        if checked_at_from is not None:
            stmt = stmt.where(
                LogAchievements.checked_at >= checked_at_from
            )

        if checked_at_to is not None:
            stmt = stmt.where(
                LogAchievements.checked_at <= checked_at_to
            )

        stmt = (
            stmt
            .order_by(LogAchievements.checked_at.desc())
            .offset(offset)
        )

        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)

        return result.scalars().all()

    async def get_log_by_uuid(
        self,
        log_uuid: str,
    ) -> LogAchievements | None:
        """Получить конкретную запись лога по UUID."""
        stmt = select(LogAchievements).where(
            LogAchievements.uuid == log_uuid
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    @classmethod
    def build_check_result(
        cls,
        rule_expression: Mapping[str, Any],
        condition_results: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Построить подробный результат проверки.

        Исходное rule_expression не изменяется. В возвращаемом дереве:

        - каждое условие содержит checked_value и result;
        - каждый блок условий содержит result;
        - корневой блок содержит итоговый result.

        Структура condition_results должна повторять вложенность
        rule_expression.
        """
        result_tree = copy.deepcopy(dict(rule_expression))

        cls._fill_node_result(
            rule_node=result_tree,
            result_node=condition_results,
            path="root",
        )

        return result_tree

    @classmethod
    def _fill_node_result(
        cls,
        rule_node: dict[str, Any],
        result_node: Mapping[str, Any],
        path: str,
    ) -> bool:
        """
        Рекурсивно дополнить узел правила результатами проверки.

        Блоком считается узел, содержащий список conditions или blocks.
        Остальные узлы считаются конечными условиями.
        """
        children_key = cls._get_children_key(rule_node)

        if children_key is None:
            if "checked_value" not in result_node:
                raise ValueError(
                    f"Для условия {path} не передано checked_value"
                )

            if "result" not in result_node:
                raise ValueError(
                    f"Для условия {path} не передан result"
                )

            checked_result = result_node["result"]

            if not isinstance(checked_result, bool):
                raise TypeError(
                    f"Результат условия {path} должен иметь тип bool"
                )

            rule_node["checked_value"] = result_node["checked_value"]
            rule_node["result"] = checked_result

            return checked_result

        rule_children = rule_node.get(children_key)

        if not isinstance(rule_children, list):
            raise TypeError(
                f"Поле {path}.{children_key} должно содержать список"
            )

        result_children = result_node.get(children_key)

        if not isinstance(result_children, list):
            raise ValueError(
                f"Для блока {path} необходимо передать список "
                f"{children_key}"
            )

        if len(rule_children) != len(result_children):
            raise ValueError(
                f"Количество результатов в {path}.{children_key} "
                f"не совпадает с количеством правил: "
                f"{len(result_children)} != {len(rule_children)}"
            )

        children_results: list[bool] = []

        for index, (rule_child, result_child) in enumerate(
            zip(rule_children, result_children, strict=True)
        ):
            if not isinstance(rule_child, dict):
                raise TypeError(
                    f"Условие {path}.{children_key}[{index}] "
                    f"должно быть объектом"
                )

            if not isinstance(result_child, Mapping):
                raise TypeError(
                    f"Результат {path}.{children_key}[{index}] "
                    f"должен быть объектом"
                )

            child_result = cls._fill_node_result(
                rule_node=rule_child,
                result_node=result_child,
                path=f"{path}.{children_key}[{index}]",
            )

            children_results.append(child_result)

        block_result = cls._calculate_block_result(
            rule_node=rule_node,
            children_results=children_results,
            path=path,
        )

        # Разрешаем вызывающему коду передать результат блока явно,
        # но проверяем, что он совпадает с вычисленным значением.
        supplied_result = result_node.get("result")

        if supplied_result is not None:
            if not isinstance(supplied_result, bool):
                raise TypeError(
                    f"Результат блока {path} должен иметь тип bool"
                )

            if supplied_result != block_result:
                raise ValueError(
                    f"Переданный результат блока {path} "
                    f"не совпадает с вычисленным: "
                    f"{supplied_result} != {block_result}"
                )

        rule_node["result"] = block_result

        return block_result

    @staticmethod
    def _get_children_key(node: Mapping[str, Any]) -> str | None:
        """
        Найти поле, содержащее дочерние условия.

        Поддерживаются оба распространённых варианта:
        conditions и blocks.
        """
        if isinstance(node.get("conditions"), list):
            return "conditions"

        if isinstance(node.get("blocks"), list):
            return "blocks"

        return None

    @staticmethod
    def _calculate_block_result(
        rule_node: Mapping[str, Any],
        children_results: Sequence[bool],
        path: str,
    ) -> bool:
        """Вычислить итог блока по его логическому оператору."""
        operator = (
            rule_node.get("operator")
            or rule_node.get("logic")
            or rule_node.get("condition")
            or "and"
        )

        normalized_operator = str(operator).strip().lower()

        if normalized_operator in {"and", "all", "&&"}:
            return all(children_results)

        if normalized_operator in {"or", "any", "||"}:
            return any(children_results)

        if normalized_operator in {"not", "!"}:
            if len(children_results) != 1:
                raise ValueError(
                    f"Блок {path} с оператором NOT должен содержать "
                    f"ровно одно условие"
                )

            return not children_results[0]

        raise ValueError(
            f"Неизвестный логический оператор блока {path}: {operator}"
        )

    @staticmethod
    def _parse_rule_expression(
        rule_expression: str | Mapping[str, Any],
    ) -> dict[str, Any]:
        """Преобразовать rule_expression в словарь."""
        if isinstance(rule_expression, str):
            try:
                parsed = json.loads(rule_expression)
            except json.JSONDecodeError as error:
                raise ValueError(
                    "rule_expression содержит некорректный JSON"
                ) from error
        else:
            parsed = dict(rule_expression)

        if not isinstance(parsed, dict):
            raise TypeError(
                "Корневой элемент rule_expression должен быть объектом"
            )

        return parsed

    @staticmethod
    def deserialize_check_result(
        log: LogAchievements,
    ) -> dict[str, Any]:
        """Десериализовать check_result конкретной записи лога."""
        try:
            result = json.loads(log.check_result)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Лог {log.uuid} содержит некорректный check_result"
            ) from error

        if not isinstance(result, dict):
            raise TypeError(
                f"check_result лога {log.uuid} должен быть объектом"
            )

        return result

    @staticmethod
    def _json_default(value: Any) -> Any:
        """Сериализация дополнительных типов в JSON."""
        if isinstance(value, datetime):
            return value.isoformat()

        raise TypeError(
            f"Объект типа {type(value).__name__} нельзя записать в JSON"
        )