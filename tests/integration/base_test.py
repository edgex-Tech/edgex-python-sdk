"""Base test class for integration tests."""

import unittest
import asyncio
import logging
import os
from typing import Dict, Any, Optional

from edgex_sdk import Client, WebSocketManager
from .config import (
    BASE_URL,
    WS_URL,
    ACCOUNT_ID,
    TRADING_PRIVATE_KEY,
    API_KEY,
    API_PASSPHRASE,
    API_SECRET,
    check_env_vars,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BaseIntegrationTest(unittest.TestCase):
    """Base class for integration tests."""

    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        # Check if required environment variables are set
        env_status = check_env_vars()
        if not env_status["all_set"]:
            missing_vars = env_status["missing_vars"]
            raise unittest.SkipTest(
                f"Skipping integration tests because the following environment variables are not set: {', '.join(missing_vars)}"
            )

        logger.info("Using EIP-712 trading key signing")

        # Store test data
        cls.test_data = {}

    @classmethod
    def tearDownClass(cls):
        """Tear down the test class."""
        pass  # No class-level cleanup needed

    def run_async(self, coro):
        """
        Run an async coroutine in the current event loop.

        Args:
            coro: The coroutine to run

        Returns:
            Any: The result of the coroutine
        """
        return self.loop.run_until_complete(coro)

    def setUp(self):
        """Set up the test."""
        # Create a new event loop for each test
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Create a fresh client for each test method
        self.client = Client(
            base_url=BASE_URL,
            account_id=ACCOUNT_ID,
            api_key=API_KEY,
            api_passphrase=API_PASSPHRASE,
            api_secret=API_SECRET,
            trading_private_key=TRADING_PRIVATE_KEY,
        )

        # Create WebSocket manager for each test
        self.ws_manager = WebSocketManager(
            base_url=WS_URL,
            account_id=ACCOUNT_ID,
            api_key=API_KEY,
            api_passphrase=API_PASSPHRASE,
            api_secret=API_SECRET,
        )

    def tearDown(self):
        """Tear down the test."""
        # Close client and WebSocket connections
        if hasattr(self, 'client'):
            self.run_async(self.client.close())

        if hasattr(self, 'ws_manager'):
            self.ws_manager.disconnect_all()

        # Close the event loop
        self.loop.close()

    def assertResponseSuccess(self, response: Dict[str, Any], msg: Optional[str] = None):
        """
        Assert that a response is successful.

        Args:
            response: The response to check
            msg: Optional message to display on failure
        """
        self.assertIn("code", response, msg=msg)
        self.assertEqual(response["code"], "SUCCESS", msg=msg)
        self.assertIn("data", response, msg=msg)
