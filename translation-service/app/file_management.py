import os
import re
import time
from pathlib import Path

from app.utils.str_utils import generate_file_name, generate_file_regex_pattern

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


def read_file_in_local_storage(
    origin_title: str = "",
    origin_author: str = "",
    folder: str = TRANSLATED_BOOK_CACHE
) -> str:
    # ensure dir exists
    os.makedirs(folder, exist_ok=True)

    # find file
    try:
        if origin_title and origin_author:
            regex_pattern = generate_file_regex_pattern(origin_title, origin_author)
        else:
            raise ValueError("Missing Title and Author")
        
        text = ""
        for entry in os.scandir(folder):
            if regex_pattern.match(entry.name):
                os.utime(entry.path)
                LRU_update(folder)
                with open(entry.path, "r", encoding="utf-8") as f:
                    text = f.read()
                break
        return text
    except Exception as e:
        print(f"An error has occured in file_management: {e}")


def write_file_to_local_storage(
    translated_text: str,
    origin_title: str,
    origin_author: str,
    trans_title: str,
    trans_author: str,
    folder: str = TRANSLATED_BOOK_CACHE
) -> str:
    print(f"[DEBUG] write_file_to_local_storage: cwd={os.getcwd()}")  # todo: remove when done
    # ensure dir exists
    os.makedirs(folder, exist_ok=True)
    print(f"Writing to path: {os.path.abspath(folder)}")  # todo: remove when done

    # filename sanitized and truncated to avoid OS limits
    file_name = generate_file_name(origin_title, origin_author, trans_title, trans_author)
    path = Path(folder) / file_name

    with open(path, "w", encoding="utf-8") as f:
        f.write(translated_text)
    print(f"[WRITE] File written!")  # todo: remove when done
    # Maintain only the LRU top 10
    os.utime(path)
    LRU_update(folder)

    return str(path)


def LRU_update(folder: str, n: int = 10) -> None:
    files = sorted(
                Path(folder).glob("*.txt"),
                key=lambda f: f.stat().st_atime,
                reverse=True
            )
    for f in files[n:]:
        os.remove(f)