from enum import Enum
from typing import Optional, List, Any, Dict


class OrderType(Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP_LIMIT = "STOP_LIMIT"
    STOP_MARKET = "STOP_MARKET"
    TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"
    TAKE_PROFIT_MARKET = "TAKE_PROFIT_MARKET"


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class TimeInForce(Enum):
    GOOD_TIL_CANCEL = "GOOD_TIL_CANCEL"
    IMMEDIATE_OR_CANCEL = "IMMEDIATE_OR_CANCEL"
    FILL_OR_KILL = "FILL_OR_KILL"
    POST_ONLY = "POST_ONLY"


class OpenTpSlParams:
    def __init__(
        self,
        side: Any,
        price: str,
        size: str,
        client_order_id: str,
        trigger_price: str,
        trigger_price_type: Any,
        expire_time: str = "",
        l2_nonce: str = "",
        l2_value: str = "",
        l2_size: str = "",
        l2_limit_fee: str = "",
        l2_expire_time: str = "",
        l2_signature: str = "",
    ):
        self.side = side
        self.price = price
        self.size = size
        self.client_order_id = client_order_id
        self.trigger_price = trigger_price
        self.trigger_price_type = trigger_price_type
        self.expire_time = expire_time
        self.l2_nonce = l2_nonce
        self.l2_value = l2_value
        self.l2_size = l2_size
        self.l2_limit_fee = l2_limit_fee
        self.l2_expire_time = l2_expire_time
        self.l2_signature = l2_signature


class CreateOrderParams:
    def __init__(
        self,
        contract_id: str,
        price: str,
        size: str,
        type: OrderType,
        side: OrderSide,
        time_in_force: str = "",
        client_order_id: str = "",
        expire_time: int = 0,
        reduce_only: bool = False,
        trigger_price: str = "",
        trigger_price_type: Any = "",
        source_key: str = "",
        is_position_tpsl: bool = False,
        open_tpsl_parent_order_id: str = "",
        is_set_open_tp: bool = False,
        open_tp: Optional[Any] = None,
        is_set_open_sl: bool = False,
        open_sl: Optional[Any] = None,
        extra_type: str = "",
        extra_data_json: str = "",
    ):
        self.contract_id = contract_id
        self.price = price
        self.size = size
        self.type = type
        self.side = side
        self.time_in_force = time_in_force
        self.client_order_id = client_order_id
        self.expire_time = expire_time
        self.reduce_only = reduce_only
        self.trigger_price = trigger_price
        self.trigger_price_type = trigger_price_type
        self.source_key = source_key
        self.is_position_tpsl = is_position_tpsl
        self.open_tpsl_parent_order_id = open_tpsl_parent_order_id
        self.is_set_open_tp = is_set_open_tp
        self.open_tp = open_tp
        self.is_set_open_sl = is_set_open_sl
        self.open_sl = open_sl
        self.extra_type = extra_type
        self.extra_data_json = extra_data_json


class CancelOrderParams:
    def __init__(
        self,
        order_id: str = "",
        client_order_id: str = "",
        contract_id: str = "",
    ):
        self.order_id = order_id
        self.client_order_id = client_order_id
        self.contract_id = contract_id


class GetActiveOrderParams:
    def __init__(
        self,
        size: str = "",
        offset_data: str = "",
        filter_coin_id_list: List[str] = None,
        filter_contract_id_list: List[str] = None,
        filter_type_list: List[str] = None,
        filter_status_list: List[str] = None,
        filter_is_liquidate: Optional[bool] = None,
        filter_is_deleverage: Optional[bool] = None,
        filter_is_position_tpsl: Optional[bool] = None,
        filter_start_created_time_inclusive: int = 0,
        filter_end_created_time_exclusive: int = 0,
    ):
        self.size = size
        self.offset_data = offset_data
        self.filter_coin_id_list = filter_coin_id_list or []
        self.filter_contract_id_list = filter_contract_id_list or []
        self.filter_type_list = filter_type_list or []
        self.filter_status_list = filter_status_list or []
        self.filter_is_liquidate = filter_is_liquidate
        self.filter_is_deleverage = filter_is_deleverage
        self.filter_is_position_tpsl = filter_is_position_tpsl
        self.filter_start_created_time_inclusive = filter_start_created_time_inclusive
        self.filter_end_created_time_exclusive = filter_end_created_time_exclusive


class OrderFillTransactionParams:
    def __init__(
        self,
        size: str = "",
        offset_data: str = "",
        filter_coin_id_list: List[str] = None,
        filter_contract_id_list: List[str] = None,
        filter_order_id_list: List[str] = None,
        filter_is_liquidate: Optional[bool] = None,
        filter_is_deleverage: Optional[bool] = None,
        filter_is_position_tpsl: Optional[bool] = None,
        filter_start_created_time_inclusive: int = 0,
        filter_end_created_time_exclusive: int = 0,
    ):
        self.size = size
        self.offset_data = offset_data
        self.filter_coin_id_list = filter_coin_id_list or []
        self.filter_contract_id_list = filter_contract_id_list or []
        self.filter_order_id_list = filter_order_id_list or []
        self.filter_is_liquidate = filter_is_liquidate
        self.filter_is_deleverage = filter_is_deleverage
        self.filter_is_position_tpsl = filter_is_position_tpsl
        self.filter_start_created_time_inclusive = filter_start_created_time_inclusive
        self.filter_end_created_time_exclusive = filter_end_created_time_exclusive


class GetHistoryOrderPageParams:
    def __init__(
        self,
        size: int = 100,
        offset_data: str = "",
        filter_coin_id_list: List[str] = None,
        filter_contract_id_list: List[str] = None,
        filter_type_list: List[str] = None,
        filter_status_list: List[str] = None,
        filter_is_liquidate: Optional[bool] = None,
        filter_is_deleverage: Optional[bool] = None,
        filter_is_position_tpsl: Optional[bool] = None,
        filter_start_created_time_inclusive: str = "",
        filter_end_created_time_exclusive: str = "",
        filter_order_id_list: List[str] = None,
    ):
        self.size = size
        self.offset_data = offset_data
        self.filter_coin_id_list = filter_coin_id_list or []
        self.filter_contract_id_list = filter_contract_id_list or []
        self.filter_type_list = filter_type_list or []
        self.filter_status_list = filter_status_list or []
        self.filter_is_liquidate = filter_is_liquidate
        self.filter_is_deleverage = filter_is_deleverage
        self.filter_is_position_tpsl = filter_is_position_tpsl
        self.filter_start_created_time_inclusive = filter_start_created_time_inclusive
        self.filter_end_created_time_exclusive = filter_end_created_time_exclusive
        self.filter_order_id_list = filter_order_id_list or []
