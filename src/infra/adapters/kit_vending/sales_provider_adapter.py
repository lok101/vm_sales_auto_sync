import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol

from beartype import beartype
from kit_api import KitVendingAPIClient, SaleModel

from src.app.ports import VendingMachineSalesProviderPort
from src.domain.entities import Sale
from src.domain.entities.product import Product
from src.domain.value_objects import VMId, ProductId
from src.infra.adapters.kit_vending.exceptions import SaleProviderMappingException, SalesProviderAdapterException
from src.project_timezone import PROJECT_TIMEZONE

logger = logging.getLogger(__name__)


class VendingMachineDataResolverPort(Protocol):
    def resolve_vm_id_by_ex_id(self, ex_id: int) -> VMId | None: pass


def _parse_product_name(product_name: str) -> tuple[str, str]:
    if "|" not in product_name:
        raise SaleProviderMappingException(f"В имени товара '{product_name}' не встречен символ разделитель '|'.")

    parts = product_name.split("|")

    return parts[0].strip(), parts[1].strip()


@beartype
@dataclass(frozen=True, slots=True, kw_only=True)
class VendingMachineSalesProviderAdapter(VendingMachineSalesProviderPort):
    kit_vending_api_client: KitVendingAPIClient

    vm_data_resolver: VendingMachineDataResolverPort

    async def get_sales_for_day(self, day: date) -> list[Sale]:
        res: list[Sale] = []

        day_start, day_end = self._get_dt_period(day)

        sales: list[SaleModel] = await self.kit_vending_api_client.get_sales(from_date=day_start, to_date=day_end)

        for sale_model in sales:
            try:
                sale: Sale = self._map_to_domain(sale_model)
                res.append(sale)

            except SalesProviderAdapterException as ex:
                logger.error(ex)

        return res

    def _map_to_domain(self, sale: SaleModel) -> Sale:
        vm_ex_id: int = sale.vending_machine_id
        vm_id: VMId | None = self.vm_data_resolver.resolve_vm_id_by_ex_id(vm_ex_id)

        if vm_id is None:
            raise SaleProviderMappingException(f"Не удалось получить Id для аппарата с внешним Id: {vm_ex_id}")

        product_code, product_name = _parse_product_name(sale.product_name)

        product_id: ProductId = ProductId(product_code)
        product: Product = Product(
            name=product_name,
            id=product_id,
        )

        return Sale(
            vm_id=vm_id,
            product=product
        )

    @staticmethod
    def _get_dt_period(day: date) -> tuple[datetime, datetime]:
        from_date: datetime = datetime.combine(day, datetime.min.time(), tzinfo=PROJECT_TIMEZONE)
        to_date: datetime = datetime.combine(day, datetime.max.time(), tzinfo=PROJECT_TIMEZONE)
        return from_date, to_date
