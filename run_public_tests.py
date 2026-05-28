#!/usr/bin/env python3
"""
Public endpoints test runner for the EdgeX Python SDK.

This script runs tests for public endpoints that don't require authentication.
"""

import os
import sys
import unittest
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set dummy values for required environment variables
# These won't be used for authentication but are needed for client initialization
os.environ["EDGEX_BASE_URL"] = "https://pro.edgex.exchange"
# Use the correct WebSocket URL
os.environ["EDGEX_WS_URL"] = "wss://quote.edgex.exchange"
os.environ["EDGEX_ACCOUNT_ID"] = "0"  # Dummy value
os.environ["EDGEX_TRADING_PRIVATE_KEY"] = "0" * 64  # Dummy value
os.environ["EDGEX_API_KEY"] = "dummy-api-key"
os.environ["EDGEX_API_PASSPHRASE"] = "dummy-passphrase"
os.environ["EDGEX_API_SECRET"] = "dummy-secret"
os.environ["EDGEX_PUBLIC_ONLY"] = "true"  # Flag to indicate public endpoints only

# Log information
logger.info("Running tests for public endpoints only")
logger.info("These tests don't require authentication credentials")

# Create the public test directory if it doesn't exist
os.makedirs("tests/integration/public", exist_ok=True)

# Create an __init__.py file in the public test directory
with open("tests/integration/public/__init__.py", "w") as f:
    f.write("# Public endpoint tests\n")

# Discover and run tests
test_loader = unittest.TestLoader()

# Run the public endpoint tests
test_suite = test_loader.discover('tests/integration/public', pattern='test_*.py')

# Run the tests
test_runner = unittest.TextTestRunner(verbosity=2)
result = test_runner.run(test_suite)

# Exit with the number of failures and errors
sys.exit(len(result.failures) + len(result.errors))
