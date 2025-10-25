"""
Unit tests for the main client.
"""

import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from edgex_sdk.client import Client
from edgex_sdk.order.types import OrderSide, OrderType, CreateOrderParams


class TestClient(unittest.TestCase):
    """Test cases for the main client."""

    def setUp(self):
        """Set up test fixtures."""
        self.base_url = "https://testnet.edgex.exchange"
        self.account_id = 12345
        self.stark_private_key = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

        # Create a client with mocked session
        with patch('edgex_sdk.client.requests.Session') as mock_session:
            self.mock_session = mock_session.return_value
            self.client = Client(
                base_url=self.base_url,
                account_id=self.account_id,
                stark_private_key=self.stark_private_key
            )

    def test_init(self):
        """Test client initialization."""
        self.assertIsNotNone(self.client.internal_client)
        self.assertIsNotNone(self.client.order)
        self.assertIsNotNone(self.client.metadata)
        self.assertIsNotNone(self.client.account)
        self.assertIsNotNone(self.client.quote)
        self.assertIsNotNone(self.client.funding)
        self.assertIsNotNone(self.client.transfer)
        self.assertIsNotNone(self.client.asset)

    def test_create_order(self):
        """Test create_order method."""
        # Mock the get_metadata method
        self.client.get_metadata = AsyncMock(return_value={"data": {"contractList": [{"contractId": "BTC-USDT"}]}})

        # Mock the order.create_order method
        self.client.order = MagicMock()
        self.client.order.create_order = AsyncMock(return_value={"code": "SUCCESS", "data": {"orderId": "123"}})

        # Create order parameters
        params = CreateOrderParams(
            contract_id="BTC-USDT",
            price="30000",
            size="0.001",
            type=OrderType.LIMIT,
            side=OrderSide.BUY
        )

        # Call the method
        result = asyncio.run(self.client.create_order(params))

        # Check that get_metadata was called
        self.client.get_metadata.assert_called_once()

        # Check that order.create_order was called with the correct arguments
        self.client.order.create_order.assert_called_once()

        # Check the result
        self.assertEqual(result, {"code": "SUCCESS", "data": {"orderId": "123"}})

    def test_get_max_order_size(self):
        """Test get_max_order_size method."""
        # Mock the order.get_max_order_size method
        self.client.order = MagicMock()
        self.client.order.get_max_order_size = AsyncMock(return_value={"code": "SUCCESS", "data": {"maxSize": "0.1"}})

        # Call the method
        result = asyncio.run(self.client.get_max_order_size("BTC-USDT", 30000))

        # Check that order.get_max_order_size was called with the correct arguments
        self.client.order.get_max_order_size.assert_called_once_with("BTC-USDT", 30000.0)

        # Check the result
        self.assertEqual(result, {"code": "SUCCESS", "data": {"maxSize": "0.1"}})

    def test_cancel_order(self):
        """Test cancel_order method."""
        # Mock the order.cancel_order method
        self.client.order = MagicMock()
        self.client.order.cancel_order = AsyncMock(return_value={"code": "SUCCESS", "data": {"success": True}})

        # Create cancel order parameters
        from edgex_sdk.order.types import CancelOrderParams
        params = CancelOrderParams(order_id="123")

        # Call the method
        result = asyncio.run(self.client.cancel_order(params))

        # Check that order.cancel_order was called with the correct arguments
        self.client.order.cancel_order.assert_called_once_with(params)

        # Check the result
        self.assertEqual(result, {"code": "SUCCESS", "data": {"success": True}})

    def test_get_account_asset(self):
        """Test get_account_asset method."""
        # Mock the account.get_account_asset method
        self.client.account = MagicMock()
        self.client.account.get_account_asset = AsyncMock(return_value={"code": "SUCCESS", "data": {"assets": []}})

        # Call the method
        result = asyncio.run(self.client.get_account_asset())

        # Check that account.get_account_asset was called
        self.client.account.get_account_asset.assert_called_once()

        # Check the result
        self.assertEqual(result, {"code": "SUCCESS", "data": {"assets": []}})

    def test_get_account_positions(self):
        """Test get_account_positions method."""
        # Mock the account.get_account_positions method
        self.client.account = MagicMock()
        self.client.account.get_account_positions = AsyncMock(return_value={"code": "SUCCESS", "data": {"positions": []}})

        # Call the method
        result = asyncio.run(self.client.get_account_positions())

        # Check that account.get_account_positions was called
        self.client.account.get_account_positions.assert_called_once()

        # Check the result
        self.assertEqual(result, {"code": "SUCCESS", "data": {"positions": []}})

    def test_create_limit_order(self):
        """Test create_limit_order method."""
        # Mock the create_order method
        self.client.create_order = AsyncMock(return_value={"code": "SUCCESS", "data": {"orderId": "123"}})

        # Call the method
        result = asyncio.run(self.client.create_limit_order(
            contract_id="BTC-USDT",
            size="0.001",
            price="30000",
            side=OrderSide.BUY
        ))

        # Check that create_order was called with the correct arguments
        self.client.create_order.assert_called_once()
        args = self.client.create_order.call_args[0][0]
        self.assertEqual(args.contract_id, "BTC-USDT")
        self.assertEqual(args.size, "0.001")
        self.assertEqual(args.price, "30000")
        self.assertEqual(args.side, OrderSide.BUY)
        self.assertEqual(args.type, OrderType.LIMIT)

        # Check the result
        self.assertEqual(result, {"code": "SUCCESS", "data": {"orderId": "123"}})

    def test_create_market_order(self):
        """Test create_market_order method."""
        # Mock the get_metadata method
        self.client.get_metadata = AsyncMock(return_value={
            "data": {
                "contractList": [
                    {
                        "contractId": "BTC-USDT",
                        "tickSize": "0.01"
                    }
                ]
            }
        })

        # Mock the get_24_hour_quote method
        self.client.get_24_hour_quote = AsyncMock(return_value={
            "data": [
                {
                    "oraclePrice": "30000"
                }
            ]
        })

        # Mock the create_order method
        self.client.create_order = AsyncMock(return_value={"code": "SUCCESS", "data": {"orderId": "123"}})

        # Call the method
        result = asyncio.run(self.client.create_order(
            CreateOrderParams(
                contract_id="BTC-USDT",
                size="0.001",
                price="0",  # Market order price should be ignored
                side=OrderSide.BUY,
                type=OrderType.MARKET
            )
        ))

        # Check that get_metadata was called
        self.client.get_metadata.assert_called_once()

        # Check that get_24_hour_quote was called with the correct arguments
        self.client.get_24_hour_quote.assert_called_once_with("BTC-USDT")

        # Check that create_order was called with the correct arguments
        self.client.create_order.assert_called_once()
        args = self.client.create_order.call_args[0][0]
        self.assertEqual(args.contract_id, "BTC-USDT")
        self.assertEqual(args.size, "0.001")
        self.assertEqual(args.side, OrderSide.BUY)
        self.assertEqual(args.type, OrderType.MARKET)

        # Check the result
        self.assertEqual(result, {"code": "SUCCESS", "data": {"orderId": "123"}})



if __name__ == '__main__':
    unittest.main()
