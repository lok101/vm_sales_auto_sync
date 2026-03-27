import asyncio
from datetime import datetime

from dotenv import load_dotenv
from kit_api import KitVendingAPIClient
from kit_api.client import KitAPIAccount

from src.app.dtos.kit_vending_account_dto import KitVendingAccountDTO
from src.app.use_case.register_sales import RegisterVendingMachinesSales
from src.infra.adapters.kit_vending.infra.product_by_matrix_resolver import ProductByMatrixResolverAdapter
from src.infra.adapters.kit_vending.infra.vm_data_resolver_adapter import VendingMachineDataResolverAdapter
from src.infra.adapters.kit_vending.sales_provider_adapter import VendingMachineSalesProviderAdapter
from src.infra.logger import configure_logging
from src.settings.kit_vending_accounts import KitVendingAccountsSettings

load_dotenv()
configure_logging()


async def main(accounts: list[KitVendingAccountDTO]):
    if not accounts:
        raise Exception("Не получено ни одного аккаунта KitVending.")

    main_account = KitAPIAccount(
        login=accounts[0].login,
        password=accounts[0].password,
        company_id=accounts[0].company_id,
    )

    async with KitVendingAPIClient(account=main_account) as client:
        day = datetime(2026, 3, 26)

        kit_data_vm_resolver = VendingMachineDataResolverAdapter(kit_vending_api_client=client)
        kit_product_by_matrix_resolver = ProductByMatrixResolverAdapter(
            kit_vending_api_client=client,
            accounts=accounts
        )
        sales_provider = VendingMachineSalesProviderAdapter(
            vm_data_resolver=kit_data_vm_resolver,
            product_by_matrix_resolver=kit_product_by_matrix_resolver,
            kit_vending_api_client=client
        )

        register_sales_uc = RegisterVendingMachinesSales(
            sales_data_provider=sales_provider
        )

        await register_sales_uc.execute(day=day)
        pass


if __name__ == "__main__":
    acc_settings = KitVendingAccountsSettings()
    accounts_dtos: list[KitVendingAccountDTO] = acc_settings.to_account_dtos()

    asyncio.run(main(accounts_dtos))
