import re
import time

def sanitize_filename(file: str) -> str:
    return re.sub(r"[^\w\d\-_.]", "_", file)


def generate_file_name(
    origin_title: str,
    origin_author: str,
    trans_title: str,
    trans_author: str,
    timestamp: str = None
) -> str:
    timestamp = timestamp or time.strftime("%Y%m%d_%H%M%S")
    file_name = (
        f"{sanitize_filename(origin_title)[:40]}___"
        f"{sanitize_filename(origin_author)[:30]}___"
        f"{sanitize_filename(trans_title)[:40]}___"
        f"{sanitize_filename(trans_author)[:30]}___"
        f"{timestamp}.txt"
    )
    return file_name


def generate_file_regex_pattern(
    origin_title: str,
    origin_author: str
) -> re.Pattern:
    origin_title = sanitize_filename(origin_title)[:40]
    origin_author = sanitize_filename(origin_author)[:30]
    pattern = (
        f"^{re.escape(origin_title)}___"
        f"{re.escape(origin_author)}___"
        r".*___"
        r".*___"
        r"\d{8}_\d{6}\.txt$"
    )
    return re.compile(pattern)


def canonize_str(s: str) -> str:
    # strip, lowercase, normalize, remove whitespace/punctuation for safety
    return "".join(filter(str.isalnum, s)).lower()