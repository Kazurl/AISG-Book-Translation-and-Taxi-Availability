import hashlib
import redis.asyncio as redis

from utils.str_utils import canonize_str

def init_redis(port: int):
    r = redis.Redis(host="localhost", port=port, db=0, decode_responses=True)
    return r

def create_job_id(
    origin_title: str,
    origin_author: str,
    trans_title: str,
    trans_author: str,
) -> hex:
    canonical = (
        canonize_str(origin_title) + "|" +
        canonize_str(origin_author) + "|" +
        canonize_str(trans_title) + "|" +
        canonize_str(trans_author)
    )
    
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]


async def start_translation_job(server, user_id: int, job_id: int) -> bool:
    semaphore_key = f"user: {user_id}:active_job"

    # auto set only if job doesn't exist
    success = await server.setnx(semaphore_key, job_id)
    if not success:
        return False  # job already running for user
    return True


async def end_translation_job(server, user_id: int, job_id: int) -> None:
    semaphore_key =  f"user: {user_id}:active_job"
    await server.delete(f"job:{job_id}:chunks")
    await server.delete(semaphore_key)


async def update_translation_job_progress(
    server,     
    job_id: int,
    chunk_no: int,
    translated_chunk: str,
    completed_chunks: int,
    total_chunks
) -> str:
    progress = f"{completed_chunks}/{total_chunks}"
    await server.hset(f"job: {job_id}:chunks", chunk_no, translated_chunk)
    await server.set(f"job: {job_id}:progress", progress)
    return progress

async def fetch_saved_chunks(server, job_id: int) -> list[str]:
    chunks = await server.hgetall(f"job:{job_id}:chunks")
    return chunks


async def complete_translation_job(server, user_id: int, job_id: int) -> list[str]:
    translations = await fetch_saved_chunks(job_id)
    await server.set(f"job:{job_id}:status", "finished")
    await end_translation_job(user_id, job_id)
    return translations


async def cancel_translation_job(server, user_id: int, job_id: int) -> None:
    await server.set(f"job:{job_id}:status", "cancelled")
    await end_translation_job(user_id, job_id)