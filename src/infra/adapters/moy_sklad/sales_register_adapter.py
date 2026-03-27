import logging
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import runtime_checkable, Protocol, Counter
from uuid import UUID

from beartype import beartype
from moy_sklad_api import MoySkladAPIClient, ProductType

from src.app.ports import RegisterSalesPort
from src.domain.entities import Sale, Product
from src.domain.value_objects import VMSales, Money, VMId
from src.infra.adapters.moy_sklad.enums import Organizations, Buyers, SalesChannels, Projects
from src.infra.adapters.moy_sklad.exceptions import MoySkaldSalesRegisterResolutionError
from src.project_timezone import PROJECT_TIMEZONE

logger = logging.getLogger(__name__)


@runtime_checkable
class WarehouseDataResolverPort(Protocol):
    async def resolve_id_by_code(self, code: str) -> UUID | None: pass


@runtime_checkable
class ProductDataResolverPort(Protocol):
    async def resolve_id_by_code(self, code: str) -> UUID | None: pass

    async def resolve_type_by_code(self, code: str) -> ProductType | None: pass


@beartype
@dataclass(frozen=True, slots=True, kw_only=True)
class MoySkaldSalesRegisterAdapter(RegisterSalesPort):
    moy_sklad_api_client: MoySkladAPIClient

    warehouse_data_resolver: WarehouseDataResolverPort
    product_data_resolver: ProductDataResolverPort

    DOCUMENT_MOMENT_HOUR: int = 23
    DOCUMENT_MOMENT_MINUTE: int = 55

    async def register_vm_sales(self, vm_sales: VMSales):
        warehouse_id: UUID | None = await self.warehouse_data_resolver.resolve_ex_id_by_code(vm_sales.id.value)

        if warehouse_id is None:
            raise MoySkaldSalesRegisterResolutionError(
                f"Не удалось получить МС Id для аппарата '{vm_sales.id.value}'.'"
            )

        organization_id: UUID = Organizations.ORLOV.value
        agent_id: UUID = Buyers.RETAIL_BUYER.value
        project_id: UUID = Projects.MY_MK.value
        sales_channel_id: UUID = self._get_sales_channel(vm_sales.id)

        moment: datetime = self._get_document_moment(vm_sales.day)

        sales_by_positons: dict[tuple[Product, Money], int] = self._group_sales_by_positions(vm_sales.sales)

        positions: list[tuple[UUID, int, int, ProductType]] = []

        for position, quantity in sales_by_positons.items():
            product, price = position

            product_ex_id: UUID | None = await self.product_data_resolver.resolve_ex_id_by_code(product.id.value)

            if product_ex_id is None:
                raise MoySkaldSalesRegisterResolutionError(
                    f"Не удалось получить МС Id для товара '{product.name}'."
                )

            product_type: ProductType | None = await self.product_data_resolver.resolve_type_by_code(product.id.value)

            if product_ex_id is None:
                raise MoySkaldSalesRegisterResolutionError(
                    f"Не удалось получить тип продукта для товара '{product.name}'."
                )

            positions.append((product_ex_id, quantity, price.kopeck, product_type))

        await self.moy_sklad_api_client.create_demand(
            warehouse_id=warehouse_id,
            positions=positions,
            moment=moment,
            organization_id=organization_id,
            agent_id=agent_id,
            project_id=project_id,
            sales_channel_id=sales_channel_id,
        )

    @staticmethod
    def _group_sales_by_positions(sales: list[Sale]) -> dict[tuple[Product, Money], int]:
        keys: list[tuple[Product, Money]] = [(sale.product, sale.price) for sale in sales]
        cnt = Counter(keys)
        return cnt

    def _get_document_moment(self, day: date):
        return datetime.combine(
            day,
            time(
                hour=self.DOCUMENT_MOMENT_HOUR,
                minute=self.DOCUMENT_MOMENT_MINUTE
            )
        ).replace(tzinfo=PROJECT_TIMEZONE)

    @staticmethod
    def _get_sales_channel(vm_id: VMId) -> UUID:
        # Id снеков начинаются только с пятёрки.
        return SalesChannels.SNACK.value if vm_id.value.startswith("5") else SalesChannels.VENDING_COFFEE.value
