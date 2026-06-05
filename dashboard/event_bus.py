import asyncio
import threading
import uuid
from collections import deque


_RING_SIZE = 20
_FLUSH_INTERVAL = 0.1


class DashboardEventBus:

    def __init__(self):
        self._loop = None
        self._subscribers: dict[str, asyncio.Queue] = {}
        self._ring: deque[dict] = deque(maxlen=_RING_SIZE)
        self._lock = threading.Lock()

    def _get_loop(self):
        if self._loop is None:
            self._loop = asyncio.get_event_loop()
        return self._loop

    def subscribe(self):
        sid = uuid.uuid4().hex
        q: asyncio.Queue = asyncio.Queue()
        with self._lock:
            self._subscribers[sid] = q
        for event in list(self._ring):
            q.put_nowait(event)
        return sid, q

    def unsubscribe(self, sid: str):
        with self._lock:
            q = self._subscribers.pop(sid, None)
        if q is not None:
            while not q.empty():
                q.get_nowait()

    def publish(self, event: dict):
        with self._lock:
            self._ring.append(event)
            subs = dict(self._subscribers)
        loop = self._get_loop()
        for sid, q in subs.items():
            try:
                loop.call_soon_threadsafe(q.put_nowait, event)
            except Exception:
                pass
