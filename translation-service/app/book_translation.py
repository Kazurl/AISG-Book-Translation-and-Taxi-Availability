import asyncio
import os
from dotenv import load_dotenv
from openai import OpenAI
from rate_limiter import RateLimiter
from transformers import AutoTokenizer

from file_management import BookInfo, read_file_in_local_storage

load_dotenv()

SEALION_API_KEY = os.getenv("SEALION_API_KEY")
SEALION_API_URL = "https://api.sea-lion.ai/v1"
API_RATE_LIMIT = 10
refill_rate = 60
MAX_TOKENS = 2000

tokenizer = AutoTokenizer.from_pretrained("aisingapore/Gemma-SEA-LION-v4-27B-IT", trust_remote_code=True)

def chunk_by_tokens(text: str, max_tokens: int = MAX_TOKENS) -> list:
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


async def translate_chunk(chunk: str, language: str) -> str:
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


async def translate_service(book: str, language: str) -> list[bool, BookInfo, str]:
    # todo: check db if translated book exists
    # translated book exists in db, return immediately

    
    # translated book doesn't exist in db yet
    # todo: set job activate and initialise redis cache


    chunks = chunk_by_tokens(book)
    rate_limiter = RateLimiter(API_RATE_LIMIT, refill_rate)
    translations = [None] * len(chunks)
    book_info = await extract_book_info(chunks[0], language, rate_limiter)
    attempted_translation = read_file_in_local_storage(book_info.origin_title, book_info.origin_author)
    if attempted_translation:
        return [False, book_info, attempted_translation]

    async def worker(i: int, chunk: str) -> None:
        await rate_limiter.acquire()
        for _ in range(2):  # retry once
            try:
                translations[i] = await translate_chunk(chunk, language)
                break
            except Exception as e:
                await asyncio.sleep(7)
        else:
            translations[i] = "[TRANSLATION FAILED]"

    # process with rate-limiter
    await asyncio.gather(*[worker(i, chunk) for i, chunk in enumerate(chunks)])
    
    cleaned_translations = [t.strip() for t in translations]
    return [True, book_info, "\n\n".join(cleaned_translations)]


async def extract_book_info(chunk: str, language: str, rl: RateLimiter) -> BookInfo:
    await rl.acquire()
    res = BookInfo()

    for _ in range(2):
        try:
            book_info = await interpret_book_info(chunk, language)
            print(book_info)
            book_info = book_info.strip("[]").split(",")
            print(book_info)
            print(len(book_info))
            res.set_book_info(book_info)
            return res
        except Exception as e:
            await asyncio.sleep(7)

    return res