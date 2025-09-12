import asyncio
import time
import random
from book_translation import chunk_by_tokens, translate_chunk
from pathlib import Path

# Use your realistic input
main_loc = Path(__file__).parent
TEXT_FILE = main_loc / "text.txt"
LANGUAGE = "chinese"
MAX_TOKENS_LIST = [2000, 4000, 8000, 16000, 32000, 64000, 128000]
API_RATE_LIMIT = 10
REFILL_RATE = 60

# ------ MOCKING translate_chunk for TESTING ----------
async def mock_translate_chunk(chunk, language):
    # Simulate network/API latency based on chunk size (~linear for big models)
    sleep_time = 1.5 + 0.001 * len(chunk)
    await asyncio.sleep(sleep_time)  # your real translate_chunk here!
    return f"TRANSLATED: {chunk[:20]}..."

# ------ BENCHMARK RUNNER ----------

async def benchmark_chunk_size(text, language, max_tokens_list, real_run=False):
    results = []
    for max_tokens in max_tokens_list:
        print(f"Testing chunk size: {max_tokens}")
        chunks = chunk_by_tokens(text, max_tokens)
        print(f"Number of chunks: {len(chunks)}")

        translations = [None] * len(chunks)
        times = [0] * len(chunks)

        async def worker(i, chunk):
            start = time.monotonic()
            if real_run:
                translations[i] = await translate_chunk(chunk, language)
            else:
                translations[i] = await mock_translate_chunk(chunk, language)
            times[i] = time.monotonic() - start

        # Simple sliding window rate limiter
        batch = []
        start_time = time.monotonic()
        for i, chunk in enumerate(chunks):
            batch.append(worker(i, chunk))
            if len(batch) == API_RATE_LIMIT or i == len(chunks)-1:
                await asyncio.gather(*batch)
                batch = []
                if i+1 < len(chunks):
                    await asyncio.sleep(REFILL_RATE)  # Simulate rate limit window

        total_time = time.monotonic() - start_time
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        results.append({
            "max_tokens": max_tokens,
            "num_chunks": len(chunks),
            "total_time": total_time,
            "avg_chunk_time": avg_time,
            "max_chunk_time": max_time,
            "min_chunk_time": min_time,
        })
        print(f"Done size {max_tokens} | Total: {total_time:.2f}s, Avg per chunk: {avg_time:.2f}s")
    return results

# ------ SCRIPT ENTRY ----------

if __name__ == "__main__":
    with open(TEXT_FILE, "r", encoding="utf-8") as f:
        book_text = f.read()
    # Use excerpt for initial runs (to avoid excessive quota/cost)
    #book_text = book_text[:5000]
    results = asyncio.run(benchmark_chunk_size(
        book_text,
        LANGUAGE,
        MAX_TOKENS_LIST,
        real_run=False  # change to True for end-to-end
    ))
    print("\n===== SUMMARY =====")
    for res in results:
        print(res)
