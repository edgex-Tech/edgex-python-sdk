import time
from decimal import Decimal
from typing import Dict, Any, List

from ..internal.async_client import AsyncClient
from ..internal.eip712 import (
    EIP712_DOMAIN_TYPE,
    ORDER_BASE_TYPE,
    LIMIT_ORDER_PARAMS_TYPE,
    build_eip712_domain,
)
from .types import (
    CreateOrderParams,
    CancelOrderParams,
    GetActiveOrderParams,
    OrderFillTransactionParams,
    GetHistoryOrderPageParams,
    TimeInForce,
    OrderType,
    OrderSide,
)


def _parse_max_fee_rate(contract: Dict[str, Any]) -> Decimal:
    default_rate = Decimal("0.001")
    taker_rate = default_rate
    maker_rate = default_rate
    taker_str = (contract.get("defaultTakerFeeRate") or "").strip()
    if taker_str:
        taker_rate = Decimal(taker_str)
    maker_str = (contract.get("defaultMakerFeeRate") or "").strip()
    if maker_str:
        maker_rate = Decimal(maker_str)
    return max(taker_rate, maker_rate)


def _enum_or_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _serialize_open_tpsl(params: Any) -> Dict[str, Any]:
    if params is None:
        return {}
    if isinstance(params, dict):
        return params
    return {
        "side": _enum_or_value(params.side),
        "price": params.price,
        "size": params.size,
        "clientOrderId": params.client_order_id,
        "triggerPrice": params.trigger_price,
        "triggerPriceType": _enum_or_value(params.trigger_price_type),
        "expireTime": params.expire_time,
        "l2Nonce": params.l2_nonce,
        "l2Value": params.l2_value,
        "l2Size": params.l2_size,
        "l2LimitFee": params.l2_limit_fee,
        "l2ExpireTime": params.l2_expire_time,
        "l2Signature": params.l2_signature,
    }


class Client:
    def __init__(self, async_client: AsyncClient):
        self.async_client = async_client

    async def create_order(self, params: CreateOrderParams, metadata: Dict[str, Any], l2_price: Decimal) -> Dict[str, Any]:
        if not params.time_in_force:
            if params.type == OrderType.MARKET:
                params.time_in_force = TimeInForce.IMMEDIATE_OR_CANCEL.value
            elif params.type == OrderType.LIMIT:
                params.time_in_force = TimeInForce.GOOD_TIL_CANCEL.value

        contract, quote_coin = self._resolve_contract_and_quote_coin(metadata, params.contract_id)

        if not self.async_client.trading_private_key:
            raise ValueError("trading private key is required for v2 EIP-712 order signing")

        size = Decimal(params.size)
        l2_value = l2_price * size

        fee_rate = _parse_max_fee_rate(contract)
        limit_fee = (l2_value * fee_rate).to_integral_value(rounding='ROUND_CEILING')

        contract_resolution = self.async_client.parse_resolution(contract.get("resolution", ""))
        quote_resolution = self.async_client.parse_resolution(quote_coin.get("resolution", ""))

        amount_synthetic = int(size * contract_resolution)
        amount_collateral = int(l2_value * quote_resolution)
        amount_fee = int(limit_fee * quote_resolution)

        client_order_id = params.client_order_id or self.async_client.get_random_client_id()
        l2_nonce = self.async_client.calc_nonce(client_order_id)

        now_millis = int(time.time() * 1000)
        order_expire_window = 30 * 24 * 60 * 60 * 1000
        l1_offset = 8 * 24 * 60 * 60 * 1000

        l2_expire_time = now_millis + order_expire_window
        expire_time = l2_expire_time - l1_offset
        if params.expire_time:
            expire_time = params.expire_time
            l2_expire_time = expire_time + l1_offset

        trading_signer = self.async_client.resolve_trading_signer_address()

        global_data = metadata.get("global", {})
        chain_id = (global_data.get("nativeChainId") or global_data.get("chainId") or "").strip()
        verifying_contract = (global_data.get("contractAddress") or "").strip()
        if not chain_id:
            raise ValueError("metadata.global.nativeChainId/chainId is required")
        if not verifying_contract:
            raise ValueError("metadata.global.contractAddress is required")

        domain = build_eip712_domain("EdgeX", "1", chain_id, verifying_contract)

        typed_data = {
            "types": {
                "EIP712Domain": EIP712_DOMAIN_TYPE,
                "OrderBase": ORDER_BASE_TYPE,
                "LimitOrderParams": LIMIT_ORDER_PARAMS_TYPE,
            },
            "primaryType": "LimitOrderParams",
            "domain": domain,
            "message": {
                "base": {
                    "nonce": str(l2_nonce),
                    "signer": trading_signer,
                    "accountId": str(self.async_client.get_account_id()),
                    "expirationTimestamp": str(expire_time // 1000),
                },
                "amountSynthetic": str(amount_synthetic),
                "amountCollateral": str(amount_collateral),
                "amountFee": str(amount_fee),
                "assetIdSynthetic": contract.get("contractId", ""),
                "assetIdCollateral": quote_coin.get("coinId") or contract.get("quoteCoinId", ""),
                "isBuyingSynthetic": params.side == OrderSide.BUY,
                "parentOrderHash": b'\x00' * 32,
                "subOrderIndex": "0",
            },
        }

        l2_signature = self.async_client.sign_typed_data_with_trading_key(typed_data)

        price = params.price
        if params.type in (OrderType.MARKET, OrderType.STOP_MARKET, OrderType.TAKE_PROFIT_MARKET):
            price = "0"

        body = {
            "accountId": str(self.async_client.get_account_id()),
            "contractId": params.contract_id,
            "price": price,
            "size": params.size,
            "type": _enum_or_value(params.type),
            "side": _enum_or_value(params.side),
            "timeInForce": params.time_in_force,
            "clientOrderId": client_order_id,
            "expireTime": str(expire_time),
            "l2Nonce": str(l2_nonce),
            "l2Signature": l2_signature,
            "l2ExpireTime": str(l2_expire_time),
            "l2Value": str(l2_value),
            "l2Size": params.size,
            "l2LimitFee": str(limit_fee),
            "reduceOnly": params.reduce_only,
            "triggerPrice": params.trigger_price,
            "triggerPriceType": _enum_or_value(params.trigger_price_type),
            "sourceKey": params.source_key,
            "isPositionTpsl": params.is_position_tpsl,
            "openTpslParentOrderId": params.open_tpsl_parent_order_id,
            "isSetOpenTp": params.is_set_open_tp,
            "openTp": _serialize_open_tpsl(params.open_tp) if params.is_set_open_tp else None,
            "isSetOpenSl": params.is_set_open_sl,
            "openSl": _serialize_open_tpsl(params.open_sl) if params.is_set_open_sl else None,
            "extraType": params.extra_type,
            "extraDataJson": params.extra_data_json,
        }

        return await self.async_client.make_authenticated_request(
            method="POST",
            path="/api/v2/private/order/createOrder",
            data=body,
        )

    async def cancel_order(self, params: CancelOrderParams) -> Dict[str, Any]:
        account_id = str(self.async_client.get_account_id())

        if params.order_id:
            path = "/api/v2/private/order/cancelOrderById"
            request_data = {"accountId": account_id, "orderIdList": [params.order_id]}
        elif params.client_order_id:
            path = "/api/v2/private/order/cancelOrderByClientOrderId"
            request_data = {"accountId": account_id, "clientOrderIdList": [params.client_order_id]}
        elif params.contract_id:
            path = "/api/v2/private/order/cancelAllOrder"
            request_data = {"accountId": account_id, "filterContractIdList": [params.contract_id]}
        else:
            raise ValueError("must provide either order_id, client_order_id, or contract_id")

        return await self.async_client.make_authenticated_request(method="POST", path=path, data=request_data)

    async def cancel_order_by_client_order_id(self, client_order_id_list: List[str]) -> Dict[str, Any]:
        data = {
            "accountId": str(self.async_client.get_account_id()),
            "clientOrderIdList": client_order_id_list,
        }
        return await self.async_client.make_authenticated_request(
            method="POST",
            path="/api/v2/private/order/cancelOrderByClientOrderId",
            data=data,
        )

    async def get_active_orders(self, params: GetActiveOrderParams) -> Dict[str, Any]:
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
        if params.filter_status_list:
            query_params["filterStatusList"] = ",".join(params.filter_status_list)
        if params.filter_is_liquidate is not None:
            query_params["filterIsLiquidateList"] = str(
                params.filter_is_liquidate
            ).lower()
        if params.filter_is_deleverage is not None:
            query_params["filterIsDeleverageList"] = str(
                params.filter_is_deleverage
            ).lower()
        if params.filter_is_position_tpsl is not None:
            query_params["filterIsPositionTpslList"] = str(
                params.filter_is_position_tpsl
            ).lower()
        if params.filter_start_created_time_inclusive > 0:
            query_params["filterStartCreatedTimeInclusive"] = str(params.filter_start_created_time_inclusive)
        if params.filter_end_created_time_exclusive > 0:
            query_params["filterEndCreatedTimeExclusive"] = str(params.filter_end_created_time_exclusive)

        return await self.async_client.make_authenticated_request(
            method="GET",
            path="/api/v2/private/order/getActiveOrderPage",
            params=query_params,
        )

    async def get_order_fill_transactions(self, params: OrderFillTransactionParams) -> Dict[str, Any]:
        query_params = {"accountId": str(self.async_client.get_account_id())}
        if params.size:
            query_params["size"] = params.size
        if params.offset_data:
            query_params["offsetData"] = params.offset_data
        if params.filter_coin_id_list:
            query_params["filterCoinIdList"] = ",".join(params.filter_coin_id_list)
        if params.filter_contract_id_list:
            query_params["filterContractIdList"] = ",".join(params.filter_contract_id_list)
        if params.filter_order_id_list:
            query_params["filterOrderIdList"] = ",".join(params.filter_order_id_list)
        if params.filter_is_liquidate is not None:
            query_params["filterIsLiquidateList"] = str(
                params.filter_is_liquidate
            ).lower()
        if params.filter_is_deleverage is not None:
            query_params["filterIsDeleverageList"] = str(
                params.filter_is_deleverage
            ).lower()
        if params.filter_is_position_tpsl is not None:
            query_params["filterIsPositionTpslList"] = str(
                params.filter_is_position_tpsl
            ).lower()
        if params.filter_start_created_time_inclusive > 0:
            query_params["filterStartCreatedTimeInclusive"] = str(params.filter_start_created_time_inclusive)
        if params.filter_end_created_time_exclusive > 0:
            query_params["filterEndCreatedTimeExclusive"] = str(params.filter_end_created_time_exclusive)

        return await self.async_client.make_authenticated_request(
            method="GET",
            path="/api/v2/private/order/getHistoryOrderFillTransactionPage",
            params=query_params,
        )

    async def get_history_order_page(self, params: GetHistoryOrderPageParams) -> Dict[str, Any]:
        query_params = {
            "accountId": str(self.async_client.get_account_id()),
            "size": str(params.size),
        }
        if params.offset_data:
            query_params["offsetData"] = params.offset_data
        if params.filter_coin_id_list:
            query_params["filterCoinIdList"] = ",".join(params.filter_coin_id_list)
        if params.filter_contract_id_list:
            query_params["filterContractIdList"] = ",".join(params.filter_contract_id_list)
        if params.filter_type_list:
            query_params["filterTypeList"] = ",".join(params.filter_type_list)
        if params.filter_status_list:
            query_params["filterStatusList"] = ",".join(params.filter_status_list)
        if params.filter_is_liquidate is not None:
            query_params["filterIsLiquidateList"] = str(params.filter_is_liquidate).lower()
        if params.filter_is_deleverage is not None:
            query_params["filterIsDeleverageList"] = str(params.filter_is_deleverage).lower()
        if params.filter_is_position_tpsl is not None:
            query_params["filterIsPositionTpslList"] = str(
                params.filter_is_position_tpsl
            ).lower()
        if params.filter_start_created_time_inclusive:
            query_params["filterStartCreatedTimeInclusive"] = params.filter_start_created_time_inclusive
        if params.filter_end_created_time_exclusive:
            query_params["filterEndCreatedTimeExclusive"] = params.filter_end_created_time_exclusive
        if params.filter_order_id_list:
            query_params["filterOrderIdList"] = ",".join(params.filter_order_id_list)

        return await self.async_client.make_authenticated_request(
            method="GET",
            path="/api/v2/private/order/getHistoryOrderPage",
            params=query_params,
        )

    async def get_orders_by_id(self, order_id_list: List[str]) -> Dict[str, Any]:
        query_params = {
            "accountId": str(self.async_client.get_account_id()),
            "orderIdList": ",".join(order_id_list),
        }
        return await self.async_client.make_authenticated_request(
            method="GET", path="/api/v2/private/order/getOrderById", params=query_params)

    async def get_orders_by_client_order_id(self, client_order_id_list: List[str]) -> Dict[str, Any]:
        query_params = {
            "accountId": str(self.async_client.get_account_id()),
            "clientOrderIdList": ",".join(client_order_id_list),
        }
        return await self.async_client.make_authenticated_request(
            method="GET", path="/api/v2/private/order/getOrderByClientOrderId", params=query_params)

    async def get_max_order_size(self, contract_id: str, price: float) -> Dict[str, Any]:
        data = {
            "accountId": str(self.async_client.get_account_id()),
            "contractId": contract_id,
            "price": str(price),
        }
        return await self.async_client.make_authenticated_request(
            method="POST",
            path="/api/v2/private/order/getMaxCreateOrderSize",
            data=data,
        )

    @staticmethod
    def _resolve_contract_and_quote_coin(metadata: Dict[str, Any], contract_id: str):
        contract = None
        for c in metadata.get("contractList", []):
            if c.get("contractId") == contract_id:
                contract = c
                break
        if contract is None:
            raise ValueError(f"contract not found: {contract_id}")

        quote_coin = None
        for coin in metadata.get("coinList", []):
            if coin.get("coinId") == contract.get("quoteCoinId"):
                quote_coin = coin
                break
        if quote_coin is None:
            raise ValueError(f"coin not found: {contract.get('quoteCoinId')}")

        return contract, quote_coin
