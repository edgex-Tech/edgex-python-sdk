from typing import Dict, Any, List
from enum import Enum

from ..internal.async_client import AsyncClient


class KlineType(Enum):
    """K-line type enumeration."""
    UNKNOWN_KLINE_TYPE = 0
    MINUTE_1 = 1
    MINUTE_5 = 2
    MINUTE_15 = 3
    MINUTE_30 = 4
    HOUR_1 = 11
    HOUR_2 = 12
    HOUR_4 = 13
    HOUR_6 = 14
    HOUR_8 = 15
    HOUR_12 = 16
    DAY_1 = 21
    WEEK_1 = 31
    MONTH_1 = 41


class PriceType(Enum):
    """Price type enumeration."""
    UNKNOWN_PRICE_TYPE = 0
    ORACLE_PRICE = 1
    INDEX_PRICE = 2
    LAST_PRICE = 3
    ASK1_PRICE = 4
    BID1_PRICE = 5
    OPEN_INTEREST = 6


class GetKLineParams:
    """Parameters for getting K-line data."""

    def __init__(
        self,
        contract_id: str,
        kline_type: KlineType,
        price_type: PriceType = PriceType.LAST_PRICE,
        size: int = 100,
        offset_data: str = "",
        filter_begin_kline_time_inclusive: str = "",
        filter_end_kline_time_exclusive: str = ""
    ):
        """
        Initialize K-line parameters.

        Args:
            contract_id: Contract ID (string)
            kline_type: K-line type (KlineType enum)
            price_type: Price type (PriceType enum, defaults to LAST_PRICE)
            size: Number of records to fetch (int, defaults to 100)
            offset_data: Pagination offset data (string)
            filter_begin_kline_time_inclusive: Start time filter (string timestamp)
            filter_end_kline_time_exclusive: End time filter (string timestamp)
        """
        self.contract_id = contract_id
        self.kline_type = kline_type
        self.price_type = price_type
        self.size = size
        self.offset_data = offset_data
        self.filter_begin_kline_time_inclusive = filter_begin_kline_time_inclusive
        self.filter_end_kline_time_exclusive = filter_end_kline_time_exclusive




class GetOrderBookDepthParams:
    """Parameters for getting order book depth."""

    def __init__(
        self,
        contract_id: str,
        limit: int = 50
    ):
        self.contract_id = contract_id
        self.limit = limit


class GetMultiContractKLineParams:
    """Parameters for getting K-line data for multiple contracts."""

    def __init__(
        self,
        contract_id_list: List[str],
        interval: str,
        limit: int = 1
    ):
        self.contract_id_list = contract_id_list
        self.interval = interval
        self.limit = limit


class Client:
    """Client for quote-related API endpoints."""

    def __init__(self, async_client: AsyncClient):
        """
        Initialize the quote client.

        Args:
            async_client: The async client for common functionality
        """
        self.async_client = async_client

    async def get_quote_summary(self, contract_id: str) -> Dict[str, Any]:
        """
        Get the quote summary for a given contract.

        Args:
            contract_id: The contract ID

        Returns:
            Dict[str, Any]: The quote summary

        Raises:
            ValueError: If the request fails
        """
        # Public endpoint - use simple GET request
        await self.async_client._ensure_session()

        url = f"{self.async_client.base_url}/api/v1/public/quote/getTicketSummary"
        params = {
            "contractId": contract_id
        }

        try:
            async with self.async_client.session.get(url, params=params) as response:
                if response.status != 200:
                    try:
                        error_detail = await response.json()
                        raise ValueError(f"request failed with status code: {response.status}, response: {error_detail}")
                    except:
                        text = await response.text()
                        raise ValueError(f"request failed with status code: {response.status}, response: {text}")

                resp_data = await response.json()

                if resp_data.get("code") != "SUCCESS":
                    error_param = resp_data.get("errorParam")
                    if error_param:
                        raise ValueError(f"request failed with error params: {error_param}")
                    raise ValueError(f"request failed with code: {resp_data.get('code')}")

                return resp_data

        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"request failed: {str(e)}")

    async def get_24_hour_quote(self, contract_id: str) -> Dict[str, Any]:
        """
        Get the 24-hour quotes for a given contract.

        Args:
            contract_id: The contract ID

        Returns:
            Dict[str, Any]: The 24-hour quotes

        Raises:
            ValueError: If the request fails
        """
        # Public endpoint - use simple GET request
        await self.async_client._ensure_session()

        url = f"{self.async_client.base_url}/api/v1/public/quote/getTicker"
        params = {
            "contractId": contract_id
        }

        try:
            async with self.async_client.session.get(url, params=params) as response:
                if response.status != 200:
                    try:
                        error_detail = await response.json()
                        raise ValueError(f"request failed with status code: {response.status}, response: {error_detail}")
                    except:
                        text = await response.text()
                        raise ValueError(f"request failed with status code: {response.status}, response: {text}")

                resp_data = await response.json()

                if resp_data.get("code") != "SUCCESS":
                    error_param = resp_data.get("errorParam")
                    if error_param:
                        raise ValueError(f"request failed with error params: {error_param}")
                    raise ValueError(f"request failed with code: {resp_data.get('code')}")

                return resp_data

        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"request failed: {str(e)}")

    async def get_k_line(self, params: GetKLineParams) -> Dict[str, Any]:
        """
        Get the K-line data for a contract.

        Args:
            params: K-line query parameters

        Returns:
            Dict[str, Any]: The K-line data

        Raises:
            ValueError: If the request fails
        """
        url = f"{self.async_client.base_url}/api/v1/public/quote/getKline"
        query_params = {
            "contractId": params.contract_id,
            "klineType": params.kline_type.name,
            "priceType": params.price_type.name,
            "size": str(params.size)
        }

        # Add optional parameters
        if params.offset_data:
            query_params["offsetData"] = params.offset_data
        if params.filter_begin_kline_time_inclusive:
            query_params["filterBeginKlineTimeInclusive"] = params.filter_begin_kline_time_inclusive
        if params.filter_end_kline_time_exclusive:
            query_params["filterEndKlineTimeExclusive"] = params.filter_end_kline_time_exclusive

        print(query_params)

        # Public endpoint - use simple GET request
        await self.async_client._ensure_session()

        try:
            async with self.async_client.session.get(url, params=query_params) as response:
                if response.status != 200:
                    try:
                        error_detail = await response.json()
                        raise ValueError(f"request failed with status code: {response.status}, response: {error_detail}")
                    except:
                        text = await response.text()
                        raise ValueError(f"request failed with status code: {response.status}, response: {text}")

                resp_data = await response.json()

                if resp_data.get("code") != "SUCCESS":
                    error_param = resp_data.get("errorParam")
                    if error_param:
                        raise ValueError(f"request failed with error params: {error_param}")
                    raise ValueError(f"request failed with code: {resp_data.get('code')}")

                return resp_data

        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"request failed: {str(e)}")

    async def get_order_book_depth(self, params: GetOrderBookDepthParams) -> Dict[str, Any]:
        """
        Get the order book depth for a contract.

        Args:
            params: Order book depth query parameters

        Returns:
            Dict[str, Any]: The order book depth

        Raises:
            ValueError: If the request fails
        """
        url = f"{self.async_client.base_url}/api/v1/public/quote/getDepth"
        query_params = {
            "contractId": params.contract_id,
            "level": str(params.limit)  # The API expects 'level', not 'limit'
        }

        # Public endpoint - use simple GET request
        await self.async_client._ensure_session()

        url = f"{self.async_client.base_url}/api/v1/public/quote/getDepth"

        try:
            async with self.async_client.session.get(url, params=query_params) as response:
                if response.status != 200:
                    try:
                        error_detail = await response.json()
                        raise ValueError(f"request failed with status code: {response.status}, response: {error_detail}")
                    except:
                        text = await response.text()
                        raise ValueError(f"request failed with status code: {response.status}, response: {text}")

                resp_data = await response.json()

                if resp_data.get("code") != "SUCCESS":
                    error_param = resp_data.get("errorParam")
                    if error_param:
                        raise ValueError(f"request failed with error params: {error_param}")
                    raise ValueError(f"request failed with code: {resp_data.get('code')}")

                return resp_data

        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"request failed: {str(e)}")

    async def get_multi_contract_k_line(self, params: GetMultiContractKLineParams) -> Dict[str, Any]:
        """
        Get the K-line data for multiple contracts.

        Args:
            params: Multi-contract K-line query parameters

        Returns:
            Dict[str, Any]: The K-line data for multiple contracts

        Raises:
            ValueError: If the request fails
        """
        # Public endpoint - use simple GET request
        await self.async_client._ensure_session()

        url = f"{self.async_client.base_url}/api/v1/public/quote/getMultiContractKline"
        query_params = {
            "contractIdList": ",".join(params.contract_id_list),
            "interval": params.interval,
            "limit": str(params.limit)
        }

        try:
            async with self.async_client.session.get(url, params=query_params) as response:
                if response.status != 200:
                    try:
                        error_detail = await response.json()
                        raise ValueError(f"request failed with status code: {response.status}, response: {error_detail}")
                    except:
                        text = await response.text()
                        raise ValueError(f"request failed with status code: {response.status}, response: {text}")

                resp_data = await response.json()

                if resp_data.get("code") != "SUCCESS":
                    error_param = resp_data.get("errorParam")
                    if error_param:
                        raise ValueError(f"request failed with error params: {error_param}")
                    raise ValueError(f"request failed with code: {resp_data.get('code')}")

                return resp_data

        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"request failed: {str(e)}")
