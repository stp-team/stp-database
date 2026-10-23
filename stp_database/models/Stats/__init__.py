"""Инициализация моделей Stats."""

from .head_premium import HeadPremium
from .sl import SL
from .spec_kpi import SpecDayKPI, SpecMonthKPI, SpecWeekKPI
from .spec_premium import SpecPremium
from .tests import AssignedTest
from .tutors_schedule import TutorsSchedule
from .questioner import QuestionerMonth, QuestionerChats
from .sales_rg import SalesRg

__all__ = [
    "HeadPremium",
    "SpecDayKPI",
    "SpecMonthKPI",
    "SpecWeekKPI",
    "SpecPremium",
    "SL",
    "AssignedTest",
    "TutorsSchedule",
    "QuestionerMonth",
    "QuestionerChats",
    "SalesRg",
]
