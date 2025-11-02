from typing import Dict, Any, List, Optional
from decimal import Decimal
import time
from datetime import datetime
from enum import Enum

from ..internal.async_client import AsyncClient


class TransferReason(Enum):
    """Transfer reason enumeration."""
    USER_TRANSFER = "USER_TRANSFER"
    FAST_WITHDRAW = "FAST_WITHDRAW"
    CROSS_DEPOSIT = "CROSS_DEPOSIT"
    CROSS_WITHDRAW = "CROSS_WITHDRAW"
    UNRECOGNIZED = "UNRECOGNIZED"


class GetTransferOutByIdParams:
    """Parameters for getting transfer out records by ID."""

    def __init__(self, transfer_id_list: List[str]):
        self.transfer_id_list = transfer_id_list


class GetTransferInByIdParams:
    """Parameters for getting transfer in records by ID."""

    def __init__(self, transfer_id_list: List[str]):
        self.transfer_id_list = transfer_id_list


class GetWithdrawAvailableAmountParams:
    """Parameters for getting available withdrawal amount."""

    def __init__(self, coin_id: str):
        self.coin_id = coin_id


class CreateTransferOutParams:
    """Parameters for creating a transfer out order."""

    def __init__(
        self,
        coin_id: str,
        amount: str,
        receiver_account_id: str,
        receiver_l2_key: str,
        transfer_reason: TransferReason = TransferReason.USER_TRANSFER,
        expire_time: Optional[datetime] = None,
        extra_type: Optional[str] = None,
        extra_data_json: Optional[str] = None
    ):
        self.coin_id = coin_id
        self.amount = amount
        self.receiver_account_id = receiver_account_id
        self.receiver_l2_key = receiver_l2_key

        # Validate and set transfer_reason
        if isinstance(transfer_reason, str):
            # Support backward compatibility by converting string to enum
            try:
                self.transfer_reason = TransferReason(transfer_reason)
            except ValueError:
                raise ValueError(f"Invalid transfer_reason: {transfer_reason}. Must be one of: {[e.value for e in TransferReason]}")
        elif isinstance(transfer_reason, TransferReason):
            self.transfer_reason = transfer_reason
        else:
            raise ValueError(f"transfer_reason must be a TransferReason enum or string, got {type(transfer_reason)}")

        self.expire_time = expire_time
        self.extra_type = extra_type
        self.extra_data_json = extra_data_json


class GetTransferOutPageParams:
    """Parameters for getting transfer out page."""

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
    """Parameters for getting transfer in page."""

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
    """Client for transfer-related API endpoints."""

    def __init__(self, async_client: AsyncClient):
        """
        Initialize the transfer client.

        Args:
            async_client: The async client for common functionality
        """
        self.async_client = async_client

    async def get_transfer_out_by_id(self, params: GetTransferOutByIdParams) -> Dict[str, Any]:
        """
        Get transfer out records by ID.

        Args:
            params: Transfer out query parameters

        Returns:
            Dict[str, Any]: The transfer out records

        Raises:
            ValueError: If the request fails
        """
        query_params = {
            "accountId": str(self.async_client.get_account_id()),
            "transferIdList": ",".join(params.transfer_id_list)
        }

        return await self.async_client.make_authenticated_request(
            method="GET",
            path="/api/v1/private/transfer/getTransferOutById",
            params=query_params
        )

    async def get_transfer_in_by_id(self, params: GetTransferInByIdParams) -> Dict[str, Any]:
        """
        Get transfer in records by ID.

        Args:
            params: Transfer in query parameters

        Returns:
            Dict[str, Any]: The transfer in records

        Raises:
            ValueError: If the request fails
        """
        query_params = {
            "accountId": str(self.async_client.get_account_id()),
            "transferIdList": ",".join(params.transfer_id_list)
        }

        return await self.async_client.make_authenticated_request(
            method="GET",
            path="/api/v1/private/transfer/getTransferInById",
            params=query_params
        )

    async def get_transferout_available_amount(self, coin_id: str) -> Dict[str, Any]:
        return await self.get_withdraw_available_amount(GetWithdrawAvailableAmountParams(coin_id=coin_id))

    async def get_withdraw_available_amount(self, params: GetWithdrawAvailableAmountParams) -> Dict[str, Any]:
        """
        Get the available withdrawal amount.

        Args:
            params: Withdrawal available amount query parameters

        Returns:
            Dict[str, Any]: The available withdrawal amount

        Raises:
            ValueError: If the request fails
        """
        query_params = {
            "accountId": str(self.async_client.get_account_id()),
            "coinId": params.coin_id
        }

        return await self.async_client.make_authenticated_request(
            method="GET",
            path="/api/v1/private/transfer/getTransferOutAvailableAmount",
            params=query_params
        )

    async def create_transfer_out(self, params: CreateTransferOutParams, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new transfer out order.

        Args:
            params: Transfer out parameters
            metadata: Exchange metadata containing coin information

        Returns:
            Dict[str, Any]: The created transfer out order

        Raises:
            ValueError: If the request fails or required metadata is missing
        """
        # Get collateral coin from metadata (following Golang logic)
        if not metadata or not metadata.get('global') or not metadata['global'].get('starkExCollateralCoin'):
            raise ValueError("metadata global is nil")

        coin = metadata['global']['starkExCollateralCoin']
        asset_id = self.async_client.hex_to_big_integer(coin['starkExAssetId'])

        # Print coin ID for debugging (matching Golang)
        print(coin['coinId'])

        # Generate client transfer ID if not provided
        client_transfer_id = self.async_client.get_random_client_id()

        # Parse decimal amount
        try:
            amount_dm = Decimal(params.amount)
        except Exception as e:
            raise ValueError(f"failed to parse amount: {e}")

        # Calculate nonce and expiration time (following Golang logic)
        nonce = self.async_client.calc_nonce(client_transfer_id)

        # Add 14 days to the provided expire_time (matching Golang logic)
        if params.expire_time:
            expire_time_plus_14_days = params.expire_time.timestamp() + (14 * 24 * 60 * 60)
            l2_expire_time = int(expire_time_plus_14_days * 1000)  # Convert to milliseconds
        else:
            l2_expire_time = int((time.time() + 14 * 24 * 60 * 60) * 1000)  # 14 days from now in milliseconds
        l2_expire_hour = l2_expire_time // (60 * 60 * 1000)

        # Remove 0x prefix from receiver L2 key if present
        receiver_l2_key = params.receiver_l2_key
        if receiver_l2_key.startswith('0x'):
            receiver_l2_key = receiver_l2_key[2:]

        # Convert receiver L2 key to big.Int
        try:
            receiver_public_key = int(receiver_l2_key, 16)
        except ValueError:
            raise ValueError(f"invalid receiver L2 key format: {params.receiver_l2_key}")

        # Parse receiver account ID
        try:
            receiver_position_id = int(params.receiver_account_id)
        except ValueError as e:
            raise ValueError(f"invalid receiver account ID: {e}")

        # Get position IDs
        sender_position_id = self.async_client.get_account_id()
        fee_position_id = sender_position_id  # Fee position is same as sender

        # Calculate max amount fee
        # 0 for internal transfer
        max_amount_fee = 0

        # Convert amount to protocol format (shift by 6 decimal places)
        shift_factor = Decimal('1000000')
        amount = int(amount_dm * shift_factor)

        # Calculate transfer hash and sign it (following Golang logic)
        msg_hash = self.async_client.calc_transfer_hash(
            asset_id,
            0,  # Use 0 as second asset ID (matching Golang: big.NewInt(0))
            receiver_public_key,
            sender_position_id,
            receiver_position_id,
            fee_position_id,
            nonce,
            amount,
            max_amount_fee,
            l2_expire_hour
        )
        signature = self.async_client.sign(msg_hash)

        # Build request body (following Golang logic)
        data = {
            "accountId": str(self.async_client.get_account_id()),
            "coinId": params.coin_id,
            "amount": params.amount,
            "receiverAccountId": params.receiver_account_id,
            "receiverL2Key": params.receiver_l2_key,
            "clientTransferId": client_transfer_id,
            "transferReason": params.transfer_reason.value,  # Use enum value
            "l2Nonce": str(nonce),
            "l2ExpireTime": str(l2_expire_time),
            "l2Signature": f"{signature.r}{signature.s}"
        }

        # Add optional fields if provided
        if params.extra_type is not None:
            data["extraType"] = params.extra_type
        if params.extra_data_json is not None:
            data["extraDataJson"] = params.extra_data_json

        # Make the request and get response
        response = await self.async_client.make_authenticated_request(
            method="POST",
            path="/api/v1/private/transfer/createTransferOut",
            data=data
        )

        # Check response code (matching Golang error handling)
        if response.get("code") != "SUCCESS":
            raise ValueError(f"request failed with code: {response.get('code')}")

        return response

    async def get_transfer_out_page(
        self,
        params: GetTransferOutPageParams
    ) -> Dict[str, Any]:
        """
        Get transfer out records with pagination.

        Args:
            params: Parameters for the request

        Returns:
            Dict[str, Any]: The transfer out records

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
            path="/api/v1/private/transfer/getActiveTransferOut",
            params=query_params
        )

    async def get_transfer_in_page(
        self,
        params: GetTransferInPageParams
    ) -> Dict[str, Any]:
        """
        Get transfer in records with pagination.

        Args:
            params: Parameters for the request

        Returns:
            Dict[str, Any]: The transfer in records

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
            path="/api/v1/private/transfer/getActiveTransferIn",
            params=query_params
        )
