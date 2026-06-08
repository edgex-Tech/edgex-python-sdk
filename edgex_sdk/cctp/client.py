import asyncio
import time
from decimal import Decimal, ROUND_CEILING
from typing import Any, Dict, List, Optional

import aiohttp
from eth_account import Account
from eth_utils import to_checksum_address


ZERO_BYTES32 = "0x" + "00" * 32
DEFAULT_IRIS_BASE_URL = "https://iris-api.circle.com"
DEFAULT_SOURCE_CCTP_DOMAIN = 28
DEFAULT_DEST_CCTP_DOMAIN = 0
DEFAULT_EDGE_USDC = "0x98d2919b9A214E6Fa5384AC81E6864bA686Ad74c"
DEFAULT_EDGE_TOKEN_MESSENGER = "0x98706A006bc632Df31CAdFCBD43F38887ce2ca5c"
DEFAULT_ETH_MESSAGE_TRANSMITTER = "0x81D40F21F12A8F0E3252Bccb954D722d4c464B64"
DEFAULT_STANDARD_FINALITY = 2000
DEFAULT_FAST_FINALITY = 1000
DEFAULT_CLAIM_GAS_LIMIT = 500000

ERC20_ABI = [
    {
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]

TOKEN_MESSENGER_V2_ABI = [
    {
        "inputs": [
            {"name": "amount", "type": "uint256"},
            {"name": "destinationDomain", "type": "uint32"},
            {"name": "mintRecipient", "type": "bytes32"},
            {"name": "burnToken", "type": "address"},
            {"name": "destinationCaller", "type": "bytes32"},
            {"name": "maxFee", "type": "uint256"},
            {"name": "minFinalityThreshold", "type": "uint32"},
        ],
        "name": "depositForBurn",
        "outputs": [{"name": "nonce", "type": "bytes32"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]

MESSAGE_TRANSMITTER_V2_ABI = [
    {
        "inputs": [
            {"name": "message", "type": "bytes"},
            {"name": "attestation", "type": "bytes"},
        ],
        "name": "receiveMessage",
        "outputs": [{"name": "success", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


def _require_web3():
    try:
        from web3 import Web3
    except ImportError as exc:
        raise ImportError("CCTP on-chain bridge helpers require `web3`. Install the bridge extra.") from exc
    return Web3


def bytes32_address(address: str) -> str:
    checksummed = to_checksum_address(address)
    return "0x" + ("00" * 12) + checksummed[2:].lower()


def extract_minimum_fee_bps(payload: Any, finality_threshold: int) -> Decimal:
    rows: List[Dict[str, Any]] = []
    if isinstance(payload, list):
        rows = [item for item in payload if isinstance(item, dict)]
    elif isinstance(payload, dict):
        if isinstance(payload.get("data"), list):
            rows.extend(item for item in payload["data"] if isinstance(item, dict))
        if isinstance(payload.get("fees"), list):
            rows.extend(item for item in payload["fees"] if isinstance(item, dict))
        if isinstance(payload.get("data"), dict):
            rows.append(payload["data"])
        else:
            rows.append(payload)

    for row in rows:
        if int(row.get("finalityThreshold", -1)) == finality_threshold:
            minimum_fee = row.get("minimumFee")
            if minimum_fee is not None and str(minimum_fee) != "":
                return Decimal(str(minimum_fee))

    available = [row.get("finalityThreshold") for row in rows if "finalityThreshold" in row]
    raise ValueError(
        "Circle fee response missing minimumFee for finalityThreshold=%s; available=%s"
        % (finality_threshold, available)
    )


def calculate_fee_from_bps(amount: int, fee_bps: Decimal) -> int:
    fee = (Decimal(amount) * Decimal(fee_bps) / Decimal(10000)).to_integral_value(
        rounding=ROUND_CEILING
    )
    return int(fee)


def iris_messages(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("messages"), list):
        return [item for item in payload["messages"] if isinstance(item, dict)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def is_complete_iris_message(message: Dict[str, Any]) -> bool:
    attestation = str(message.get("attestation") or "")
    return (
        str(message.get("status", "")).lower() == "complete"
        and attestation.startswith("0x")
        and attestation.lower() != "pending_confirmations"
    )


def select_iris_message(
    payload: Any,
    message_index: Optional[int] = None,
    event_nonce: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    messages = iris_messages(payload)
    if not messages:
        return None
    if message_index is not None:
        if message_index < 0 or message_index >= len(messages):
            raise ValueError(
                "Iris message index out of range: %s; count=%s"
                % (message_index, len(messages))
            )
        return messages[message_index]
    if event_nonce:
        target = event_nonce.lower()
        for message in messages:
            if str(message.get("eventNonce", "")).lower() == target:
                return message
        raise ValueError("Iris response missing eventNonce=%s" % event_nonce)
    complete = [message for message in messages if is_complete_iris_message(message)]
    return complete[0] if complete else messages[0]


class CCTPBridgeClient:
    def __init__(
        self,
        edge_rpc: str = "",
        dest_rpc: str = "",
        iris_base_url: str = DEFAULT_IRIS_BASE_URL,
        source_domain: int = DEFAULT_SOURCE_CCTP_DOMAIN,
        dest_domain: int = DEFAULT_DEST_CCTP_DOMAIN,
        token_messenger: str = DEFAULT_EDGE_TOKEN_MESSENGER,
        edge_usdc: str = DEFAULT_EDGE_USDC,
        dest_message_transmitter: str = DEFAULT_ETH_MESSAGE_TRANSMITTER,
    ):
        self.edge_rpc = edge_rpc
        self.dest_rpc = dest_rpc
        self.iris_base_url = iris_base_url.rstrip("/")
        self.source_domain = int(source_domain)
        self.dest_domain = int(dest_domain)
        self.token_messenger = to_checksum_address(token_messenger)
        self.edge_usdc = to_checksum_address(edge_usdc)
        self.dest_message_transmitter = to_checksum_address(dest_message_transmitter)

    async def quote_fast_fee(self, amount: int, finality_threshold: int = DEFAULT_FAST_FINALITY) -> int:
        url = "%s/v2/burn/USDC/fees/%d/%d" % (
            self.iris_base_url,
            self.source_domain,
            self.dest_domain,
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError("Circle fee request failed: status=%s" % response.status)
                payload = await response.json()
        return calculate_fee_from_bps(
            amount,
            extract_minimum_fee_bps(payload, finality_threshold),
        )

    async def fetch_iris_payload(self, source_tx_hash: str) -> Any:
        url = "%s/v2/messages/%d?transactionHash=%s" % (
            self.iris_base_url,
            self.source_domain,
            source_tx_hash,
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError("Iris request failed: status=%s" % response.status)
                return await response.json()

    async def wait_for_attestation(
        self,
        source_tx_hash: str,
        timeout: float = 1800.0,
        poll_interval: float = 30.0,
        message_index: Optional[int] = None,
        event_nonce: Optional[str] = None,
    ) -> Dict[str, Any]:
        deadline = time.time() + timeout
        last_status = "unknown"
        while True:
            payload = await self.fetch_iris_payload(source_tx_hash)
            message = select_iris_message(payload, message_index, event_nonce)
            if message and is_complete_iris_message(message):
                return message
            if message:
                last_status = str(message.get("status", "unknown"))
            if time.time() >= deadline:
                raise TimeoutError(
                    "Iris attestation not complete before timeout; last_status=%s"
                    % last_status
                )
            await asyncio.sleep(poll_interval)

    @staticmethod
    def build_tx(w3, account: str, tx, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        tx_params = {
            "from": account,
            "nonce": w3.eth.get_transaction_count(account),
            "chainId": w3.eth.chain_id,
        }
        if extra:
            tx_params.update(extra)
        return tx.build_transaction(tx_params)

    @staticmethod
    def send_and_wait(w3, private_key: str, tx: Dict[str, Any], timeout: int = 180) -> str:
        signed = w3.eth.account.sign_transaction(tx, private_key=private_key)
        raw_tx = getattr(signed, "rawTransaction", None) or signed.raw_transaction
        tx_hash = w3.eth.send_raw_transaction(raw_tx)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
        if receipt.status != 1:
            raise RuntimeError("transaction reverted: %s" % tx_hash.hex())
        return tx_hash.hex()

    def bridge_usdc(
        self,
        private_key: str,
        amount: int,
        recipient: str = "",
        mode: str = "standard",
        max_fee: Optional[int] = None,
        finality_threshold: Optional[int] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        Web3 = _require_web3()
        w3 = Web3(Web3.HTTPProvider(self.edge_rpc))
        if not w3.is_connected():
            raise ValueError("failed to connect to edge_rpc")

        sender = Account.from_key(private_key).address
        recipient = to_checksum_address(recipient or sender)
        if mode == "standard":
            max_fee = 0 if max_fee is None else max_fee
            finality_threshold = finality_threshold or DEFAULT_STANDARD_FINALITY
        elif mode == "fast":
            if max_fee is None:
                raise ValueError("fast mode requires max_fee; call quote_fast_fee first")
            finality_threshold = finality_threshold or DEFAULT_FAST_FINALITY
        else:
            raise ValueError("mode must be standard or fast")

        usdc = w3.eth.contract(address=self.edge_usdc, abi=ERC20_ABI)
        messenger = w3.eth.contract(address=self.token_messenger, abi=TOKEN_MESSENGER_V2_ABI)
        approve_tx = self.build_tx(w3, sender, usdc.functions.approve(self.token_messenger, amount))
        burn_tx = self.build_tx(
            w3,
            sender,
            messenger.functions.depositForBurn(
                amount,
                self.dest_domain,
                bytes32_address(recipient),
                self.edge_usdc,
                ZERO_BYTES32,
                max_fee,
                finality_threshold,
            ),
        )
        if dry_run:
            return {"approveTx": approve_tx, "burnTx": burn_tx}

        approve_hash = self.send_and_wait(w3, private_key, approve_tx)
        burn_hash = self.send_and_wait(w3, private_key, burn_tx)
        return {"approveTxHash": approve_hash, "burnTxHash": burn_hash}

    def claim_on_destination(
        self,
        private_key: str,
        iris_message: Dict[str, Any],
        dry_run: bool = False,
        gas_limit: int = DEFAULT_CLAIM_GAS_LIMIT,
    ) -> Dict[str, Any]:
        Web3 = _require_web3()
        w3 = Web3(Web3.HTTPProvider(self.dest_rpc))
        if not w3.is_connected():
            raise ValueError("failed to connect to dest_rpc")

        claimer = Account.from_key(private_key).address
        message_hex = iris_message.get("message")
        attestation_hex = iris_message.get("attestation")
        if not isinstance(message_hex, str) or not message_hex.startswith("0x"):
            raise ValueError("Iris message missing hex message")
        if not isinstance(attestation_hex, str) or not attestation_hex.startswith("0x"):
            raise ValueError("Iris message missing hex attestation")

        transmitter = w3.eth.contract(
            address=self.dest_message_transmitter,
            abi=MESSAGE_TRANSMITTER_V2_ABI,
        )
        claim_tx = self.build_tx(
            w3,
            claimer,
            transmitter.functions.receiveMessage(
                Web3.to_bytes(hexstr=message_hex),
                Web3.to_bytes(hexstr=attestation_hex),
            ),
            {"gas": gas_limit} if gas_limit > 0 else None,
        )
        if dry_run:
            return {"claimTx": claim_tx}
        return {"claimTxHash": self.send_and_wait(w3, private_key, claim_tx)}
