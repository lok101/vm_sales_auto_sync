from dataclasses import dataclass

from beartype import beartype

from src.domain.value_objects.ids.product_id import ProductId
from src.domain.value_objects.ids.product_moy_sklad_id import ProductMoySkaldId


@beartype
@dataclass(frozen=True, slots=True, kw_only=True)
class Product:
    id: ProductId
    name: str

    def __hash__(self):
        return hash(self.id)
