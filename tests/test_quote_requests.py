import asyncio
import unittest

from edgex_sdk.quote.client import (
    Client as QuoteClient,
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
