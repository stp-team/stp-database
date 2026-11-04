from sqlalchemy import Enum, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from stp_database.models.base import Base


class ServicesParametrs(Base):
    __tablename__ = "services_parametrs"
    __table_args__ = (
        UniqueConstraint("service", "name", name="services_parametrs_pk"),
    )

    service: Mapped[str] = mapped_column(
        String(250), nullable=False
    )
    name: Mapped[str] = mapped_column(
        String(250), nullable=False
    )
    type: Mapped[str] = mapped_column(
        Enum("int", "float", "string", "text", "json"),
        nullable=False,
    )
    value: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # В БД используется UNIQUE KEY
    __mapper_args__ = {
        "primary_key": [service, name],
    }
    def __repr__(self):
        return (
            f"<ParserParameter "
            f"service={self.service} "
            f"name={self.name}>"
        )
