import datetime
import asyncio

from ipyc import AsyncIPyCHost, AsyncIPyCLink

host = AsyncIPyCHost()

@host.on_connect
async def on_client_connect(connection: AsyncIPyCLink):
    while connection.is_active():
        message = await connection.receive()
        if message:
            print(f"[{datetime.datetime.now()}] - Client says: {message}")
            await connection.send('Message received.')
    print(f"[{datetime.datetime.now()}] - Connection was closed!")

host.run()
