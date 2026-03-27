from dataclasses import dataclass

from beartype import beartype


@beartype
@dataclass(frozen=True, slots=True, kw_only=True)
class KitVendingAccountDTO:
    name: str
    login: str
    password: str
    company_id: int
