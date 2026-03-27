import logging
import re
from dataclasses import dataclass

from beartype import beartype
from kit_api import KitVendingAPIClient, VendingMachineModel

from src.domain.value_objects import VMId
from src.infra.adapters.kit_vending.exceptions import ResolverCacheLoadingError

logger = logging.getLogger(__name__)


def _extract_vending_machine_id(vending_machine_name: str) -> str | None:
    pattern = r'\[(\d+)\]'
    match = re.search(pattern, vending_machine_name)

    if match:
        return match.group(1)

    return None


@beartype
@dataclass(slots=True, kw_only=True)
class VendingMachineDataResolverAdapter:
    kit_vending_api_client: KitVendingAPIClient

    _id_by_vm_ex_id: dict[int, VMId] | None = None

    async def load(self) -> None:

        vending_machines: list[VendingMachineModel] = await self.kit_vending_api_client.get_vending_machines()

        if not vending_machines:
            raise ResolverCacheLoadingError("От API кит вендинг не были получены аппараты.")

        id_by_vm_ex_id: dict[int, VMId] = {}

        for vm in vending_machines:
            _id: str | None = _extract_vending_machine_id(vm.name)
            ex_id: int = vm.id

            if _id is None or not ex_id:
                continue

            vm_id: VMId = VMId(_id)

            id_by_vm_ex_id[ex_id] = vm_id

        self._id_by_vm_ex_id = id_by_vm_ex_id

    async def resolve_vm_id_by_ex_id(self, ex_id: int) -> VMId | None:
        if self._id_by_vm_ex_id is None:
            await self.load()

        return self._id_by_vm_ex_id.get(ex_id)
