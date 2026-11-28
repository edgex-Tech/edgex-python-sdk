import asyncio
import unittest

from edgex_sdk.quote.client import (
    Client as QuoteClient,
    GetMultiContractKLineParams,
    PriceType,
    GetMarketStatusParams,
)


class FakeAsyncClient:
    def __init__(self):
        self.calls = []

    async def make_public_request(self, method, path, params=None):
        self.calls.append((method, path, params))
        return {"code": "SUCCESS", "data": {"ok": True}}


class QuoteClientRequestTest(unittest.TestCase):
    def setUp(self):
        self.fake = FakeAsyncClient()
        self.client = QuoteClient(self.fake)

    def test_get_multi_contract_k_line_default_price_type(self):
        params = GetMultiContractKLineParams(["30000001", "30000002"], "MINUTE_1")

        asyncio.run(self.client.get_multi_contract_k_line(params))

        self.assertEqual(
            self.fake.calls[-1],
            (
                "GET",
                "/api/v2/public/quote/getMultiContractKline",
                {
                    "contractIdList": "30000001,30000002",
                    "klineType": "MINUTE_1",
                    "priceType": "LAST_PRICE",
                    "size": "1",
                },
            ),
        )

    def test_get_multi_contract_k_line_price_type(self):
        params = GetMultiContractKLineParams(
            ["30000001"], "HOUR_1", size=3, price_type=PriceType.INDEX_PRICE
        )

        asyncio.run(self.client.get_multi_contract_k_line(params))

        self.assertEqual(
            self.fake.calls[-1][2],
            {
                "contractIdList": "30000001",
                "klineType": "HOUR_1",
                "priceType": "INDEX_PRICE",
                "size": "3",
            },
        )

    def test_get_market_status(self):
        params = GetMarketStatusParams(contract_id="10000001")

        asyncio.run(self.client.get_market_status(params))

        self.assertEqual(
            self.fake.calls[-1],
            (
                "GET",
                "/api/v2/public/quote/getMarketStatus",
                {"contractId": "10000001"},
            ),
        )


if __name__ == "__main__":
    unittest.main()
