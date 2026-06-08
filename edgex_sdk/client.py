import time
from typing import Dict, Any, Optional
from decimal import Decimal

from .internal.async_client import AsyncClient
from .internal.auth import DEFAULT_HEADER_KEY
from .account.client import Client as AccountClient
from .asset.client import Client as AssetClient
from .funding.client import Client as FundingClient
from .metadata.client import Client as MetadataClient
from .order.client import Client as OrderClient
from .quote.client import Client as QuoteClient
from .transfer.client import Client as TransferClient
from .unified_asset.client import Client as UnifiedAssetClient
from .order.types import CreateOrderParams, CancelOrderParams, GetActiveOrderParams, OrderFillTransactionParams, OrderType, OrderSide


class Client:
    """Main EdgeX SDK client (v2 only)."""

    def __init__(
        self,
        base_url: str,
        account_id: int,
        api_key: str = "",
        api_passphrase: str = "",
        api_secret: str = "",
        trading_private_key: str = "",
        wallet_private_key: str = "",
        trading_address: str = "",
        wallet_address: str = "",
        auth_header_key: str = DEFAULT_HEADER_KEY,
        timeout: float = 30.0,
    ):
        self.async_client = AsyncClient(
            base_url=base_url,
            account_id=int(account_id),
            api_key=api_key,
            api_passphrase=api_passphrase,
            api_secret=api_secret,
            trading_private_key=trading_private_key,
            wallet_private_key=wallet_private_key,
            trading_address=trading_address,
            wallet_address=wallet_address,
            auth_header_key=auth_header_key,
            timeout=timeout,
        )

        self.metadata = MetadataClient(self.async_client)
        self.account = AccountClient(self.async_client)
        self.order = OrderClient(self.async_client)
        self.quote = QuoteClient(self.async_client)
        self.funding = FundingClient(self.async_client)
        self.transfer = TransferClient(self.async_client)
        self.asset = AssetClient(self.async_client)
        self.unified_asset = UnifiedAssetClient(self.async_client)

        self._metadata_cache = None
        self._metadata_cache_time = 0.0
        self._metadata_cache_ttl = 3600.0

    async def __aenter__(self):
        await self.async_client._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        await self.async_client.close()

    async def get_metadata(self) -> Dict[str, Any]:
        now = time.time()
        if self._metadata_cache and (now - self._metadata_cache_time) < self._metadata_cache_ttl:
            return self._metadata_cache
        self._metadata_cache = await self.metadata.get_metadata()
        self._metadata_cache_time = now
        return self._metadata_cache

    async def get_server_time(self) -> Dict[str, Any]:
        return await self.metadata.get_server_time()

    async def create_order(self, params: CreateOrderParams) -> Dict[str, Any]:
        metadata = await self.get_metadata()
        if not metadata:
            raise ValueError("failed to get metadata")

        l2_price = params.price
        if params.type == OrderType.MARKET:
            price = await self._get_market_order_price(params.contract_id, params.side)
            if price is None:
                raise ValueError("failed to get market order price")
            l2_price = price
            params.price = "0"

        l2_price_decimal = Decimal(l2_price)
        return await self.order.create_order(params, metadata.get("data", {}), l2_price_decimal)

    async def create_limit_order(
        self,
        contract_id: str,
        size: str,
        price: str,
        side: OrderSide,
        time_in_force: str = "",
        client_order_id: str = "",
        expire_time: int = 0,
        reduce_only: bool = False,
    ) -> Dict[str, Any]:
        return await self.create_order(
            CreateOrderParams(
                contract_id=contract_id,
                price=price,
                size=size,
                type=OrderType.LIMIT,
                side=side,
                time_in_force=time_in_force,
                client_order_id=client_order_id,
                expire_time=expire_time,
                reduce_only=reduce_only,
            )
        )

    async def create_market_order(
        self,
        contract_id: str,
        size: str,
        side: OrderSide,
        client_order_id: str = "",
        expire_time: int = 0,
        reduce_only: bool = False,
    ) -> Dict[str, Any]:
        return await self.create_order(
            CreateOrderParams(
                contract_id=contract_id,
                price="0",
                size=size,
                type=OrderType.MARKET,
                side=side,
                client_order_id=client_order_id,
                expire_time=expire_time,
                reduce_only=reduce_only,
            )
        )

    async def create_transfer_out(self, params) -> Dict[str, Any]:
        metadata = await self.get_metadata()
        if not metadata:
            raise ValueError("failed to get metadata")
        return await self.transfer.create_transfer_out(params, metadata.get("data", {}))

    async def create_withdraw(self, params) -> Dict[str, Any]:
        return await self.unified_asset.create_withdraw(params)

    async def create_normal_withdrawal(self, params) -> Dict[str, Any]:
        return await self.create_withdraw(params)

    async def cancel_order(self, params: CancelOrderParams) -> Dict[str, Any]:
        return await self.order.cancel_order(params)

    async def get_active_orders(self, params: GetActiveOrderParams) -> Dict[str, Any]:
        return await self.order.get_active_orders(params)

    async def get_order_fill_transactions(self, params: OrderFillTransactionParams) -> Dict[str, Any]:
        return await self.order.get_order_fill_transactions(params)

    async def get_account_asset(self) -> Dict[str, Any]:
        return await self.account.get_account_asset()

    async def get_account_positions(self) -> Dict[str, Any]:
        return await self.account.get_account_positions()

    async def get_24_hour_quote(self, contract_id: str) -> Dict[str, Any]:
        return await self.quote.get_24_hour_quote(contract_id)

    async def get_max_order_size(self, contract_id: str, price: Decimal) -> Dict[str, Any]:
        return await self.order.get_max_order_size(contract_id, float(price))

    async def _get_market_order_price(self, contract_id: str, side: OrderSide) -> Optional[str]:
        metadata = await self.get_metadata()
        if not metadata:
            raise ValueError("failed to get metadata")

        contract = None
        for c in metadata.get("data", {}).get("contractList", []):
            if c.get("contractId") == contract_id:
                contract = c
                break
        if not contract:
            raise ValueError(f"contract not found: {contract_id}")

        if side == OrderSide.BUY:
            quote = await self.get_24_hour_quote(contract_id)
            if not quote:
                return None
            oracle_price = Decimal(quote.get("data", [])[0].get("oraclePrice", "0"))
            tick_size = Decimal(contract.get("tickSize", "0"))
            precision = abs(tick_size.as_tuple().exponent)
            price = str(round(oracle_price * Decimal("10"), precision))
        else:
            price = contract.get("tickSize", "0")

        return price
