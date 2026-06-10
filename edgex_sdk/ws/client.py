import base64
import json
import logging
import threading
import time
from typing import Dict, Any, Optional, Callable

import websocket

from ..internal.auth import build_hmac_signature, DEFAULT_HEADER_KEY


class Client:
    def __init__(
        self,
        url: str,
        is_private: bool,
        account_id: int,
        api_key: str = "",
        api_passphrase: str = "",
        api_secret: str = "",
        auth_header_key: str = DEFAULT_HEADER_KEY,
        request_uri: str = "",
    ):
        self.url = url
        self.is_private = is_private
        self.account_id = account_id
        self.api_key = api_key
        self.api_passphrase = api_passphrase
        self.api_secret = api_secret
        self.auth_header_key = auth_header_key
        self.request_uri = request_uri

        self.conn = None
        self.handlers: Dict[str, Callable[[str], None]] = {}
        self.done = threading.Event()
        self.ping_thread = None
        self.subscriptions: set = set()
        self.on_connect_hooks: list = []
        self.on_message_hooks: list = []
        self.on_disconnect_hooks: list = []
        self.logger = logging.getLogger(__name__)

    def connect(self):
        headers = {}
        url = self.url
        timestamp = str(int(time.time() * 1000))

        if self.is_private:
            request_uri = self.request_uri
            if not request_uri:
                from urllib.parse import urlparse
                parsed = urlparse(self.url)
                request_uri = parsed.path or "/api/v1/private/ws"

            body_str = f"accountId={self.account_id}&timestamp={timestamp}"
            signature = build_hmac_signature(
                self.api_secret, timestamp, "GET", request_uri, body_str)

            auth_headers = {
                f"X-{self.auth_header_key}-Api-Key": self.api_key,
                f"X-{self.auth_header_key}-Passphrase": self.api_passphrase,
                f"X-{self.auth_header_key}-Signature": signature,
                f"X-{self.auth_header_key}-Timestamp": timestamp,
            }
            headers.update(auth_headers)

            # Also encode as subprotocol for browser compatibility
            protocol_str = base64.b64encode(json.dumps(auth_headers).encode()).decode().rstrip("=")

            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}accountId={self.account_id}&timestamp={timestamp}"

            try:
                self.conn = websocket.create_connection(url, header=headers, subprotocols=[protocol_str])
            except Exception as e:
                raise ValueError(f"failed to connect to WebSocket: {str(e)}")
        else:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}timestamp={timestamp}"
            try:
                self.conn = websocket.create_connection(url, header=headers)
            except Exception as e:
                raise ValueError(f"failed to connect to WebSocket: {str(e)}")

        self.done.clear()
        self.ping_thread = threading.Thread(target=self._ping_loop, daemon=True)
        self.ping_thread.start()
        self.message_thread = threading.Thread(target=self._handle_messages, daemon=True)
        self.message_thread.start()

        for hook in self.on_connect_hooks:
            hook()

    def close(self):
        self.done.set()
        if self.conn:
            self.conn.close()
            self.conn = None

    def _ping_loop(self):
        while not self.done.is_set():
            if self.conn:
                try:
                    self.conn.send(json.dumps({"type": "ping", "time": str(int(time.time() * 1000))}))
                except Exception as e:
                    self.logger.error(f"Failed to send ping: {e}")
                    break
            self.done.wait(30)

    def _handle_messages(self):
        while not self.done.is_set():
            if not self.conn:
                break
            try:
                message = self.conn.recv()
                for hook in self.on_message_hooks:
                    hook(message)
                try:
                    msg = json.loads(message)
                except json.JSONDecodeError:
                    continue

                if msg.get("type") == "ping":
                    self._handle_pong(msg.get("time", ""))
                    continue

                if msg.get("type") == "quote-event":
                    channel = msg.get("channel", "")
                    channel_type = channel.split(".")[0] if "." in channel else channel
                    if channel_type in self.handlers:
                        self.handlers[channel_type](message)
                    continue

                msg_type = msg.get("type", "")
                if msg_type in self.handlers:
                    self.handlers[msg_type](message)

                if msg_type == "trade-event":
                    self._dispatch_private_trade_event(message, msg)

            except Exception as e:
                if self.done.is_set() or self.conn is None:
                    self.logger.debug(f"WebSocket receive loop stopped during shutdown: {e}")
                    break
                self.logger.error(f"Error handling message: {e}")
                for hook in self.on_disconnect_hooks:
                    hook(e)
                break

    def _dispatch_private_trade_event(self, message: str, msg: Dict[str, Any]):
        content = msg.get("content")
        if not isinstance(content, dict):
            return

        data = content.get("data")
        if not isinstance(data, dict):
            return

        for group in (
            "account",
            "collateral",
            "collateralTransaction",
            "position",
            "positionTransaction",
            "deposit",
            "withdraw",
            "transferIn",
            "transferOut",
            "order",
            "orderFillTransaction",
        ):
            payload = data.get(group)
            if payload is None:
                continue
            if isinstance(payload, list) and not payload:
                continue
            handler = self.handlers.get(group)
            if handler:
                handler(message)

    def _handle_pong(self, timestamp: str):
        try:
            self.conn.send(json.dumps({"type": "pong", "time": timestamp}))
        except Exception as e:
            self.logger.error(f"Failed to send pong: {e}")

    def subscribe(self, topic: str, params: Dict[str, Any] = None) -> bool:
        if self.is_private:
            raise ValueError("cannot subscribe on private WebSocket connection")
        if not self.conn:
            raise ValueError("WebSocket connection is not established")
        sub_msg = {"type": "subscribe", "channel": topic}
        if params:
            sub_msg.update(params)
        self.conn.send(json.dumps(sub_msg))
        self.subscriptions.add(topic)
        return True

    def unsubscribe(self, topic: str) -> bool:
        if self.is_private:
            raise ValueError("cannot unsubscribe on private WebSocket connection")
        if not self.conn:
            raise ValueError("WebSocket connection is not established")
        self.conn.send(json.dumps({"type": "unsubscribe", "channel": topic}))
        self.subscriptions.discard(topic)
        return True

    def on_message(self, msg_type: str, handler: Callable[[str], None]):
        self.handlers[msg_type] = handler

    def on_message_hook(self, hook: Callable[[str], None]):
        self.on_message_hooks.append(hook)

    def on_connect(self, hook: Callable[[], None]):
        self.on_connect_hooks.append(hook)

    def on_disconnect(self, hook: Callable[[Exception], None]):
        self.on_disconnect_hooks.append(hook)
