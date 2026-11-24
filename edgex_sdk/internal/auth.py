import base64
import hashlib
import hmac
import time
from typing import Dict, Any, Optional, Union, List

API_VERSION_V1 = "v1"
API_VERSION_V2 = "v2"

SIGNING_METHOD_HMAC = "hmac"

DEFAULT_HEADER_KEY = "edgeX"

# Public V2 market-data routes on which the gateway reads an optional account
# identity. A request for a contract is then answered from the order book that
# account trades on. Every other public route is always anonymous.
MARKET_DATA_IDENTITY_PATHS = frozenset({
    "/api/v2/public/quote/getTicker",
    "/api/v2/public/quote/getDepth",
    "/api/v2/public/quote/getKline",
    "/api/v2/public/quote/getMultiContractKline",
    "/api/v2/public/quote/getMultiDayKline",
    "/api/v2/public/quote/getAccurateOpenInterest",
    "/api/v2/public/quote/getMarketStatus",
    "/api/v2/public/funding/getLatestFundingRate",
    "/api/v2/public/funding/getFundingRatePage",
    "/api/v2/public/index/getIndexPriceConfig",
    "/api/v2/public/index/getMarketTradingSchedule",
})

PUBLIC_WS_PATH = "/api/v1/public/ws"


def has_market_data_identity(account_id: Any, api_key: str, api_passphrase: str, api_secret: str) -> bool:
    """An account plus the three HMAC credentials: what a market-data identity needs."""
    try:
        account = int(account_id)
    except (TypeError, ValueError):
        return False
    return account > 0 and bool(api_key and api_passphrase and api_secret)


def build_hmac_signature(
    api_secret: str,
    timestamp: str,
    method: str,
    request_uri: str,
    body: str
) -> str:
    message = f"{timestamp}{method}{request_uri}{body}"
    secret_bytes = base64.b64encode(api_secret.encode())
    mac = hmac.new(secret_bytes, message.encode(), hashlib.sha256)
    return mac.hexdigest()


def build_hmac_headers(
    api_key: str,
    api_passphrase: str,
    api_secret: str,
    timestamp: str,
    method: str,
    request_uri: str,
    body: str,
    header_key: str = DEFAULT_HEADER_KEY
) -> Dict[str, str]:
    signature = build_hmac_signature(api_secret, timestamp, method, request_uri, body)
    return {
        f"X-{header_key}-Api-Key": api_key,
        f"X-{header_key}-Passphrase": api_passphrase,
        f"X-{header_key}-Signature": signature,
        f"X-{header_key}-Timestamp": timestamp,
    }


def should_sign_with_hmac(path: str) -> bool:
    lower = path.lower()
    if "private" in lower:
        return True
    if "/opt/" in lower:
        return True
    if "invite" in lower:
        return True
    if "points" in lower:
        return True
    if "/public/codeinfo" in lower:
        return True
    if lower.startswith("/ranking"):
        return True
    if "nft" in lower:
        return True
    if "vault" in lower:
        return True
    if lower.startswith("/activity"):
        return True
    if "public/info" in lower:
        return True
    if "/download" in lower:
        return True
    return False


def rewrite_path_to_v2(path: str) -> str:
    if "/api/api/v1/" in path:
        return path.replace("/api/api/v1/", "/api/v2/", 1)
    if path.endswith("/api/api/v1"):
        return path[:-len("/api/api/v1")] + "/api/v2"
    if "/api/v1/" in path:
        return path.replace("/api/v1/", "/api/v2/", 1)
    if path.endswith("/api/v1"):
        return path[:-len("/api/v1")] + "/api/v2"
    if "/v1/" in path:
        return path.replace("/v1/", "/v2/", 1)
    if path.endswith("/v1"):
        return path[:-len("/v1")] + "/v2"
    return path


def get_value(data: Union[Dict[str, Any], List[Any], str, int, float, bool, None]) -> str:
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    if isinstance(data, bool):
        return str(data).lower()
    if isinstance(data, (int, float)):
        return str(data)
    if isinstance(data, list):
        if len(data) == 0:
            return ""
        return "&".join(get_value(item) for item in data)
    if isinstance(data, dict):
        keys = sorted(data.keys())
        return "&".join(f"{k}={get_value(data[k])}" for k in keys)
    return str(data)
