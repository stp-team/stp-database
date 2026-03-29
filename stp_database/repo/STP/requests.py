"""Репозиторий для работы с моделями БД STP."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from stp_database.repo.STP.achievement import AchievementsRepo
from stp_database.repo.STP.achievements_new import AchievementsNewRepo
from stp_database.repo.STP.broadcast import BroadcastRepo
from stp_database.repo.STP.employee import EmployeeRepo
from stp_database.repo.STP.event_log import EventLogRepo
from stp_database.repo.STP.exchange import ExchangeRepo
from stp_database.repo.STP.files import FilesRepo
from stp_database.repo.STP.group import GroupRepo
from stp_database.repo.STP.group_member import GroupMemberRepo
from stp_database.repo.STP.product import ProductsRepo
from stp_database.repo.STP.purchase import PurchaseRepo
from stp_database.repo.STP.transactions import TransactionRepo


@dataclass
class MainRequestsRepo:
    """Репозиторий для обработки операций с БД. Этот класс содержит все репозитории для моделей базы данных STP.

    Ты можешь добавить дополнительные репозитории в качестве свойств к этому классу, чтобы они были легко доступны.
    """

    session: AsyncSession

    @property
    def employee(self) -> EmployeeRepo:
        """Инициализация репозитория Employee с сессией для работы с записями сотрудников."""
        return EmployeeRepo(self.session)

    @property
    def achievement(self) -> AchievementsRepo:
        """Инициализация репозитория AchievementsRepo с сессией для работы с достижениями."""
        return AchievementsRepo(self.session)

    @property
    def achievement_new(self) -> AchievementsNewRepo:
        """Инициализация репозитория AchievementsNewRepo с сессией для работы с достижениями."""
        return AchievementsNewRepo(self.session)

    @property
    def product(self) -> ProductsRepo:
        """Инициализация репозитория ProductsRepo с сессией для работы с предметами."""
        return ProductsRepo(self.session)

    @property
    def purchase(self) -> PurchaseRepo:
        """Инициализация репозитория PurchaseRepo с сессией для работы с покупками."""
        return PurchaseRepo(self.session)

    @property
    def transaction(self) -> TransactionRepo:
        """Инициализация репозитория TransactionRepo с сессией для работы с транзакциями."""
        return TransactionRepo(self.session)

    @property
    def broadcast(self) -> BroadcastRepo:
        """Инициализация репозитория BroadcastRepo с сессией для работы с рассылками."""
        return BroadcastRepo(self.session)

    @property
    def upload(self) -> FilesRepo:
        """Инициализация репозитория ScheduleLogRepo с сессией для работы с загрузкой файлов."""
        return FilesRepo(self.session)

    @property
    def group(self) -> GroupRepo:
        """Инициализация репозитория GroupRepo с сессией для работы с управляемыми группами."""
        return GroupRepo(self.session)

    @property
    def group_member(self) -> GroupMemberRepo:
        """Инициализация репозитория GroupMemberRepo с сессией для работы с участниками отслеживаемых групп."""
        return GroupMemberRepo(self.session)

    @property
    def exchange(self) -> ExchangeRepo:
        """Инициализация репозитория ExchangeRepo с сессией для работы с биржей подменов."""
        return ExchangeRepo(self.session)

    @property
    def event_log(self) -> EventLogRepo:
        """Инициализация репозитория EventLogRepo с сессией для работы с логами ивентов."""
        return EventLogRepo(self.session)
