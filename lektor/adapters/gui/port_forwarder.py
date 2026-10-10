"""
lektor.adapters.gui.port_forwarder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Lightweight TCP forwarder redirecting port 80 traffic to GUI port 7860.
"""

import asyncio
import sys


async def _pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        while True:
            data = await reader.read(65536)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except (asyncio.CancelledError, ConnectionResetError, BrokenPipeError):
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def _handle_client(client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter) -> None:
    try:
        target_reader, target_writer = await asyncio.open_connection("127.0.0.1", 7860)
    except Exception:
        client_writer.close()
        return

    try:
        await asyncio.gather(
            _pipe(client_reader, target_writer),
            _pipe(target_reader, client_writer),
            return_exceptions=True,
        )
    finally:
        try:
            client_writer.close()
        except Exception:
            pass


async def main() -> None:
    server = await asyncio.start_server(_handle_client, "0.0.0.0", 80)
    print("Port 80 -> 7860 forwarder aktywny na 0.0.0.0:80")
    sys.stdout.flush()
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
