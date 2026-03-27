import logging
from dataclasses import dataclass
from uuid import UUID

from beartype import beartype
from moy_sklad_api import MoySkladAPIClient, WarehouseModel, Filter

logger = logging.getLogger(__name__)

_warehouse_paths: list[str] = ["СНЭК ТА", "Кофейни (Мои МК)"]


@beartype
@dataclass(slots=True, kw_only=True)
class MoySkaldWarehouseDataResolverAdapter:
    moy_sklad_api_client: MoySkladAPIClient

    _warehouse_id_by_code: dict[str, UUID] = None

    async def load(self):
        warehouses: list[WarehouseModel] = await self.moy_sklad_api_client.get_warehouses(
            filters=[
                Filter(field="pathName", value=_warehouse_paths)
            ]
        )

        if not warehouses:
            logger.warning("От API мой склад не были получены склады.")
            return

        warehouse_id_by_code: dict[str, UUID] = {}

        for wh in warehouses:
            code: str | None = wh.code
            _id: UUID = wh.id

            if code is None:
                continue

            warehouse_id_by_code[code] = _id

        self._warehouse_id_by_code = warehouse_id_by_code

    async def resolve_id_by_code(self, code: str) -> UUID | None:
        if self._warehouse_id_by_code is None:
            await self.load()

        return self._warehouse_id_by_code.get(code)
