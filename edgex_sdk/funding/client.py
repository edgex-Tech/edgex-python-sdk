from typing import Dict, Any, List

from ..internal.async_client import AsyncClient


class Client:
    def __init__(self, async_client: AsyncClient):
        self.async_client = async_client

    async def get_funding_rate_page(
        self,
        size: str = "",
        offset_data: str = "",
        contract_id: str = "",
        filter_settlement_funding_rate: bool = False,
        filter_begin_time_inclusive: int = 0,
        filter_end_time_exclusive: int = 0,
    ) -> Dict[str, Any]:
        query_params = {}
        if size:
            query_params["size"] = size
        if offset_data:
            query_params["offsetData"] = offset_data
        if contract_id:
            query_params["contractId"] = contract_id
        if filter_settlement_funding_rate:
            query_params["filterSettlementFundingRate"] = "true"
        if filter_begin_time_inclusive > 0:
            query_params["filterBeginTimeInclusive"] = str(filter_begin_time_inclusive)
        if filter_end_time_exclusive > 0:
            query_params["filterEndTimeExclusive"] = str(filter_end_time_exclusive)
        return await self.async_client.make_public_request(
            method="GET", path="/api/v2/public/funding/getFundingRatePage", params=query_params)

    async def get_latest_funding_rate(self, contract_ids: List[str] = None) -> Dict[str, Any]:
        query_params = {}
        if contract_ids:
            query_params["contractId"] = ",".join(contract_ids)
        return await self.async_client.make_public_request(
            method="GET", path="/api/v2/public/funding/getLatestFundingRate", params=query_params)
