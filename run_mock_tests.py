#!/usr/bin/env python3
"""
Mock test runner for the EdgeX Python SDK.

This script runs the integration tests with dummy values for the environment variables.
It's useful for checking test wiring without real API credentials.
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set dummy environment variables
os.environ["EDGEX_BASE_URL"] = "https://testnet.edgex.exchange"
os.environ["EDGEX_WS_URL"] = "wss://testnet.edgex.exchange"
os.environ["EDGEX_ACCOUNT_ID"] = "12345"
os.environ["EDGEX_TRADING_PRIVATE_KEY"] = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
os.environ["EDGEX_API_KEY"] = "dummy-api-key"
os.environ["EDGEX_API_PASSPHRASE"] = "dummy-passphrase"
os.environ["EDGEX_API_SECRET"] = "dummy-secret"

# Log information about the mock tests
logger.info("Running integration tests with dummy credentials.")
logger.info("This means that API calls will fail, but the test wiring can be exercised.")
logger.info("For actual API testing, use the run_integration_tests.py script with valid credentials.")

# Run the integration tests as a module
result = subprocess.run([sys.executable, "-m", "tests.integration"])

# Exit with the same exit code
sys.exit(result.returncode)
