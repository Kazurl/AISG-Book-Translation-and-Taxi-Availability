import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pathlib import Path
from pydantic import BaseModel

from book_translation import translate_service
from file_management import write_file_to_local_storage
from job_handler import init_redis

load_dotenv()

redis_port = os.getenv("REDIS_PORT")

app = FastAPI()
redis_server = init_redis(redis_port)

class TranslateRequest(BaseModel):
    book: str
    language: str

@app.post("/translate_book")
async def translate_book(req: TranslateRequest):
    main_loc = Path(__file__).parent
    translated_text_loc = main_loc / "translated_story.txt"
    try:
        book_info, translated = await translate_service(req.book, req.language)

        write_file_to_local_storage()
        return translated
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/")
async def translate_book():
    main_loc = Path(__file__).parent
    path = main_loc / "text2.txt"
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
            isNewTranslation, book_info, translated = await translate_service(text, "chinese")

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