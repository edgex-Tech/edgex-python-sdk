import asyncio
import unittest
from decimal import Decimal

from edgex_sdk.order.client import Client as OrderClient
from edgex_sdk.order.types import (
    CreateOrderParams,
    GetActiveOrderParams,
    GetHistoryOrderPageParams,
    OpenTpSlParams,
    OrderFillTransactionParams,
    OrderSide,
    OrderType,
)


class FakeAsyncClient:
    def __init__(self):
        self.account_id = 12345
        self.trading_private_key = "present"
        self.calls = []

    def get_account_id(self):
        return self.account_id

    def get_random_client_id(self):
        return "client-1"

    def calc_nonce(self, client_order_id):
        self.calls.append(("nonce", client_order_id))
        return 123456

    def resolve_trading_signer_address(self):
        return "0xFCAd0B19bB29D4674531d6f115237E16AfCE377c"

    def sign_typed_data_with_trading_key(self, typed_data, include_0x=False):
        self.calls.append(("sign", typed_data, include_0x))
        return "11" * 65

    def parse_resolution(self, resolution):
        return Decimal(resolution)

    async def make_authenticated_request(
        self, method, path, data=None, params=None, rewrite_version=True
    ):
        self.calls.append((method, path, data, params, rewrite_version))
        return {"code": "SUCCESS", "data": {"ok": True}}


class OrderClientRequestTest(unittest.TestCase):
    def setUp(self):
        self.fake = FakeAsyncClient()
        self.client = OrderClient(self.fake)
        self.metadata = {
            "global": {
                "nativeChainId": "33431",
                "contractAddress": "0x1ae109ea449cfe0bed08bfe8911e968a49a919b1",
            },
            "contractList": [
                {
                    "contractId": "10000001",
                    "quoteCoinId": "1000",
                    "resolution": "1000",
                    "defaultTakerFeeRate": "0.001",
                    "defaultMakerFeeRate": "0.0005",
                }
            ],
            "coinList": [{"coinId": "1000", "resolution": "1000000"}],
        }

    def test_get_active_orders_serializes_bool_lists(self):
        params = GetActiveOrderParams(
            filter_is_liquidate=True,
            filter_is_deleverage=False,
            filter_is_position_tpsl=True,
        )

        asyncio.run(self.client.get_active_orders(params))

        request = self.fake.calls[-1]
        self.assertEqual(request[0], "GET")
        self.assertEqual(request[1], "/api/v2/private/order/getActiveOrderPage")
        self.assertEqual(
            request[3],
            {
                "accountId": "12345",
                "filterIsLiquidateList": "true",
                "filterIsDeleverageList": "false",
                "filterIsPositionTpslList": "true",
            },
        )

    def test_get_order_fill_transactions_serializes_bool_lists(self):
        params = OrderFillTransactionParams(
            filter_is_liquidate=True,
            filter_is_deleverage=False,
            filter_is_position_tpsl=False,
        )

        asyncio.run(self.client.get_order_fill_transactions(params))

        request = self.fake.calls[-1]
        self.assertEqual(
            request[3],
            {
                "accountId": "12345",
                "filterIsLiquidateList": "true",
                "filterIsDeleverageList": "false",
                "filterIsPositionTpslList": "false",
            },
        )

    def test_get_history_order_page_keeps_list_fields(self):
        params = GetHistoryOrderPageParams(
            filter_is_liquidate=True,
            filter_is_deleverage=False,
            filter_is_position_tpsl=True,
        )

        asyncio.run(self.client.get_history_order_page(params))

        request = self.fake.calls[-1]
        self.assertEqual(request[0], "POST")
        self.assertEqual(
            request[2],
            {
                "accountId": "12345",
                "size": 100,
                "filterIsLiquidateList": "true",
                "filterIsDeleverageList": "false",
                "filterIsPositionTpslList": "true",
            },
        )

    def test_create_order_includes_advanced_fields(self):
        params = CreateOrderParams(
            contract_id="10000001",
            price="123.45",
            size="0.1",
            type=OrderType.STOP_LIMIT,
            side=OrderSide.BUY,
            time_in_force="GOOD_TIL_CANCEL",
            trigger_price="120.00",
            trigger_price_type="ORACLE_PRICE",
            source_key="source-1",
            is_position_tpsl=True,
            open_tpsl_parent_order_id="777",
            is_set_open_tp=True,
            open_tp=OpenTpSlParams(
                side=OrderSide.SELL,
                price="130.00",
                size="0.1",
                client_order_id="tp-1",
                trigger_price="129.00",
                trigger_price_type="LAST_PRICE",
                expire_time="1718000000000",
                l2_nonce="1",
                l2_value="13.0",
                l2_size="0.1",
                l2_limit_fee="0.01",
                l2_expire_time="1719000000000",
                l2_signature="aa" * 64,
            ),
            is_set_open_sl=True,
            open_sl={
                "side": "SELL",
                "price": "119.00",
                "size": "0.1",
                "clientOrderId": "sl-1",
                "triggerPrice": "119.50",
                "triggerPriceType": "INDEX_PRICE",
                "expireTime": "1718000000000",
                "l2Nonce": "2",
                "l2Value": "11.9",
                "l2Size": "0.1",
                "l2LimitFee": "0.01",
                "l2ExpireTime": "1719000000000",
                "l2Signature": "bb" * 64,
            },
            extra_type="strategy",
            extra_data_json='{"foo":"bar"}',
        )

        asyncio.run(
            self.client.create_order(params, self.metadata, Decimal("123.45"))
        )

        request = self.fake.calls[-1]
        self.assertEqual(request[0], "POST")
        self.assertEqual(request[1], "/api/v2/private/order/createOrder")
        body = request[2]
        self.assertEqual(body["triggerPrice"], "120.00")
        self.assertEqual(body["triggerPriceType"], "ORACLE_PRICE")
        self.assertEqual(body["sourceKey"], "source-1")
        self.assertTrue(body["isPositionTpsl"])
        self.assertEqual(body["openTpslParentOrderId"], "777")
        self.assertTrue(body["isSetOpenTp"])
        self.assertEqual(body["openTp"]["clientOrderId"], "tp-1")
        self.assertTrue(body["isSetOpenSl"])
        self.assertEqual(body["openSl"]["clientOrderId"], "sl-1")
        self.assertEqual(body["extraType"], "strategy")
        self.assertEqual(body["extraDataJson"], '{"foo":"bar"}')


if __name__ == "__main__":
    unittest.main()
