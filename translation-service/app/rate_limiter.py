import asyncio
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_calls: int, refill_rate: int):
        self.max_calls = max_calls
        self.refill_rate = refill_rate
        self.calls = deque()
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.monotonic()
            # refill new API calls
            while self.calls and self.calls[0] + self.refill_rate > now:
                self.calls.popleft()
            if len(self.calls) < self.max_calls:
                self.calls.append(now)
                return
            
            # wait until next API call slot frees up
            wait_time = self.refill_rate - (now - self.calls[0])
        await asyncio.sleep(wait_time)
        await self.acquire()