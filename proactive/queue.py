import asyncio


class ProactiveQueue:
    def __init__(self):
        self._queue: asyncio.Queue[str] = asyncio.Queue()

    async def put(self, message: str):
        await self._queue.put(message)

    def put_nowait(self, message: str):
        self._queue.put_nowait(message)

    async def get(self) -> str:
        return await self._queue.get()

    def get_nowait(self) -> str:
        return self._queue.get_nowait()

    def empty(self) -> bool:
        return self._queue.empty()

    def qsize(self) -> int:
        return self._queue.qsize()
