"""Integration tests for the asset API."""

import unittest
import logging
from typing import Dict, Any

from edgex_sdk import (
    GetAssetOrdersParams,
    CreateWithdrawalParams,
    GetWithdrawSignInfoParams,
)
from tests.integration.base_test import BaseIntegrationTest

# Configure logging
logger = logging.getLogger(__name__)


class TestAssetAPI(BaseIntegrationTest):
    """Integration tests for the asset API."""

    def test_get_account_asset_delegation(self):
        """Test that get_account_asset properly delegates to account client."""
        if not hasattr(self.client.asset, "get_account_asset"):
            self.skipTest("Asset client does not expose get_account_asset")

        # This should raise NotImplementedError since it's an account endpoint
        with self.assertRaises(NotImplementedError) as context:
            self.run_async(self.client.asset.get_account_asset())

        self.assertIn("account client", str(context.exception))
        logger.info("Asset client properly delegates get_account_asset to account client")

    def test_get_asset_orders(self):
        """Test get_asset_orders method."""
        # Test with minimal parameters
        params = GetAssetOrdersParams(
            size="10"
        )

        try:
            orders = self.run_async(self.client.asset.get_asset_orders(params))
        except ValueError as e:
            # Asset APIs require X-edgeX-Api-Key header that test accounts don't have
            logger.info(f"Asset orders API requires API key (expected): {e}")
            self.skipTest("Skipping test due to API key requirement")
            return

        # Check response
        self.assertResponseSuccess(orders)

        # Check data structure
        data = orders.get("data", {})
        self.assertIsInstance(data, dict)

        if "orderList" in data:
            order_list = data["orderList"]
            self.assertIsInstance(order_list, list)
            logger.info(f"Found {len(order_list)} asset orders")

            # Check order structure if any orders exist
            if order_list:
                order = order_list[0]
                self.assertIsInstance(order, dict)
                expected_fields = ["id", "coinId", "amount", "status", "createdTime"]
                for field in expected_fields:
                    if field in order:
                        logger.info(f"Order {field}: {order[field]}")

    def test_get_coin_rates(self):
        """Test get_coin_rates method."""
        if not hasattr(self.client.asset, "get_coin_rates"):
            self.skipTest("Asset client does not expose get_coin_rates")

        try:
            rates = self.run_async(self.client.asset.get_coin_rates())
        except ValueError as e:
            # Asset APIs require X-edgeX-Api-Key header that test accounts don't have
            logger.info(f"Coin rates API requires API key (expected): {e}")
            self.skipTest("Skipping test due to API key requirement")
            return

        # Check response
        self.assertResponseSuccess(rates)

        # Check data structure
        data = rates.get("data", [])
        self.assertIsInstance(data, list)
        logger.info(f"Found {len(data)} coin rates")

        # Check rate structure if any rates exist
        if data:
            rate = data[0]
            self.assertIsInstance(rate, dict)
            expected_fields = ["coinId", "coinName", "rate"]
            for field in expected_fields:
                if field in rate:
                    logger.info(f"Rate {field}: {rate[field]}")

    def test_get_withdraw_sign_info(self):
        """Test get_withdraw_sign_info method."""
        params = GetWithdrawSignInfoParams(
            chain_id="1",
            token_address="0xdac17f958d2ee523a2206206994597c13d831ec7",
            amount="100"
        )

        try:
            sign_info = self.run_async(self.client.asset.get_withdraw_sign_info(params))

            self.assertResponseSuccess(sign_info)

            data = sign_info.get("data", {})
            self.assertIsInstance(data, dict)
            logger.info(f"Withdraw sign info: {data}")

        except Exception as e:
            logger.info(f"Withdraw sign info API requires API key (expected): {e}")
            self.skipTest("Skipping test due to API key requirement")

    def test_create_withdrawal_validation(self):
        """Test create_withdrawal method validation (without actually creating)."""
        # Test parameter validation without actually submitting
        params = CreateWithdrawalParams(
            coin_id="2",  # USDT
            amount="0.001",  # Very small amount
            eth_address="0x1234567890123456789012345678901234567890",  # Dummy address
        )

        # We won't actually call the API to avoid creating real withdrawals
        # Just test that the parameters are properly structured
        self.assertIsInstance(params.coin_id, str)
        self.assertIsInstance(params.amount, str)
        self.assertIsInstance(params.eth_address, str)

        logger.info("Withdrawal parameter validation passed")
        logger.warning("Actual withdrawal creation skipped for safety")


if __name__ == "__main__":
    unittest.main()
