from ipyc import AsyncIPyCClient, AsyncIPyCLink

class IPyCMixin():
    ipyc_client: AsyncIPyCClient
    ipyc_connection: AsyncIPyCLink

    async def client_setup(self):
        await super().client_setup() # type: ignore
        self.ipyc_client = AsyncIPyCClient()
        self.ipyc_connection = await self.ipyc_client.connect()
