from typing import Dict, Any

from ..internal.async_client import AsyncClient


class Client:
    def __init__(self, async_client: AsyncClient):
        self.async_client = async_client

    async def get_metadata(self) -> Dict[str, Any]:
        return await self.async_client.make_public_request(
            method="GET", path="/api/v2/public/meta/getMetaData")

    async def get_server_time(self) -> Dict[str, Any]:
        return await self.async_client.make_public_request(
            method="GET", path="/api/v2/public/meta/getServerTime")
