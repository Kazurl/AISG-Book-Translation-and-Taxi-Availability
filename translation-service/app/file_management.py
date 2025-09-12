import os
import re
import time
from pathlib import Path

TRANSLATED_BOOK_CACHE = "translated_books_cache"

class BookInfo:
    def __init__(self) -> None:
        self.origin_title = "NA"
        self.origin_author = "NA"
        self.trans_title = "NA"
        self.trans_author = "NA"
    
    def get_book_info(self) -> dict:
        res = {
            "origin_title": self.origin_title,
            "origin_author": self.origin_author,
            "trans_title": self.trans_title,
            "trans_author": self.trans_author
        }
        return res
    
    def set_book_info(self, fields: list[str]) -> None:
        self.origin_title = fields[0]
        self.origin_author = fields[1]
        self.trans_title = fields[2]
        self.trans_author = fields[3]


def sanitize_filename(file: str) -> str:
    return re.sub(r"[^\w\d\-_.]", "_", file)


def read_file_in_local_storage(
    origin_title: str = "",
    origin_author: str = "",
    folder: str = TRANSLATED_BOOK_CACHE
) -> str:
    # ensure dir exists
    os.makedirs(folder, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")

    # find file
    try:
        if origin_title and origin_author:
            file_name = rf"^{origin_title}___{origin_author}___.*"
        else:
            raise ValueError("Missing Title and Author")
        
        text = ""
        for entry in os.scandir(folder):
            if re.search(file_name, entry.name):
                new_file_name = entry.name.replace(r"{8}[0-9]_{6}[0-9]", ts)
                os.rename(entry.name, new_file_name)
                LRU_update(folder)
                with os.open(new_file_name, "w", encoding="utf-8") as f:
                    text = f.read()
                break
        return text
    except Exception as e:
        print(f"An error has occured: {e}")


def write_file_to_local_storage(
    translated_text: str,
    origin_title: str,
    origin_author: str,
    trans_title: str,
    trans_author: str,
    folder: str = TRANSLATED_BOOK_CACHE
) -> str:
    # ensure dir exists
    os.makedirs(folder, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")

    # filename sanitized and truncated to avoid OS limits
    file_name = f"{sanitize_filename(origin_title)[:40]}___{sanitize_filename(origin_author)[:30]}___{sanitize_filename(trans_title)[:40]}___{sanitize_filename(trans_author)[:30]}___{ts}.txt"
    path = Path(folder) / file_name

    with open(path, "w", encoding="utf-8") as f:
        f.write(translated_text)
    
    # Maintain only the LRU top 10
    LRU_update(folder, n=10)

    return path


def LRU_update(folder: str, n: int = 10) -> None:
    files = sorted(
                Path(folder).glob("*.txt"),
                key=lambda f: f.stat().st_atime,
                reverse=True
            )
    for f in files[n:]:
        os.remove(f)