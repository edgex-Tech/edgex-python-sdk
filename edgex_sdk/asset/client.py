import time
from decimal import Decimal
from typing import Dict, Any, List

from ..internal.async_client import AsyncClient
from ..internal.eip712 import (
    EIP712_DOMAIN_TYPE,
    WITHDRAWAL_PARAMS_TYPE,
    build_eip712_domain,
)


class GetAssetOrdersParams:
    def __init__(self, size: str = "10", offset_data: str = "", chain_id: str = "",
                 type_list: List[str] = None, start_time: int = 0, end_time: int = 0):
        self.size = size
        self.offset_data = offset_data
        self.chain_id = chain_id
        self.type_list = type_list or []
        self.start_time = start_time
        self.end_time = end_time


class CreateWithdrawalParams:
    def __init__(self, coin_id: str, amount: str, eth_address: str):
        self.coin_id = coin_id
        self.amount = amount
        self.eth_address = eth_address


class GetWithdrawSignInfoParams:
    def __init__(self, chain_id: str, token_address: str, amount: str):
        self.chain_id = chain_id
        self.token_address = token_address
        self.amount = amount


class Client:
    def __init__(self, async_client: AsyncClient):
        self.async_client = async_client

    async def get_asset_orders(self, params: GetAssetOrdersParams) -> Dict[str, Any]:
        query_params = {"accountId": str(self.async_client.get_account_id())}
        if params.size:
            query_params["size"] = params.size
        if params.offset_data:
            query_params["offsetData"] = params.offset_data
        if params.chain_id:
            query_params["chainId"] = params.chain_id
        if params.type_list:
            query_params["typeList"] = ",".join(params.type_list)
        if params.start_time > 0:
            query_params["startTime"] = str(params.start_time)
        if params.end_time > 0:
            query_params["endTime"] = str(params.end_time)
        return await self.async_client.make_authenticated_request(
            method="GET", path="/api/v2/private/assets/getAllOrdersPage", params=query_params)

    async def create_withdrawal(self, params: CreateWithdrawalParams, metadata: Dict[str, Any]) -> Dict[str, Any]:
        coin = None
        for coin_data in metadata.get("coinList", []):
            if coin_data.get("coinId") == params.coin_id:
                coin = coin_data
                break
        if not coin:
            raise ValueError(f"coin not found: {params.coin_id}")

        if not self.async_client.wallet_pri_key:
            raise ValueError("wallet private key is required for v2 EIP-712 withdrawal signing")

        account_id = str(self.async_client.get_account_id())
        client_id = self.async_client.get_random_client_id()
        nonce = self.async_client.calc_nonce(client_id)

        l2_expire_time = int(time.time() * 1000) + (14 * 24 * 60 * 60 * 1000)
        expiration_timestamp_seconds = l2_expire_time // 1000

        coin_resolution = self.async_client.parse_resolution(coin.get("resolution", ""))
        amount_dm = Decimal(params.amount)
        amount_int = str(int(amount_dm * coin_resolution))

        global_data = metadata.get("global", {})
        chain_id = (global_data.get("nativeChainId") or global_data.get("chainId") or "").strip()
        verifying_contract = (global_data.get("contractAddress") or "").strip()
        if not chain_id:
            raise ValueError("metadata.global.nativeChainId/chainId is required")
        if not verifying_contract:
            raise ValueError("metadata.global.contractAddress is required")

        signer = self.async_client.resolve_wallet_signer_address()
        domain = build_eip712_domain("EdgeX", "1", chain_id, verifying_contract)

        typed_data = {
            "types": {
                "EIP712Domain": EIP712_DOMAIN_TYPE,
                "WithdrawalParams": WITHDRAWAL_PARAMS_TYPE,
            },
            "primaryType": "WithdrawalParams",
            "domain": domain,
            "message": {
                "from": account_id,
                "toAddress": params.eth_address,
                "amount": amount_int,
                "feeAmount": "0",
                "nonce": str(nonce),
                "expirationTimestamp": str(expiration_timestamp_seconds),
                "signer": signer,
            },
        }

        l2_signature = self.async_client.sign_typed_data_with_wallet_key(typed_data)

        data = {
            "accountId": account_id,
            "coinId": params.coin_id,
            "amount": params.amount,
            "ethAddress": params.eth_address,
            "clientWithdrawId": client_id,
            "l2ExpireTime": str(l2_expire_time),
            "signature": l2_signature,
            "signer": signer,
            "nonce": str(nonce),
        }

        return await self.async_client.make_authenticated_request(
            method="POST", path="/api/v2/private/assets/createNormalWithdraw", data=data)

    async def get_withdraw_sign_info(self, params: GetWithdrawSignInfoParams) -> Dict[str, Any]:
        query_params = {
            "accountId": str(self.async_client.get_account_id()),
            "chainId": params.chain_id,
            "tokenAddress": params.token_address,
            "amount": params.amount,
        }
        return await self.async_client.make_authenticated_request(
            method="GET", path="/api/v2/private/assets/getWithdrawSignInfo", params=query_params)
