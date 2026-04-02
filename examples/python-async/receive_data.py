import asyncio
import sys

from dora import Node


async def dummy_ticker():
    while True:
        await asyncio.sleep(0.01)

async def main():
    if sys.platform == "win32":
        asyncio.create_task(dummy_ticker())

    node = Node()
    for _ in range(50):
        event = await node.recv_async()
        if event["type"] == "STOP":
            break
        del event
    print("done!")


if __name__ == "__main__":
    asyncio.run(main())
