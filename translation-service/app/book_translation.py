import asyncio
import os
import re
import redis.asyncio as redis
import types
from dotenv import load_dotenv
from openai import OpenAI
from transformers import AutoTokenizer
from typing import Tuple

from app.file_management import (
    BookInfo,
    read_file_in_local_storage,
    write_file_to_local_storage
)
from app.job_handler import (
    cancel_translation_job,
    complete_translation_job,
    fetch_saved_chunks,
    get_last_user_job,
    get_todo_job_chunks,
    start_translation_job,
    update_translation_job_progress
)
from app.rate_limiter import RateLimiter

load_dotenv()

SEALION_API_KEY = os.getenv("SEALION_API_KEY")
SEALION_API_URL = os.getenv("SEALION_API_URL")
API_RATE_LIMIT = 10
refill_rate = 60
MAX_TOKENS = 2000

tokenizer = AutoTokenizer.from_pretrained("aisingapore/Gemma-SEA-LION-v4-27B-IT", trust_remote_code=True)

def chunk_by_tokens(text: str, max_tokens: int = MAX_TOKENS) -> list:
    """
        Splits the input text into chunks, each not exceeding max_tokens when tokenized.
        The splitting is done at paragraph boundaries to maintain coherence.
    """
    paragraphs = [p for p in text.split("\n\n") if p]
    chunks = []
    curr = ""
    for p in paragraphs:
        candidate = f"{curr}\n\n{p}" if curr else p
        if len(tokenizer.encode(candidate)) <= max_tokens:
            curr = candidate
        else:
            if curr:
                chunks.append(curr)
            curr = p
    
    if curr:
        chunks.append(curr)
    return chunks


async def interpret_book_info(chunk: str, language: str) -> str:
    """
        Uses the LLM to extract book title and author in both original and translated languages from the given text chunk.
        Returns a string in the format: [english book title, english book author, translated book title, translated book author]
    """
    client = OpenAI(
        api_key=SEALION_API_KEY,
        base_url=SEALION_API_URL
    )

    completion = client.chat.completions.create(
        model="aisingapore/Llama-SEA-LION-v3.5-70B-R",
        messages=[
            {
                "role": "user",
                "content": f"Read the text and translate the following text from english to {language}. ONLY return [english book title, english book author, translated book title, translated book author] in this exact format. If there are any missing fields, just leave it as NA. Text: {chunk}"
            }
        ],
        extra_body={
            "chat_template_kwargs": {
                "thinking_mode": "off"
            }
        },
    )
    return completion.choices[0].message.content


async def extract_book_info(chunk: str, language: str, rl: RateLimiter) -> BookInfo:
    """
        Extracts book information (title and author in both original and translated languages) from the given text chunk.
        Utilizes a rate limiter to control the frequency of API calls.
        Retries up to 2 times in case of failure."""
    await rl.acquire()
    res = BookInfo()

    for _ in range(2):
        try:
            book_info = await interpret_book_info(chunk, language)
            print(f"[RAW LLM OUTPUT]: {book_info}")  # todo: remove when done
            book_info = book_info.strip("[]").split(",")
            res.set_book_info(book_info)
            return res
        except Exception as e:
            await asyncio.sleep(7)

    return res


async def translate_chunk(chunk: str, language: str) -> str:
    """
        Translates the given text chunk into the specified language using the LLM.
        Returns the translated text.
    """
    client = OpenAI(
        api_key=SEALION_API_KEY,
        base_url=SEALION_API_URL
    )

    completion = client.chat.completions.create(
        model="aisingapore/Llama-SEA-LION-v3.5-70B-R",
        messages=[
            {
                "role": "user",
                "content": f"Translate the following text from english to {language}. Return ONLY the most accurate translation in ${language}, without any explanation, alternatives, or romanization. Text: {chunk}"
            }
        ],
        extra_body={
            "chat_template_kwargs": {
                "thinking_mode": "off"
            }
        },
    )
    return completion.choices[0].message.content


async def worker(
    job_id: str,
    chunk_idx: int,
    chunk: str,
    language: str,
    total_chunks: int,
    rate_limiter: RateLimiter,
    redis_server: redis.Redis
) -> None:
    """
        Worker function to translate a single chunk of text.
        Utilizes a rate limiter to control the frequency of API calls.
        Retries up to max_retries times in case of failure, with exponential backoff.
        Updates the translation job progress in Redis after successful translation.
    """
    await rate_limiter.acquire()
    max_retries = 5
    delay = 7
    for attempt in range(max_retries):  # retry once
        try:
            translation = await translate_chunk(chunk, language)
            await update_translation_job_progress(
                redis_server, job_id, chunk_idx, translation, total_chunks
            )
            return
        except Exception as e:
            await asyncio.sleep(delay * (2 ** attempt // 2))
    
    # After max_retries, log but don't crash; pick up again in next round
    print(f"Chunk {chunk_idx} failed after {max_retries} attempts.")


async def translate_service(
    job_id: str,
    email: str,
    language: str,
    book_info: BookInfo,
    chunks: list[str],
    rate_limiter: RateLimiter,
    redis_server: redis.Redis
) -> Tuple[bool, str]:
    """
        Main translation service function.
        Sets up the translation job, processes chunks with rate limiting, and handles job completion.
        Returns a tuple indicating success status and the full translated text."""
    print(f"[TRANSLATE_SERVICE] CALLED in sync mode, job_id={job_id}")
  # todo: remove when done
    # set job active and initialise redis cache
    try:
        print("[TRANSLATE_SERVICE] CWD:", os.getcwd())  # todo: remove when done
        if not await start_translation_job(
            redis_server, email, job_id, book_info.origin_title, book_info.origin_author, len(chunks)
        ):
            raise Exception("Ongoing job already in progress!")
        
        # process with rate-limiter
        for _ in range(10):
            remaining_chunk_indx = await get_todo_job_chunks(redis_server, job_id)
            if not remaining_chunk_indx:
                break
            await asyncio.gather(*[
                worker(job_id, i, chunks[i], language, len(chunks), rate_limiter, redis_server) for i in remaining_chunk_indx
            ])
            await asyncio.sleep(2)

        # return cleaned translations
        translations = await complete_translation_job(redis_server, email, job_id)
        cleaned_translations = [t.strip() for t in translations]
        full_book = "\n\n".join(cleaned_translations)
        print(f"[TRANSLATE_SERVICE] About to write: {book_info.origin_title}, {book_info.origin_author}")  # todo: remove logging when done

        print(f"[TRANSLATE_SERVICE] About to write file: {book_info.origin_title}, {book_info.origin_author}")  # todo: remove logging when done
        write_file_to_local_storage(
            full_book,
            book_info.origin_title,
            book_info.origin_author,
            book_info.trans_title,
            book_info.trans_author
        )
        print("[TRANSLATE_SERVICE] File written!")  # todo: remove logging when done
        
        return True, full_book
    except Exception as e:
        print(f"An error has occured in translate_service: {e}")
        return False, None
# async def translate_service(  # todo: remove when done testing
#     job_id, email, language, book_info, chunks, rate_limiter, redis_server
# ):
#     print(f"[TRANSLATE_SERVICE] CALLED")
#     print(f"[INPUT] Chunks: {chunks}")
#     print(f"[INPUT] Book info: {book_info}")
#     result = "test text"
#     from file_management import write_file_to_local_storage
#     write_file_to_local_storage(
#         result, book_info.origin_title, book_info.origin_author, book_info.trans_title, book_info.trans_author
#     )
#     print("[TRANSLATE_SERVICE] File write attempted")
#     return True, result



async def cancel_translation_service(
    job_id: str,
    email: str,
    redis_server: redis.Redis
) -> None:
    """
        Cancels an ongoing translation job for the given job_id and user email.
    """
    try:
        await cancel_translation_job(redis_server, email, job_id)
    except Exception as e:
        print(f"An error has occured in book_translation: {e}")


async def fetch_translation_progress(
    job_id: str,
    origin_title: str,
    origin_author: str,
    redis_server: redis.Redis
) -> dict:
    """
        Fetches the progress of an ongoing translation job or the result if completed.
        If no job is found for the given job_id, it returns an error message.
    """
    try:
        # get job status
        remaining_chunk_idx = await get_todo_job_chunks(redis_server, job_id)
        is_all_translated = len(remaining_chunk_idx) == 0
        res = {
            "running": not is_all_translated,
            "chunks_remaining": len(remaining_chunk_idx)
        }

        if is_all_translated:
            try:
                translated = read_file_in_local_storage(origin_title, origin_author)
                if not translated:
                    res["result"] = None
                    res["error"] = "Translation appears complete but no file found."
                else:
                    res["result"] = translated
            except Exception as e:
                res["result"] = None
                res["error"] = f"Translated book could not be loaded from storage: {str(e)}"
        return res
    except Exception as e:
        print(f"An error has occured in fetc_translation_progress: {e}")
        return { "error": e }
    

async def fetch_last_user_job(
    email: str,
    redis_server: redis.Redis
) -> dict | None:
    """
        Fetches metadata of the last translation job for the given user email.
        If no job is found, it returns a not found error.
    """
    try:
        last_job = await get_last_user_job(redis_server, email)
        if "error" in last_job:
            raise ValueError("This user had no past translation jobs.")
        
        job_id = last_job["job_id"]
        metadata = { k: v for k, v in last_job.items() if k != "job_id" }

        # try local file cache first
        book_text = None
        try:
            if "origin_title" in metadata and "origin_author" in metadata:
                book_text = read_file_in_local_storage(metadata["origin_title"], metadata["origin_author"])
        except Exception:
            pass

        # fallback to redis cache reconstruction
        if not book_text:
            translations = await fetch_saved_chunks(redis_server, job_id)
            cleaned_translations = [t.strip() for t in translations]
            full_book = "\n\n".join(cleaned_translations)

        return {
            "job_id": job_id,
            "metadata": metadata,
            "translated_book": full_book
        }
    except Exception as e:
        print(f"An error has occured in fetch_last_user_job: {e}")
        return None