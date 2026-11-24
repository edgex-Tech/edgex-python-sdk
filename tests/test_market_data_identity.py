"""
Member market-data identity: public market-data requests and the public
WebSocket handshake name the account when the client has full credentials.

The signatures are recorded from an independent HMAC-SHA256 (key =
base64("test-secret")) over timestamp + "GET" + path + sorted query.
"""

import asyncio
import base64
import json
import unittest
from unittest import mock

from edgex_sdk import Client
from edgex_sdk.internal.async_client import AsyncClient
from edgex_sdk.internal.auth import MARKET_DATA_IDENTITY_PATHS
from edgex_sdk.ws.client import Client as WsClient
from edgex_sdk.ws.manager import Manager

NOW = 1700000000.0
TIMESTAMP = "1700000000000"
# GET /api/v2/public/quote/getDepth, accountId=42&contractId=10000001&level=15
DEPTH_SIGNATURE = "66a9037e65c02d8b5cc2c65006ada384a8509d0854d29e6b0ab8a2ec640511b5"
# GET /api/v2/public/quote/getMarketStatus, accountId=42
MARKET_STATUS_SIGNATURE = "e847caa79cab8d46e23e5fa921441e08ee4a5055e762f86184962dcbea8b6780"
# GET /api/v1/public/ws, accountId=42&timestamp=1700000000000
PUBLIC_WS_SIGNATURE = "fefae46abb70c5e69968f56b9b5ac83155d12f049a28beb826dd53f6267d2615"

CREDENTIALS = dict(api_key="test-api-key", api_passphrase="test-passphrase", api_secret="test-secret")
IDENTITY_HEADERS = ("X-edgeX-Api-Key", "X-edgeX-Passphrase", "X-edgeX-Signature", "X-edgeX-Timestamp")


class FakeResponse:
    status = 200

    async def json(self):
        return {"code": "SUCCESS", "data": []}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class FakeSession:
    closed = False

    def __init__(self):
        self.calls = []

    def request(self, **kwargs):
        self.calls.append(kwargs)
        return FakeResponse()


def send(client: AsyncClient, path: str, params=None) -> dict:
    """Send one public GET through `client` and return what reached the session."""
    session = FakeSession()
    client._session = session
    with mock.patch("edgex_sdk.internal.async_client.time.time", return_value=NOW):
        asyncio.run(client.make_public_request("GET", path, params))
    return session.calls[-1]


class HttpIdentityTest(unittest.TestCase):
    def test_depth_is_signed_like_a_private_request(self):
        client = Client(base_url="https://example.invalid", account_id=42, **CREDENTIALS)
        session = FakeSession()
        client.async_client._session = session

        from edgex_sdk.quote.client import GetOrderBookDepthParams
        with mock.patch("edgex_sdk.internal.async_client.time.time", return_value=NOW):
            asyncio.run(client.quote.get_order_book_depth(GetOrderBookDepthParams("10000001", 15)))

        call = session.calls[-1]
        self.assertEqual(call["url"], "https://example.invalid/api/v2/public/quote/getDepth")
        self.assertEqual(call["params"], {"contractId": "10000001", "level": "15", "accountId": "42"})
        self.assertEqual(call["headers"], {
            "X-edgeX-Api-Key": "test-api-key",
            "X-edgeX-Passphrase": "test-passphrase",
            "X-edgeX-Signature": DEPTH_SIGNATURE,
            "X-edgeX-Timestamp": TIMESTAMP,
        })

    def test_request_without_parameters_signs_the_account_alone(self):
        client = AsyncClient(base_url="https://example.invalid", account_id=42, **CREDENTIALS)

        call = send(client, "/api/v2/public/quote/getMarketStatus", {})

        self.assertEqual(call["params"], {"accountId": "42"})
        self.assertEqual(call["headers"]["X-edgeX-Signature"], MARKET_STATUS_SIGNATURE)

    def test_configured_account_replaces_a_caller_supplied_one(self):
        client = AsyncClient(base_url="https://example.invalid", account_id=42, **CREDENTIALS)
        params = {"contractId": "10000001", "level": "15", "accountId": "7"}

        call = send(client, "/api/v2/public/quote/getDepth", params)

        self.assertEqual(call["params"]["accountId"], "42")
        self.assertEqual(call["headers"]["X-edgeX-Signature"], DEPTH_SIGNATURE)
        self.assertEqual(params["accountId"], "7", "the caller's dict is not modified")

    def test_every_mapped_route_and_nothing_else(self):
        client = AsyncClient(base_url="https://example.invalid", account_id=42, **CREDENTIALS)

        self.assertEqual(MARKET_DATA_IDENTITY_PATHS, {
            "/api/v2/public/quote/getTicker",
            "/api/v2/public/quote/getDepth",
            "/api/v2/public/quote/getKline",
            "/api/v2/public/quote/getMultiContractKline",
            "/api/v2/public/quote/getMultiDayKline",
            "/api/v2/public/quote/getAccurateOpenInterest",
            "/api/v2/public/quote/getMarketStatus",
            "/api/v2/public/funding/getLatestFundingRate",
            "/api/v2/public/funding/getFundingRatePage",
            "/api/v2/public/index/getIndexPriceConfig",
            "/api/v2/public/index/getMarketTradingSchedule",
        })
        for path in MARKET_DATA_IDENTITY_PATHS:
            call = send(client, path, {"contractId": "10000001"})
            self.assertEqual(call["params"]["accountId"], "42", path)
            self.assertEqual(set(call["headers"]), set(IDENTITY_HEADERS), path)

        for path in (
            "/api/v2/public/meta/getMetaData",
            "/api/v2/public/meta/getServerTime",
            "/api/v2/public/quote/getExchangeLongShortRatio",
            "/api/v2/public/quote/getTicketSummary",
        ):
            call = send(client, path, {"contractId": "10000001"})
            self.assertEqual(call["params"], {"contractId": "10000001"}, path)
            self.assertIsNone(call["headers"], path)

    def test_anonymous_without_full_identity(self):
        cases = {
            "no credentials": dict(account_id=0),
            "account only": dict(account_id=42),
            "no account": dict(account_id=0, **CREDENTIALS),
            "incomplete key": dict(account_id=42, **{**CREDENTIALS, "api_secret": ""}),
            "identity disabled": dict(account_id=42, market_data_identity=False, **CREDENTIALS),
        }
        for name, config in cases.items():
            with self.subTest(name):
                client = AsyncClient(base_url="https://example.invalid", **config)

                call = send(client, "/api/v2/public/quote/getDepth", {"contractId": "10000001", "level": "15"})

                self.assertEqual(call["params"], {"contractId": "10000001", "level": "15"})
                self.assertIsNone(call["headers"])


class PublicWsIdentityTest(unittest.TestCase):
    def connect(self, client: WsClient) -> mock.Mock:
        """Run the handshake with the socket and the reader threads stubbed out."""
        with mock.patch("edgex_sdk.ws.client.websocket.create_connection") as create, \
                mock.patch("edgex_sdk.ws.client.threading.Thread"), \
                mock.patch("edgex_sdk.ws.client.time.time", return_value=NOW):
            client.connect()
        return create

    def test_handshake_carries_the_signed_account(self):
        manager = Manager(base_url="wss://example.invalid", account_id=42, **CREDENTIALS)

        create = self.connect(manager.get_public_client())

        (url,), kwargs = create.call_args
        expected = {
            "X-edgeX-Api-Key": "test-api-key",
            "X-edgeX-Passphrase": "test-passphrase",
            "X-edgeX-Signature": PUBLIC_WS_SIGNATURE,
            "X-edgeX-Timestamp": TIMESTAMP,
        }
        self.assertEqual(url, f"wss://example.invalid/api/v1/public/ws?accountId=42&timestamp={TIMESTAMP}")
        self.assertEqual(kwargs["header"], expected)
        (protocol,) = kwargs["subprotocols"]
        self.assertNotIn("=", protocol)
        decoded = json.loads(base64.b64decode(protocol + "=" * (-len(protocol) % 4)))
        self.assertEqual(decoded, expected)

    def test_identified_public_connection_can_still_subscribe(self):
        client = Manager(base_url="wss://example.invalid", account_id=42, **CREDENTIALS).get_public_client()
        self.assertFalse(client.is_private)
        client.conn = mock.Mock()

        self.assertTrue(client.subscribe("depth.10000001.15"))

    def test_anonymous_without_full_identity(self):
        cases = {
            "no credentials": dict(account_id=42),
            "no account": dict(account_id=0, **CREDENTIALS),
            "incomplete key": dict(account_id=42, **{**CREDENTIALS, "api_passphrase": ""}),
            "identity disabled": dict(account_id=42, market_data_identity=False, **CREDENTIALS),
        }
        for name, config in cases.items():
            with self.subTest(name):
                manager = Manager(base_url="wss://example.invalid", **config)

                create = self.connect(manager.get_public_client())

                (url,), kwargs = create.call_args
                self.assertEqual(url, f"wss://example.invalid/api/v1/public/ws?timestamp={TIMESTAMP}")
                self.assertEqual(kwargs, {"header": {}})


if __name__ == "__main__":
    unittest.main()
