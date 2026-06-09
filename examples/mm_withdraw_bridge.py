"""
Market maker withdrawal and CCTP bridge example.

Flow:
1. Withdraw raw USDC amount from Spot or Perp V2 through unified-asset.
2. Bridge USDC from Edge Mainnet to Ethereum Mainnet with Circle CCTP.
3. Optionally claim an existing Edge burn transaction on Ethereum.

Set MM_SUBMIT_WITHDRAW=true or MM_SEND_BRIDGE=true before using live actions.
"""

import asyncio
import os

from edgex_sdk import Client, CreateWithdrawParams
from edgex_sdk.cctp import CCTPBridgeClient


async def withdraw_from_spot():
    client = Client(
        base_url=os.environ["EDGEX_BASE_URL"],
        account_id=int(os.environ["EDGEX_SPOT_ACCOUNT_ID"]),
        api_key=os.environ["EDGEX_API_KEY"],
        api_passphrase=os.environ["EDGEX_API_PASSPHRASE"],
        api_secret=os.environ["EDGEX_API_SECRET"],
        wallet_private_key=os.environ["EDGEX_SIGNER_PRIVATE_KEY"],
    )
    async with client:
        params = CreateWithdrawParams(
            amount_raw=os.environ["WITHDRAW_AMOUNT_RAW"],
            user_address=os.environ["USER_ADDRESS"],
            profile=os.getenv("WITHDRAW_PROFILE", "mainnet-usdc"),
            privy_address=os.getenv(
                "PRIVY_ADDRESS",
                "0x0000000000000000000000000000000000000000",
            ),
            privy_identity_token=os.getenv("PRIVY_IDENTITY_TOKEN", ""),
        )
        return await client.create_withdraw(params)


async def quote_or_claim():
    bridge = CCTPBridgeClient(
        edge_rpc=os.getenv("EDGE_RPC", ""),
        dest_rpc=os.getenv("ETH_RPC", ""),
    )

    if os.getenv("CLAIM_TX_HASH"):
        iris_message = await bridge.wait_for_attestation(os.environ["CLAIM_TX_HASH"])
        return bridge.claim_on_destination(
            private_key=os.environ["PRIVATE_KEY"],
            iris_message=iris_message,
            dry_run=os.getenv("MM_SEND_BRIDGE", "false").lower() != "true",
        )

    amount = int(os.environ["WITHDRAW_AMOUNT_RAW"])
    mode = os.getenv("CCTP_MODE", "standard")
    max_fee = await bridge.quote_fast_fee(amount) if mode == "fast" else None
    return bridge.bridge_usdc(
        private_key=os.environ["PRIVATE_KEY"],
        amount=amount,
        mode=mode,
        max_fee=max_fee,
        dry_run=os.getenv("MM_SEND_BRIDGE", "false").lower() != "true",
    )


async def main():
    if os.getenv("MM_SUBMIT_WITHDRAW", "false").lower() == "true":
        print(await withdraw_from_spot())
    print(await quote_or_claim())


if __name__ == "__main__":
    asyncio.run(main())
