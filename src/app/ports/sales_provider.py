from abc import ABC, abstractmethod
from datetime import date

from src.domain.entities.sale import Sale


class VendingMachineSalesProviderPort(ABC):
    @abstractmethod
    async def get_sales_for_day(self, day: date) -> list[Sale]: pass
