import asyncio
import unittest
from unittest.mock import patch

from edgex_sdk.account.client import Client as AccountClient, SetMarginModeParams


class FakeAsyncClient:
    def __init__(self, trading_private_key="unused-by-fake-client"):
        self.account_id = 12345
        self.trading_private_key = trading_private_key
        self.calls = []

    def get_account_id(self):
        return self.account_id

    def get_random_client_id(self):
        return "client-1"

    def calc_nonce(self, client_order_id):
        self.calls.append(("nonce", client_order_id))
        return 123456

    def resolve_trading_signer_address(self):
        self.calls.append(("resolve_trading",))
        return "0xFCAd0B19bB29D4674531d6f115237E16AfCE377c"

    def sign_typed_data_with_trading_key(self, typed_data, include_0x=False):
        self.calls.append(("sign_trading", typed_data, include_0x))
        return "11" * 65

    def sign_typed_data_with_wallet_key(self, typed_data, include_0x=False):
        raise AssertionError("wallet key must not be used for setMarginMode")

    async def make_authenticated_request(
        self, method, path, data=None, params=None, rewrite_version=True
    ):
        self.calls.append((method, path, data, params, rewrite_version))
        return {"code": "SUCCESS", "data": {"ok": True}}


class AccountClientTest(unittest.TestCase):
    def setUp(self):
        self.metadata = {
            "global": {
                "nativeChainId": "33431",
                "contractAddress": "0x1ae109ea449cfe0bed08bfe8911e968a49a919b1",
            }
        }

    def test_set_margin_mode_signs_with_trading_key(self):
        fake = FakeAsyncClient()
        client = AccountClient(fake)
        params = SetMarginModeParams(contract_id="10000001", margin_mode="1")

        with patch("time.time", return_value=1718001234.0):
            result = asyncio.run(client.set_margin_mode(params, self.metadata))

        self.assertEqual(result, {"code": "SUCCESS", "data": {"ok": True}})
        sign_call = next(call for call in fake.calls if call[0] == "sign_trading")
        typed_data = sign_call[1]
        self.assertEqual(typed_data["primaryType"], "SetMarginPreferenceParams")
        self.assertEqual(typed_data["message"]["accountId"], "12345")
        self.assertEqual(typed_data["message"]["assetId"], "10000001")
        self.assertEqual(typed_data["message"]["marginMode"], 1)
        self.assertEqual(typed_data["message"]["nonce"], "123456")
        self.assertEqual(
            typed_data["message"]["signer"],
            "0xFCAd0B19bB29D4674531d6f115237E16AfCE377c",
        )

        request_call = fake.calls[-1]
        self.assertEqual(request_call[0], "POST")
        self.assertEqual(request_call[1], "/api/v2/private/account/setMarginMode")
        self.assertEqual(
            request_call[2],
            {
                "accountId": "12345",
                "contractId": "10000001",
                "marginMode": "1",
                "l2Nonce": "123456",
                "l2ExpireTime": "1719212400000",
                "signer": "0xFCAd0B19bB29D4674531d6f115237E16AfCE377c",
                "l2Signature": "11" * 65,
            },
        )

    def test_set_margin_mode_requires_trading_private_key(self):
        client = AccountClient(FakeAsyncClient(trading_private_key=""))
        params = SetMarginModeParams(contract_id="10000001", margin_mode="CROSS")

        with self.assertRaises(ValueError):
            asyncio.run(client.set_margin_mode(params, self.metadata))


if __name__ == "__main__":
    unittest.main()
