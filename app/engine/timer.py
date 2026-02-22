import asyncio
import time
from typing import Callable, Awaitable


class SessionTimer:
    """Manages per-session tick loop for timer updates and AI logic."""

    def __init__(self, room_code: str, tick_callback: Callable[..., Awaitable]):
        self.room_code = room_code
        self.tick_callback = tick_callback
        self._task: asyncio.Task | None = None
        self._running = False

    def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._tick_loop())

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    async def _tick_loop(self):
        """Run tick every 10 seconds."""
        while self._running:
            try:
                await self.tick_callback(self.room_code)
            except Exception as e:
                print(f"[Timer] tick error for {self.room_code}: {e}")
            await asyncio.sleep(10)
