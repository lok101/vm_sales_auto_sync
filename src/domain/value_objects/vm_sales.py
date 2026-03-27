from dataclasses import dataclass
from datetime import date

from beartype import beartype

from src.domain.entities.sale import Sale
from src.domain.value_objects import VMId


@beartype
@dataclass(frozen=True, slots=True, kw_only=True)
class VMSales:
    id: VMId
    day: date
    sales: list[Sale]
