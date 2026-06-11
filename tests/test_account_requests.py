import asyncio
import unittest

from edgex_sdk.account.client import (
    Client as AccountClient,
    GetCollateralTransactionPageParams,
    GetPositionTransactionPageParams,
)


class FakeAsyncClient:
    def __init__(self):
        self.account_id = 12345
        self.calls = []

    def get_account_id(self):
        return self.account_id

    async def make_authenticated_request(
        self, method, path, data=None, params=None, rewrite_version=True
    ):
        self.calls.append((method, path, data, params, rewrite_version))
        return {"code": "SUCCESS", "data": {"ok": True}}


class AccountClientRequestTest(unittest.TestCase):
    def setUp(self):
        self.fake = FakeAsyncClient()
        self.client = AccountClient(self.fake)

    def test_get_position_transaction_page_includes_doc_fields(self):
        params = GetPositionTransactionPageParams(
            filter_coin_id_list=["1000"],
            filter_contract_id_list=["10000001"],
            filter_type_list=["SETTLE_FUNDING_FEE"],
            filter_close_only=True,
            filter_open_only=False,
        )

        asyncio.run(self.client.get_position_transaction_page(params))

        request = self.fake.calls[-1]
        self.assertEqual(request[0], "GET")
        self.assertEqual(
            request[3],
            {
                "accountId": "12345",
                "filterCoinIdList": "1000",
                "filterContractIdList": "10000001",
                "filterTypeList": "SETTLE_FUNDING_FEE",
                "filterCloseOnly": "true",
                "filterOpenOnly": "false",
            },
        )

    def test_get_collateral_transaction_page_includes_doc_fields(self):
        params = GetCollateralTransactionPageParams(
            filter_coin_id_list=["1000", "1001"],
            filter_type_list=["DEPOSIT", "WITHDRAW"],
        )

        asyncio.run(self.client.get_collateral_transaction_page(params))

        request = self.fake.calls[-1]
        self.assertEqual(request[0], "GET")
        self.assertEqual(
            request[3],
            {
                "accountId": "12345",
                "filterCoinIdList": "1000,1001",
                "filterTypeList": "DEPOSIT,WITHDRAW",
            },
        )


if __name__ == "__main__":
    unittest.main()
