from pydantic import BaseModel

class TranslateRequest(BaseModel):
    book: str
    language: str
    email: str


class CancelRequest(BaseModel):
    origin_title: str
    origin_author: str
    email: str