import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from beartype import beartype
from kit_api import KitVendingAPIClient, MatricesKitCollection, GoodsMatrixModel, RecipeMatrixModel
from kit_api.client import KitAPIAccount
from kit_api.models import GoodsCell, RecipeCell

from src.app.dtos.kit_vending_account_dto import KitVendingAccountDTO

logger = logging.getLogger(__name__)


@runtime_checkable
class DrinkDataResolverPort(Protocol):
    async def resolve_product_name_by_drink_id(self, drink_id: int) -> str: pass


@beartype
@dataclass(slots=True, kw_only=True)
class ProductByMatrixResolverAdapter:
    kit_vending_api_client: KitVendingAPIClient
    drinks_data_resolver: DrinkDataResolverPort
    accounts: list[KitVendingAccountDTO]

    _product_names_by_matrix_cords: dict[int, dict[int, str]] = None

    async def load(self):
        matrices: list[GoodsMatrixModel | RecipeMatrixModel] = []

        for account in self.accounts:
            kit_account = KitAPIAccount(
                login=account.login,
                password=account.password,
                company_id=account.company_id
            )

            matrices_collect: MatricesKitCollection = await self.kit_vending_api_client.get_product_matrices(
                account=kit_account
            )

            if not matrices_collect:
                logger.debug(f"Для аккаунта '{account.name}' не были получены товарные матрицы.")
                continue

            goods_matrics = matrices_collect.get_snack_matrices()
            drinks_matrices = matrices_collect.get_recipes_matrices()

            matrices.extend(goods_matrics)
            matrices.extend(drinks_matrices)

        product_names_by_matrix_cords: dict[int, dict[int, str]] = defaultdict(lambda: defaultdict(str))

        for matrix in matrices:
            for cell in matrix.cells:
                product_name: str | None = None

                if isinstance(cell, GoodsCell):
                    product_name: str = cell.product_name

                elif isinstance(cell, RecipeCell):
                    product_name: str | None = await self.drinks_data_resolver.resolve_product_name_by_drink_id(
                        cell.recipe_id
                    )

                if product_name is None:
                    logger.debug(
                        f"Не удалось определить имя товара для ячейки номер {cell.line_number}, "
                        f"матрица: {matrix.name}."
                    )
                    continue

                product_names_by_matrix_cords[matrix.id][cell.line_number] = product_name

        self._product_names_by_matrix_cords = product_names_by_matrix_cords

    async def resolve_product_name_by_position_in_matrix(self, matrix_id: int, line_number: int) -> str:
        if not self._product_names_by_matrix_cords:
            await self.load()

        return self._product_names_by_matrix_cords.get(matrix_id, {}).get(line_number)
