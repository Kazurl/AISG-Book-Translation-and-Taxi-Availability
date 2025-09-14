import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import traceback  # todo: remove when done

from app.book_translation import (
    cancel_translation_service,
    chunk_by_tokens,
    extract_book_info,
    fetch_translation_progress,
    fetch_last_user_job,
    translate_service
)
from app.file_management import read_file_in_local_storage, write_file_to_local_storage
from app.job_handler import (
    init_redis,
    check_job_status,
    create_job_id,
    JobCompletion,
    JobStatus
)
from app.rate_limiter import RateLimiter
from app.schema import CancelRequest, TranslateRequest

load_dotenv()

# REDIS CACHE & RATE LIMITER INIT
redis_port = os.getenv("REDIS_PORT")
API_RATE_LIMIT = 10
refill_rate = 60
redis_server = init_redis(redis_port)
rate_limiter = RateLimiter(API_RATE_LIMIT, refill_rate)

# FASTAPI INIT
app = FastAPI()
# middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# routes
@app.get("/")
async def root():
    """
        Health check endpoint.
    """
    return {"service": f"Translation Service is running!"}


from fastapi.responses import JSONResponse  # todo: remove when done
from fastapi.exceptions import RequestValidationError
from fastapi import Request

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
        Handles validation errors and returns a JSON response with error details.
    """
    print(f"\n[VALIDATION ERROR] {exc}\n")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )



@app.post("/translate_book")
async def translate_book(req: TranslateRequest, background_tasks: BackgroundTasks):
    """
        Initiates the book translation process. 
        If a translation job for the same book by the same user is already completed and cached, it returns the cached result.
        If a different job is in progress for the user, it returns a conflict error.
        Otherwise, it starts a new translation job in the background and returns the job status."""
    print("Received POST /translate_book")  # todo: remove when done
    print(f"[DEBUG] Received req: {req}")  # todo: remove when done

    try:
        if not req.book:
            raise HTTPException(status_code=400, detail="Empty input text.")
        
        chunks = chunk_by_tokens(req.book)
        print(f"[DEBUG] Full book: {repr(req.book)}")  # todo: remove when done
        print(f"[DEBUG] chunk[0]: {repr(chunks[0])}")  # todo: remove when done
        #print(f"[DEBUG] chunk lines = {chunks.splitlines()}")  # todo: remove when done


        book_info = await extract_book_info(chunks[0], req.language, rate_limiter)
        print(f"[DEBUG] Extracted book_info: {book_info.origin_title=}, {book_info.origin_author=}")  # todo: remove when done
        if (
            not book_info.origin_title or
            not book_info.origin_author or
            book_info.origin_title == "NA" or
            book_info.origin_author == "NA"
        ):
            raise HTTPException(status_code=400, detail="No book title and/or author")
        
        job_id = create_job_id(book_info.origin_title, book_info.origin_author)
        print(f"book_info: {book_info.origin_title}, job_id: {job_id}")  # todo: remove when done

        # Check ongoing job status and disk cache
        job_status = await check_job_status(redis_server, req.email, job_id)
        if job_status is None:
            pass
        elif job_status == JobStatus.SAME_JOB:
            attempted_translation = read_file_in_local_storage(
                                        book_info.origin_title,
                                        book_info.origin_author
                                    )
            if attempted_translation:
                return { "status": JobCompletion.DONE, "result": attempted_translation }
            else:
                pass
        elif job_status == JobStatus.DIFFERENT_JOB:
            raise HTTPException(status_code=409, detail="Another translation already in progress.")
        
        # Start translation in background
        success, translated = await translate_service(
            job_id,
            req.email,
            req.language,
            book_info,
            chunks,
            rate_limiter,
            redis_server
        )
        if not success:
            raise HTTPException(status_code=500, detail="Translation failed.")
        
        # print("[ENDPOINT] Task scheduled!")  # todo: remove when done
        # return {
        #     "status": JobCompletion.STARTED,
        #     "job_id": job_id,
        #     "message": "Translation started. Check /translation_progress"
        # }
        result = {  # todo: remove wben done
            "status": JobCompletion.DONE,
            "job_id": job_id,
            "result": translated,
            "origin_title": book_info.origin_title,
            "origin_author": book_info.origin_author,
        }
        print(result)  # todo: remove wben done
        return result

    except Exception as e:
        traceback.print_exc()  # todo: remove when done
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/translation_progress")
async def get_translation_progress(
    origin_title: str,
    origin_author: str
):
    """
        Fetches the progress of an ongoing translation job or the result if completed.
        If no job is found for the given book title and author, it returns a not found error.
    """
    try:
        # todo: Check if user has active job or old job as per requested
        
        # fetch chunks from redis and get progress
        job_id = create_job_id(origin_title, origin_author)
        res = await fetch_translation_progress(job_id, origin_title, origin_author, redis_server)
        if "error" in res:
            raise HTTPException(status_code=404, detail=res["error"])
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cancel_translation")
async def cancel_translation(req: CancelRequest):
    """
        Cancels an ongoing translation job for the given book title and author.
        If no such job is found, it returns a not found error.
    """
    try:
        job_id = create_job_id(req.origin_title, req.origin_author)
        await cancel_translation_service(job_id, req.email, redis_server)
        return { "status": JobCompletion.CANCELLED, "job_id": job_id }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/last_job")
async def last_job(email: str):
    """
        Fetches metadata of the last translation job for the given user email.
        If no job is found, it returns a not found error.
    """
    try:
        last_job = await fetch_last_user_job(email, redis_server)
        if not last_job:
            raise HTTPException(status_code=404, detail="No recent job for this email!")
        return last_job
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# @app.get("/")
# async def translate_book():
#     main_loc = Path(__file__).parent
#     path = main_loc / "test_texts/text2.txt"
#     email = "john123@email.com"
#     try:
#         with open(path, "r", encoding="utf-8") as f:
#             text = f.read()
#             chunks = chunk_by_tokens(text)
#             book_info = await extract_book_info(chunks[0], "chinese", rate_limiter)
#             job_id = create_job_id(book_info.origin_title, book_info.origin_author)

#             job_status = await check_job_status(redis_server, email, job_id)
#             if job_status is None:
#                 pass
#             elif job_status:
#                 attempted_translation = read_file_in_local_storage(
#                                             book_info.origin_title,
#                                             book_info.origin_author
#                                         )
#                 if attempted_translation:
#                     return attempted_translation
#                 else:
#                     return "Job is in progress."
#             else:
#                 raise HTTPException(status_code=409, detail="Another translation already in progress.")

#             success, translated = await translate_service(
#                                                                 job_id,
#                                                                 email,
#                                                                 "chinese",
#                                                                 book_info,
#                                                                 chunks,
#                                                                 rate_limiter,
#                                                                 redis_server
#                                                             )
        
#         return translated
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))