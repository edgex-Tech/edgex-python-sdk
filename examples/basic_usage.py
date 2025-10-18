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

from edgex_sdk import (
    Client,
    OrderSide,
    GetKLineParams,
    GetOrderBookDepthParams,
    WebSocketManager
)
from edgex_sdk.account.client import RegisterAccountParams
from edgex_sdk.asset.client import CreateWithdrawalParams


async def main():
    # Load configuration from environment variables
    base_url = os.getenv("EDGEX_BASE_URL", "https://testnet.edgex.exchange")
    account_id = int(os.getenv("EDGEX_ACCOUNT_ID", "665403845421039873"))
    stark_private_key = os.getenv("EDGEX_STARK_PRIVATE_KEY", "04a266bc1e005725a278034bc4ab0f3075a7110a47d390b0b1b7841cabac0c4d")

    # Create a new client
    client = Client(
        base_url=base_url,
        account_id=account_id,
        stark_private_key=stark_private_key
    )
    
    result = await client.account.get_account_asset()
    print(f"Line 39 result: {result}")

    registerParm = RegisterAccountParams(
        l2_key="0503fcc5930194246e5a41e690c72ff2075bfd7b97fb25dbbbdc0c57fb072ee3",
        l2_key_y_coordinate="05c5725ca5111e6e0f67fc2002ffb98ed3396ad5b3b0445d9dd5606953148a50",
        client_account_id="12345"
    )
    registerResult = await client.account.register_account(registerParm)
    print(f"Line 54 registerResult: {registerResult}")
    
    withdrawResult = await client.asset.create_withdrawal(CreateWithdrawalParams(
        coin_id="1000",
        amount="0.001",
        eth_address="0x83D9424105c689e9DC0dfB54496B7F722276fAFE",
        tag=""
    ))
    print(f"Line 72 withdrawResult: {withdrawResult}")

'''
    # Get exchange metadata
    metadata = await client.get_metadata()
    print(f"Available contracts: {len(metadata.get('data', {}).get('contractList', []))}")

    # Get account assets
    assets = await client.get_account_asset()
    print(f"Account Assets: {assets}")

    # Get account positions
    positions = await client.get_account_positions()
    print(f"Account Positions: {positions}")

    # Get 24-hour market data for BNBUSDT (contract ID: 10000004)
    quote = await client.get_24_hour_quote("10000004")
    print(f"BNBUSDT Price: {quote}")

    # Get K-line data for BTCUSDT (contract ID: 10000001)
    kline_params = GetKLineParams(
        contract_id="10000001",  # BTCUSDT
        interval="1m",
        size="10"
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
    # order = await client.create_limit_order(
    #     contract_id="10000004",  # BNBUSDT
    #     size="0.01",
    #     price="600.00",
    #     side=OrderSide.BUY
    # )
    # print(f"Order created: {order}")

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
'''

if __name__ == "__main__":
    asyncio.run(main())
