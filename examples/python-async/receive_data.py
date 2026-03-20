import asyncio
import sys

from dora import Node


async def main():
    node = Node()
    for _ in range(50):
        event = await node.recv_async()
        if event["type"] == "STOP":
            break
        del event
    print("done!")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
