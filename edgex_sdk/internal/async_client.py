import hashlib
import time
import json
from typing import Dict, Any, Optional, List, Union
from decimal import Decimal

import aiohttp

from .auth import (
    API_VERSION_V2,
    SIGNING_METHOD_HMAC,
    DEFAULT_HEADER_KEY,
    build_hmac_headers,
    should_sign_with_hmac,
    rewrite_path_to_v2,
    get_value,
)
from .eip712 import (
    derive_address_from_private_key,
    sign_typed_data,
)


class AsyncClient:
    def __init__(
        self,
        base_url: str,
        account_id: int,
        asset_base_url: str = "",
        api_key: str = "",
        api_passphrase: str = "",
        api_secret: str = "",
        trading_private_key: str = "",
        wallet_private_key: str = "",
        trading_address: str = "",
        wallet_address: str = "",
        auth_header_key: str = DEFAULT_HEADER_KEY,
        timeout: float = 30.0,
        connector_limit: int = 100,
    ):
        self.base_url = base_url.rstrip("/")
        self.asset_base_url = (asset_base_url or base_url).rstrip("/")
        self.account_id = account_id
        self.api_key = api_key
        self.api_passphrase = api_passphrase
        self.api_secret = api_secret
        self.trading_private_key = trading_private_key
        self.wallet_private_key = wallet_private_key
        self.trading_address = trading_address
        self.wallet_address = wallet_address
        self.auth_header_key = auth_header_key

        self._session: Optional[aiohttp.ClientSession] = None
        self._timeout = timeout
        self._connector_limit = connector_limit
        self._closed = False

    async def __aenter__(self):
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _ensure_session(self):
        if self._session is None or self._session.closed:
            timeout_config = aiohttp.ClientTimeout(total=self._timeout)
            connector = aiohttp.TCPConnector(
                limit=self._connector_limit,
                limit_per_host=30,
                keepalive_timeout=30,
                enable_cleanup_closed=True,
            )
            self._session = aiohttp.ClientSession(
                timeout=timeout_config,
                connector=connector,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
        self._closed = True

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            raise RuntimeError("Session not initialized. Use 'async with client:' or call '_ensure_session()'")
        return self._session

    def get_account_id(self) -> int:
        return self.account_id

    # ── resolution parsing ──

    @staticmethod
    def parse_resolution(resolution: str) -> Decimal:
        resolution = (resolution or "").strip()
        if not resolution:
            raise ValueError("resolution is empty")
        lower = resolution.lower()
        if lower.startswith("0x"):
            return Decimal(int(lower, 16))
        return Decimal(resolution)

    # ── signer address helpers ──

    def resolve_trading_signer_address(self) -> str:
        if self.trading_address:
            return self.trading_address
        if not self.trading_private_key:
            raise ValueError("trading private key is required to derive signer address")
        self.trading_address = derive_address_from_private_key(self.trading_private_key)
        return self.trading_address

    def resolve_wallet_signer_address(self) -> str:
        if self.wallet_address:
            return self.wallet_address
        if not self.wallet_private_key:
            raise ValueError("wallet private key is required to derive signer address")
        self.wallet_address = derive_address_from_private_key(self.wallet_private_key)
        return self.wallet_address

    def sign_typed_data_with_trading_key(self, typed_data: Dict[str, Any], include_0x: bool = False) -> str:
        if not self.trading_private_key:
            raise ValueError("trading private key is required for EIP-712 signing")
        return sign_typed_data(self.trading_private_key, typed_data, include_0x=include_0x)

    def sign_typed_data_with_wallet_key(self, typed_data: Dict[str, Any], include_0x: bool = False) -> str:
        if not self.wallet_private_key:
            raise ValueError("wallet private key is required for EIP-712 signing")
        return sign_typed_data(self.wallet_private_key, typed_data, include_0x=include_0x)

    # ── nonce / client id ──

    @staticmethod
    def calc_nonce(client_order_id: str) -> int:
        h = hashlib.sha256()
        h.update(client_order_id.encode())
        return int(h.hexdigest()[:8], 16)

    @staticmethod
    def get_random_client_id() -> str:
        return str(time.time_ns())

    # ── HTTP request ──

    async def make_authenticated_request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        rewrite_version: bool = True,
    ) -> Dict[str, Any]:
        await self._ensure_session()

        actual_path = rewrite_path_to_v2(path) if rewrite_version else path
        base_url = self._base_url_for_path(actual_path)
        url = f"{base_url}{actual_path}"

        timestamp = str(int(time.time() * 1000))
        headers: Dict[str, str] = {}

        if should_sign_with_hmac(actual_path):
            if method.upper() == "GET":
                if params:
                    sorted_pairs = sorted(params.items())
                    body_str = "&".join(f"{k}={v}" for k, v in sorted_pairs)
                else:
                    body_str = ""
            else:
                body_str = get_value(data) if data else ""

            headers = build_hmac_headers(
                api_key=self.api_key,
                api_passphrase=self.api_passphrase,
                api_secret=self.api_secret,
                timestamp=timestamp,
                method=method,
                request_uri=actual_path,
                body=body_str,
                header_key=self.auth_header_key,
            )

        try:
            async with self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
            ) as response:
                if response.status != 200:
                    try:
                        error_detail = await response.json()
                        raise ValueError(f"request failed with status code: {response.status}, response: {error_detail}")
                    except (aiohttp.ContentTypeError, json.JSONDecodeError):
                        text = await response.text()
                        raise ValueError(f"request failed with status code: {response.status}, response: {text}")

                resp_data = await response.json()
                return resp_data

        except aiohttp.ClientError as e:
            raise ValueError(f"HTTP request failed: {str(e)}")

    async def make_public_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        await self._ensure_session()

        actual_path = rewrite_path_to_v2(path)
        url = f"{self.base_url}{actual_path}"

        try:
            async with self.session.request(
                method=method,
                url=url,
                params=params,
            ) as response:
                if response.status != 200:
                    try:
                        error_detail = await response.json()
                        raise ValueError(f"request failed with status code: {response.status}, response: {error_detail}")
                    except (aiohttp.ContentTypeError, json.JSONDecodeError):
                        text = await response.text()
                        raise ValueError(f"request failed with status code: {response.status}, response: {text}")

                resp_data = await response.json()
                return resp_data

        except aiohttp.ClientError as e:
            raise ValueError(f"HTTP request failed: {str(e)}")

    def _base_url_for_path(self, path: str) -> str:
        if path.startswith("/api/v1/private/unified-asset/"):
            return self.asset_base_url
        return self.base_url
