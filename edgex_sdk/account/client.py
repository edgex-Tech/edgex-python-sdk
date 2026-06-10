import time
from typing import Dict, Any, List, Optional

from ..internal.async_client import AsyncClient
from ..internal.eip712 import EIP712_DOMAIN_TYPE, SET_MARGIN_MODE_PARAMS_TYPE, build_eip712_domain


class GetPositionTransactionPageParams:
    def __init__(self, size: str = "", offset_data: str = "", filter_coin_id_list: List[str] = None,
                 filter_contract_id_list: List[str] = None, filter_type_list: List[str] = None,
                 filter_start_created_time_inclusive: int = 0, filter_end_created_time_exclusive: int = 0,
                 filter_close_only: Optional[bool] = None, filter_open_only: Optional[bool] = None):
        self.size = size
        self.offset_data = offset_data
        self.filter_coin_id_list = filter_coin_id_list or []
        self.filter_contract_id_list = filter_contract_id_list or []
        self.filter_type_list = filter_type_list or []
        self.filter_start_created_time_inclusive = filter_start_created_time_inclusive
        self.filter_end_created_time_exclusive = filter_end_created_time_exclusive
        self.filter_close_only = filter_close_only
        self.filter_open_only = filter_open_only


class GetCollateralTransactionPageParams:
    def __init__(self, size: str = "", offset_data: str = "", filter_coin_id_list: List[str] = None,
                 filter_type_list: List[str] = None, filter_start_created_time_inclusive: int = 0,
                 filter_end_created_time_exclusive: int = 0):
        self.size = size
        self.offset_data = offset_data
        self.filter_coin_id_list = filter_coin_id_list or []
        self.filter_type_list = filter_type_list or []
        self.filter_start_created_time_inclusive = filter_start_created_time_inclusive
        self.filter_end_created_time_exclusive = filter_end_created_time_exclusive


class GetPositionOrdersParams:
    # term_count must be > 0, defaults to 1
    def __init__(self, contract_id: str, term_count: int = 1, page: int = 1, page_size: int = 20):
        self.contract_id = contract_id
        self.term_count = term_count
        self.page = page
        self.page_size = page_size


class GetPositionTermPageParams:
    def __init__(self, size: str = "", offset_data: str = "", filter_coin_id_list: List[str] = None,
                 filter_contract_id_list: List[str] = None, filter_is_long_position: Optional[bool] = None,
                 filter_start_created_time_inclusive: int = 0, filter_end_created_time_exclusive: int = 0):
        self.size = size
        self.offset_data = offset_data
        self.filter_coin_id_list = filter_coin_id_list or []
        self.filter_contract_id_list = filter_contract_id_list or []
        self.filter_is_long_position = filter_is_long_position
        self.filter_start_created_time_inclusive = filter_start_created_time_inclusive
        self.filter_end_created_time_exclusive = filter_end_created_time_exclusive


class GetAccountAssetSnapshotPageParams:
    def __init__(self, coin_id: str, size: str = "", offset_data: str = "", filter_time_tag: Optional[int] = None,
                 filter_start_time_inclusive: int = 0, filter_end_time_exclusive: int = 0):
        self.coin_id = coin_id
        self.size = size
        self.offset_data = offset_data
        self.filter_time_tag = filter_time_tag
        self.filter_start_time_inclusive = filter_start_time_inclusive
        self.filter_end_time_exclusive = filter_end_time_exclusive


class GetAccountPageParams:
    def __init__(self, size: str = "", offset_data: str = ""):
        self.size = size
        self.offset_data = offset_data


class SetMarginModeParams:
    def __init__(self, contract_id: str, margin_mode: str, client_order_id: str = ""):
        self.contract_id = contract_id
        self.margin_mode = margin_mode
        self.client_order_id = client_order_id


class Client:
    def __init__(self, async_client: AsyncClient):
        self.async_client = async_client

    @staticmethod
    def _calc_l2_expire_time_ms(now_seconds: float) -> str:
        now_ms = int(now_seconds * 1000)
        next_hour_ms = ((now_ms + 3_600_000 - 1) // 3_600_000) * 3_600_000
        expire_time_ms = next_hour_ms + 14 * 24 * 60 * 60 * 1000
        return str(expire_time_ms)

    async def get_account_asset(self) -> Dict[str, Any]:
        params = {"accountId": str(self.async_client.get_account_id())}
        return await self.async_client.make_authenticated_request(method="GET", path="/api/v2/private/account/getAccountAsset", params=params)

    async def get_account_positions(self) -> Dict[str, Any]:
        return await self.get_account_asset()

    async def get_account_by_id(self) -> Dict[str, Any]:
        params = {"accountId": str(self.async_client.get_account_id())}
        return await self.async_client.make_authenticated_request(method="GET", path="/api/v2/private/account/getAccountById", params=params)

    async def get_position_transaction_page(self, params: GetPositionTransactionPageParams) -> Dict[str, Any]:
        query_params = {"accountId": str(self.async_client.get_account_id())}
        if params.size:
            query_params["size"] = params.size
        if params.offset_data:
            query_params["offsetData"] = params.offset_data
        if params.filter_coin_id_list:
            query_params["filterCoinIdList"] = ",".join(params.filter_coin_id_list)
        if params.filter_contract_id_list:
            query_params["filterContractIdList"] = ",".join(params.filter_contract_id_list)
        if params.filter_type_list:
            query_params["filterTypeList"] = ",".join(params.filter_type_list)
        if params.filter_start_created_time_inclusive > 0:
            query_params["filterStartCreatedTimeInclusive"] = str(params.filter_start_created_time_inclusive)
        if params.filter_end_created_time_exclusive > 0:
            query_params["filterEndCreatedTimeExclusive"] = str(params.filter_end_created_time_exclusive)
        if params.filter_close_only is not None:
            query_params["filterCloseOnly"] = str(params.filter_close_only).lower()
        if params.filter_open_only is not None:
            query_params["filterOpenOnly"] = str(params.filter_open_only).lower()
        return await self.async_client.make_authenticated_request(method="GET", path="/api/v2/private/account/getPositionTransactionPage", params=query_params)

    async def get_collateral_transaction_page(self, params: GetCollateralTransactionPageParams) -> Dict[str, Any]:
        query_params = {"accountId": str(self.async_client.get_account_id())}
        if params.size:
            query_params["size"] = params.size
        if params.offset_data:
            query_params["offsetData"] = params.offset_data
        if params.filter_coin_id_list:
            query_params["filterCoinIdList"] = ",".join(params.filter_coin_id_list)
        if params.filter_type_list:
            query_params["filterTypeList"] = ",".join(params.filter_type_list)
        if params.filter_start_created_time_inclusive > 0:
            query_params["filterStartCreatedTimeInclusive"] = str(params.filter_start_created_time_inclusive)
        if params.filter_end_created_time_exclusive > 0:
            query_params["filterEndCreatedTimeExclusive"] = str(params.filter_end_created_time_exclusive)
        return await self.async_client.make_authenticated_request(method="GET", path="/api/v2/private/account/getCollateralTransactionPage", params=query_params)

    async def get_account_deleverage_light(self) -> Dict[str, Any]:
        params = {"accountId": str(self.async_client.get_account_id())}
        return await self.async_client.make_authenticated_request(method="GET", path="/api/v2/private/account/getAccountDeleverageLight", params=params)

    async def update_leverage_setting(self, contract_id: str, leverage: str) -> Dict[str, Any]:
        data = {
            "accountId": str(self.async_client.get_account_id()),
            "contractId": contract_id,
            "leverage": leverage,
        }
        return await self.async_client.make_authenticated_request(method="POST", path="/api/v2/private/account/updateLeverageSetting", data=data)

    async def set_margin_mode(self, params: SetMarginModeParams, metadata: Dict[str, Any]) -> Dict[str, Any]:
        if not self.async_client.trading_private_key:
            raise ValueError("trading private key is required for v2 EIP-712 margin mode signing")

        global_data = metadata.get("global", {})
        chain_id = (global_data.get("nativeChainId") or global_data.get("chainId") or "").strip()
        verifying_contract = (global_data.get("contractAddress") or "").strip()
        if not chain_id:
            raise ValueError("metadata.global.nativeChainId/chainId is required")
        if not verifying_contract:
            raise ValueError("metadata.global.contractAddress is required")

        client_order_id = params.client_order_id or self.async_client.get_random_client_id()
        l2_nonce = self.async_client.calc_nonce(client_order_id)
        trading_signer = self.async_client.resolve_trading_signer_address()
        l2_expire_time = self._calc_l2_expire_time_ms(time.time())
        domain = build_eip712_domain("EdgeX", "1", chain_id, verifying_contract)

        typed_data = {
            "types": {
                "EIP712Domain": EIP712_DOMAIN_TYPE,
                "SetMarginPreferenceParams": SET_MARGIN_MODE_PARAMS_TYPE,
            },
            "primaryType": "SetMarginPreferenceParams",
            "domain": domain,
            "message": {
                "accountId": str(self.async_client.get_account_id()),
                "assetId": params.contract_id,
                "marginMode": int(params.margin_mode),
                "nonce": str(l2_nonce),
                "signer": trading_signer,
            },
        }

        l2_signature = self.async_client.sign_typed_data_with_trading_key(typed_data)
        data = {
            "accountId": str(self.async_client.get_account_id()),
            "contractId": params.contract_id,
            "marginMode": params.margin_mode,
            "l2Nonce": str(l2_nonce),
            "l2ExpireTime": l2_expire_time,
            "signer": trading_signer,
            "l2Signature": l2_signature,
        }
        return await self.async_client.make_authenticated_request(method="POST", path="/api/v2/private/account/setMarginMode", data=data)

    async def get_position_orders(self, params: GetPositionOrdersParams) -> Dict[str, Any]:
        query_params = {
            "accountId": str(self.async_client.get_account_id()),
            "contractId": params.contract_id,
            "termCount": str(params.term_count),
            "page": str(params.page),
            "pageSize": str(params.page_size),
        }
        return await self.async_client.make_authenticated_request(method="GET", path="/api/v2/private/account/getPositionOrders", params=query_params)

    async def get_position_by_contract_id(self, contract_id_list: List[str]) -> Dict[str, Any]:
        query_params = {
            "accountId": str(self.async_client.get_account_id()),
            "contractIdList": ",".join(contract_id_list),
        }
        return await self.async_client.make_authenticated_request(method="GET", path="/api/v2/private/account/getPositionByContractId", params=query_params)

    async def get_position_term_page(self, params: GetPositionTermPageParams) -> Dict[str, Any]:
        query_params = {"accountId": str(self.async_client.get_account_id())}
        if params.size:
            query_params["size"] = params.size
        if params.offset_data:
            query_params["offsetData"] = params.offset_data
        if params.filter_coin_id_list:
            query_params["filterCoinIdList"] = ",".join(params.filter_coin_id_list)
        if params.filter_contract_id_list:
            query_params["filterContractIdList"] = ",".join(params.filter_contract_id_list)
        if params.filter_is_long_position is not None:
            query_params["filterIsLongPosition"] = str(params.filter_is_long_position).lower()
        if params.filter_start_created_time_inclusive > 0:
            query_params["filterStartCreatedTimeInclusive"] = str(params.filter_start_created_time_inclusive)
        if params.filter_end_created_time_exclusive > 0:
            query_params["filterEndCreatedTimeExclusive"] = str(params.filter_end_created_time_exclusive)
        return await self.async_client.make_authenticated_request(method="GET", path="/api/v2/private/account/getPositionTermPage", params=query_params)

    async def get_collateral_by_coin_id(self, coin_id_list: List[str] = None) -> Dict[str, Any]:
        query_params = {"accountId": str(self.async_client.get_account_id())}
        if coin_id_list:
            query_params["coinIdList"] = ",".join(coin_id_list)
        return await self.async_client.make_authenticated_request(method="GET", path="/api/v2/private/account/getCollateralByCoinId", params=query_params)

    async def get_account_asset_snapshot_page(self, params: GetAccountAssetSnapshotPageParams) -> Dict[str, Any]:
        query_params = {
            "accountId": str(self.async_client.get_account_id()),
            "coinId": params.coin_id,
        }
        if params.size:
            query_params["size"] = params.size
        if params.offset_data:
            query_params["offsetData"] = params.offset_data
        if params.filter_time_tag is not None:
            query_params["filterTimeTag"] = str(params.filter_time_tag)
        if params.filter_start_time_inclusive > 0:
            query_params["filterStartTimeInclusive"] = str(params.filter_start_time_inclusive)
        if params.filter_end_time_exclusive > 0:
            query_params["filterEndTimeExclusive"] = str(params.filter_end_time_exclusive)
        return await self.async_client.make_authenticated_request(method="GET", path="/api/v2/private/account/getAccountAssetSnapshotPage", params=query_params)

    async def get_position_transaction_by_id(self, transaction_id_list: List[str]) -> Dict[str, Any]:
        query_params = {
            "accountId": str(self.async_client.get_account_id()),
            "positionTransactionIdList": ",".join(transaction_id_list),
        }
        return await self.async_client.make_authenticated_request(method="GET", path="/api/v2/private/account/getPositionTransactionById", params=query_params)

    async def get_collateral_transaction_by_id(self, transaction_id_list: List[str]) -> Dict[str, Any]:
        query_params = {
            "accountId": str(self.async_client.get_account_id()),
            "collateralTransactionIdList": ",".join(transaction_id_list),
        }
        return await self.async_client.make_authenticated_request(method="GET", path="/api/v2/private/account/getCollateralTransactionById", params=query_params)

    async def get_account_page(self, params: GetAccountPageParams) -> Dict[str, Any]:
        query_params = {"accountId": str(self.async_client.get_account_id())}
        if params.size:
            query_params["size"] = params.size
        if params.offset_data:
            query_params["offsetData"] = params.offset_data
        return await self.async_client.make_authenticated_request(method="GET", path="/api/v2/private/account/getAccountPage", params=query_params)
