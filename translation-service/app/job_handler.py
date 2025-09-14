import hashlib
import redis.asyncio as redis
from enum import Enum

from utils.str_utils import canonize_str

class JobStatus(Enum):
    NO_JOB = 0
    SAME_JOB = 1
    DIFFERENT_JOB = -1


class JobCompletion(Enum):
    DONE = "DONE"
    RUNNING = "RUNNING"
    STARTED = "STARTED"
    CANCELLED = "CANCELLED"


def init_redis(port: int) -> redis.Redis:
    """
        Initializes and returns a Redis client connected to the specified port.
    """
    r = redis.Redis(host="localhost", port=port, db=0, decode_responses=True)
    return r

def create_job_id(
    origin_title: str,
    origin_author: str
) -> str:
    """
        Creates a unique job ID based on the book's original title and author.
        The ID is a SHA-256 hash of the canonicalized title and author, truncated to 32 characters.
    """
    canonical = (
        canonize_str(origin_title) + "|" +
        canonize_str(origin_author)
    )
    
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]


async def start_translation_job(
    server: redis.Redis,
    user_id: str,
    job_id: str,
    origin_title: str,
    origin_author: str,
    total_chunks: int
) -> bool:
    """
        Starts a translation job for the user if no other job is active.
        Sets up necessary Redis keys to track the job's progress and metadata.
        Returns True if the job was started successfully, False if another job is already active."""
    semaphore_key = f"user:{user_id}:active_job"

    # auto set only if job doesn't exist
    job_status = await check_job_status(server, user_id, job_id)
    if job_status == JobStatus.DIFFERENT_JOB:
        return False  # different job already running for user
    elif job_status == JobStatus.NO_JOB:
        await server.setnx(semaphore_key, job_id)
        await server.set(f"job:{job_id}:total_chunks", total_chunks)
        await server.hmset(f"job:{job_id}:meta", {
            "origin_title": origin_title,
            "origin_author": origin_author
        })
    return True


async def end_translation_job(server: redis.Redis, user_id: str, job_id: str) -> None:
    """
        Ends the translation job for the user by cleaning up Redis keys.
        Deletes the job chunks and releases the semaphore indicating no active job for the user.
    """
    semaphore_key =  f"user:{user_id}:active_job"
    await server.delete(f"job:{job_id}:chunks")
    await server.delete(semaphore_key)


async def check_user_allowed(server: redis.Redis, user_id: str) -> bool:
    """
        Checks if the user is allowed to start a new translation job.
        A user is allowed if they have no active job currently running.
        Returns True if allowed, False otherwise.
    """
    semaphore_key = f"user:{user_id}:active_job"
    if await server.exists(semaphore_key): return False
    return True


async def check_job_status(server: redis.Redis, user_id: str, job_id: str) -> JobStatus:
    """
        Checks the status of a translation job for the user.
        Returns JobStatus.NO_JOB if no job is active,
        JobStatus.SAME_JOB if the active job matches the given job_id,
        and JobStatus.DIFFERENT_JOB if a different job is active.
    """
    semaphore_key = f"user:{user_id}:active_job"
    current_job = await server.get(semaphore_key)
    if current_job is None:
        return JobStatus.NO_JOB
    elif current_job == job_id:
        return JobStatus.SAME_JOB
    else:
        return JobStatus.DIFFERENT_JOB
    

async def get_last_user_job(server: redis.Redis, user_id: str) -> dict:
    """
        Fetches metadata of the last translation job for the given user ID.
        If no job is found, it returns an error message.
    """
    job_id = await server.get(f"user:{user_id}:active_job")
    if job_id is None:
        return { "error": "No recent job for this email!" }
    metadata = await server.hgetall(f"job:{job_id}:meta")
    return { "job_id": job_id, **metadata }


async def update_translation_job_progress(
    server: redis.Redis,     
    job_id: str,
    chunk_no: int,
    translated_chunk: str,
    total_chunks: int
) -> str:
    """
        Updates the progress of a translation job by saving the translated chunk in Redis.
        Also updates the overall progress status in the format "completed_chunks/total_chunks".
        Returns the updated progress string.
    """
    completed_chunks = len(set(map(int, await server.hkeys(f"job:{job_id}:chunks"))))
    progress = f"{completed_chunks}/{total_chunks}"
    await server.hset(f"job:{job_id}:chunks", chunk_no, translated_chunk)
    await server.set(f"job:{job_id}:progress", progress)
    return progress


async def fetch_saved_chunks(server: redis.Redis, job_id: str) -> list[str]:
    """
        Fetches all saved translated chunks for the given job_id from Redis.
        Returns a list of translated chunks ordered by their chunk number.
    """
    chunks = await server.hgetall(f"job:{job_id}:chunks")
    keys = sorted(map(int, chunks.keys()))
    ordered_chunks = [chunks[str(k)] for k in keys]
    return ordered_chunks


async def complete_translation_job(server: redis.Redis, user_id: str, job_id: str) -> list[str]:
    """
        Completes the translation job by fetching all saved chunks and marking the job as finished.
        Cleans up Redis keys related to the job and releases the semaphore for the user.
        Returns the list of translated chunks.
    """
    translations = await fetch_saved_chunks(server, job_id)
    await server.set(f"job:{job_id}:status", "finished")
    await end_translation_job(server, user_id, job_id)
    return translations


async def cancel_translation_job(server: redis.Redis, user_id: str, job_id: str) -> None:
    """
        Cancels an ongoing translation job for the given job_id and user ID.
        Marks the job as cancelled in Redis and cleans up related keys.
    """
    await server.set(f"job:{job_id}:status", "cancelled")
    await end_translation_job(server, user_id, job_id)


async def get_todo_job_chunks(server: redis.Redis, job_id: str) -> set:
    """
        Fetches the indices of chunks that are yet to be translated for the given job_id.
        Returns a sorted list of chunk indices that are still pending translation.
    """
    total_chunks = await get_total_chunks(server, job_id)
    completed_indices = set(map(int, await server.hkeys(f"job:{job_id}:chunks")))
    all_indices = set(range(total_chunks))
    return sorted(all_indices-completed_indices)


async def get_total_chunks(server: redis.Redis, job_id: str) -> int:
    """
        Fetches the total number of chunks for the given job_id from Redis.
        Returns the total chunk count as an integer.
    """
    total_chunks = await server.get(f"job:{job_id}:total_chunks")
    return int(total_chunks) if total_chunks else 0