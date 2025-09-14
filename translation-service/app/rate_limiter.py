import asyncio
import time
from collections import deque

class RateLimiter:
    """
        A simple rate limiter that allows a maximum number of calls within a specified time frame.
        Uses asyncio for asynchronous operation.
    """
    def __init__(self, max_calls: int, refill_rate: int):
        self.max_calls = max_calls
        self.refill_rate = refill_rate
        self.calls = deque()
        self.lock = asyncio.Lock()

    async def acquire(self):
        """
            Acquires a slot for making an API call.
            If the rate limit is reached, it waits until a slot is available.
        """
        async with self.lock:
            now = time.monotonic()
            # refill new API calls
            while self.calls and self.calls[0] + self.refill_rate <= now:
                self.calls.popleft()
            if len(self.calls) < self.max_calls:
                self.calls.append(now)
                return
            
            # wait until next API call slot frees up
            wait_time = max(self.refill_rate - (now - self.calls[0]), 0)
        await asyncio.sleep(wait_time)
        await self.acquire()