"""
Basic usage example for the EdgeX Python SDK.

This example demonstrates the basic functionality of the SDK:
- Creating a client
- Getting server time and metadata
- Getting account assets and positions
- Getting market data (K-lines, order book depth)
- Creating orders (commented out to avoid actual order creation)
- Using WebSockets for real-time data
"""

import asyncio
import os
from datetime import datetime, timedelta

from edgex_sdk import (
    Client,
    OrderSide,
    GetKLineParams,
    GetOrderBookDepthParams,
    KlineType,
    WebSocketManager,
    GetWithdrawalRecordsParams,
    CreateTransferOutParams,
    TransferReason
)
from edgex_sdk.account.client import RegisterAccountParams
from edgex_sdk.asset.client import CreateWithdrawalParams
from edgex_sdk.order.types import CreateOrderParams, OrderType


async def main():
    # Load configuration from environment variables
    base_url = os.getenv("EDGEX_BASE_URL", "https://testnet.edgex.exchange")
    account_id = int(os.getenv("EDGEX_ACCOUNT_ID", "your-account-id"))
    stark_private_key = os.getenv("EDGEX_STARK_PRIVATE_KEY", "your-stark-private-key")

    # Create a new client
    client = Client(
        base_url=base_url,
        account_id=account_id,
        stark_private_key=stark_private_key
    )

    # Get server time
    server_time = await client.get_server_time()
    print(f"Server Time: {server_time}")

    # Get exchange metadata first (required for transfer operations)
    metadata = await client.get_metadata()
    print(f"Available contracts: {len(metadata.get('data', {}).get('contractList', []))}")

    # Get account assets
    assets = await client.get_account_asset()
    print(f"Account Assets: {assets}")

    # Get K-line data for BTCUSDT (contract ID: 10000001)
    kline_params = GetKLineParams(
        contract_id="10000001",  # BTCUSDT
        kline_type=KlineType.MINUTE_1,
        size=10
    )
    klines = await client.quote.get_k_line(kline_params)
    print(f"K-lines: {klines}")

    # Get account positions
    positions = await client.get_account_positions()
    print(f"Account Positions: {positions}")

    # Get 24-hour market data for BNBUSDT (contract ID: 10000004)
    quote = await client.get_24_hour_quote("10000004")
    print(f"BNBUSDT Price: {quote}")

    # Get K-line data for BTCUSDT (contract ID: 10000001)
    kline_params = GetKLineParams(
        contract_id="10000001",  # BTCUSDT
        kline_type=KlineType.MINUTE_1,
        size=10
    )
    klines = await client.quote.get_k_line(kline_params)
    print(f"K-lines: {klines}")

    # Get order book depth for ETHUSDT (contract ID: 10000002)
    depth_params = GetOrderBookDepthParams(
        contract_id="10000002",  # ETHUSDT
        limit=15  # Valid values are 15 or 200
    )
    depth = await client.quote.get_order_book_depth(depth_params)
    print(f"Order Book Depth: {depth}")

    # Create a limit order (commented out to avoid actual order creation)
    order = await client.create_order(CreateOrderParams(
        contract_id="10000004",  # BNBUSDT
        size="0.01",
        price="600.00",
        type=OrderType.LIMIT,
        side=OrderSide.BUY,
    ))
    print(f"Order created: {order}")

    # Create a market order 
    order = await client.create_order(CreateOrderParams(
        contract_id="10000004",  # BNBUSDT
        size="0.01",
        price="0",
        type=OrderType.MARKET,
        side=OrderSide.BUY
    ))
    print(f"Order created: {order}")

    # Create a transfer out order with new optional parameters
    try:
        # Set expiration time to 24 hours from now
        expire_time = datetime.now() + timedelta(hours=24)

        transfer_result = await client.create_transfer_out(
            CreateTransferOutParams(
                coin_id="1000",
                amount="10",
                receiver_account_id="your-receiver-account-id",
                receiver_l2_key="your-receiver-l2-key", # "0x111111"
                transfer_reason=TransferReason.USER_TRANSFER,
                expire_time=expire_time,
                extra_type="CUSTOM_TYPE",
                extra_data_json='{"custom_field": "custom_value"}'
            ))
        print(f"Transfer out result: {transfer_result}")
    except ValueError as e:
        print(f"Failed to create transfer out: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    # Create a withdrawal order
    withdrawResult = await client.create_normal_withdrawal(CreateWithdrawalParams(
        coin_id="1000",
        amount="10",
        eth_address="your-eth-address", # "0x111111"
        tag=""
    ))
    print(f"WithdrawResult: {withdrawResult}")

    # Get withdrawal records with default parameters
    withdrawal_params = GetWithdrawalRecordsParams(size="10")
    withdrawResult = await client.asset.get_withdrawal_records(withdrawal_params)
    print(f"withdrawResult: {withdrawResult}")


    # WebSocket example
    ws_url = os.getenv("EDGEX_WS_URL", "wss://quote-testnet.edgex.exchange")
    ws_manager = WebSocketManager(
        base_url=ws_url,
        account_id=account_id,
        stark_pri_key=stark_private_key
    )

    # Define message handlers
    def ticker_handler(message):
        print(f"Ticker Update: {message}")

    def kline_handler(message):
        print(f"K-line Update: {message}")

    # Connect to public WebSocket for market data
    ws_manager.connect_public()

    # Subscribe to real-time updates for BNBUSDT (contract ID: 10000004)
    ws_manager.subscribe_ticker("10000004", ticker_handler)
    ws_manager.subscribe_kline("10000004", "1m", kline_handler)

    # Wait for updates
    await asyncio.sleep(30)

    # Disconnect all connections
    ws_manager.disconnect_all()

if __name__ == "__main__":
    asyncio.run(main())
