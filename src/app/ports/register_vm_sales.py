from abc import ABC, abstractmethod

from src.domain.value_objects import VMSales


class RegisterSalesPort(ABC):
    @abstractmethod
    async def register_vm_sales(self, vm_sales: VMSales): pass
