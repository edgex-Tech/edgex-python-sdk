from typing import Dict, Any, List
from enum import Enum

from ..internal.async_client import AsyncClient


class KlineType(Enum):
    MINUTE_1 = "MINUTE_1"
    MINUTE_5 = "MINUTE_5"
    MINUTE_15 = "MINUTE_15"
    MINUTE_30 = "MINUTE_30"
    HOUR_1 = "HOUR_1"
    HOUR_2 = "HOUR_2"
    HOUR_4 = "HOUR_4"
    HOUR_6 = "HOUR_6"
    HOUR_8 = "HOUR_8"
    HOUR_12 = "HOUR_12"
    DAY_1 = "DAY_1"
    WEEK_1 = "WEEK_1"
    MONTH_1 = "MONTH_1"


class PriceType(Enum):
    ORACLE_PRICE = "ORACLE_PRICE"
    INDEX_PRICE = "INDEX_PRICE"
    LAST_PRICE = "LAST_PRICE"
    ASK1_PRICE = "ASK1_PRICE"
    BID1_PRICE = "BID1_PRICE"
    OPEN_INTEREST = "OPEN_INTEREST"


class GetKLineParams:
    def __init__(self, contract_id: str, kline_type: KlineType, price_type: PriceType = PriceType.LAST_PRICE,
                 size: int = 100, offset_data: str = "", filter_begin_kline_time_inclusive: str = "",
                 filter_end_kline_time_exclusive: str = ""):
        self.contract_id = contract_id
        self.kline_type = kline_type
        self.price_type = price_type
        self.size = size
        self.offset_data = offset_data
        self.filter_begin_kline_time_inclusive = filter_begin_kline_time_inclusive
        self.filter_end_kline_time_exclusive = filter_end_kline_time_exclusive


class GetOrderBookDepthParams:
    def __init__(self, contract_id: str, limit: int = 50):
        self.contract_id = contract_id
        self.limit = limit


class GetMultiContractKLineParams:
    def __init__(self, contract_id_list: List[str], kline_type: str, size: int = 1):
        self.contract_id_list = contract_id_list
        self.kline_type = kline_type
        self.size = size


class Client:
    def __init__(self, async_client: AsyncClient):
        self.async_client = async_client

    async def get_quote_summary(self, period: str = "LAST_DAY_1") -> Dict[str, Any]:
        return await self.async_client.make_public_request(
            method="GET", path="/api/v2/public/quote/getTicketSummary",
            params={"period": period})

    async def get_24_hour_quote(self, contract_id: str) -> Dict[str, Any]:
        return await self.async_client.make_public_request(
            method="GET", path="/api/v2/public/quote/getTicker",
            params={"contractId": contract_id})

    async def get_k_line(self, params: GetKLineParams) -> Dict[str, Any]:
        query_params = {
            "contractId": params.contract_id,
            "klineType": params.kline_type.value,
            "priceType": params.price_type.value,
            "size": str(params.size),
        }
        if params.offset_data:
            query_params["offsetData"] = params.offset_data
        if params.filter_begin_kline_time_inclusive:
            query_params["filterBeginKlineTimeInclusive"] = params.filter_begin_kline_time_inclusive
        if params.filter_end_kline_time_exclusive:
            query_params["filterEndKlineTimeExclusive"] = params.filter_end_kline_time_exclusive
        return await self.async_client.make_public_request(
            method="GET", path="/api/v2/public/quote/getKline", params=query_params)

    async def get_order_book_depth(self, params: GetOrderBookDepthParams) -> Dict[str, Any]:
        # level only accepts 15 or 200
        return await self.async_client.make_public_request(
            method="GET", path="/api/v2/public/quote/getDepth",
            params={"contractId": params.contract_id, "level": str(params.limit)})

    async def get_multi_contract_k_line(self, params: GetMultiContractKLineParams) -> Dict[str, Any]:
        return await self.async_client.make_public_request(
            method="GET", path="/api/v2/public/quote/getMultiContractKline",
            params={
                "contractIdList": ",".join(params.contract_id_list),
                "klineType": params.kline_type,
                "size": str(params.size),
            })
