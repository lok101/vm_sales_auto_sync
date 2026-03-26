from abc import ABC, abstractmethod
from datetime import date

from src.domain.value_objects import VMId


class SalesRegisterDataProviderPort(ABC):
    @abstractmethod
    async def is_sales_registered(self, day: date, vm_id: VMId) -> bool: pass
