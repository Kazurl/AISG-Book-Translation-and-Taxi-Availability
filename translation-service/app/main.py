import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pathlib import Path
from pydantic import BaseModel
from typing import Optional

from book_translation import translate_service
from file_management import write_file_to_local_storage
from job_handler import init_redis
from rate_limiter import RateLimiter

load_dotenv()

redis_port = os.getenv("REDIS_PORT")
API_RATE_LIMIT = 10
refill_rate = 60

app = FastAPI()
redis_server = init_redis(redis_port)
rate_limiter = RateLimiter(API_RATE_LIMIT, refill_rate)

# schema
class TranslateRequest(BaseModel):
    book: str
    language: str
    email: str


class ProgressRequest(BaseModel):
    origin_title: str
    origin_author: str
    email: str
    language: str


class CancelRequest(BaseModel):
    book: str
    language: str
    email: str


# routes
@app.get("/")
async def root():
    return {"service": f"Translation Service is running!"}


@app.post("/translate_book")
async def translate_book(req: TranslateRequest, background_tasks: BackgroundTasks):
    try:
        if not req.book:
            raise HTTPException(status_code=400, detail="Empty input text.")
        book_info, translated = await translate_service(req.book, req.language)

        write_file_to_local_storage()
        return translated
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# todo: post job progress
@app.post("/cancel_translation")
async def cancel_translation():
    pass


# todo: post cancel job
@app.post("/translation_progress")
async def get_translation_progress():
    pass
    

@app.get("/")
async def translate_book():
    main_loc = Path(__file__).parent
    path = main_loc / "test_texts/text2.txt"
    email = "john@email.com"
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
            isNewTranslation, book_info, translated = await translate_service(
                                                                text,
                                                                "chinese",
                                                                email,
                                                                rate_limiter,
                                                                redis_server
                                                            )

        if isNewTranslation:
            write_file_to_local_storage(
                translated,
                book_info.origin_title,
                book_info.origin_author,
                book_info.trans_title,
                book_info.trans_author
            )
        
        return translated
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))