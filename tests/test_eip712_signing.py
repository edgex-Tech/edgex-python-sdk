"""
Unit tests for the v2 EIP-712 signing helpers.
"""

import unittest

from edgex_sdk.internal.eip712 import (
    build_eip712_domain,
    derive_address_from_private_key,
    sign_typed_data,
)


class TestEip712Signing(unittest.TestCase):
    def setUp(self):
        self.private_key_hex = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
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

    def test_derive_address_from_private_key(self):
        address = derive_address_from_private_key(self.private_key_hex)
        self.assertTrue(address.startswith("0x"))
        self.assertEqual(len(address), 42)

    def test_sign_typed_data(self):
        signature = sign_typed_data(self.private_key_hex, self.typed_data)
        self.assertFalse(signature.startswith("0x"))
        self.assertEqual(len(signature), 130)
        int(signature, 16)

    def test_sign_typed_data_with_0x_prefix(self):
        signature = sign_typed_data(self.private_key_hex, self.typed_data, include_0x=True)
        self.assertTrue(signature.startswith("0x"))
        self.assertEqual(len(signature), 132)
        int(signature[2:], 16)


if __name__ == "__main__":
    unittest.main()
