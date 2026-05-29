"""Base test class for public endpoint tests."""

import unittest
import asyncio
import logging
import os
from typing import Dict, Any, Optional

from edgex_sdk import Client
from tests.integration.config import BASE_URL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BasePublicEndpointTest(unittest.TestCase):
    """Base class for public endpoint tests."""

    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        # Store test data
        cls.test_data = {}

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

        # Create client with dummy values
        # The account_id and trading_private_key won't be used for public endpoints
        self.client = Client(
            base_url=BASE_URL,
            account_id=0,  # Dummy value
            trading_private_key="0" * 64,  # Dummy value
        )

    def tearDown(self):
        """Tear down the test."""
        # Close client
        if hasattr(self, 'client'):
            self.run_async(self.client.close())

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
