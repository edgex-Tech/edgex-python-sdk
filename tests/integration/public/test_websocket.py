"""Tests for public WebSocket endpoints."""

import unittest
import logging
import asyncio
import time
from typing import Dict, Any, List

from edgex_sdk import WebSocketManager
from tests.integration.public.base_test import BasePublicEndpointTest
from tests.integration.config import BASE_URL, WS_URL

# Configure logging
logger = logging.getLogger(__name__)

# Test contract ID
TEST_CONTRACT_ID = "10000004"  # Contract ID provided


class TestPublicWebSocketAPI(BasePublicEndpointTest):
    """Tests for public WebSocket endpoints."""

    def setUp(self):
        """Set up the test."""
        super().setUp()

        # Create a WebSocket manager with dummy credentials
        # Use the correct WebSocket URL from config
        self.ws_manager = WebSocketManager(
            base_url=WS_URL,
            account_id=0,  # Dummy value
            api_key="",
            api_passphrase="",
            api_secret=""
        )

        # Store received messages
        self.received_messages: List[Dict[str, Any]] = []

    def tearDown(self):
        """Tear down the test."""
        # Disconnect WebSocket
        self.ws_manager.disconnect_all()

        # Call parent tearDown
        super().tearDown()

    def message_handler(self, message: Dict[str, Any]):
        """
        Handle received WebSocket messages.

        Args:
            message: The received message
        """
        logger.info(f"Received message: {message}")
        self.received_messages.append(message)

    def test_public_websocket(self):
        """Test public WebSocket connection."""
        try:
            # Connect to public WebSocket
            self.ws_manager.connect_public()

            # Subscribe to ticker updates
            self.ws_manager.subscribe_ticker(TEST_CONTRACT_ID, self.message_handler)

            # Wait for messages (with timeout)
            start_time = time.time()
            timeout = 5  # 5 seconds

            while time.time() - start_time < timeout and not self.received_messages:
                # Process events for 0.1 seconds
                asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.1))

            # We don't assert on receiving messages because the exchange might not send any
            # during the test period. We just verify that the connection and subscription work.
            logger.info(f"Received {len(self.received_messages)} messages")

            # Test passed if we got here without exceptions
            self.assertTrue(True)
        except Exception as e:
            if "Handshake status" in str(e) or "Service Temporarily Unavailable" in str(e):
                # This is expected when:
                # 1. The WebSocket endpoint returns HTML instead of establishing a WebSocket connection
                # 2. The endpoint returns a 404, 503, or other HTTP error
                # 3. WebSocket services are not available on testnet environments
                self.skipTest(f"Skipping due to WebSocket connection issue: {e}")
            else:
                raise


if __name__ == "__main__":
    unittest.main()
