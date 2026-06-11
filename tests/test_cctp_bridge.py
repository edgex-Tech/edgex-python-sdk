import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from edgex_sdk.cctp.client import (
    CCTPBridgeClient,
    DEFAULT_DEST_CCTP_DOMAIN,
    DEFAULT_ETH_MESSAGE_TRANSMITTER,
    DEFAULT_IRIS_BASE_URL,
    DEFAULT_SOURCE_CCTP_DOMAIN,
    ZERO_BYTES32,
    bytes32_address,
    extract_minimum_fee_bps,
    is_complete_iris_message,
    select_iris_message,
)


class CCTPBridgeTest(unittest.TestCase):
    def test_mainnet_defaults_match_edge_to_ethereum(self):
        self.assertEqual(DEFAULT_IRIS_BASE_URL, "https://iris-api.circle.com")
        self.assertEqual(DEFAULT_SOURCE_CCTP_DOMAIN, 28)
        self.assertEqual(DEFAULT_DEST_CCTP_DOMAIN, 0)
        self.assertEqual(
            DEFAULT_ETH_MESSAGE_TRANSMITTER,
            "0x81D40F21F12A8F0E3252Bccb954D722d4c464B64",
        )

    def test_bytes32_address_left_pads_evm_address(self):
        self.assertEqual(
            bytes32_address("0xFCAd0B19bB29D4674531d6f115237E16AfCE377c"),
            "0x000000000000000000000000fcad0b19bb29d4674531d6f115237e16afce377c",
        )
        self.assertEqual(len(ZERO_BYTES32), 66)

    def test_fee_parser_uses_matching_finality_threshold(self):
        payload = [
            {"finalityThreshold": 1000, "minimumFee": 1.5},
            {"finalityThreshold": 2000, "minimumFee": 0},
        ]
        self.assertEqual(extract_minimum_fee_bps(payload, 1000), Decimal("1.5"))
        self.assertEqual(extract_minimum_fee_bps(payload, 2000), Decimal("0"))

    def test_select_iris_message_by_event_nonce(self):
        payload = {
            "messages": [
                {"status": "pending", "eventNonce": "0x1", "attestation": ""},
                {"status": "complete", "eventNonce": "0x2", "attestation": "0xab"},
            ]
        }
        self.assertEqual(select_iris_message(payload, event_nonce="0x2")["eventNonce"], "0x2")
        self.assertTrue(is_complete_iris_message(payload["messages"][1]))

    def test_select_iris_message_defaults_to_first_complete(self):
        payload = {
            "messages": [
                {"status": "pending", "eventNonce": "0x1", "attestation": ""},
                {"status": "complete", "eventNonce": "0x2", "attestation": "0xab"},
            ]
        }
        self.assertEqual(select_iris_message(payload)["eventNonce"], "0x2")

    def test_bridge_usdc_dry_run_uses_distinct_nonces(self):
        client = RecordingBridgeClient(edge_rpc="https://edge-rpc.example")

        with patch("edgex_sdk.cctp.client._require_web3", return_value=FakeWeb3), patch(
            "edgex_sdk.cctp.client.Account.from_key",
            return_value=SimpleNamespace(address=FakeEth.sender),
        ):
            result = client.bridge_usdc("0xabc", 1000, dry_run=True)

        self.assertEqual(result["approveTx"]["nonce"], 7)
        self.assertEqual(result["burnTx"]["nonce"], 8)

    def test_bridge_usdc_builds_burn_after_approval_send(self):
        client = RecordingBridgeClient(edge_rpc="https://edge-rpc.example")

        with patch("edgex_sdk.cctp.client._require_web3", return_value=FakeWeb3), patch(
            "edgex_sdk.cctp.client.Account.from_key",
            return_value=SimpleNamespace(address=FakeEth.sender),
        ):
            result = client.bridge_usdc("0xabc", 1000)

        self.assertEqual(result, {"approveTxHash": "approve-hash", "burnTxHash": "burn-hash"})
        self.assertEqual(client.sent_nonces, [7, 8])


class FakeFunctions:
    def approve(self, spender, amount):
        return {"name": "approve", "spender": spender, "amount": amount}

    def depositForBurn(self, *args):
        return {"name": "depositForBurn", "args": args}


class FakeContract:
    functions = FakeFunctions()


class FakeEth:
    sender = "0xFCAd0B19bB29D4674531d6f115237E16AfCE377c"

    def __init__(self):
        self.chain_id = 3343
        self.nonce = 7

    def get_transaction_count(self, account):
        return self.nonce

    def contract(self, address, abi):
        return FakeContract()


class FakeWeb3:
    @staticmethod
    def HTTPProvider(url):
        return url

    def __init__(self, provider):
        self.provider = provider
        self.eth = FakeEth()

    def is_connected(self):
        return True


class RecordingBridgeClient(CCTPBridgeClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sent_nonces = []

    @staticmethod
    def build_tx(w3, account, tx, extra=None):
        extra = extra or {}
        return {
            "from": account,
            "chainId": w3.eth.chain_id,
            "nonce": extra.get("nonce", w3.eth.get_transaction_count(account)),
            "call": tx["name"],
        }

    def send_and_wait(self, w3, private_key, tx, timeout=180):
        self.sent_nonces.append(tx["nonce"])
        w3.eth.nonce = tx["nonce"] + 1
        return "approve-hash" if tx["call"] == "approve" else "burn-hash"


if __name__ == "__main__":
    unittest.main()
