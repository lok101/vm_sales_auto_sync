import logging
from dataclasses import dataclass

from beartype import beartype
from kit_api import KitVendingAPIClient, RecipeModel
from kit_api.client import KitAPIAccount

from src.app.dtos.kit_vending_account_dto import KitVendingAccountDTO

logger = logging.getLogger(__name__)


@beartype
@dataclass(slots=True, kw_only=True)
class DrinkDataResolverAdapter:
    kit_vending_api_client: KitVendingAPIClient

    accounts: list[KitVendingAccountDTO]

    _recipe_name_by_id: dict[int, str] = None

    async def load(self):
        all_recipes: list[RecipeModel] = []

        for account in self.accounts:
            kit_account = KitAPIAccount(
                login=account.login,
                password=account.password,
                company_id=account.company_id
            )

            recipes: list[RecipeModel] = await self.kit_vending_api_client.get_recipes(account=kit_account)

            if not recipes:
                logger.debug(f"Для аккаунта '{account.name}' не были получены рецепты напитков.")
                continue

            all_recipes.extend(recipes)

        recipe_name_by_id: dict[int, str] = {}

        for recipe in all_recipes:
            recipe_name_by_id[recipe.id] = recipe.name

        self._recipe_name_by_id = recipe_name_by_id

    async def resolve_product_name_by_drink_id(self, drink_id: int) -> str:
        if self._recipe_name_by_id is None:
            await self.load()

        return self._recipe_name_by_id.get(drink_id)
