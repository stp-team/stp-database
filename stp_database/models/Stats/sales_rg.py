from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from stp_database.models.base import Base


class SalesRg(Base):
    """План/Факт продаж групп РГ за календарный месяц."""
    __tablename__ = "SalesRg"

    employee_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    extraction_period: Mapped[datetime] = mapped_column(DateTime, primary_key=True, nullable=False)
    division: Mapped[str | None] = mapped_column(String(3), nullable=True)

    # План в цифрах.
    router_plan: Mapped[int | None] = mapped_column(Integer)
    tv_plan: Mapped[int | None] = mapped_column(Integer)
    video_plan: Mapped[int | None] = mapped_column(Integer)
    dmf_plan: Mapped[int | None] = mapped_column(Integer)
    credit_plan: Mapped[int | None] = mapped_column(Integer)
    ps_plan: Mapped[int | None] = mapped_column(Integer)
    fullduplex_plan: Mapped[int | None] = mapped_column(Integer)
    vas_plan: Mapped[int | None] = mapped_column(Integer)
    services_plan: Mapped[int | None] = mapped_column(Integer)
    general_plan: Mapped[int | None] = mapped_column(Integer)

    # Факт в цифрах.
    router_fact: Mapped[int | None] = mapped_column(Integer)
    tv_fact: Mapped[int | None] = mapped_column(Integer)
    video_fact: Mapped[int | None] = mapped_column(Integer)
    dmf_fact: Mapped[int | None] = mapped_column(Integer)

    # Прочее.
    ps_fact: Mapped[int | None] = mapped_column(Integer)
    fullduplex_fact: Mapped[int | None] = mapped_column(Integer)
    vas_fact: Mapped[int | None] = mapped_column(Integer)
    services_fact: Mapped[int | None] = mapped_column(Integer)
    general_fact: Mapped[int | None] = mapped_column(Integer)

    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.now(), onupdate=datetime.now())