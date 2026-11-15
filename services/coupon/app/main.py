import asyncio
import signal

from app.api.server import start_grpc_server
from app.core.config import Settings
from app.di import create_container


async def serve() -> None:
    container = create_container()
    settings = await container.get(Settings)
    server = await start_grpc_server(container, settings.grpc_port)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)
    await stop.wait()
    await server.stop(grace=5)
    await container.close()


if __name__ == "__main__":
    asyncio.run(serve())
