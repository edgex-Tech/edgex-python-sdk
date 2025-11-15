import time
from decimal import Decimal
from typing import Dict, Any, List

from ..internal.async_client import AsyncClient
from .types import (
    CreateOrderParams,
    CancelOrderParams,
    GetActiveOrderParams,
    GetHistoryOrderParams,
    OrderFillTransactionParams,
    TimeInForce,
    OrderType,
    OrderSide
)


class Client:
    """Client for order-related API endpoints."""

    def __init__(self, async_client: AsyncClient):
        """
        Initialize the order client.

        Args:
            async_client: The async client for common functionality
        """
        self.async_client = async_client

    async def create_order(self, params: CreateOrderParams, metadata: Dict[str, Any], l2_price: Decimal) -> Dict[str, Any]:
        """
        Create a new order with the given parameters.

        Args:
            params: Order parameters
            metadata: Exchange metadata

        Returns:
            Dict[str, Any]: The created order

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        if not params.time_in_force:
            if params.type == OrderType.MARKET:
                params.time_in_force = TimeInForce.IMMEDIATE_OR_CANCEL.value
            elif params.type == OrderType.LIMIT:
                params.time_in_force = TimeInForce.GOOD_TIL_CANCEL.value

        contract = None
        contract_list = metadata.get("contractList")
        if contract_list is not None:
            for c in contract_list:
                if c.get("contractId") == params.contract_id:
                    contract = c
                    break

        if contract is None:
            raise ValueError(f"contract not found: {params.contract_id}")

        quote_coin = None
        coin_list = metadata.get("coinList")
        if coin_list is not None:
            quote_coin_id = contract.get("quoteCoinId")
            for coin in coin_list:
                if coin.get("coinId") == quote_coin_id:
                    quote_coin = coin
                    break

        if quote_coin is None:
            raise ValueError(f"coin not found: {contract.get('quoteCoinId')}")

        print(f"contract: {contract}")

        try:
            synthetic_factor_big = self.async_client.hex_to_big_integer(contract.get("starkExResolution", "0x0"))
            synthetic_factor = Decimal(synthetic_factor_big)
        except (ValueError, TypeError) as e:
            raise ValueError(f"failed to parse synthetic factor: {e}")

        try:
            shift_factor_big = self.async_client.hex_to_big_integer(quote_coin.get("starkExResolution", "0x0"))
            shift_factor = Decimal(shift_factor_big)
        except (ValueError, TypeError) as e:
            raise ValueError(f"failed to parse shift factor: {e}")

        try:
            size = Decimal(params.size)
        except (ValueError, TypeError) as e:
            raise ValueError(f"failed to parse size: {e}")

        value_dm = l2_price * size

        amount_synthetic = int(size * synthetic_factor)
        amount_collateral = int(value_dm * shift_factor)

        fee_rate = Decimal("0.00038")  # Default fee rate
        default_taker_fee_rate = contract.get("defaultTakerFeeRate")
        if default_taker_fee_rate:
            try:
                fee_rate = Decimal(default_taker_fee_rate)
            except (ValueError, TypeError) as e:
                raise ValueError(f"failed to parse fee rate: {e}")

        limit_fee = (size * l2_price * fee_rate).quantize(Decimal('1'), rounding='ROUND_CEILING')
        max_amount_fee = limit_fee * shift_factor

        client_order_id = params.client_order_id or self.async_client.get_random_client_id()

        nonce = self.async_client.calc_nonce(client_order_id)

        expire_time = int(time.time() * 1000) + (24 * 60 * 60 * 1000)  
        if params.expire_time:
            expire_time = params.l2_expire_time
        l2_expire_time = expire_time + (9 * 24 * 60 * 60 * 1000)  

        l2_expire_hour = l2_expire_time // (60 * 60 * 1000)

        msg_hash = self.async_client.calc_limit_order_hash(
            contract.get("starkExSyntheticAssetId", ""),
            quote_coin.get("starkExAssetId", ""),
            quote_coin.get("starkExAssetId", ""),
            params.side == OrderSide.BUY,
            amount_synthetic,
            amount_collateral,
            int(max_amount_fee),
            nonce,
            self.async_client.get_account_id(),
            l2_expire_hour
        )

        try:
            signature = self.async_client.sign(msg_hash)
        except Exception as e:
            raise ValueError(f"failed to sign withdrawal hash: {e}")

        sig_str = f"{signature.r}{signature.s}"
        print(f"sig_str: {sig_str}")

        body = {
            "accountId": str(self.async_client.get_account_id()),
            "contractId": params.contract_id,
            "price": params.price,
            "size": params.size,
            "type": params.type.value,
            "side": params.side.value,
            "timeInForce": params.time_in_force,
            "clientOrderId": client_order_id,
            "expireTime": str(expire_time),
            "l2Nonce": str(nonce),
            "l2Signature": sig_str,
            "l2ExpireTime": str(l2_expire_time),
            "l2Value": str(value_dm),
            "l2Size": params.size,
            "l2LimitFee": str(limit_fee),
            "reduceOnly": params.reduce_only
        }

        try:
            result = await self.async_client.make_authenticated_request(
                method="POST",
                path="/api/v1/private/order/createOrder",
                data=body
            )

            # Check if the request was successful
            if result.get("code") != "SUCCESS":
                raise ValueError(f"request failed with code: {result.get('code')}")

            return result

        except Exception as e:
            raise ValueError(f"failed to create order: {e}")

    async def cancel_order(self, params: CancelOrderParams) -> Dict[str, Any]:
        """
        Cancel a specific order.

        Args:
            params: Cancel order parameters

        Returns:
            Dict[str, Any]: The cancellation result

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        account_id = str(self.async_client.get_account_id())

        if params.order_id:
            path = "/api/v1/private/order/cancelOrderById"
            request_data = {
                "accountId": account_id,
                "orderIdList": [params.order_id]
            }
        elif params.client_order_id:
            path = "/api/v1/private/order/cancelOrderByClientOrderId"
            request_data = {
                "accountId": account_id,
                "clientOrderIdList": [params.client_order_id]
            }
        elif params.contract_id:
            path = "/api/v1/private/order/cancelAllOrder"
            request_data = {
                "accountId": account_id,
                "filterContractIdList": [params.contract_id]
            }
        else:
            raise ValueError("must provide either order_id, client_id, or contract_id")

        # Execute request using async client
        return await self.async_client.make_authenticated_request(
            method="POST",
            path=path,
            data=request_data
        )

    async def get_active_orders(self, params: GetActiveOrderParams) -> Dict[str, Any]:
        """
        Get active orders with pagination and filters.

        Args:
            params: Active order query parameters

        Returns:
            Dict[str, Any]: The active orders

        Raises:
            ValueError: If the request fails
        """
        # Build query parameters
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
        if params.filter_contract_id_list:
            query_params["filterContractIdList"] = ",".join(params.filter_contract_id_list)
        if params.filter_type_list:
            query_params["filterTypeList"] = ",".join(params.filter_type_list)
        if params.filter_status_list:
            query_params["filterStatusList"] = ",".join(params.filter_status_list)

        # Add boolean filters
        if params.filter_is_liquidate is not None:
            query_params["filterIsLiquidateList"] = str(params.filter_is_liquidate).lower()
        if params.filter_is_deleverage is not None:
            query_params["filterIsDeleverageList"] = str(params.filter_is_deleverage).lower()
        if params.filter_is_position_tpsl is not None:
            query_params["filterIsPositionTpslList"] = str(params.filter_is_position_tpsl).lower()

        # Add time filters
        if params.filter_start_created_time_inclusive > 0:
            query_params["filterStartCreatedTimeInclusive"] = str(params.filter_start_created_time_inclusive)
        if params.filter_end_created_time_exclusive > 0:
            query_params["filterEndCreatedTimeExclusive"] = str(params.filter_end_created_time_exclusive)

        # Execute request using async client
        return await self.async_client.make_authenticated_request(
            method="GET",
            path="/api/v1/private/order/getActiveOrderPage",
            params=query_params
        )

    async def get_history_orders(self, params: GetHistoryOrderParams) -> Dict[str, Any]:
        """
        Get historical orders with pagination and filters.

        Args:
            params: History order query parameters

        Returns:
            Dict[str, Any]: The historical orders

        Raises:
            ValueError: If the request fails
        """
        # Build query parameters
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
        if params.filter_contract_id_list:
            query_params["filterContractIdList"] = ",".join(params.filter_contract_id_list)
        if params.filter_type_list:
            query_params["filterTypeList"] = ",".join(params.filter_type_list)
        if params.filter_status_list:
            query_params["filterStatusList"] = ",".join(params.filter_status_list)

        # Add boolean filters
        if params.filter_is_liquidate is not None:
            query_params["filterIsLiquidateList"] = str(params.filter_is_liquidate).lower()
        if params.filter_is_deleverage is not None:
            query_params["filterIsDeleverageList"] = str(params.filter_is_deleverage).lower()
        if params.filter_is_position_tpsl is not None:
            query_params["filterIsPositionTpslList"] = str(params.filter_is_position_tpsl).lower()

        # Add time filters
        if params.filter_start_created_time_inclusive > 0:
            query_params["filterStartCreatedTimeInclusive"] = str(params.filter_start_created_time_inclusive)
        if params.filter_end_created_time_exclusive > 0:
            query_params["filterEndCreatedTimeExclusive"] = str(params.filter_end_created_time_exclusive)

        # Execute request using async client
        return await self.async_client.make_authenticated_request(
            method="GET",
            path="/api/v1/private/order/getHistoryOrderPage",
            params=query_params
        )

    async def get_order_fill_transactions(self, params: OrderFillTransactionParams) -> Dict[str, Any]:
        """
        Get order fill transactions with pagination and filters.

        Args:
            params: Order fill transaction query parameters

        Returns:
            Dict[str, Any]: The order fill transactions

        Raises:
            ValueError: If the request fails
        """
        # Build query parameters
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
        if params.filter_contract_id_list:
            query_params["filterContractIdList"] = ",".join(params.filter_contract_id_list)
        if params.filter_order_id_list:
            query_params["filterOrderIdList"] = ",".join(params.filter_order_id_list)

        # Add boolean filters
        if params.filter_is_liquidate is not None:
            query_params["filterIsLiquidateList"] = str(params.filter_is_liquidate).lower()
        if params.filter_is_deleverage is not None:
            query_params["filterIsDeleverageList"] = str(params.filter_is_deleverage).lower()
        if params.filter_is_position_tpsl is not None:
            query_params["filterIsPositionTpslList"] = str(params.filter_is_position_tpsl).lower()

        # Add time filters
        if params.filter_start_created_time_inclusive > 0:
            query_params["filterStartCreatedTimeInclusive"] = str(params.filter_start_created_time_inclusive)
        if params.filter_end_created_time_exclusive > 0:
            query_params["filterEndCreatedTimeExclusive"] = str(params.filter_end_created_time_exclusive)

        # Execute request using async client
        return await self.async_client.make_authenticated_request(
            method="GET",
            path="/api/v1/private/order/getHistoryOrderFillTransactionPage",
            params=query_params
        )

    async def get_orders_by_ids(self, order_id_list: List[str]) -> Dict[str, Any]:
        """
        Get orders by account ID and order IDs (batch).

        Args:
            order_id_list: List of order IDs to fetch

        Returns:
            Dict[str, Any]: Orders matching the provided IDs

        Raises:
            ValueError: If input is invalid or request fails
        """
        if not order_id_list:
            raise ValueError("order_id_list must not be empty")

        query_params = {
            "accountId": str(self.async_client.get_account_id()),
            "orderIdList": ",".join(order_id_list),
        }

        return await self.async_client.make_authenticated_request(
            method="GET",
            path="/api/v1/private/order/getOrderById",
            params=query_params,
        )

    async def get_orders_by_client_order_ids(self, client_order_id_list: List[str]) -> Dict[str, Any]:
        """
        Get orders by client order IDs (batch).

        Args:
            client_order_id_list: List of client order IDs to fetch

        Returns:
            Dict[str, Any]: Orders matching the provided client order IDs

        Raises:
            ValueError: If input is invalid or request fails
        """
        if not client_order_id_list:
            raise ValueError("client_order_id_list must not be empty")

        query_params = {
            "accountId": str(self.async_client.get_account_id()),
            "clientOrderIdList": ",".join(client_order_id_list),
        }

        return await self.async_client.make_authenticated_request(
            method="GET",
            path="/api/v1/private/order/getOrderByClientOrderId",
            params=query_params,
        )

    async def get_max_order_size(self, contract_id: str, price: float) -> Dict[str, Any]:
        """
        Get the maximum order size for a given contract and price.

        Args:
            contract_id: The contract ID
            price: The price

        Returns:
            Dict[str, Any]: The maximum order size information

        Raises:
            ValueError: If the request fails
        """
        # Build request body (API expects POST with JSON body)
        data = {
            "accountId": str(self.async_client.get_account_id()),
            "contractId": contract_id,
            "price": str(price)
        }

        # Execute request using async client
        return await self.async_client.make_authenticated_request(
            method="POST",
            path="/api/v1/private/order/getMaxCreateOrderSize",
            data=data
        )
