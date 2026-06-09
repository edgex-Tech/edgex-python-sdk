import asyncio
import json
import unittest

from edgex_sdk.client import Client
from edgex_sdk.internal.eip712 import build_typed_data_from_server_response
from edgex_sdk.unified_asset.client import (
    CreateSpotDepositParams,
    CreateWithdrawParams,
    ZERO_ADDRESS,
    apply_fee_to_attempt,
    build_spot_deposit_attempt,
    build_withdraw_attempt,
    profile_name_for_asset,
    resolve_withdraw_profile,
)


class FakeAsyncClient:
    def __init__(self):
        self.account_id = 12345
        self.wallet_private_key = "unused-by-fake-client"
        self.calls = []

    def get_account_id(self):
        return self.account_id

    def resolve_wallet_signer_address(self):
        return "0xFCAd0B19bB29D4674531d6f115237E16AfCE377c"

    def sign_typed_data_with_wallet_key(self, typed_data, include_0x=False):
        self.calls.append(("sign", typed_data, include_0x))
        return "0x" + "11" * 65 if include_0x else "11" * 65

    async def make_authenticated_request(self, method, path, data=None, params=None, rewrite_version=True):
        self.calls.append((method, path, data, params, rewrite_version))
        if path.endswith("/getFeeByAssetFlow"):
            return {"code": "SUCCESS", "data": {"fee": "10"}}
        if path.endswith("/getEIP712Data"):
            return {
                "code": "SUCCESS",
                "data": {
                    "types": {
                        "AssetFlowAttempt": {
                            "fields": [{"name": "amount", "type": "uint256"}]
                        }
                    },
                    "primaryType": "AssetFlowAttempt",
                    "domain": {"name": "EdgeX", "version": "1"},
                    "messageJson": json.dumps({"amount": "990"}),
                },
            }
        if path.endswith("/submitAssetFlow"):
            return {"code": "SUCCESS", "data": {"flowId": "1"}}
        if path.endswith("/getDepositData"):
            return {
                "code": "SUCCESS",
                "data": {
                    "chainId": 33431,
                    "to": "0x86245522276a9F845a65a591b485cd4AaA51D86c",
                    "data": "0x1234",
                    "value": "0",
                },
            }
        raise AssertionError(path)


class UnifiedAssetWithdrawTest(unittest.TestCase):
    def test_client_initializes_unified_asset_namespace(self):
        client = Client(base_url="https://example.com", account_id=12345)
        self.assertIsNotNone(client.unified_asset)

    def test_build_spot_withdraw_attempt_uses_raw_amount_and_zero_privy(self):
        attempt = build_withdraw_attempt(
            user_address="0xFCAd0B19bB29D4674531d6f115237E16AfCE377c",
            source="spot",
            source_account="12345",
            token_address="0x98d2919b9A214E6Fa5384AC81E6864bA686Ad74c",
            amount_raw="1000",
            chain_id=3343,
            expire_time=123456,
            client_withdraw_id="849849126827855872",
        )

        self.assertEqual(attempt["source"], "spot")
        self.assertEqual(attempt["sourceAccount"], "12345")
        self.assertEqual(attempt["amount"], "1000")
        self.assertEqual(attempt["fee"], "0")
        self.assertEqual(attempt["destination"], "chain-3343")
        self.assertEqual(attempt["destinationAccount"], attempt["userAddress"])
        self.assertEqual(attempt["privyAddress"], ZERO_ADDRESS)
        self.assertEqual(attempt["clientWithdrawId"], "849849126827855872")

    def test_perpv2_withdraw_attempt_reuses_unified_asset_source(self):
        attempt = build_withdraw_attempt(
            user_address="0xFCAd0B19bB29D4674531d6f115237E16AfCE377c",
            source="perpv2",
            source_account="67890",
            token_address="0x98d2919b9A214E6Fa5384AC81E6864bA686Ad74c",
            amount_raw="1000",
            chain_id=3343,
            expire_time=123456,
            client_withdraw_id="849849126827855872",
        )

        self.assertEqual(attempt["source"], "perpv2")
        self.assertEqual(attempt["sourceAccount"], "67890")
        self.assertEqual(attempt["destination"], "chain-3343")

    def test_build_spot_deposit_attempt_uses_chain_to_spot_direction(self):
        attempt = build_spot_deposit_attempt(
            user_address="0xFCAd0B19bB29D4674531d6f115237E16AfCE377c",
            privy_address=ZERO_ADDRESS,
            source_account="0xFCAd0B19bB29D4674531d6f115237E16AfCE377c",
            token_address="******************************************",
            amount_raw="1000",
            chain_id=33431,
            spot_account_id="12345",
        )

        self.assertEqual(attempt["source"], "chain-33431")
        self.assertEqual(attempt["sourceAccount"], attempt["userAddress"])
        self.assertEqual(attempt["tokenAddress"], "******************************************")
        self.assertEqual(attempt["amount"], "1000")
        self.assertEqual(attempt["fee"], "0")
        self.assertEqual(attempt["destination"], "spot")
        self.assertEqual(attempt["destinationAccount"], "12345")

    def test_apply_fee_to_attempt_subtracts_fee_from_gross_amount(self):
        attempt = {"amount": "1000", "fee": "0"}
        apply_fee_to_attempt(attempt, "10")
        self.assertEqual(attempt["amount"], "990")
        self.assertEqual(attempt["fee"], "10")

    def test_apply_fee_to_attempt_rejects_fee_not_less_than_amount(self):
        with self.assertRaises(ValueError):
            apply_fee_to_attempt({"amount": "1000", "fee": "0"}, "1000")

    def test_profile_resolution_supports_mm_assets(self):
        self.assertEqual(profile_name_for_asset("usdc", "mainnet"), "mainnet-usdc")
        profile = resolve_withdraw_profile("mainnet-usdc")
        self.assertEqual(profile["source"], "spot")
        self.assertEqual(profile["chain_id"], 3343)

    def test_build_typed_data_from_server_response_normalizes_fields(self):
        typed_data = build_typed_data_from_server_response(
            {
                "types": {
                    "AssetFlowAttempt": {
                        "fields": [{"name": "amount", "type": "uint256"}]
                    }
                },
                "primaryType": "AssetFlowAttempt",
                "domain": {"name": "EdgeX", "version": "1"},
                "messageJson": "{\"amount\":\"990\"}",
            }
        )

        self.assertIn("EIP712Domain", typed_data["types"])
        self.assertEqual(typed_data["primaryType"], "AssetFlowAttempt")
        self.assertEqual(typed_data["message"]["amount"], "990")
        self.assertNotIn("chainId", typed_data["domain"])

    def test_create_withdraw_uses_unified_asset_v1_paths_without_rewrite(self):
        fake = FakeAsyncClient()
        from edgex_sdk.unified_asset.client import Client as UnifiedAssetClient

        unified = UnifiedAssetClient(fake)
        result = asyncio.run(
            unified.create_withdraw(
                CreateWithdrawParams(
                    amount_raw="1000",
                    user_address="0xFCAd0B19bB29D4674531d6f115237E16AfCE377c",
                    token_address="0x98d2919b9A214E6Fa5384AC81E6864bA686Ad74c",
                    chain_id=3343,
                    client_withdraw_id="849849126827855872",
                    expire_time=123456,
                )
            )
        )

        paths = [call[1] for call in fake.calls if call[0] in {"GET", "POST"}]
        rewrite_flags = [call[4] for call in fake.calls if call[0] in {"GET", "POST"}]
        self.assertEqual(
            paths,
            [
                "/api/v1/private/unified-asset/getFeeByAssetFlow",
                "/api/v1/private/unified-asset/getEIP712Data",
                "/api/v1/private/unified-asset/submitAssetFlow",
            ],
        )
        self.assertEqual(rewrite_flags, [False, False, False])
        submit_body = fake.calls[-1][2]
        self.assertEqual(submit_body["attempt"]["fee"], "10")
        self.assertEqual(submit_body["attempt"]["amount"], "990")
        self.assertEqual(submit_body["userSignature"][:2], "0x")
        self.assertEqual(result["flowId"], "1")

    def test_get_spot_deposit_data_uses_deposit_path_without_signing(self):
        fake = FakeAsyncClient()
        from edgex_sdk.unified_asset.client import Client as UnifiedAssetClient

        unified = UnifiedAssetClient(fake)
        result = asyncio.run(
            unified.get_spot_deposit_data(
                CreateSpotDepositParams(
                    amount_raw="1000",
                    user_address="0xFCAd0B19bB29D4674531d6f115237E16AfCE377c",
                    token_address="******************************************",
                    chain_id=33431,
                    spot_account_id="12345",
                )
            )
        )

        request_calls = [call for call in fake.calls if call[0] in {"GET", "POST"}]
        self.assertEqual(len(request_calls), 1)
        method, path, body, params, rewrite_version = request_calls[0]
        self.assertEqual(method, "POST")
        self.assertEqual(path, "/api/v1/private/unified-asset/getDepositData")
        self.assertIsNone(params)
        self.assertFalse(rewrite_version)
        self.assertEqual(body["extraData"], "")
        self.assertEqual(body["attempt"]["source"], "chain-33431")
        self.assertEqual(body["attempt"]["sourceAccount"], body["attempt"]["userAddress"])
        self.assertEqual(body["attempt"]["destination"], "spot")
        self.assertEqual(body["attempt"]["destinationAccount"], "12345")
        self.assertEqual(result["chainId"], 33431)
        self.assertFalse(any(call[0] == "sign" for call in fake.calls))


if __name__ == "__main__":
    unittest.main()
