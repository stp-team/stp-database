"""Инициализация моделей Stats."""

from .head_premium import HeadPremium
from .spec_kpi import SpecDayKPI, SpecMonthKPI, SpecWeekKPI
from .spec_premium import SpecPremium
from .questioner import QuestionerMonth, QuestionerChats
from .sales_rg import SalesRg

__all__ = [
    "HeadPremium",
    "SpecDayKPI",
    "SpecMonthKPI",
    "SpecWeekKPI",
    "SpecPremium",
    "QuestionerMonth",
    "QuestionerChats",
    "SalesRg",
]
