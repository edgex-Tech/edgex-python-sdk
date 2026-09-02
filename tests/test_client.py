"""
Unit tests for the main client.
"""

import unittest
import asyncio
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock

from edgex_sdk.client import Client
from edgex_sdk.order.types import (
    CreateOrderParams,
    OrderSide,
    OrderType,
    TriggerPriceType,
)
from edgex_sdk.account.client import SetMarginModeParams


class TestClient(unittest.TestCase):
    """Test cases for the main client."""

    def setUp(self):
        """Set up test fixtures."""
        self.base_url = "https://testnet.edgex.exchange"
        self.account_id = 12345
        self.trading_private_key = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

        self.client = Client(
            base_url=self.base_url,
            account_id=self.account_id,
            trading_private_key=self.trading_private_key,
        )

    def test_init(self):
        """Test client initialization."""
        self.assertIsNotNone(self.client.async_client)
        self.assertIsNotNone(self.client.order)
        self.assertIsNotNone(self.client.metadata)
        self.assertIsNotNone(self.client.account)
        self.assertIsNotNone(self.client.quote)
        self.assertIsNotNone(self.client.funding)
        self.assertIsNotNone(self.client.transfer)

    def test_create_order(self):
        """Test create_order method."""
        self.client.get_metadata = AsyncMock(return_value={"data": {"contractList": [{"contractId": "BTC-USDT"}]}})
        self.client.order = MagicMock()
        self.client.order.create_order = AsyncMock(return_value={"code": "SUCCESS", "data": {"orderId": "123"}})

        params = CreateOrderParams(
            contract_id="BTC-USDT",
            price="30000",
            size="0.001",
            type=OrderType.LIMIT,
            side=OrderSide.BUY,
        )

        result = asyncio.run(self.client.create_order(params))

        self.client.get_metadata.assert_called_once()
        self.client.order.create_order.assert_called_once()
        self.assertEqual(result, {"code": "SUCCESS", "data": {"orderId": "123"}})

    def test_get_max_order_size(self):
        """Test get_max_order_size method."""
        self.client.order = MagicMock()
        self.client.order.get_max_order_size = AsyncMock(return_value={"code": "SUCCESS", "data": {"maxSize": "0.1"}})

        result = asyncio.run(self.client.get_max_order_size("BTC-USDT", 30000))

        self.client.order.get_max_order_size.assert_called_once_with("BTC-USDT", 30000.0)
        self.assertEqual(result, {"code": "SUCCESS", "data": {"maxSize": "0.1"}})

    def test_cancel_order(self):
        """Test cancel_order method."""
        self.client.order = MagicMock()
        self.client.order.cancel_order = AsyncMock(return_value={"code": "SUCCESS", "data": {"success": True}})

        from edgex_sdk.order.types import CancelOrderParams
        params = CancelOrderParams(order_id="123")

        result = asyncio.run(self.client.cancel_order(params))

        self.client.order.cancel_order.assert_called_once_with(params)
        self.assertEqual(result, {"code": "SUCCESS", "data": {"success": True}})

    def test_get_account_asset(self):
        """Test get_account_asset method."""
        self.client.account = MagicMock()
        self.client.account.get_account_asset = AsyncMock(return_value={"code": "SUCCESS", "data": {"assets": []}})

        result = asyncio.run(self.client.get_account_asset())

        self.client.account.get_account_asset.assert_called_once()
        self.assertEqual(result, {"code": "SUCCESS", "data": {"assets": []}})

    def test_get_account_positions(self):
        """Test get_account_positions method."""
        self.client.account = MagicMock()
        self.client.account.get_account_positions = AsyncMock(return_value={"code": "SUCCESS", "data": {"positions": []}})

        result = asyncio.run(self.client.get_account_positions())

        self.client.account.get_account_positions.assert_called_once()
        self.assertEqual(result, {"code": "SUCCESS", "data": {"positions": []}})

    def test_set_margin_mode(self):
        """Test set_margin_mode method."""
        self.client.get_metadata = AsyncMock(return_value={"data": {"global": {"nativeChainId": "33431"}}})
        self.client.account = MagicMock()
        self.client.account.set_margin_mode = AsyncMock(return_value={"code": "SUCCESS", "data": {"ok": True}})
        params = SetMarginModeParams(contract_id="10000001", margin_mode="1")

        result = asyncio.run(self.client.set_margin_mode(params))

        self.client.get_metadata.assert_called_once()
        self.client.account.set_margin_mode.assert_called_once_with(params, {"global": {"nativeChainId": "33431"}})
        self.assertEqual(result, {"code": "SUCCESS", "data": {"ok": True}})

    def test_create_limit_order(self):
        """Test create_limit_order method."""
        self.client.create_order = AsyncMock(return_value={"code": "SUCCESS", "data": {"orderId": "123"}})

        result = asyncio.run(self.client.create_limit_order(contract_id="BTC-USDT", size="0.001", price="30000", side=OrderSide.BUY))

        self.client.create_order.assert_called_once()
        args = self.client.create_order.call_args[0][0]
        self.assertEqual(args.contract_id, "BTC-USDT")
        self.assertEqual(args.size, "0.001")
        self.assertEqual(args.price, "30000")
        self.assertEqual(args.side, OrderSide.BUY)
        self.assertEqual(args.type, OrderType.LIMIT)
        self.assertEqual(result, {"code": "SUCCESS", "data": {"orderId": "123"}})

    def test_create_market_order(self):
        """Test create_market_order method."""
        self.client.create_order = AsyncMock(return_value={"code": "SUCCESS", "data": {"orderId": "123"}})

        result = asyncio.run(self.client.create_market_order(contract_id="BTC-USDT", size="0.001", side=OrderSide.BUY))

        self.client.create_order.assert_called_once()
        args = self.client.create_order.call_args[0][0]
        self.assertEqual(args.contract_id, "BTC-USDT")
        self.assertEqual(args.size, "0.001")
        self.assertEqual(args.price, "0")
        self.assertEqual(args.side, OrderSide.BUY)
        self.assertEqual(args.type, OrderType.MARKET)
        self.assertEqual(result, {"code": "SUCCESS", "data": {"orderId": "123"}})

    def test_create_order_params_normalizes_string_enums(self):
        params = CreateOrderParams(
            contract_id="30000043",
            size="79",
            price="0",
            side="SELL",
            type="STOP_MARKET",
            trigger_price="2.481",
        )

        self.assertIs(params.type, OrderType.STOP_MARKET)
        self.assertIs(params.side, OrderSide.SELL)
        self.assertEqual(params.time_in_force, "")
        self.assertIs(params.trigger_price_type, TriggerPriceType.LAST_PRICE)

    def test_create_order_params_rejects_invalid_enum_values(self):
        valid = {
            "contract_id": "30000043",
            "size": "79",
            "price": "0",
            "side": "SELL",
            "type": "STOP_MARKET",
            "trigger_price": "2.481",
        }
        invalid_values = (
            ({**valid, "type": "STOP_MAKRET"}, "invalid order type"),
            ({**valid, "side": "SHORT"}, "invalid order side"),
            ({**valid, "time_in_force": "IOC"}, "invalid time in force"),
            (
                {**valid, "trigger_price_type": "MARK_PRICE"},
                "invalid trigger price type",
            ),
        )

        for values, error in invalid_values:
            with self.subTest(values=values), self.assertRaisesRegex(
                ValueError, error
            ):
                CreateOrderParams(**values)

    def test_conditional_order_requires_trigger_price(self):
        with self.assertRaisesRegex(ValueError, "trigger_price is required"):
            CreateOrderParams(
                contract_id="30000043",
                size="79",
                price="0",
                side=OrderSide.SELL,
                type=OrderType.STOP_MARKET,
            )

    def test_conditional_market_order_request_uses_market_protection_price(self):
        metadata = {
            "data": {
                "global": {
                    "nativeChainId": "42161",
                    "contractAddress": "0x0000000000000000000000000000000000000001",
                },
                "coinList": [{"coinId": "2", "resolution": "1000000"}],
                "contractList": [{
                    "contractId": "30000043",
                    "quoteCoinId": "2",
                    "tickSize": "0.001",
                    "resolution": "100000000",
                    "defaultTakerFeeRate": "0.00043",
                    "defaultMakerFeeRate": "0.00038",
                }],
            }
        }
        self.client.get_metadata = AsyncMock(return_value=metadata)
        self.client.get_24_hour_quote = AsyncMock(
            return_value={"data": [{"oraclePrice": "2.427"}]}
        )
        self.client.async_client.resolve_trading_signer_address = MagicMock(
            return_value="0x0000000000000000000000000000000000000002"
        )
        self.client.async_client.sign_typed_data_with_trading_key = MagicMock(
            return_value="0x" + "00" * 65
        )
        self.client.async_client.make_authenticated_request = AsyncMock(
            return_value={"code": "SUCCESS", "data": {"orderId": "123"}}
        )

        cases = (
            ("STOP_MARKET", "SELL", Decimal("0.079")),
            (OrderType.TAKE_PROFIT_MARKET, OrderSide.SELL, Decimal("0.079")),
            ("STOP_MARKET", "BUY", Decimal("1917.33")),
            (OrderType.TAKE_PROFIT_MARKET, OrderSide.BUY, Decimal("1917.33")),
        )
        for order_type, side, expected_l2_value in cases:
            with self.subTest(order_type=order_type, side=side):
                params = CreateOrderParams(
                    contract_id="30000043",
                    size="79",
                    price="0",
                    side=side,
                    type=order_type,
                    reduce_only=True,
                    trigger_price="2.481",
                    trigger_price_type=TriggerPriceType.LAST_PRICE,
                )

                asyncio.run(self.client.create_order(params))

                request = self.client.async_client.make_authenticated_request.await_args.kwargs
                body = request["data"]
                self.assertEqual(request["path"], "/api/v2/private/order/createOrder")
                self.assertEqual(body["price"], "0")
                self.assertEqual(body["triggerPrice"], "2.481")
                self.assertEqual(body["triggerPriceType"], "LAST_PRICE")
                self.assertEqual(body["timeInForce"], "IMMEDIATE_OR_CANCEL")
                self.assertEqual(Decimal(body["l2Value"]), expected_l2_value)
                self.assertEqual(body["l2Size"], "79")

                self.client.async_client.make_authenticated_request.reset_mock()


if __name__ == "__main__":
    unittest.main()
