"""Configuration for integration tests."""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load environment variables
BASE_URL = os.getenv("EDGEX_BASE_URL", "https://testnet.edgex.exchange")
WS_URL = os.getenv("EDGEX_WS_URL", "wss://quote-testnet.edgex.exchange")
ACCOUNT_ID = int(os.getenv("EDGEX_ACCOUNT_ID", "0"))
TRADING_PRIVATE_KEY = os.getenv("EDGEX_TRADING_PRIVATE_KEY", "")
API_KEY = os.getenv("EDGEX_API_KEY", "")
API_PASSPHRASE = os.getenv("EDGEX_API_PASSPHRASE", "")
API_SECRET = os.getenv("EDGEX_API_SECRET", "")

# Test data
TEST_CONTRACT_ID = os.getenv("EDGEX_TEST_CONTRACT_ID", "30000001")
TEST_ORDER_SIZE = "0.001"
TEST_ORDER_PRICE = "30000"

# Check if required environment variables are set
def check_env_vars() -> Dict[str, Any]:
    """
    Check if required environment variables are set.

    Returns:
        Dict[str, Any]: A dictionary with the status of each environment variable
    """
    env_vars = {
        "EDGEX_BASE_URL": BASE_URL,
        "EDGEX_WS_URL": WS_URL,
        "EDGEX_ACCOUNT_ID": ACCOUNT_ID,
        "EDGEX_TRADING_PRIVATE_KEY": TRADING_PRIVATE_KEY,
        "EDGEX_API_KEY": API_KEY,
        "EDGEX_API_PASSPHRASE": API_PASSPHRASE,
        "EDGEX_API_SECRET": API_SECRET,
    }

    missing_vars = []
    for var_name, var_value in env_vars.items():
        if not var_value or (var_name == "EDGEX_ACCOUNT_ID" and var_value == 0):
            missing_vars.append(var_name)

    return {
        "all_set": len(missing_vars) == 0,
        "missing_vars": missing_vars,
        "env_vars": env_vars
    }
