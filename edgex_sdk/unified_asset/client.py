import os
import threading
import time
from typing import Any, Dict, Optional

from ..internal.async_client import AsyncClient
from ..internal.eip712 import build_typed_data_from_server_response


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
NATIVE_TOKEN_ADDRESS = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"

EDGE_MAINNET_USDC = "0x98d2919b9A214E6Fa5384AC81E6864bA686Ad74c"
EDGE_TESTNET_USDC = "0x5a4f218dcb4e257a4586159e9ee925b0fa1df610"

UNIFIED_ASSET_BASE_PATH = "/api/v1/private/unified-asset"

WITHDRAW_PROFILES = {
    "mainnet-usdc": {
        "asset": "usdc",
        "network": "mainnet",
        "source": "spot",
        "chain_id": 3343,
        "token_address": EDGE_MAINNET_USDC,
        "flow_type": "spot_normal_withdraw",
        "description": "USDC spot withdraw to Edge Mainnet",
    },
    "testnet-usdc": {
        "asset": "usdc",
        "network": "testnet",
        "source": "spot",
        "chain_id": 33431,
        "token_address": EDGE_TESTNET_USDC,
        "flow_type": "spot_normal_withdraw",
        "description": "USDC spot withdraw to Edge Testnet",
    },
    "mainnet-eth-native": {
        "asset": "eth-native",
        "network": "mainnet",
        "source": "spot",
        "chain_id": 42161,
        "token_address": NATIVE_TOKEN_ADDRESS,
        "flow_type": "spot_native_withdraw",
        "description": "ETH native bridge withdraw from Spot to Arbitrum Mainnet",
    },
    "testnet-eth-native": {
        "asset": "eth-native",
        "network": "testnet",
        "source": "spot",
        "chain_id": 421614,
        "token_address": NATIVE_TOKEN_ADDRESS,
        "flow_type": "spot_native_withdraw",
        "description": "ETH native bridge withdraw from Spot to Arbitrum Sepolia",
    },
}

ASSET_PROFILE_MAP = {
    ("usdc", "mainnet"): "mainnet-usdc",
    ("usdc", "testnet"): "testnet-usdc",
    ("eth-native", "mainnet"): "mainnet-eth-native",
    ("eth-native", "testnet"): "testnet-eth-native",
}

_SF_LOCK = threading.Lock()
_SF_LAST_TS = 0
_SF_SEQ = 0
_SF_EPOCH_MS = 1577836800000


class GatewayError(RuntimeError):
    def __init__(self, code: str, msg: str, trace_id: str):
        super().__init__("[%s] %s (trace=%s)" % (code, msg, trace_id))
        self.code = code
        self.msg = msg
        self.trace_id = trace_id


class CreateWithdrawParams:
    def __init__(
        self,
        amount_raw: str,
        user_address: str,
        token_address: str = "",
        chain_id: int = 0,
        source: str = "spot",
        source_account: str = "",
        profile: str = "",
        asset: str = "usdc",
        network: str = "mainnet",
        privy_address: str = ZERO_ADDRESS,
        privy_identity_token: str = "",
        client_withdraw_id: str = "",
        expire_seconds: int = 300,
        expire_time: int = 0,
        extra_data: str = "",
    ):
        self.amount_raw = str(amount_raw)
        self.user_address = user_address
        self.token_address = token_address
        self.chain_id = int(chain_id) if chain_id else 0
        self.source = source
        self.source_account = str(source_account) if source_account else ""
        self.profile = profile
        self.asset = asset
        self.network = network
        self.privy_address = privy_address or ZERO_ADDRESS
        self.privy_identity_token = privy_identity_token
        self.client_withdraw_id = client_withdraw_id
        self.expire_seconds = expire_seconds
        self.expire_time = expire_time
        self.extra_data = extra_data


class CreateSpotDepositParams:
    def __init__(
        self,
        amount_raw: str,
        user_address: str,
        token_address: str,
        chain_id: int,
        spot_account_id: str = "",
        source_account: str = "",
        privy_address: str = ZERO_ADDRESS,
        extra_data: str = "",
    ):
        self.amount_raw = str(amount_raw)
        self.user_address = user_address
        self.token_address = token_address
        self.chain_id = int(chain_id)
        self.spot_account_id = str(spot_account_id) if spot_account_id else ""
        self.source_account = source_account
        self.privy_address = privy_address or ZERO_ADDRESS
        self.extra_data = extra_data


def next_snowflake_id() -> int:
    global _SF_LAST_TS, _SF_SEQ
    node = int(os.getenv("NODE_ID", "1")) & 0x3FF
    with _SF_LOCK:
        now = int(time.time() * 1000)
        if now == _SF_LAST_TS:
            _SF_SEQ = (_SF_SEQ + 1) & 0xFFF
            if _SF_SEQ == 0:
                while now <= _SF_LAST_TS:
                    now = int(time.time() * 1000)
        else:
            _SF_SEQ = 0
        _SF_LAST_TS = now
        return ((now - _SF_EPOCH_MS) << 22) | (node << 12) | _SF_SEQ


def _unwrap_response(response: Dict[str, Any]) -> Any:
    if response.get("code") and response.get("code") != "SUCCESS":
        raise GatewayError(
            response.get("code", ""),
            response.get("msg") or "",
            response.get("traceId") or "",
        )
    return response.get("data", response)


def resolve_withdraw_profile(profile_name: str) -> Dict[str, Any]:
    if profile_name not in WITHDRAW_PROFILES:
        known = ", ".join(sorted(WITHDRAW_PROFILES))
        raise ValueError("unknown withdraw profile %r; known: %s" % (profile_name, known))
    return dict(WITHDRAW_PROFILES[profile_name])


def profile_name_for_asset(asset: str, network: str) -> str:
    key = (asset, network)
    if key not in ASSET_PROFILE_MAP:
        known = ", ".join("%s/%s" % item for item in sorted(ASSET_PROFILE_MAP))
        raise ValueError("unknown asset/network %r/%r; known: %s" % (asset, network, known))
    return ASSET_PROFILE_MAP[key]


def build_withdraw_attempt(
    user_address: str,
    source: str,
    source_account: str,
    token_address: str,
    amount_raw: str,
    chain_id: int,
    expire_time: int,
    client_withdraw_id: str,
    privy_address: str = ZERO_ADDRESS,
) -> Dict[str, Any]:
    return {
        "userAddress": user_address,
        "privyAddress": privy_address or ZERO_ADDRESS,
        "source": source,
        "sourceAccount": str(source_account),
        "tokenAddress": token_address,
        "amount": str(amount_raw),
        "fee": "0",
        "destination": "chain-%d" % int(chain_id),
        "destinationAccount": user_address,
        "clientWithdrawId": str(client_withdraw_id),
        "expireTime": int(expire_time),
    }


def build_spot_deposit_attempt(
    user_address: str,
    source_account: str,
    token_address: str,
    amount_raw: str,
    chain_id: int,
    spot_account_id: str,
    privy_address: str = ZERO_ADDRESS,
) -> Dict[str, Any]:
    return {
        "userAddress": user_address,
        "privyAddress": privy_address or ZERO_ADDRESS,
        "source": "chain-%d" % int(chain_id),
        "sourceAccount": source_account,
        "tokenAddress": token_address,
        "amount": str(amount_raw),
        "fee": "0",
        "destination": "spot",
        "destinationAccount": str(spot_account_id),
    }


def apply_fee_to_attempt(attempt: Dict[str, Any], fee: str) -> None:
    gross_amount = int(attempt["amount"])
    fee_amount = int(fee)
    if fee_amount < 0:
        raise ValueError("fee must be non-negative")
    if fee_amount >= gross_amount:
        raise ValueError(
            "fee must be less than gross amount: fee=%d, gross=%d"
            % (fee_amount, gross_amount)
        )
    attempt["fee"] = str(fee_amount)
    attempt["amount"] = str(gross_amount - fee_amount)


class Client:
    def __init__(self, async_client: AsyncClient):
        self.async_client = async_client

    async def get_fee_by_asset_flow(self, attempt: Dict[str, Any]) -> Dict[str, Any]:
        response = await self.async_client.make_authenticated_request(
            method="POST",
            path=UNIFIED_ASSET_BASE_PATH + "/getFeeByAssetFlow",
            data={"attempt": attempt},
            rewrite_version=False,
        )
        return _unwrap_response(response)

    async def get_eip712_data(self, attempt: Dict[str, Any]) -> Dict[str, Any]:
        response = await self.async_client.make_authenticated_request(
            method="POST",
            path=UNIFIED_ASSET_BASE_PATH + "/getEIP712Data",
            data={"attempt": attempt},
            rewrite_version=False,
        )
        return _unwrap_response(response)

    async def get_deposit_data(
        self,
        attempt: Dict[str, Any],
        extra_data: str = "",
    ) -> Dict[str, Any]:
        response = await self.async_client.make_authenticated_request(
            method="POST",
            path=UNIFIED_ASSET_BASE_PATH + "/getDepositData",
            data={"attempt": attempt, "extraData": extra_data},
            rewrite_version=False,
        )
        return _unwrap_response(response)

    async def submit_asset_flow(
        self,
        attempt: Dict[str, Any],
        user_signature: str,
        privy_identity_token: str = "",
        extra_data: str = "",
    ) -> Dict[str, Any]:
        response = await self.async_client.make_authenticated_request(
            method="POST",
            path=UNIFIED_ASSET_BASE_PATH + "/submitAssetFlow",
            data={
                "attempt": attempt,
                "userSignature": user_signature,
                "extraData": extra_data,
                "privyIdentityToken": privy_identity_token,
            },
            rewrite_version=False,
        )
        return _unwrap_response(response)

    async def query_asset_flows(self, params: Dict[str, Any]) -> Dict[str, Any]:
        response = await self.async_client.make_authenticated_request(
            method="GET",
            path=UNIFIED_ASSET_BASE_PATH + "/queryAssetFlows",
            params=params,
            rewrite_version=False,
        )
        return _unwrap_response(response)

    async def create_withdraw(self, params: CreateWithdrawParams) -> Dict[str, Any]:
        profile_name = params.profile or profile_name_for_asset(params.asset, params.network)
        profile = resolve_withdraw_profile(profile_name)

        source = params.source or profile.get("source", "spot")
        source_account = params.source_account or str(self.async_client.get_account_id())
        token_address = params.token_address or profile.get("token_address", "")
        chain_id = params.chain_id or int(profile.get("chain_id", 0))
        if not token_address:
            raise ValueError("token_address is required")
        if chain_id <= 0:
            raise ValueError("chain_id is required")

        client_withdraw_id = params.client_withdraw_id or str(next_snowflake_id())
        expire_time = params.expire_time or int(time.time()) + int(params.expire_seconds)
        attempt = build_withdraw_attempt(
            user_address=params.user_address,
            privy_address=params.privy_address,
            source=source,
            source_account=source_account,
            token_address=token_address,
            amount_raw=params.amount_raw,
            chain_id=chain_id,
            expire_time=expire_time,
            client_withdraw_id=client_withdraw_id,
        )

        fee_data = await self.get_fee_by_asset_flow(attempt)
        apply_fee_to_attempt(attempt, str(fee_data.get("fee", "0")))

        eip712_response = await self.get_eip712_data(attempt)
        typed_data = build_typed_data_from_server_response(eip712_response)
        signature = self.async_client.sign_typed_data_with_wallet_key(
            typed_data, include_0x=True
        )

        return await self.submit_asset_flow(
            attempt=attempt,
            user_signature=signature,
            privy_identity_token=params.privy_identity_token,
            extra_data=params.extra_data,
        )

    async def get_spot_deposit_data(self, params: CreateSpotDepositParams) -> Dict[str, Any]:
        if not params.token_address:
            raise ValueError("token_address is required")
        if params.chain_id <= 0:
            raise ValueError("chain_id is required")

        spot_account_id = params.spot_account_id or str(self.async_client.get_account_id())
        source_account = params.source_account or params.user_address
        attempt = build_spot_deposit_attempt(
            user_address=params.user_address,
            privy_address=params.privy_address,
            source_account=source_account,
            token_address=params.token_address,
            amount_raw=params.amount_raw,
            chain_id=params.chain_id,
            spot_account_id=spot_account_id,
        )
        return await self.get_deposit_data(attempt, params.extra_data)
