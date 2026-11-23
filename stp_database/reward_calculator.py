"""
Универсальный математический калькулятор наград.
"""

import json

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any


class RewardFormulaError(ValueError):
    """Некорректная формула или ошибка расчёта."""


# Разрешённые числовые показатели уже
# загружаемых ресурсов.
ALLOWED_FIELDS = {
    "universal": {
        "sales", "contacts_count",
        "csat", "aht", "flr", "csi",
        "pok", "delay",
        "sales_conversion",
        "sales_potential",
        "sales_potential_conversion",
        "services", "services_conversion",
        "q_answered", "q_asked",
        "q_asked_conversion", "thanks",
    },
    "spec_premium": {
        "contacts_count", "aht",
        "aht_normative", "aht_pers_normative",
        "aht_normative_rate",
        "csat", "csat_normative",
        "csat_pers_normative",
        "csat_normative_rate",
        "csi", "csi_normative",
        "csi_normative_rate",
        "gok", "gok_normative",
        "gok_pers_normative",
        "gok_normative_rate",
        "revenue", "revenue_normative",
        "revenue_normative_rate",
        "raw_premium", "total_premium",
    },
    "rg_premium": {
        "gok", "gok_normative",
        "gok_pers_normative",
        "gok_normative_rate",
        "flr", "flr_normative",
        "flr_pers_normative",
        "flr_normative_rate",
        "aht", "aht_normative",
        "aht_pers_normative",
        "aht_normative_rate",
        "raw_premium", "total_premium",
    },
    "questioner_month": {
        "count_questions_asked",
        "count_questions_answered",
        "average_duration_asked_question",
        "average_duration_answered_question",
        "rate_requester", "rate_responder",
    },
    "employee": {
        "tutor_type",
        "tutor_subtype",
    },
    "tutors": {
        "shifts_count",
        "trainee_count",
    },
}

MAX_DEPTH = 12
MAX_NODES = 128
MAX_ARGS = 16
MAX_ABS_VALUE = Decimal("1000000000")
MAX_REWARD = 1000000


def _number(value: Any) -> Decimal:
    """Строгое преобразование числового значения."""

    if type(value) not in (int, float, Decimal):
        raise RewardFormulaError(
            f"Ожидалось число, получено {type(value).__name__}"
        )

    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise RewardFormulaError(
            "Некорректное числовое значение"
        ) from exc

    if (
        not result.is_finite()
        or abs(result) > MAX_ABS_VALUE
    ):
        raise RewardFormulaError(
            "Число вне допустимого диапазона"
        )

    return result


def _parse(formula: Any) -> dict:
    if isinstance(formula, str):
        try:
            formula = json.loads(formula)
        except json.JSONDecodeError as exc:
            raise RewardFormulaError(
                "Невалидный JSON reward_calc"
            ) from exc

    if not isinstance(formula, dict):
        raise RewardFormulaError(
            "reward_calc должен быть JSON-объектом"
        )

    return formula


def validate_reward_formula(
    formula: Any,
) -> set[tuple[str, str]]:
    """
    Проверяет структуру формулы.

    Возвращает набор используемых
    пар (resource, variable).
    """

    document = _parse(formula)
    references = set()
    nodes = 0

    def walk(node: Any, depth: int) -> None:
        nonlocal nodes

        nodes += 1

        if depth > MAX_DEPTH or nodes > MAX_NODES:
            raise RewardFormulaError(
                "Формула превышает ограничения сложности"
            )

        if not isinstance(node, dict):
            raise RewardFormulaError(
                "Каждый элемент формулы должен быть объектом"
            )

        op = node.get("op")

        if op == "const":
            if set(node) != {"op", "value"}:
                raise RewardFormulaError(
                    "const требует только op и value"
                )

            _number(node["value"])
            return

        if op == "ref":
            if set(node) != {
                "op", "resource", "variable"
            }:
                raise RewardFormulaError(
                    "ref требует op, resource, variable"
                )

            resource = node["resource"]
            variable = node["variable"]

            if (
                not isinstance(resource, str)
                or not isinstance(variable, str)
                or variable not in ALLOWED_FIELDS.get(
                    resource, set()
                )
            ):
                raise RewardFormulaError(
                    f"Недопустимое поле {resource}.{variable}"
                )

            references.add((resource, variable))
            return

        if op == "lookup":
            if set(node) != {"op", "by", "cases"}:
                raise RewardFormulaError(
                    "lookup требует op, by, cases"
                )

            cases = node["cases"]

            if (
                not isinstance(cases, dict)
                or not 1 <= len(cases) <= 32
            ):
                raise RewardFormulaError(
                    "Некорректная таблица тарифов"
                )

            for key, value in cases.items():
                if not isinstance(key, str) or len(key) > 64:
                    raise RewardFormulaError(
                        "Некорректный ключ тарифа"
                    )
                _number(value)

            walk(node["by"], depth + 1)
            return

        arity = {
            "add": (2, MAX_ARGS),
            "sub": (2, 2),
            "mul": (2, MAX_ARGS),
            "div": (2, 2),
            "min": (2, MAX_ARGS),
            "max": (2, MAX_ARGS),
            "round": (1, 1),
        }

        if op not in arity:
            raise RewardFormulaError(
                f"Неизвестная операция: {op}"
            )

        if set(node) != {"op", "args"}:
            raise RewardFormulaError(
                f"{op}: ожидаются только op и args"
            )

        args = node["args"]
        minimum, maximum = arity[op]

        if (
            not isinstance(args, list)
            or not minimum <= len(args) <= maximum
        ):
            raise RewardFormulaError(
                f"Некорректные аргументы операции {op}"
            )

        for child in args:
            walk(child, depth + 1)

    walk(document, 0)

    return references


def calculate_reward(
    formula: Any,
    resources: Mapping[str, Any],
) -> int:
    """
    Возвращает готовое целое количество баллов.
    Не обращается к БД.
    """

    document = _parse(formula)
    validate_reward_formula(document)

    def evaluate(node: dict) -> Decimal:
        op = node["op"]

        if op == "const":
            return _number(node["value"])

        if op == "ref":
            resource_name = node["resource"]
            variable = node["variable"]

            resource = resources.get(resource_name)

            if resource is None:
                raise RewardFormulaError(
                    f"Отсутствует ресурс {resource_name}"
                )

            if isinstance(resource, Mapping):
                value = resource.get(variable)
            else:
                value = getattr(
                    resource,
                    variable,
                    None,
                )

            if value is None:
                raise RewardFormulaError(
                    f"Отсутствует значение "
                    f"{resource_name}.{variable}"
                )

            return _number(value)

        if op == "lookup":
            selector = evaluate(node["by"])

            key = format(selector, "f")
            if "." in key:
                key = key.rstrip("0").rstrip(".")

            if key not in node["cases"]:
                raise RewardFormulaError(
                    f"Не найден тариф для значения {key}"
                )

            return _number(node["cases"][key])

        values = [
            evaluate(child)
            for child in node["args"]
        ]

        if op == "add":
            result = sum(values, Decimal(0))

        elif op == "sub":
            result = values[0] - values[1]

        elif op == "mul":
            result = Decimal(1)
            for value in values:
                result *= value
                result = _number(result)

        elif op == "div":
            if values[1] == 0:
                raise RewardFormulaError(
                    "Деление на ноль"
                )
            result = values[0] / values[1]

        elif op == "min":
            result = min(values)

        elif op == "max":
            result = max(values)

        elif op == "round":
            result = values[0].quantize(
                Decimal("1"),
                rounding=ROUND_HALF_UP,
            )

        else:
            raise RewardFormulaError(
                f"Неизвестная операция {op}"
            )

        return _number(result)

    result = evaluate(document)

    if result != result.to_integral_value():
        raise RewardFormulaError(
            "Награда должна быть целым числом. "
            "Добавь операцию round."
        )

    if not 0 <= result <= MAX_REWARD:
        raise RewardFormulaError(
            f"Награда должна быть от 0 до {MAX_REWARD}"
        )

    return int(result)
