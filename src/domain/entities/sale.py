from dataclasses import dataclass
from beartype import beartype

from src.domain.entities.product import Product
from src.domain.value_objects import VMId, Money


@beartype
@dataclass(frozen=True, slots=True, kw_only=True)
class Sale:
    vm_id: VMId
    vm_name: str
    product: Product
    price: Money
    # line_number: int

    # timestamp: datetime
