import logging
from typing import Optional, Callable

from ..internal.auth import DEFAULT_HEADER_KEY
from .client import Client


class Manager:
    def __init__(
        self,
        base_url: str,
        account_id: int,
        api_key: str = "",
        api_passphrase: str = "",
        api_secret: str = "",
        auth_header_key: str = DEFAULT_HEADER_KEY,
        private_ws_path: str = "",
    ):
        self.base_url = base_url
        self.account_id = account_id
        self.api_key = api_key
        self.api_passphrase = api_passphrase
        self.api_secret = api_secret
        self.auth_header_key = auth_header_key
        self.private_ws_path = private_ws_path or "/api/v1/private/ws"

        self.public_client: Optional[Client] = None
        self.private_client: Optional[Client] = None
        self.logger = logging.getLogger(__name__)

    def get_public_client(self) -> Client:
        if not self.public_client:
            self.public_client = Client(
                url=f"{self.base_url}/api/v1/public/ws",
                is_private=False,
                account_id=self.account_id,
            )
        return self.public_client

    def get_private_client(self) -> Client:
        if not self.private_client:
            self.private_client = Client(
                url=f"{self.base_url}{self.private_ws_path}?accountId={self.account_id}",
                is_private=True,
                account_id=self.account_id,
                api_key=self.api_key,
                api_passphrase=self.api_passphrase,
                api_secret=self.api_secret,
                auth_header_key=self.auth_header_key,
                request_uri=self.private_ws_path,
            )
        return self.private_client

    def connect_public(self):
        self.get_public_client().connect()

    def connect_private(self):
        self.get_private_client().connect()

    def disconnect_public(self):
        if self.public_client:
            self.public_client.close()

    def disconnect_private(self):
        if self.private_client:
            self.private_client.close()

    def disconnect_all(self):
        self.disconnect_public()
        self.disconnect_private()

    def subscribe_ticker(self, contract_id: str, handler: Callable[[str], None]):
        client = self.get_public_client()
        client.on_message("ticker", handler)
        client.subscribe(f"ticker.{contract_id}")

    def subscribe_kline(self, contract_id: str, interval: str, handler: Callable[[str], None]):
        client = self.get_public_client()
        client.on_message("kline", handler)
        client.subscribe(f"kline.{contract_id}.{interval}")

    def subscribe_depth(self, contract_id: str, handler: Callable[[str], None]):
        client = self.get_public_client()
        client.on_message("depth", handler)
        client.subscribe(f"depth.{contract_id}")

    def subscribe_trade(self, contract_id: str, handler: Callable[[str], None]):
        client = self.get_public_client()
        client.on_message("trade", handler)
        client.subscribe(f"trade.{contract_id}")

    def subscribe_account_update(self, handler: Callable[[str], None]):
        self.get_private_client().on_message("account", handler)

    def subscribe_order_update(self, handler: Callable[[str], None]):
        self.get_private_client().on_message("order", handler)

    def subscribe_position_update(self, handler: Callable[[str], None]):
        self.get_private_client().on_message("position", handler)
