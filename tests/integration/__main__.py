"""
Main module for running integration tests.
"""

import unittest
import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Running integration tests for the v2 EIP-712 signing path.")
logger.info("This test suite exercises the current SDK request and signing flow.")

# Discover and run tests
test_loader = unittest.TestLoader()
test_suite = test_loader.discover(os.path.dirname(__file__), pattern='test_*.py')

# Run the tests
test_runner = unittest.TextTestRunner(verbosity=2)
result = test_runner.run(test_suite)

# Exit with the number of failures and errors
sys.exit(len(result.failures) + len(result.errors))
