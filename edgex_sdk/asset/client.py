from typing import Dict, Any, List

import time
from ..internal.async_client import AsyncClient


class GetAssetOrdersParams:
    """Parameters for getting asset orders."""

    def __init__(self, size: str = "10", offset_data: str = "", filter_coin_id_list: List[str] = None,
                 filter_start_created_time_inclusive: int = 0, filter_end_created_time_exclusive: int = 0):
        self.size = size
        self.offset_data = offset_data
        self.filter_coin_id_list = filter_coin_id_list or []
        self.filter_start_created_time_inclusive = filter_start_created_time_inclusive
        self.filter_end_created_time_exclusive = filter_end_created_time_exclusive


class CreateWithdrawalParams:
    """Parameters for creating a withdrawal."""

    def __init__(self, coin_id: str, amount: str, eth_address: str, tag: str = ""):
        self.coin_id = coin_id
        self.amount = amount
        self.eth_address = eth_address
        self.tag = tag


class GetWithdrawalRecordsParams:
    """Parameters for getting withdrawal records."""

    def __init__(self, size: str = "10", offset_data: str = "", filter_coin_id_list: List[str] = None,
                 filter_status_list: List[str] = None, filter_start_created_time_inclusive: int = 0,
                 filter_end_created_time_exclusive: int = 0):
        self.size = size
        self.offset_data = offset_data
        self.filter_coin_id_list = filter_coin_id_list or []
        self.filter_status_list = filter_status_list or []
        self.filter_start_created_time_inclusive = filter_start_created_time_inclusive
        self.filter_end_created_time_exclusive = filter_end_created_time_exclusive


class Client:
    """Client for asset-related API endpoints."""

    def __init__(self, async_client: AsyncClient):
        """
        Initialize the asset client.

        Args:
            async_client: The async client for common functionality
        """
        self.async_client = async_client

    async def get_account_asset(self) -> Dict[str, Any]:
        """
        Get the account asset information.
        Note: This method delegates to the account client since it's an account endpoint.

        Returns:
            Dict[str, Any]: The account asset information

        Raises:
            ValueError: If the request fails
        """
        # This is actually an account endpoint, not an asset endpoint
        # We should delegate to the account client
        raise NotImplementedError("This method should be called from the account client: client.account.get_account_asset()")

    async def get_asset_orders(
        self,
        params: GetAssetOrdersParams
    ) -> Dict[str, Any]:
        """
        Get asset orders with pagination.

        Args:
            params: Parameters for the request

        Returns:
            Dict[str, Any]: The asset orders

        Raises:
            ValueError: If the request fails
        """
        query_params = {
            "accountId": str(self.async_client.get_account_id())
        }

        # Add pagination parameters
        if params.size:
            query_params["size"] = params.size
        if params.offset_data:
            query_params["offsetData"] = params.offset_data

        # Add filter parameters
        if params.filter_coin_id_list:
            query_params["filterCoinIdList"] = ",".join(params.filter_coin_id_list)

        # Add time filters
        if params.filter_start_created_time_inclusive > 0:
            query_params["filterStartCreatedTimeInclusive"] = str(params.filter_start_created_time_inclusive)
        if params.filter_end_created_time_exclusive > 0:
            query_params["filterEndCreatedTimeExclusive"] = str(params.filter_end_created_time_exclusive)

        return await self.async_client.make_authenticated_request(
            method="GET",
            path="/api/v1/private/assets/getAllOrdersPage",
            params=query_params
        )

    async def get_coin_rates(self, chain_id: str = "1", coin: str = "0xdac17f958d2ee523a2206206994597c13d831ec7") -> Dict[str, Any]:
        """
        Get coin rates.

        Args:
            chain_id: Chain ID (default: "1" for Ethereum mainnet)
            coin: Coin contract address (default: USDT)

        Returns:
            Dict[str, Any]: The coin rates

        Raises:
            ValueError: If the request fails
        """
        params = {
            "chainId": chain_id,
            "coin": coin
        }

        return await self.async_client.make_authenticated_request(
            method="GET",
            path="/api/v1/private/assets/getCoinRate",
            params=params
        )

    async def create_withdrawal(self, param : CreateWithdrawalParams, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a withdrawal request.

        Args:
            coin_id: The coin ID
            amount: The withdrawal amount
            eth_address: The Ethereum address to withdraw to

        Returns:
            Dict[str, Any]: The withdrawal result

        Raises:
            ValueError: If the request fails
        """
        coin = None
        for coin_data in metadata['coinList']:
            if coin_data.get('coinId') == param.coin_id:
                coin = coin_data
                break

        if not coin:
            raise ValueError(f"coin not found: {param.coin_id}")

        position_id = str(self.async_client.get_account_id())
        client_id = self.async_client.get_random_client_id()
        nonce = self.async_client.calc_nonce(client_id)

        l2_expire_time = int(time.time() * 1000) + (14 * 24 * 60 * 60 * 1000)  # 14 days
        l2_expire_hour = l2_expire_time / (60 * 60 * 1000)
        expire_time_unix = str(int(l2_expire_hour))
        normalized_amount = str(int(float(param.amount) * 10 ** int(coin.get('decimal', 6))))

        sig_hash = self.async_client.calc_withdrawal_to_address_hash(
            coin.get('starkExAssetId', ''),
            position_id,
            param.eth_address,
            nonce,
            expire_time_unix,
            normalized_amount
        )

        # Sign the order
        sig = self.async_client.sign(sig_hash)

        # Convert signature to string (include v component like Go SDK, even though it's empty)
        sig_str = f"{sig.r}{sig.s}{sig.v if hasattr(sig, 'v') and sig.v else ''}"


        data = {
            "accountId": position_id,
            "coinId": param.coin_id,
            "amount": param.amount,
            "ethAddress": param.eth_address,
            "clientWithdrawId": client_id,
            "expireTime": str(l2_expire_time),
            "l2Signature": sig_str
        }

        return await self.async_client.make_authenticated_request(
            method="POST",
            path="/api/v1/private/assets/createNormalWithdraw",
            data=data
        )

    async def get_withdrawal_records(
        self,
        size: str = "",
        offset_data: str = "",
        filter_coin_id_list: List[str] = None,
        filter_status_list: List[str] = None,
        filter_start_created_time_inclusive: int = 0,
        filter_end_created_time_exclusive: int = 0
    ) -> Dict[str, Any]:
        """
        Get withdrawal records with pagination.

        Args:
            size: Size of the page
            offset_data: Offset data for pagination
            filter_coin_id_list: Filter by coin IDs
            filter_status_list: Filter by status
            filter_start_created_time_inclusive: Filter start time (inclusive)
            filter_end_created_time_exclusive: Filter end time (exclusive)

        Returns:
            Dict[str, Any]: The withdrawal records

        Raises:
            ValueError: If the request fails
        """
        query_params = {
            "accountId": str(self.async_client.get_account_id())
        }

        # Add pagination parameters
        if size:
            query_params["size"] = size
        if offset_data:
            query_params["offsetData"] = offset_data

        # Add filter parameters
        if filter_coin_id_list:
            query_params["filterCoinIdList"] = ",".join(filter_coin_id_list)
        if filter_status_list:
            query_params["filterStatusList"] = ",".join(filter_status_list)

        # Add time filters
        if filter_start_created_time_inclusive > 0:
            query_params["filterStartCreatedTimeInclusive"] = str(filter_start_created_time_inclusive)
        if filter_end_created_time_exclusive > 0:
            query_params["filterEndCreatedTimeExclusive"] = str(filter_end_created_time_exclusive)

        return await self.async_client.make_authenticated_request(
            method="GET",
            path="/api/v1/private/assets/getNormalWithdrawById",
            params=query_params
        )

    async def get_withdrawable_amount(self, address: str) -> Dict[str, Any]:
        """
        Get the withdrawable amount for a coin.

        Args:
            address: The coin contract address

        Returns:
            Dict[str, Any]: The withdrawable amount information

        Raises:
            ValueError: If the request fails
        """
        query_params = {
            "accountId": str(self.async_client.get_account_id()),
            "address": address
        }

        return await self.async_client.make_authenticated_request(
            method="GET",
            path="/api/v1/private/assets/getNormalWithdrawableAmount",
            params=query_params
        )

    async def get_withdrawal_records(self, params: GetWithdrawalRecordsParams) -> Dict[str, Any]:
        """
        Get withdrawal records with pagination.

        Args:
            params: Parameters for the request

        Returns:
            Dict[str, Any]: The withdrawal records

        Raises:
            ValueError: If the request fails
        """
        query_params = {
            "accountId": str(self.async_client.get_account_id())
        }

        # Add pagination parameters
        if params.size:
            query_params["size"] = params.size
        if params.offset_data:
            query_params["offsetData"] = params.offset_data

        # Add filter parameters
        if params.filter_coin_id_list:
            query_params["filterCoinIdList"] = ",".join(params.filter_coin_id_list)
        if params.filter_status_list:
            query_params["filterStatusList"] = ",".join(params.filter_status_list)

        # Add time filters
        if params.filter_start_created_time_inclusive > 0:
            query_params["filterStartCreatedTimeInclusive"] = str(params.filter_start_created_time_inclusive)
        if params.filter_end_created_time_exclusive > 0:
            query_params["filterEndCreatedTimeExclusive"] = str(params.filter_end_created_time_exclusive)

        return await self.async_client.make_authenticated_request(
            method="GET",
            path="/api/v1/private/assets/getNormalWithdrawById",
            params=query_params
        )
