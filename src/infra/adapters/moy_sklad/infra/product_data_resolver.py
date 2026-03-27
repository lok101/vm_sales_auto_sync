import logging
from dataclasses import dataclass
from uuid import UUID

from beartype import beartype
from moy_sklad_api import MoySkladAPIClient, ProductModel, Filter, ProductType, BundleModel

logger = logging.getLogger(__name__)

_product_paths: list[str] = ["Основной склад/СНЕК", "Основной склад/СНЕК/Еда"]
_bundle_paths: list[str] = [""]


@beartype
@dataclass(slots=True, kw_only=True)
class MoySkaldProductDataResolverAdapter:
    moy_sklad_api_client: MoySkladAPIClient

    _product_id_by_code: dict[str, UUID] = None
    _product_type_by_code: dict[str, ProductType] = None

    async def load(self):
        await self._load_products()
        await self._load_bundles()

    async def _load_products(self):
        products: list[ProductModel] = await self.moy_sklad_api_client.get_products(
            filters=[
                Filter(field="pathName", value=_product_paths),
            ]
        )

        if not products:
            logger.warning("От API мой склад не были получены товары.")
            return

        product_id_by_code: dict[str, UUID] = {}
        product_type_by_code: dict[str, ProductType] = {}

        for product in products:
            product_id_by_code[product.code] = product.id
            product_type_by_code[product.code] = ProductType.SINGLE_PRODUCT

        if self._product_id_by_code is None:
            self._product_id_by_code = product_id_by_code

        else:
            self._product_id_by_code.update(product_id_by_code)

        if self._product_type_by_code is None:
            self._product_type_by_code = product_type_by_code

        else:
            self._product_type_by_code.update(product_type_by_code)

    async def _load_bundles(self):
        bundles: list[BundleModel] = await self.moy_sklad_api_client.get_bundles(
            filters=[
                Filter(field="pathName", value=_bundle_paths),
            ]
        )

        if not bundles:
            logger.warning("От API мой склад не были получены комплекты.")
            return

        product_id_by_code: dict[str, UUID] = {}
        product_type_by_code: dict[str, ProductType] = {}

        for bundle in bundles:
            product_id_by_code[bundle.code] = bundle.id
            product_type_by_code[bundle.code] = ProductType.COMPOSITE_PRODUCT

        if self._product_id_by_code is None:
            self._product_id_by_code = product_id_by_code

        else:
            self._product_id_by_code.update(product_id_by_code)

        if self._product_type_by_code is None:
            self._product_type_by_code = product_type_by_code

        else:
            self._product_type_by_code.update(product_type_by_code)

    async def resolve_id_by_code(self, code: str) -> UUID | None:
        if self._product_id_by_code is None:
            await self.load()

        return self._product_id_by_code.get(code)

    async def resolve_type_by_code(self, code: str) -> ProductType | None:
        if self._product_type_by_code is None:
            await self.load()

        return self._product_type_by_code.get(code)
