import hashlib
import redis.asyncio as redis
from enum import Enum

from utils.str_utils import canonize_str

class JobStatus(Enum):
    NO_JOB = 0
    SAME_JOB = 1
    DIFFERENT_JOB = -1


def init_redis(port: int) -> redis.Redis:
    r = redis.Redis(host="localhost", port=port, db=0, decode_responses=True)
    return r

def create_job_id(
    origin_title: str,
    origin_author: str
) -> str:
    canonical = (
        canonize_str(origin_title) + "|" +
        canonize_str(origin_author)
    )
    
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]


async def start_translation_job(server: redis.Redis, user_id: str, job_id: str) -> bool:
    semaphore_key = f"user:{user_id}:active_job"

    # auto set only if job doesn't exist
    job_status = await check_job_status(server, user_id, job_id)
    if job_status == JobStatus.DIFFERENT_JOB:
        return False  # different job already running for user
    elif job_status == JobStatus.NO_JOB:
        await server.setnx(semaphore_key, job_id)
    return True


async def end_translation_job(server: redis.Redis, user_id: str, job_id: str) -> None:
    semaphore_key =  f"user:{user_id}:active_job"
    await server.delete(f"job:{job_id}:chunks")
    await server.delete(semaphore_key)


async def check_job_status(server: redis.Redis, user_id: str, job_id: str) -> JobStatus:
    semaphore_key = f"user:{user_id}:active_job"
    current_job = await server.get(semaphore_key)
    if current_job is None:
        return JobStatus.NO_JOB
    elif current_job == job_id:
        return JobStatus.SAME_JOB
    else:
        return JobStatus.DIFFERENT_JOB


async def update_translation_job_progress(
    server: redis.Redis,     
    job_id: str,
    chunk_no: int,
    translated_chunk: str,
    total_chunks: int
) -> str:
    completed_chunks = len(set(map(int, await server.hkeys(f"job:{job_id}:chunks"))))
    progress = f"{completed_chunks}/{total_chunks}"
    await server.hset(f"job:{job_id}:chunks", chunk_no, translated_chunk)
    await server.set(f"job:{job_id}:progress", progress)
    return progress


async def fetch_saved_chunks(server: redis.Redis, job_id: str) -> dict:
    chunks = await server.hgetall(f"job:{job_id}:chunks")
    ordered_chunks = [chunks[str(i)] for i in range(len(chunks))]
    return ordered_chunks


async def complete_translation_job(server: redis.Redis, user_id: str, job_id: str) -> list[str]:
    translations = await fetch_saved_chunks(server, job_id)
    await server.set(f"job:{job_id}:status", "finished")
    await end_translation_job(server, user_id, job_id)
    return translations


async def cancel_translation_job(server: redis.Redis, user_id: str, job_id: str) -> None:
    await server.set(f"job:{job_id}:status", "cancelled")
    await end_translation_job(server, user_id, job_id)


async def get_todo_job_chunks(server: redis.Redis, job_id: str, total_chunks: int) -> set:
    completed_indices = set(map(int, await server.hkeys(f"job:{job_id}:chunks")))
    all_indices = set(range(total_chunks))
    return sorted(all_indices-completed_indices)