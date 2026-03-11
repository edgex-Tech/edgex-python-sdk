import time
from decimal import Decimal
from typing import Dict, Any, List, Optional
from enum import Enum

from ..internal.async_client import AsyncClient
from ..internal.eip712 import (
    EIP712_DOMAIN_TYPE,
    TRANSFER_PARAMS_TYPE,
    build_eip712_domain,
)


class TransferReason(Enum):
    USER_TRANSFER = "USER_TRANSFER"
    FAST_WITHDRAW = "FAST_WITHDRAW"
    CROSS_DEPOSIT = "CROSS_DEPOSIT"
    CROSS_WITHDRAW = "CROSS_WITHDRAW"


class CreateTransferOutParams:
    def __init__(
        self,
        coin_id: str,
        amount: str,
        receiver_account_id: str,
        transfer_reason: TransferReason = TransferReason.USER_TRANSFER,
        client_transfer_id: str = "",
        l2_nonce: str = "",
        l2_expire_time: str = "",
        l2_signature: str = "",
        signer: str = "",
        extra_type: Optional[str] = None,
        extra_data_json: Optional[str] = None,
    ):
        self.coin_id = coin_id
        self.amount = amount
        self.receiver_account_id = receiver_account_id
        self.transfer_reason = transfer_reason
        self.client_transfer_id = client_transfer_id
        self.l2_nonce = l2_nonce
        self.l2_expire_time = l2_expire_time
        self.l2_signature = l2_signature
        self.signer = signer
        self.extra_type = extra_type
        self.extra_data_json = extra_data_json


class GetTransferOutByIdParams:
    def __init__(self, transfer_id_list: List[str]):
        self.transfer_id_list = transfer_id_list


class GetTransferInByIdParams:
    def __init__(self, transfer_id_list: List[str]):
        self.transfer_id_list = transfer_id_list


class GetWithdrawAvailableAmountParams:
    def __init__(self, coin_id: str):
        self.coin_id = coin_id


class GetTransferOutPageParams:
    def __init__(self, size: str = "10", offset_data: str = "", filter_coin_id_list: List[str] = None,
                 filter_status_list: List[str] = None, filter_start_created_time_inclusive: int = 0,
                 filter_end_created_time_exclusive: int = 0):
        self.size = size
        self.offset_data = offset_data
        self.filter_coin_id_list = filter_coin_id_list or []
        self.filter_status_list = filter_status_list or []
        self.filter_start_created_time_inclusive = filter_start_created_time_inclusive
        self.filter_end_created_time_exclusive = filter_end_created_time_exclusive


class GetTransferInPageParams:
    def __init__(self, size: str = "10", offset_data: str = "", filter_coin_id_list: List[str] = None,
                 filter_status_list: List[str] = None, filter_start_created_time_inclusive: int = 0,
                 filter_end_created_time_exclusive: int = 0):
        self.size = size
        self.offset_data = offset_data
        self.filter_coin_id_list = filter_coin_id_list or []
        self.filter_status_list = filter_status_list or []
        self.filter_start_created_time_inclusive = filter_start_created_time_inclusive
        self.filter_end_created_time_exclusive = filter_end_created_time_exclusive


def _resolve_coin_resolution(metadata: Dict[str, Any], coin_id: str) -> str:
    for coin in metadata.get("coinList", []):
        if coin.get("coinId") == coin_id:
            resolution = (coin.get("resolution") or "").strip()
            if not resolution:
                raise ValueError(f"resolution not found for coin: {coin_id}")
            return resolution
    raise ValueError(f"coin not found in metadata: {coin_id}")


class Client:
    def __init__(self, async_client: AsyncClient):
        self.async_client = async_client

    async def get_transfer_out_by_id(self, params: GetTransferOutByIdParams) -> Dict[str, Any]:
        query_params = {
            "accountId": str(self.async_client.get_account_id()),
            "transferOutIdList": ",".join(params.transfer_id_list),
        }
        return await self.async_client.make_authenticated_request(
            method="GET", path="/api/v2/private/transfer/getTransferOutById", params=query_params)

    async def get_transfer_in_by_id(self, params: GetTransferInByIdParams) -> Dict[str, Any]:
        query_params = {
            "accountId": str(self.async_client.get_account_id()),
            "transferInIdList": ",".join(params.transfer_id_list),
        }
        return await self.async_client.make_authenticated_request(
            method="GET", path="/api/v2/private/transfer/getTransferInById", params=query_params)

    async def get_withdraw_available_amount(self, params: GetWithdrawAvailableAmountParams) -> Dict[str, Any]:
        query_params = {
            "accountId": str(self.async_client.get_account_id()),
            "coinId": params.coin_id,
        }
        return await self.async_client.make_authenticated_request(
            method="GET", path="/api/v2/private/transfer/getTransferOutAvailableAmount", params=query_params)

    async def create_transfer_out(self, params: CreateTransferOutParams, metadata: Dict[str, Any]) -> Dict[str, Any]:
        if not metadata or not metadata.get("global"):
            raise ValueError("metadata.global is nil")

        client_transfer_id = (params.client_transfer_id or "").strip()
        if not client_transfer_id:
            client_transfer_id = self.async_client.get_random_client_id()

        l2_nonce = (params.l2_nonce or "").strip()
        if not l2_nonce:
            l2_nonce = str(self.async_client.calc_nonce(client_transfer_id))

        l2_expire_time = (params.l2_expire_time or "").strip()
        if not l2_expire_time:
            l2_expire_time = str(int(time.time() * 1000) + 10 * 24 * 60 * 60 * 1000)

        deadline = str(int(l2_expire_time) // 1000)

        coin_resolution_str = _resolve_coin_resolution(metadata, params.coin_id)
        coin_resolution = self.async_client.parse_resolution(coin_resolution_str)
        amount_dm = Decimal(params.amount)
        amount_int = str(int(amount_dm * coin_resolution))

        l2_signature = (params.l2_signature or "").strip()
        if not l2_signature:
            if not self.async_client.wallet_pri_key:
                raise ValueError("wallet private key is required for v2 EIP-712 transfer signing")

            signer = (params.signer or "").strip()
            if not signer:
                signer = self.async_client.resolve_wallet_signer_address()

            global_data = metadata.get("global", {})
            chain_id = (global_data.get("chainId") or global_data.get("nativeChainId") or "").strip()
            verifying_contract = (global_data.get("contractAddress") or "").strip()
            if not chain_id:
                raise ValueError("metadata.global.chainId/nativeChainId is required")
            if not verifying_contract:
                raise ValueError("metadata.global.contractAddress is required")

            domain = build_eip712_domain("EdgeX", "1", chain_id, verifying_contract)

            typed_data = {
                "types": {
                    "EIP712Domain": EIP712_DOMAIN_TYPE,
                    "TransferParams": TRANSFER_PARAMS_TYPE,
                },
                "primaryType": "TransferParams",
                "domain": domain,
                "message": {
                    "from": str(self.async_client.get_account_id()),
                    "to": params.receiver_account_id,
                    "assetId": params.coin_id,
                    "amount": amount_int,
                    "nonce": l2_nonce,
                    "deadline": deadline,
                    "signer": signer,
                },
            }

            l2_signature = self.async_client.sign_typed_data_with_wallet_key(typed_data)

        body = {
            "accountId": str(self.async_client.get_account_id()),
            "coinId": params.coin_id,
            "amount": params.amount,
            "receiverAccountId": params.receiver_account_id,
            "clientTransferId": client_transfer_id,
            "transferReason": params.transfer_reason.value if hasattr(params.transfer_reason, 'value') else str(params.transfer_reason),
            "l2Nonce": l2_nonce,
            "l2ExpireTime": l2_expire_time,
            "l2Signature": l2_signature,
        }
        if params.extra_type is not None:
            body["extraType"] = params.extra_type
        if params.extra_data_json is not None:
            body["extraDataJson"] = params.extra_data_json

        return await self.async_client.make_authenticated_request(
            method="POST", path="/api/v2/private/transfer/createTransferOut", data=body)

    async def get_transfer_out_page(self, params: GetTransferOutPageParams) -> Dict[str, Any]:
        query_params = {"accountId": str(self.async_client.get_account_id())}
        if params.size:
            query_params["size"] = params.size
        if params.offset_data:
            query_params["offsetData"] = params.offset_data
        if params.filter_coin_id_list:
            query_params["filterCoinIdList"] = ",".join(params.filter_coin_id_list)
        if params.filter_status_list:
            query_params["filterStatusList"] = ",".join(params.filter_status_list)
        if params.filter_start_created_time_inclusive > 0:
            query_params["filterStartCreatedTimeInclusive"] = str(params.filter_start_created_time_inclusive)
        if params.filter_end_created_time_exclusive > 0:
            query_params["filterEndCreatedTimeExclusive"] = str(params.filter_end_created_time_exclusive)
        return await self.async_client.make_authenticated_request(
            method="GET", path="/api/v2/private/transfer/getActiveTransferOut", params=query_params)

    async def get_transfer_in_page(self, params: GetTransferInPageParams) -> Dict[str, Any]:
        query_params = {"accountId": str(self.async_client.get_account_id())}
        if params.size:
            query_params["size"] = params.size
        if params.offset_data:
            query_params["offsetData"] = params.offset_data
        if params.filter_coin_id_list:
            query_params["filterCoinIdList"] = ",".join(params.filter_coin_id_list)
        if params.filter_status_list:
            query_params["filterStatusList"] = ",".join(params.filter_status_list)
        if params.filter_start_created_time_inclusive > 0:
            query_params["filterStartCreatedTimeInclusive"] = str(params.filter_start_created_time_inclusive)
        if params.filter_end_created_time_exclusive > 0:
            query_params["filterEndCreatedTimeExclusive"] = str(params.filter_end_created_time_exclusive)
        return await self.async_client.make_authenticated_request(
            method="GET", path="/api/v2/private/transfer/getActiveTransferIn", params=query_params)
