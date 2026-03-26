from dataclasses import dataclass

from beartype import beartype


@beartype
@dataclass(frozen=True, slots=True, kw_only=True)
class Money:
    """Валюта в копейках."""
    kopeck: int
