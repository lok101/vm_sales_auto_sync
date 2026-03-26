import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from beartype import beartype

from src.app.ports import (
    RegisterSalesPort,
    VendingMachineSalesProviderPort,
    SalesRegisterDataProviderPort,
)

from src.domain.entities import Sale
from src.domain.value_objects import VMId, VMSales

logger = logging.getLogger(__name__)


@beartype
@dataclass(frozen=True, slots=True, kw_only=True)
class RegisterVendingMachinesSales:
    sales_data_provider: VendingMachineSalesProviderPort
    sales_registered_data_provider: SalesRegisterDataProviderPort
    register_sales_port: RegisterSalesPort

    async def execute(self, day: date):
        sales_for_day: list[Sale] = await self.sales_data_provider.get_sales_for_day(day)

        if not sales_for_day:
            logger.info(f"Не были получены продажи за указанные день: {day.isoformat()}.")
            return

        sales_by_vending_machines: list[VMSales] = self._group_sales_by_vending_machine(sales_for_day)

        for vm_sales in sales_by_vending_machines:
            vm_id: VMId = vm_sales.id

            sales_already_registered: bool = await self.sales_registered_data_provider.is_sales_registered(day, vm_id)

            if sales_already_registered:
                logger.info(
                    f"Для аппарата '{vm_id}' уже есть зарегистрированные продажи "
                    f"за переданный день: {day.isoformat()}."
                )
                return

            await self.register_sales_port.register_vm_sales(vm_sales)

            logger.info(f"Продажи для аппарата '{vm_id}' успешно зарегистрированы.")

    @staticmethod
    def _group_sales_by_vending_machine(sales: list[Sale]) -> list[VMSales]:

        sales_data: dict[VMId, list[Sale]] = defaultdict(list)

        for sale in sales:
            sales_data[sale.vm_id].append(sale)

        return [
            VMSales(
                id=vm_id,
                sales=sales
            ) for vm_id, sales in sales_data.items()
        ]
