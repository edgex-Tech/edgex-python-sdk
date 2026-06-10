"""
Unit tests for the main client.
"""

import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from edgex_sdk.client import Client
from edgex_sdk.order.types import OrderSide, OrderType, CreateOrderParams
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
        params = SetMarginModeParams(contract_id="10000001", margin_mode="ISOLATED")

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


if __name__ == "__main__":
    unittest.main()
