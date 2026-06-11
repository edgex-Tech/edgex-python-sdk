import asyncio
import unittest

from edgex_sdk.quote.client import (
    Client as QuoteClient,
    GetAccurateOpenInterestParams,
    GetExchangeLongShortRatioParams,
    GetEstimatedFeeParams,
    GetMarketStatusParams,
    GetStatDayTradeParams,
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

    def test_get_accurate_open_interest(self):
        params = GetAccurateOpenInterestParams(contract_id_list=["10000001", "10000002"])

        asyncio.run(self.client.get_accurate_open_interest(params))

        self.assertEqual(
            self.fake.calls[-1],
            (
                "GET",
                "/api/v2/public/quote/getAccurateOpenInterest",
                {"contractIdList": "10000001,10000002"},
            ),
        )

    def test_get_stat_day_trade(self):
        params = GetStatDayTradeParams(
            start_day_time_inclusive="1734480000000",
            end_day_time_exclusive="1734566400000",
        )

        asyncio.run(self.client.get_stat_day_trade(params))

        self.assertEqual(
            self.fake.calls[-1],
            (
                "GET",
                "/api/v2/public/quote/getStatDayTrade",
                {
                    "startDayTimeInclusive": "1734480000000",
                    "endDayTimeExclusive": "1734566400000",
                },
            ),
        )

    def test_get_exchange_long_short_ratio(self):
        params = GetExchangeLongShortRatioParams(
            range="1h",
            filter_contract_id_list=["10000001"],
            filter_exchange_list=["binance", "okx"],
        )

        asyncio.run(self.client.get_exchange_long_short_ratio(params))

        self.assertEqual(
            self.fake.calls[-1],
            (
                "GET",
                "/api/v2/public/quote/getExchangeLongShortRatio",
                {
                    "range": "1h",
                    "filterContractIdList": "10000001",
                    "filterExchangeList": "binance,okx",
                },
            ),
        )

    def test_get_estimated_fee(self):
        params = GetEstimatedFeeParams(
            filter_begin_kline_time_inclusive=1734480000000,
            filter_end_kline_time_exclusive=1734566400000,
        )

        asyncio.run(self.client.get_estimated_fee(params))

        self.assertEqual(
            self.fake.calls[-1],
            (
                "GET",
                "/api/v2/public/quote/fee",
                {
                    "filterBeginKlineTimeInclusive": "1734480000000",
                    "filterEndKlineTimeExclusive": "1734566400000",
                },
            ),
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
