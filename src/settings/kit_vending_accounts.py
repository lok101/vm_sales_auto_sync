import json
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.app.dtos.kit_vending_account_dto import KitVendingAccountDTO


class KitVendingAccount(BaseModel):
    """Модель аккаунта Kit Vending."""
    name: str
    login: str
    password: str
    company_id: int


class KitVendingAccountsSettings(BaseSettings):
    """Настройки аккаунтов Kit Vending."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="KIT_VENDING_",
        case_sensitive=False,
        extra="ignore",
    )

    accounts_file: Annotated[
        Path,
        Field(
            default=Path("kit_vending_accounts.json"),
            description="Путь к JSON файлу с аккаунтами",
        ),
    ] = Path("kit_vending_accounts.json")

    accounts: list[KitVendingAccount] = Field(default_factory=list)
    pass

    @field_validator("accounts_file", mode="before")
    @classmethod
    def validate_accounts_file(cls, v: str | Path) -> Path:
        """Преобразует строку в Path объект."""
        if isinstance(v, str):
            return Path(v)
        return v

    @model_validator(mode="after")
    def load_accounts_from_file(self) -> "KitVendingAccountsSettings":
        """Загружает аккаунты из JSON файла после инициализации."""
        loaded_accounts: list[KitVendingAccount] = []
        if self.accounts_file.exists():
            with open(self.accounts_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    loaded_accounts = [KitVendingAccount(**account) for account in data]
                elif isinstance(data, dict) and "accounts" in data:
                    loaded_accounts = [
                        KitVendingAccount(**account) for account in data["accounts"]
                    ]

        self.accounts = loaded_accounts
        return self

    def to_account_dtos(self) -> list[KitVendingAccountDTO]:
        """Преобразует настройки аккаунтов в список AccountDTO."""
        return [
            KitVendingAccountDTO(
                login=account.login,
                password=account.password,
                company_id=account.company_id,
                name=account.name
            )
            for account in self.accounts
        ]
