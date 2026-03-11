from typing import Dict, Any, List, Optional

from ..internal.async_client import AsyncClient


class GetPositionTransactionPageParams:
    def __init__(self, size: str = "", offset_data: str = "", filter_contract_id_list: List[str] = None,
                 filter_start_created_time_inclusive: int = 0, filter_end_created_time_exclusive: int = 0):
        self.size = size
        self.offset_data = offset_data
        self.filter_contract_id_list = filter_contract_id_list or []
        self.filter_start_created_time_inclusive = filter_start_created_time_inclusive
        self.filter_end_created_time_exclusive = filter_end_created_time_exclusive


class GetCollateralTransactionPageParams:
    def __init__(self, size: str = "", offset_data: str = "",
                 filter_start_created_time_inclusive: int = 0, filter_end_created_time_exclusive: int = 0):
        self.size = size
        self.offset_data = offset_data
        self.filter_start_created_time_inclusive = filter_start_created_time_inclusive
        self.filter_end_created_time_exclusive = filter_end_created_time_exclusive


class GetPositionOrdersParams:
    # term_count must be > 0, defaults to 1
    def __init__(self, contract_id: str, term_count: int = 1, page: int = 1, page_size: int = 20):
        self.contract_id = contract_id
        self.term_count = term_count
        self.page = page
        self.page_size = page_size


class Client:
    def __init__(self, async_client: AsyncClient):
        self.async_client = async_client

    async def get_account_asset(self) -> Dict[str, Any]:
        params = {"accountId": str(self.async_client.get_account_id())}
        return await self.async_client.make_authenticated_request(
            method="GET", path="/api/v2/private/account/getAccountAsset", params=params)

    async def get_account_positions(self) -> Dict[str, Any]:
        return await self.get_account_asset()

    async def get_account_by_id(self) -> Dict[str, Any]:
        params = {"accountId": str(self.async_client.get_account_id())}
        return await self.async_client.make_authenticated_request(
            method="GET", path="/api/v2/private/account/getAccountById", params=params)

    async def get_position_transaction_page(self, params: GetPositionTransactionPageParams) -> Dict[str, Any]:
        query_params = {"accountId": str(self.async_client.get_account_id())}
        if params.size:
            query_params["size"] = params.size
        if params.offset_data:
            query_params["offsetData"] = params.offset_data
        if params.filter_contract_id_list:
            query_params["filterContractIdList"] = ",".join(params.filter_contract_id_list)
        if params.filter_start_created_time_inclusive > 0:
            query_params["filterStartCreatedTimeInclusive"] = str(params.filter_start_created_time_inclusive)
        if params.filter_end_created_time_exclusive > 0:
            query_params["filterEndCreatedTimeExclusive"] = str(params.filter_end_created_time_exclusive)
        return await self.async_client.make_authenticated_request(
            method="GET", path="/api/v2/private/account/getPositionTransactionPage", params=query_params)

    async def get_collateral_transaction_page(self, params: GetCollateralTransactionPageParams) -> Dict[str, Any]:
        query_params = {"accountId": str(self.async_client.get_account_id())}
        if params.size:
            query_params["size"] = params.size
        if params.offset_data:
            query_params["offsetData"] = params.offset_data
        if params.filter_start_created_time_inclusive > 0:
            query_params["filterStartCreatedTimeInclusive"] = str(params.filter_start_created_time_inclusive)
        if params.filter_end_created_time_exclusive > 0:
            query_params["filterEndCreatedTimeExclusive"] = str(params.filter_end_created_time_exclusive)
        return await self.async_client.make_authenticated_request(
            method="GET", path="/api/v2/private/account/getCollateralTransactionPage", params=query_params)

    async def get_account_deleverage_light(self) -> Dict[str, Any]:
        params = {"accountId": str(self.async_client.get_account_id())}
        return await self.async_client.make_authenticated_request(
            method="GET", path="/api/v2/private/account/getAccountDeleverageLight", params=params)

    async def update_leverage_setting(self, contract_id: str, leverage: str) -> Dict[str, Any]:
        data = {
            "accountId": str(self.async_client.get_account_id()),
            "contractId": contract_id,
            "leverage": leverage,
        }
        return await self.async_client.make_authenticated_request(
            method="POST", path="/api/v2/private/account/updateLeverageSetting", data=data)

    async def get_position_orders(self, params: GetPositionOrdersParams) -> Dict[str, Any]:
        query_params = {
            "accountId": str(self.async_client.get_account_id()),
            "contractId": params.contract_id,
            "termCount": str(params.term_count),
            "page": str(params.page),
            "pageSize": str(params.page_size),
        }
        return await self.async_client.make_authenticated_request(
            method="GET", path="/api/v2/private/account/getPositionOrders", params=query_params)
