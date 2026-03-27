import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol, runtime_checkable

from beartype import beartype
from kit_api import KitVendingAPIClient, SaleModel

from src.app.ports import VendingMachineSalesProviderPort
from src.domain.entities import Sale
from src.domain.entities.product import Product
from src.domain.value_objects import VMId, ProductId, Money
from src.infra.adapters.kit_vending.exceptions import SaleProviderMappingException, SalesProviderAdapterException, \
    SaleProviderResolutionException
from src.project_timezone import PROJECT_TIMEZONE

logger = logging.getLogger(__name__)


@runtime_checkable
class VendingMachineDataResolverPort(Protocol):
    async def resolve_vm_id_by_ex_id(self, ex_id: int) -> VMId: pass


@runtime_checkable
class ProductByMatrixResolverPort(Protocol):
    async def resolve_product_name_by_position_in_matrix(self, matrix_id: int, line_number: int) -> str: pass


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
    product_by_matrix_resolver: ProductByMatrixResolverPort

    async def get_sales_for_day(self, day: date) -> list[Sale]:
        res: list[Sale] = []

        day_start, day_end = self._get_dt_period(day)

        sales: list[SaleModel] = await self.kit_vending_api_client.get_sales(from_date=day_start, to_date=day_end)

        for sale_model in sales:
            product: Product | None = None

            if "переплата" in sale_model.product_name.lower():
                logger.info(f"Встречена позиция 'Переплата', она будет пропущена.")
                continue

            if "товар" in sale_model.product_name.lower():
                product_name: str | None = await self.product_by_matrix_resolver.resolve_product_name_by_position_in_matrix(
                    matrix_id=sale_model.matrix_id,
                    line_number=sale_model.line
                )

                if product_name is None:
                    raise SaleProviderResolutionException(
                        f"Не удалось определить товар по ни по имени, ни по матрице. "
                        f"Имя товара: {sale_model.product_name}. "
                        f"Аппарат: {sale_model.vending_machine_name}. "
                        f"Номер линии: {sale_model.line}."
                    )

                product: Product = self._map_to_product(product_name)

            try:
                sale: Sale = await self._map_to_domain(sale_model, product)
                res.append(sale)

            except SalesProviderAdapterException as ex:
                logger.error(ex)

        return res

    async def _map_to_domain(self, sale: SaleModel, product: Product | None) -> Sale:
        vm_ex_id: int = sale.vending_machine_id
        vm_id: VMId | None = await self.vm_data_resolver.resolve_vm_id_by_ex_id(vm_ex_id)

        if vm_id is None:
            raise SaleProviderMappingException(f"Не удалось получить Id для аппарата с внешним Id: {vm_ex_id}")

        if product is None:
            product: Product = self._map_to_product(sale.product_name)

        price: Money = Money(kopeck=int(sale.price * 100)) # приходит в рублях, переводим в копейки.

        return Sale(
            vm_id=vm_id,
            vm_name=sale.vending_machine_name,
            product=product,
            price=price,
        )

    @staticmethod
    def _get_dt_period(day: date) -> tuple[datetime, datetime]:
        from_date: datetime = datetime.combine(day, datetime.min.time(), tzinfo=PROJECT_TIMEZONE)
        to_date: datetime = datetime.combine(day, datetime.max.time(), tzinfo=PROJECT_TIMEZONE)
        return from_date, to_date

    @staticmethod
    def _map_to_product(product_name: str) -> Product:
        product_code, product_name = _parse_product_name(product_name)
        product_id: ProductId = ProductId(product_code)
        return Product(
            name=product_name,
            id=product_id,
        )
