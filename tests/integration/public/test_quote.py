"""Tests for public quote endpoints."""

import unittest
import logging

from edgex_sdk import GetKLineParams, GetOrderBookDepthParams, GetMultiContractKLineParams, KlineType
from tests.integration.public.base_test import BasePublicEndpointTest

# Configure logging
logger = logging.getLogger(__name__)

# Test contract ID
TEST_CONTRACT_ID = "10000004"  # Contract ID provided


class TestPublicQuoteAPI(BasePublicEndpointTest):
    """Tests for public quote endpoints."""

    def test_get_24_hour_quote(self):
        """Test get_24_hour_quote method."""
        # Get 24-hour quote
        quote = self.run_async(self.client.quote.get_24_hour_quote(TEST_CONTRACT_ID))

        # Check response
        self.assertResponseSuccess(quote)

        # Check data
        data = quote.get("data", [])
        self.assertIsInstance(data, list)

        # Log quote details
        if data:
            first_quote = data[0]
            logger.info(f"24-hour quote for {TEST_CONTRACT_ID}: {first_quote.get('lastPrice')}")
        else:
            logger.info(f"No 24-hour quote data for {TEST_CONTRACT_ID}")

    def test_get_k_line(self):
        """Test get_k_line method."""
        # Create parameters
        params = GetKLineParams(
            contract_id=TEST_CONTRACT_ID,
            kline_type=KlineType.HOUR_1,
            size=10
        )

        # Get K-line data
        klines = self.run_async(self.client.quote.get_k_line(params))

        # Check response
        self.assertResponseSuccess(klines)

        # Check data
        data = klines.get("data", {})

        # Log K-line details
        if "list" in data and data["list"]:
            first_kline = data["list"][0]
            logger.info(f"First K-line for {TEST_CONTRACT_ID}: {first_kline}")
        else:
            logger.info(f"No K-line data for {TEST_CONTRACT_ID}")

    def test_get_order_book_depth(self):
        """Test get_order_book_depth method."""
        # Create parameters
        params = GetOrderBookDepthParams(
            contract_id=TEST_CONTRACT_ID,
            limit=200  # Use a valid depth level (15 or 200)
        )

        try:
            # Get order book depth
            depth = self.run_async(self.client.quote.get_order_book_depth(params))

            # Check response
            self.assertResponseSuccess(depth)

            # Check data
            data = depth.get("data", [])
            self.assertIsInstance(data, list)

            # The data might be empty for the test contract
            if data:
                depth_data = data[0]  # Get first item from list
                self.assertIn("asks", depth_data)
                self.assertIn("bids", depth_data)
                self.assertIsInstance(depth_data["asks"], list)
                self.assertIsInstance(depth_data["bids"], list)

                # Log depth details
                asks = depth_data["asks"]
                bids = depth_data["bids"]
                logger.info(f"Order book depth for {TEST_CONTRACT_ID}: {len(asks)} asks, {len(bids)} bids")
            else:
                # Log that no data was returned
                logger.info(f"No order book depth data for {TEST_CONTRACT_ID}")
        except ValueError as e:
            # Skip the test if we get an INVALID_DEPTH_LEVEL error
            if "INVALID_DEPTH_LEVEL" in str(e):
                self.skipTest(f"Skipping due to API error: {e}")
            else:
                raise


if __name__ == "__main__":
    unittest.main()
