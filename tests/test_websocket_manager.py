import json
import unittest

from edgex_sdk.ws.client import Client as WsClient
from edgex_sdk.ws.manager import Manager


class DummyPublicClient:
    def __init__(self):
        self.handlers = {}
        self.subscriptions = []

    def on_message(self, msg_type, handler):
        self.handlers[msg_type] = handler

    def subscribe(self, topic, params=None):
        self.subscriptions.append((topic, params))


class WebSocketManagerTest(unittest.TestCase):
    def test_public_topics_match_gateway(self):
        manager = Manager(base_url="wss://example", account_id=123)
        dummy = DummyPublicClient()
        manager.public_client = dummy

        manager.subscribe_kline("10000001", "MINUTE_1", lambda _: None)
        manager.subscribe_depth("10000001", lambda _: None)
        manager.subscribe_trade("10000001", lambda _: None)

        self.assertEqual(
            dummy.subscriptions,
            [
                ("kline.LAST_PRICE.10000001.MINUTE_1", None),
                ("depth.10000001.200", None),
                ("trades.10000001", None),
            ],
        )
        self.assertIn("kline", dummy.handlers)
        self.assertIn("depth", dummy.handlers)
        self.assertIn("trades", dummy.handlers)


class PrivateWsDispatchTest(unittest.TestCase):
    def setUp(self):
        self.client = WsClient("wss://example", True, 123)
        self.account_messages = []
        self.order_messages = []
        self.position_messages = []
        self.trade_event_messages = []

    def test_trade_event_dispatches_group_handlers(self):
        self.client.on_message("account", self.account_messages.append)
        self.client.on_message("order", self.order_messages.append)
        self.client.on_message("position", self.position_messages.append)
        self.client.on_message("trade-event", self.trade_event_messages.append)

        message = json.dumps(
            {
                "type": "trade-event",
                "content": {
                    "event": "Snapshot",
                    "data": {
                        "account": [{"id": "1"}],
                        "order": [{"id": "2"}],
                        "position": [{"id": "3"}],
                    },
                },
            }
        )

        self.client._dispatch_private_trade_event(message, json.loads(message))
        self.client.handlers["trade-event"](message)

        self.assertEqual(self.account_messages, [message])
        self.assertEqual(self.order_messages, [message])
        self.assertEqual(self.position_messages, [message])
        self.assertEqual(self.trade_event_messages, [message])


if __name__ == "__main__":
    unittest.main()
