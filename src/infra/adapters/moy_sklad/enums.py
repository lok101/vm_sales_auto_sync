import enum
from uuid import UUID


class Organizations(enum.Enum):
    ORLOV = UUID("1783080e-d9e8-11ed-0a80-0145000af55f")


class Buyers(enum.Enum):
    RETAIL_BUYER = UUID("cc3f0392-55a8-11ed-0a80-023100027de0")


class Projects(enum.Enum):
    MY_MK = UUID("cbe343bc-55a9-11ed-0a80-0f9500024a24")


class SalesChannels(enum.Enum):
    SNACK = UUID("d26282ce-b395-11ee-0a80-15b7003a3ba3")
    VENDING_COFFEE = UUID("82179b30-55c7-11ed-0a80-09d60006bb10")
