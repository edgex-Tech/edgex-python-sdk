"""Integration tests for the quote API."""

import unittest
import logging
from typing import Dict, Any

from edgex_sdk import GetKLineParams, GetOrderBookDepthParams, GetMultiContractKLineParams, KlineType
from tests.integration.base_test import BaseIntegrationTest
from tests.integration.config import TEST_CONTRACT_ID

# Configure logging
logger = logging.getLogger(__name__)


class TestQuoteAPI(BaseIntegrationTest):
    """Integration tests for the quote API."""

    def test_get_24_hour_quote(self):
        """Test get_24_hour_quote method."""
        # Get 24-hour quote
        quote = self.run_async(self.client.quote.get_24_hour_quote(TEST_CONTRACT_ID))

        # Check response
        self.assertResponseSuccess(quote)

        # Check data
        data = quote.get("data", [])
        self.assertIsInstance(data, list)

        # The data might be empty for the test contract
        if data:
            # Check first quote
            first_quote = data[0]
            self.assertIn("contractId", first_quote)
            self.assertEqual(first_quote["contractId"], TEST_CONTRACT_ID)

            # Log quote details
            logger.info(f"24-hour quote for {TEST_CONTRACT_ID}: {first_quote.get('lastPrice')}")
        else:
            # Log that no data was returned
            logger.info(f"No 24-hour quote data for {TEST_CONTRACT_ID}")

    def test_get_k_line(self):
        """Test get_k_line method."""
        # Create parameters
        params = GetKLineParams(
            contract_id=TEST_CONTRACT_ID,
            kline_type=KlineType.MINUTE_1,
            size=10
        )

        # Get K-line data
        klines = self.run_async(self.client.quote.get_k_line(params))

        # Check response
        self.assertResponseSuccess(klines)

        # Check data
        data = klines.get("data", {})
        # The API returns 'dataList' instead of 'list'
        if "dataList" in data:
            self.assertIsInstance(data["dataList"], list)
            kline_list = data["dataList"]
        elif "list" in data:
            self.assertIsInstance(data["list"], list)
            kline_list = data["list"]
        else:
            self.fail("Neither 'dataList' nor 'list' found in response data")

        # Check K-line count
        self.assertLessEqual(len(kline_list), 10)

        # Check first K-line
        if kline_list:
            first_kline = kline_list[0]
            self.assertIn("open", first_kline)
            self.assertIn("high", first_kline)
            self.assertIn("low", first_kline)
            self.assertIn("close", first_kline)
            self.assertIn("volume", first_kline)

            # Log K-line details
            logger.info(f"First K-line for {TEST_CONTRACT_ID}: {first_kline}")
        else:
            logger.info(f"No K-line data for {TEST_CONTRACT_ID}")

    def test_get_order_book_depth(self):
        """Test get_order_book_depth method."""
        # Create parameters - API supports 15 or 200 levels
        params = GetOrderBookDepthParams(
            contract_id=TEST_CONTRACT_ID,
            limit=15
        )

        # Get order book depth
        depth = self.run_async(self.client.quote.get_order_book_depth(params))

        # Check response
        self.assertResponseSuccess(depth)

        # Check data - API returns a list of depth objects
        data = depth.get("data", [])
        self.assertIsInstance(data, list)

        # The data might be empty for the test contract
        if data:
            depth_data = data[0]  # Get first item from list
            self.assertIn("asks", depth_data)
            self.assertIn("bids", depth_data)
            self.assertIsInstance(depth_data["asks"], list)
            self.assertIsInstance(depth_data["bids"], list)

            # Check ask and bid count
            asks = depth_data["asks"]
            bids = depth_data["bids"]
            self.assertLessEqual(len(asks), 15)
            self.assertLessEqual(len(bids), 15)

            # Log depth details
            logger.info(f"Order book depth for {TEST_CONTRACT_ID}: {len(asks)} asks, {len(bids)} bids")
        else:
            # Log that no data was returned
            logger.info(f"No order book depth data for {TEST_CONTRACT_ID}")

    def test_get_multi_contract_k_line(self):
        """Test get_multi_contract_k_line method."""
        # Create parameters
        params = GetMultiContractKLineParams(
            contract_id_list=[TEST_CONTRACT_ID],
            interval="1m",
            limit=1
        )

        # Get multi-contract K-line data
        klines = self.run_async(self.client.quote.get_multi_contract_k_line(params))

        # Check response
        self.assertResponseSuccess(klines)

        # Check data
        data = klines.get("data", {})
        # The API returns a list directly instead of a dict with 'list' key
        if isinstance(data, list):
            kline_list = data
        elif "list" in data:
            self.assertIsInstance(data["list"], list)
            kline_list = data["list"]
        else:
            self.fail("Expected list or dict with 'list' key in response data")

        # Check K-line count
        self.assertLessEqual(len(kline_list), 1)

        # Check first K-line
        if kline_list:
            first_kline = kline_list[0]
            self.assertIn("contractId", first_kline)
            # The API might return '0' for empty data or the actual contract ID
            contract_id = first_kline["contractId"]
            if contract_id != "0":
                self.assertEqual(contract_id, TEST_CONTRACT_ID)

            # Log K-line details
            logger.info(f"Multi-contract K-line for {TEST_CONTRACT_ID}: {first_kline}")
        else:
            logger.info(f"No multi-contract K-line data for {TEST_CONTRACT_ID}")


if __name__ == "__main__":
    unittest.main()
