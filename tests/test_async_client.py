"""
Unit tests for the internal async client helpers.
"""

import unittest

from edgex_sdk.internal.async_client import AsyncClient
from edgex_sdk.internal.eip712 import build_eip712_domain


class TestAsyncClient(unittest.TestCase):
    def setUp(self):
        self.private_key_hex = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        self.client = AsyncClient(
            base_url="https://testnet.edgex.exchange",
            account_id=12345,
            trading_private_key=self.private_key_hex,
        )
        self.typed_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "Message": [
                    {"name": "value", "type": "uint256"},
                ],
            },
            "primaryType": "Message",
            "domain": build_eip712_domain("EdgeX", "1", "33431", "0x1ae109ea449cfe0bed08bfe8911e968a49a919b1"),
            "message": {"value": "1"},
        }

    def test_parse_resolution(self):
        self.assertEqual(AsyncClient.parse_resolution("1000000"), 1000000)
        self.assertEqual(AsyncClient.parse_resolution("0x10"), 16)

        with self.assertRaises(ValueError):
            AsyncClient.parse_resolution("")

    def test_resolve_trading_signer_address(self):
        address = self.client.resolve_trading_signer_address()

        self.assertTrue(address.startswith("0x"))
        self.assertEqual(len(address), 42)
        self.assertEqual(self.client.trading_address, address)

    def test_sign_typed_data_with_trading_key(self):
        signature = self.client.sign_typed_data_with_trading_key(self.typed_data)

        self.assertTrue(signature.startswith("0x"))
        self.assertEqual(len(signature), 132)

    def test_sign_typed_data_with_trading_key_requires_key(self):
        client = AsyncClient(
            base_url="https://testnet.edgex.exchange",
            account_id=12345,
        )

        with self.assertRaises(ValueError):
            client.sign_typed_data_with_trading_key(self.typed_data)


if __name__ == "__main__":
    unittest.main()
